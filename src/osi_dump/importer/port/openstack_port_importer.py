from typing import Any, Generator, Dict
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.port import PortModel

class OpenStackPortImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[PortModel, None, None]:
        # Phase 1: Cache Projects & Networks
        project_map: Dict[str, str] = {}
        network_map: Dict[str, str] = {}
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
            
            for net in self.conn.network.networks():
                network_map[net.id] = net.name
        except Exception:
            pass

        # Phase 2: Fetch Ports
        try:
            ports = self.conn.network.ports()
            for port in ports:
                try:
                    yield PortModel(
                        id=port.id,
                        name=port.name,
                        status=port.status,
                        mac_address=port.mac_address,
                        network_id=port.network_id,
                        network_name=network_map.get(port.network_id),
                        project_id=port.project_id,
                        project_name=project_map.get(port.project_id),
                        device_id=port.device_id,
                        device_owner=port.device_owner,
                        fixed_ips=port.fixed_ips,
                        created_at=port.created_at
                    )
                except Exception as e:
                    self.logger.error(f"Error processing port {port.id}: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list ports: {e}")
