import logging
from typing import Generator, Optional, Union
from openstack.connection import Connection
from openstack.compute.v2.server import Server
from openstack.compute.v2.flavor import Flavor as OSFlavor

from osi_dump.importer.instance.instance_importer import InstanceImporter
from osi_dump.model.instance import Instance

# Set Server resource maximum microversion to 2.95 to prevent openstacksdk
# from negotiating 2.96 with clusters supporting 2.96 (avoiding Nova upstream KeyError bug)
Server._max_microversion = "2.95"

logger = logging.getLogger(__name__)


class OpenStackInstanceImporter(InstanceImporter):
    def __init__(self, connection: Connection):
        self.connection = connection
        self.projects = {}
        self.domains = {}
        self.flavors = {}
        self._metadata_fetched = False

        # Enforce microversion 2.95 on compute proxy and connection config
        try:
            if hasattr(self.connection, "compute") and hasattr(self.connection.compute, "default_microversion"):
                self.connection.compute.default_microversion = "2.95"
        except Exception as e:
            logger.debug(f"Could not set default_microversion in OpenStackInstanceImporter: {e}")

    def _fetch_metadata(self):
        """Pre-cache projects, domains, and flavors to avoid N+1 REST API calls."""
        if self._metadata_fetched:
            return

        logger.info(
            f"Pre-caching metadata (projects, domains, flavors) for {self.connection.auth['auth_url']}"
        )

        try:
            for p in self.connection.identity.projects():
                self.projects[p.id] = p
        except Exception as e:
            logger.warning(f"Could not pre-fetch projects: {e}")

        try:
            for d in self.connection.identity.domains():
                self.domains[d.id] = d
        except Exception as e:
            logger.warning(f"Could not pre-fetch domains: {e}")

        try:
            for f in self.connection.compute.flavors():
                self.flavors[f.id] = f
        except Exception as e:
            logger.warning(f"Could not pre-fetch flavors: {e}")

        self._metadata_fetched = True

    def _fetch_page(self, marker: Optional[str], limit: int) -> tuple[Optional[list], bool]:
        """Fetch a single page of servers with microversion 2.95.
        Returns (servers_list, is_server_error_500).
        """
        params = {
            "all_projects": True,
            "limit": limit,
        }
        if marker:
            params["marker"] = marker

        try:
            response = self.connection.compute.get(
                "/servers/detail",
                params=params,
                microversion="2.95",
            )
            # If not a real HTTP response (e.g. test mock), return None
            if not hasattr(response, "status_code") or not isinstance(response.status_code, int):
                return None, False

            if response.status_code == 200:
                data = response.json().get("servers", [])
                return data, False

            if response.status_code == 500:
                logger.warning(
                    f"HTTP 500 Server Error encountered on servers page (marker={marker}, limit={limit}): {getattr(response, 'text', '')}"
                )
                return None, True

            logger.warning(
                f"Unexpected status {response.status_code} on servers page (marker={marker}, limit={limit}): {getattr(response, 'text', '')}"
            )
            return None, False

        except Exception as e:
            is_500 = "500" in str(e) or "KeyError" in str(e)
            if is_500:
                logger.warning(f"HTTP 500 exception on servers page (marker={marker}, limit={limit}): {e}")
            else:
                logger.error(f"Error fetching servers page (marker={marker}, limit={limit}): {e}")
            return None, is_500

    def _skip_corrupt_server(self, marker: Optional[str], page_limit: int) -> tuple[Generator[dict, None, None], Optional[str]]:
        """Isolate and skip corrupt server(s) causing HTTP 500 within a page window.
        Uses limit=1 to safely iterate through healthy servers up to the corrupt one,
        skips the corrupt entry, and returns the next valid marker.
        """
        current_marker = marker
        recovered_servers = []

        logger.warning(
            f"Fault-tolerant isolation active: Stepping through instances one-by-one from marker={marker} to isolate corrupt VM..."
        )

        # Step 1-by-1 through the range that failed
        for step in range(page_limit):
            single_list, is_500 = self._fetch_page(marker=current_marker, limit=1)

            if single_list and len(single_list) > 0:
                # Successfully retrieved a healthy server in this batch
                good_server = single_list[0]
                recovered_servers.append(good_server)
                current_marker = good_server.get("id")
                # If retrieved fewer than 1 (empty), reached end
                if len(single_list) < 1:
                    break
            elif is_500:
                # Found the corrupt server! A single-item query starting after current_marker failed with 500
                logger.warning(
                    f"Identified corrupt instance immediately following marker={current_marker}. Skipping corrupt entry to preserve sheet integrity."
                )
                # Try to probe next ID using basic non-detail query (/servers)
                next_marker = self._probe_next_marker(current_marker)
                if next_marker:
                    logger.info(f"Resuming pagination after corrupt instance. New marker={next_marker}")
                    current_marker = next_marker
                else:
                    logger.warning(f"Could not determine next marker past {current_marker}. Returning recovered servers.")
                    return recovered_servers, current_marker
                break
            else:
                # No more items or end of list
                break

        return recovered_servers, current_marker

    def _probe_next_marker(self, current_marker: Optional[str]) -> Optional[str]:
        """Try fetching a basic non-detail server list (/servers) to find the ID after the corrupt server.
        When querying /servers?marker=<current_marker>&limit=2:
          - servers[0] is the corrupt server (which failed in /servers/detail)
          - servers[1] is the next healthy server after the corrupt one
        Returning servers[0]['id'] as the marker instructs Nova to resume starting after the corrupt server!
        If only 1 server is returned, servers[0] is the last server, so we return its ID to conclude cleanly.
        """
        try:
            params = {"all_projects": True, "limit": 2}
            if current_marker:
                params["marker"] = current_marker
            # Basic /servers does not load RequestSpec/extended attributes, avoiding the 500 bug
            resp = self.connection.compute.get("/servers", params=params, microversion="2.95")
            if hasattr(resp, "status_code") and resp.status_code == 200:
                servers = resp.json().get("servers", [])
                if servers:
                    corrupt_id = servers[0].get("id")
                    logger.warning(
                        f"Isolated corrupt server ID via basic /servers query: {corrupt_id}. Setting marker past it to continue dump."
                    )
                    return corrupt_id
        except Exception as e:
            logger.debug(f"Could not probe basic server list for marker: {e}")
        return None

    def _iter_servers_safely(self) -> Generator[Server, None, None]:
        """Fetch servers with microversion 2.95 and resilient per-instance fault tolerance.
        If a server causes HTTP 500 (e.g. corrupt DB / missing RequestSpec),
        isolate and skip that specific server, continuing to fetch the rest.
        """
        use_direct_get = hasattr(self.connection.compute, "get") and callable(self.connection.compute.get)

        if use_direct_get:
            marker = None
            limit = 1000
            total_imported = 0
            use_fallback_iterator = False

            while True:
                servers_data, is_500 = self._fetch_page(marker=marker, limit=limit)

                # Check if connection.compute.get is not a real HTTP proxy (e.g. mock in unit tests)
                if servers_data is None and not is_500 and total_imported == 0 and marker is None:
                    use_fallback_iterator = True
                    break

                # If page succeeded
                if servers_data is not None:
                    if not servers_data:
                        logger.info(f"Completed instance fetching. Total instances retrieved: {total_imported}")
                        return

                    for raw_s in servers_data:
                        yield Server.existing(connection=self.connection, **raw_s)
                        total_imported += 1

                    marker = servers_data[-1].get("id")
                    if len(servers_data) < limit:
                        logger.info(f"Reached last page of instances. Total instances retrieved: {total_imported}")
                        return
                    continue

                # If page failed with 500, isolate and skip corrupt VM
                if is_500:
                    recovered_servers, next_marker = self._skip_corrupt_server(marker=marker, page_limit=limit)
                    for raw_s in recovered_servers:
                        yield Server.existing(connection=self.connection, **raw_s)
                        total_imported += 1

                    if not next_marker or next_marker == marker:
                        logger.warning(
                            f"Fault-tolerant pagination reached boundary at marker={marker}. Stopping gracefully. Total retrieved: {total_imported}"
                        )
                        return

                    marker = next_marker
                    continue

                # Any other unrecoverable page failure
                logger.error(f"Stopping instance retrieval gracefully at marker={marker}. Total retrieved: {total_imported}")
                return

            if not use_fallback_iterator:
                return

        # Fallback to compute.servers() iterator for mock objects or unsupported adapters
        try:
            logger.info("Using standard compute.servers() iterator fallback with microversion 2.95...")
            servers_iter = iter(
                self.connection.compute.servers(details=True, all_projects=True, microversion="2.95")
            )
            while True:
                try:
                    server = next(servers_iter)
                    yield server
                except StopIteration:
                    break
                except Exception as iter_err:
                    logger.error(
                        f"Exception during server streaming iterator: {iter_err}. Stopping gracefully to preserve gathered servers."
                    )
                    break
        except Exception as e:
            logger.error(f"Error initializing compute.servers iterator: {e}")

    def import_instances(self) -> Generator[Instance, None, None]:
        """Import instances information from Openstack as a generator."""

        logger.info(f"Importing instances for {self.connection.auth['auth_url']}")
        self._fetch_metadata()

        for server in self._iter_servers_safely():
            try:
                yield self._get_instance_info(server)
            except Exception as e:
                server_id = getattr(server, "id", "unknown")
                server_name = getattr(server, "name", "unknown")
                logger.error(
                    f"Error processing instance ID {server_id} (Name: {server_name}): {e}"
                )
                continue

        logger.info(
            f"Finished importing instances for {self.connection.auth['auth_url']}"
        )

    def _get_project_and_domain(self, project_id: Optional[str]):
        if not project_id:
            return None, None, None

        project = self.projects.get(project_id)
        if not project:
            try:
                project = self.connection.identity.get_project(project_id)
                if project:
                    self.projects[project_id] = project
            except Exception as e:
                logger.warning(
                    f"Unable to fetch project {project_id}: {e}"
                )

        project_name = project.name if project else None
        domain_name = None
        domain_id = getattr(project, "domain_id", None) if project else None

        if domain_id:
            domain = self.domains.get(domain_id)
            if not domain:
                try:
                    domain = self.connection.identity.get_domain(domain_id)
                    if domain:
                        self.domains[domain_id] = domain
                except Exception as e:
                    logger.warning(
                        f"Unable to fetch domain {domain_id}: {e}"
                    )
            domain_name = domain.name if domain else None

        return project_id, project_name, domain_name

    def _get_instance_info(self, server: Server) -> Instance:
        server_name = getattr(server, "name", None)
        server_id = getattr(server, "id", None)

        project_id, project_name, domain_name = self._get_project_and_domain(
            getattr(server, "project_id", None)
        )

        private_v4_ips = []
        floating_ip = None

        try:
            if getattr(server, "addresses", None):
                for ips in server.addresses.values():
                    for ip in ips:
                        if ip.get("OS-EXT-IPS:type") == "fixed":
                            private_v4_ips.append(ip.get("addr"))
                        elif ip.get("OS-EXT-IPS:type") == "floating":
                            floating_ip = ip.get("addr")
        except Exception as e:
            logger.warning(
                f"Unable to obtain IP address information for instance {server_name}: {e}"
            )

        vgpus = None
        vgpu_type = None
        vgpu_metadata_property = "pci_passthrough:alias"

        flavor_dict = getattr(server, "flavor", {}) or {}
        flavor_id = flavor_dict.get("id")
        flavor_ram = flavor_dict.get("ram", 0)
        flavor_vcpus = flavor_dict.get("vcpus", 0)

        if flavor_id:
            try:
                flavor = self.flavors.get(flavor_id)
                if not flavor:
                    flavor = self.connection.get_flavor(name_or_id=flavor_id)
                    if flavor:
                        self.flavors[flavor_id] = flavor

                if flavor and getattr(flavor, "extra_specs", None):
                    vgpu_prop = flavor.extra_specs.get(vgpu_metadata_property)
                    if vgpu_prop:
                        vgpu_props = str(vgpu_prop).split(":")
                        if len(vgpu_props) >= 2:
                            vgpu_type = vgpu_props[0]
                            vgpus = int(vgpu_props[1])
            except Exception:
                pass

        image_dict = getattr(server, "image", None) or {}
        image_id = image_dict.get("id") if isinstance(image_dict, dict) else None

        created_at_val = getattr(server, "created_at", "") or ""
        updated_at_val = getattr(server, "updated_at", "") or ""

        return Instance(
            instance_id=str(server_id) if server_id else "",
            instance_name=str(server_name) if server_name is not None else None,
            project_id=project_id,
            project_name=project_name,
            domain_name=domain_name,
            private_v4_ips=[str(ip) for ip in private_v4_ips if ip is not None] if private_v4_ips else [],
            floating_ip=str(floating_ip) if floating_ip is not None else None,
            status=str(getattr(server, "status", "")),
            hypervisor=str(server.hypervisor_hostname) if getattr(server, "hypervisor_hostname", None) is not None else None,
            ram=int(flavor_ram or 0),
            vcpus=int(flavor_vcpus or 0),
            created_at=str(created_at_val),
            updated_at=str(updated_at_val),
            user_id=str(server.user_id) if getattr(server, "user_id", None) is not None else None,
            vgpus=vgpus,
            vgpu_type=vgpu_type,
            image_id=image_id,
            flavor_id=str(flavor_id) if flavor_id is not None else None,
        )