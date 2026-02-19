from typing import Any, Generator, Dict
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.network import NetworkModel

class OpenStackNetworkImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[NetworkModel, None, None]:
        # Phase 1: Cache Projects
        project_map: Dict[str, str] = {}
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
        except Exception:
            pass

        # Phase 2: Fetch Networks
        try:
            networks = self.conn.network.networks()
            for net in networks:
                try:
                    yield NetworkModel(
                        id=net.id,
                        name=net.name,
                        status=net.status,
                        is_shared=net.is_shared,
                        is_admin_state_up=net.is_admin_state_up,
                        is_router_external=net.is_router_external,
                        project_id=net.project_id,
                        project_name=project_map.get(net.project_id),
                        subnets=net.subnet_ids or [],
                        created_at=net.created_at
                    )
                except Exception as e:
                    self.logger.error(f"Error processing network {net.id}: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list networks: {e}")