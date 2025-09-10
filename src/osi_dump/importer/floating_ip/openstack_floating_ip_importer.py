import logging
from typing import Generator
from openstack.connection import Connection
from openstack.network.v2.floating_ip import FloatingIP as OSFloatingIP

from osi_dump.importer.floating_ip.floating_ip_importer import FloatingIPImporter
from osi_dump.model.floating_ip import FloatingIP

logger = logging.getLogger(__name__)

class OpenStackFloatingIPImporter(FloatingIPImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_floating_ips(self) -> Generator[FloatingIP, None, None]:
        logger.info(f"Importing floating ips for {self.connection.auth['auth_url']}")
        try:
            osfloating_ip_iterator = self.connection.list_floating_ips()
            
            for floating_ip in osfloating_ip_iterator:
                yield self._get_floating_ip_info(floating_ip)

        except Exception as e:
            logger.error(f"Cannot fetch floating IPs for {self.connection.auth['auth_url']}: {e}")
            return 

        logger.info(f"Finished importing floating ips for {self.connection.auth['auth_url']}")

    def _get_floating_ip_info(self, floating_ip: OSFloatingIP) -> FloatingIP:
        return FloatingIP(
            floating_ip_id=floating_ip.id,
            project_id=floating_ip.project_id,
            floating_ip_address=floating_ip.floating_ip_address,
            floating_network=floating_ip.floating_network_id,
            fixed_ip_address=floating_ip.fixed_ip_address,
            router_id=floating_ip.router_id,
            port_id=floating_ip.port_id,
            status=floating_ip.status,
            created_at=floating_ip.created_at,
            updated_at=floating_ip.updated_at,
        )
