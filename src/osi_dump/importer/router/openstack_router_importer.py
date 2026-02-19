from typing import Any, Generator, Dict
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.router import RouterModel

class OpenStackRouterImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[RouterModel, None, None]:
        # Phase 1: Cache Projects
        project_map: Dict[str, str] = {}
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
        except Exception:
            pass

        # Phase 2: Fetch Routers
        try:
            routers = self.conn.network.routers()
            for r in routers:
                try:
                    yield RouterModel(
                        id=r.id,
                        name=r.name,
                        status=r.status,
                        admin_state_up=r.admin_state_up,
                        project_id=r.project_id,
                        project_name=project_map.get(r.project_id),
                        external_gateway_info=r.external_gateway_info,
                        created_at=r.created_at
                    )
                except Exception as e:
                    self.logger.error(f"Error processing router {r.id}: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list routers: {e}")
