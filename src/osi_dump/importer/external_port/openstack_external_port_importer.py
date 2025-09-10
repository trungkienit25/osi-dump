import logging
import ipaddress
from typing import Generator
from openstack.connection import Connection
from openstack.network.v2.port import Port as OSPort
from openstack.network.v2.subnet import Subnet as OSSubnet
from openstack.network.v2.network import Network as OSNetwork

from osi_dump.importer.external_port.external_port_importer import ExternalPortImporter
from osi_dump.model.external_port import ExternalPort
import osi_dump.api.neutron as osi_neutron

logger = logging.getLogger(__name__)

class OpenStackExternalPortImporter(ExternalPortImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def _get_external_ports_stream(self) -> Generator[OSPort, None, None]:
        """Generator để lấy về từng port trên các network ngoại vi."""
        try:
            external_networks = self.connection.network.networks(is_router_external=True)
            
            for network in external_networks:
                ports_on_network = self.connection.network.ports(network_id=network.id)
                yield from ports_on_network 
        except Exception as e:
            logger.error(f"Failed to stream external networks/ports: {e}")


    def import_external_ports(self) -> Generator[ExternalPort, None, None]:
        logger.info(f"Importing external ports for {self.connection.auth['auth_url']}")
        
        for os_port in self._get_external_ports_stream():
            yield self._get_external_port_info(os_port)
            
        logger.info(f"Finished importing external ports for {self.connection.auth['auth_url']}")

    def _get_external_port_info(self, external_port: OSPort) -> ExternalPort:
        subnet_id = None
        ip_address = None
        subnet_cidr = None

        if external_port.fixed_ips:
            ip_address = external_port.fixed_ips[0].get("ip_address")
            subnet_id = external_port.fixed_ips[0].get("subnet_id")

        if subnet_id:
            try:
                subnet: OSSubnet = self.connection.get_subnet(subnet_id)
                if subnet:
                    subnet_cidr = subnet.cidr
            except Exception as e:
                logger.warning(f"Could not get subnet cidr for {subnet_id}: {e}")

        project_id = external_port.project_id
        mapped_device_projects = ["network:floatingip", "network:router_gateway"]
        if external_port.device_owner in mapped_device_projects and external_port.device_id:
            project_id = self._map_project_id(
                device_owner=external_port.device_owner,
                device_id=external_port.device_id,
            )
        
        network: OSNetwork = self.connection.get_network(external_port.network_id)
        vlan_id = network.provider_segmentation_id if network else None
        
        return ExternalPort(
            port_id=external_port.id,
            project_id=project_id,
            network_id=external_port.network_id,
            network_name=network.name if network else None,
            subnet_id=subnet_id,
            subnet_cidr=subnet_cidr,
            ip_address=ip_address,
            allowed_address_pairs=external_port.allowed_address_pairs,
            device_id=external_port.device_id,
            device_owner=external_port.device_owner,
            status=external_port.status,
            vlan_id=vlan_id
        )

    def _map_project_id(self, device_owner: str, device_id: str) -> str:
        try:
            if device_owner == "network:router_gateway":
                return osi_neutron.get_router_project(self.connection, router_id=device_id)
            elif device_owner == "network:floatingip":
                return osi_neutron.get_floating_ip_project(self.connection, floating_ip_id=device_id)
        except Exception as e:
            logger.warning(f"Could not map project ID for {device_owner}:{device_id}: {e}")
        return None
