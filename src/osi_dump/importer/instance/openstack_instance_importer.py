import logging
from typing import Generator
from openstack.connection import Connection
from openstack.compute.v2.server import Server
from openstack.compute.v2.flavor import Flavor as OSFlavor

from osi_dump.importer.instance.instance_importer import InstanceImporter
from osi_dump.model.instance import Instance

logger = logging.getLogger(__name__)


class OpenStackInstanceImporter(InstanceImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_instances(self) -> Generator[Instance, None, None]:
        """Import instances information from Openstack as a generator."""

        logger.info(f"Importing instances for {self.connection.auth['auth_url']}")
        try:
            server_iterator = self.connection.compute.servers(details=True, all_projects=True)
            
            for server in server_iterator:
                yield self._get_instance_info(server)

        except Exception as e:
            logger.error(f"Cannot fetch instances for {self.connection.auth['auth_url']}: {e}")
            return 
        
        logger.info(f"Finished importing instances for {self.connection.auth['auth_url']}")

    def _get_instance_info(self, server: Server) -> Instance:
        project_name = None
        project_id = None
        project = None 
        try:
            project = self.connection.identity.get_project(server.project_id)
            project_name = project.name
            project_id = project.id
        except Exception as e:
            logger.warning(
                f"Unable to obtain project name for instance: {server.name}: {e}"
            )

        domain_name = None
        if project: 
            try:
                domain = self.connection.identity.get_domain(project.domain_id)
                domain_name = domain.name
            except Exception as e:
                logger.warning(
                    f"Unable to obtain domain name for instance {server.name}: {e}"
                )

        private_v4_ips = []
        floating_ip = None

        try:
            for ips in server.addresses.values():
                for ip in ips:
                    if ip["OS-EXT-IPS:type"] == "fixed":
                        private_v4_ips.append(ip["addr"])
                    elif ip["OS-EXT-IPS:type"] == "floating":
                        floating_ip = ip["addr"]
        except Exception as e:
            logger.warning(
                f"Unable to obtain IP address information for instance {server.name}: {e}"
            )

        vgpus = None
        vgpu_type = None
        vgpu_metadata_property = "pci_passthrough:alias"

        try:
            flavor: OSFlavor = self.connection.get_flavor(
                name_or_id=server.flavor["id"]
            )
            if flavor and flavor.extra_specs:
                vgpu_prop: str = flavor.extra_specs.get(vgpu_metadata_property)
                if vgpu_prop:
                    vgpu_props = vgpu_prop.split(":")
                    vgpu_type = vgpu_props[0]
                    vgpus = int(vgpu_props[1])
        except Exception:
            pass
        
        image_id = server.image.get("id") if server.image else None
        flavor_id = server.flavor.get("id") if server.flavor else None
        
        return Instance(
            instance_id=server.id,
            instance_name=server.name,
            project_id=project_id,
            project_name=project_name,
            domain_name=domain_name,
            private_v4_ips=private_v4_ips,
            floating_ip=floating_ip,
            status=server.status,
            hypervisor=server.hypervisor_hostname,
            ram=server.flavor["ram"],
            vcpus=server.flavor["vcpus"],
            created_at=server.created_at,
            updated_at=server.updated_at,
            user_id=server.user_id,
            vgpus=vgpus,
            vgpu_type=vgpu_type,
            image_id=image_id, 
            flavor_id=flavor_id
        )