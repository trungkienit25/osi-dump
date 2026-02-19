from typing import Any, Generator, Dict
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.floating_ip import FloatingIPModel

class OpenStackFloatingIPImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[FloatingIPModel, None, None]:
        # Phase 1: Cache Projects
        project_map: Dict[str, str] = {}
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
        except Exception:
            pass

        # Phase 2: Fetch Floating IPs
        try:
            fips = self.conn.network.ips()
            for fip in fips:
                try:
                    yield FloatingIPModel(
                        id=fip.id,
                        floating_ip_address=fip.floating_ip_address,
                        status=fip.status,
                        router_id=fip.router_id,
                        port_id=fip.port_id,
                        fixed_ip_address=fip.fixed_ip_address,
                        project_id=fip.project_id,
                        project_name=project_map.get(fip.project_id),
                        created_at=fip.created_at
                    )
                except Exception as e:
                    self.logger.error(f"Error processing floating ip {fip.id}: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list floating ips: {e}")
