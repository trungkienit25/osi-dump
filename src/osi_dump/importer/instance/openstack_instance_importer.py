import logging
from typing import Generator, Optional, Union
from openstack.connection import Connection
from openstack.compute.v2.server import Server
from openstack.compute.v2.flavor import Flavor as OSFlavor

from osi_dump.importer.instance.instance_importer import InstanceImporter
from osi_dump.model.instance import Instance

logger = logging.getLogger(__name__)


class OpenStackInstanceImporter(InstanceImporter):
    def __init__(self, connection: Connection):
        self.connection = connection
        self.projects = {}
        self.domains = {}
        self.flavors = {}
        self._metadata_fetched = False

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

    def _iter_servers_safely(self) -> Generator[Server, None, None]:
        """Fetch servers page by page using the cluster's highest microversion.
        If any specific page fails with HTTP 500 (e.g. Nova upstream 2.96 KeyError bug),
        transparently retry that exact page with microversion 2.95 and continue.
        """
        # Check if direct REST endpoint retrieval is supported
        use_direct_get = hasattr(self.connection.compute, "get") and callable(self.connection.compute.get)

        if use_direct_get:
            marker = None
            limit = 1000
            consecutive_errors = 0
            max_consecutive_errors = 3
            use_fallback_servers = False

            while True:
                params = {
                    "all_projects": True,
                    "limit": limit,
                }
                if marker:
                    params["marker"] = marker

                servers_data = None

                # Attempt 1: Fetch current page with default (highest) microversion
                try:
                    response = self.connection.compute.get(
                        "/servers/detail",
                        params=params,
                    )
                    # If mock/proxy object without int status_code, switch to fallback
                    if not hasattr(response, "status_code") or not isinstance(response.status_code, int):
                        use_fallback_servers = True
                        break

                    if response.status_code == 200:
                        servers_data = response.json().get("servers", [])
                    elif response.status_code == 500:
                        logger.warning(
                            f"Page with marker={marker} returned 500 under default microversion. "
                            f"Retrying this page with microversion 2.95..."
                        )
                    else:
                        logger.warning(
                            f"Page with marker={marker} returned status {response.status_code}: {getattr(response, 'text', '')}"
                        )
                except Exception as e:
                    if "500" in str(e) or "KeyError" in str(e):
                        logger.warning(
                            f"Page with marker={marker} raised 500 ({e}). Retrying with microversion 2.95..."
                        )
                    else:
                        logger.error(f"Error fetching page (marker={marker}): {e}")

                # Attempt 2: If attempt 1 failed with 500 or error, retry this exact page with 2.95
                if servers_data is None:
                    try:
                        response_fb = self.connection.compute.get(
                            "/servers/detail",
                            params=params,
                            microversion="2.95",
                        )
                        if hasattr(response_fb, "status_code") and response_fb.status_code == 200:
                            servers_data = response_fb.json().get("servers", [])
                            logger.info(f"Successfully recovered page with marker={marker} using microversion 2.95.")
                        else:
                            err_code = getattr(response_fb, "status_code", "unknown")
                            logger.error(f"Fallback page with marker={marker} failed with status {err_code}")
                    except Exception as fb_err:
                        logger.error(f"Fallback page with marker={marker} raised error: {fb_err}")

                # If both attempts failed, check error threshold
                if servers_data is None:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("Too many consecutive page errors. Stopping server import safely.")
                        return
                    return

                consecutive_errors = 0
                if not servers_data:
                    return

                for raw_s in servers_data:
                    yield Server.existing(
                        connection=self.connection,
                        **raw_s,
                    )

                marker = servers_data[-1].get("id")
                if len(servers_data) < limit:
                    return

            if not use_fallback_servers:
                return

        # Fallback to compute.servers() iterator if direct REST get is not available (e.g. unit test mocks)
        try:
            for server in self.connection.compute.servers(details=True, all_projects=True):
                yield server
        except Exception as e:
            logger.error(f"Error fetching servers via compute.servers: {e}")

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