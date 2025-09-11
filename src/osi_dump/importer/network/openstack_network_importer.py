import logging
from typing import Generator
from openstack.network.v2.network import Network as OSNetwork
from openstack.network.v2.subnet import Subnet as OSSubnet
from openstack.connection import Connection

from osi_dump.importer.network.network_importer import NetworkImporter 
from osi_dump.model.network import Network 

logger = logging.getLogger(__name__)

class OpenStackNetworkImporter(NetworkImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_networks(self) -> Generator[Network, None, None]:
        logger.info(f"Importing networks for {self.connection.auth['auth_url']}")
        try:
            network_iterator = self.connection.list_networks()

            for network in network_iterator:
                yield self._get_network_info(network)

        except Exception as e:
            logger.error(f"Cannot fetch networks for {self.connection.auth['auth_url']}: {e}")
            return 

        logger.info(f"Finished importing networks for {self.connection.auth['auth_url']}")

    def _get_network_info(self, network: OSNetwork) -> Network:
        subnets = self._get_subnets_info(subnet_ids=network.subnet_ids)

        return Network(
            network_id=network.id,
            project_id=network.project_id, 
            name=network.name, 
            mtu=network.mtu, 
            port_security_enabled=network.is_port_security_enabled,
            network_type=network.provider_network_type, 
            physical_network=network.provider_physical_network,
            segmentation_id=network.provider_segmentation_id,
            status=network.status, 
            shared=network.is_shared,
            created_at=network.created_at,
            updated_at=network.updated_at,
            subnets=subnets
        )
    
    def _get_subnets_info(self, subnet_ids: list[str]) -> list[dict]: 
        subnets = []
        if not subnet_ids:
            return subnets

        for subnet_id in subnet_ids: 
            try:
                os_subnet: OSSubnet = self.connection.get_subnet(subnet_id) 
                if os_subnet: 
                    subnets.append({
                        "id": os_subnet.id, 
                        "cidr": os_subnet.cidr
                    })
            except Exception as e:
                logger.warning(f"Could not get info for subnet {subnet_id}: {e}")
                
        return subnets