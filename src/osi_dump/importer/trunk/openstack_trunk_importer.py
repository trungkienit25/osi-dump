from typing import Any, Generator, Dict
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.trunk import TrunkModel

class OpenStackTrunkImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[TrunkModel, None, None]:
        # Phase 1: Cache Projects
        project_map: Dict[str, str] = {}
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
        except Exception:
            pass

        # Phase 2: Fetch Trunks
        try:
            trunks = self.conn.network.trunks()
            for trunk in trunks:
                try:
                    yield TrunkModel(
                        id=trunk.id,
                        name=trunk.name,
                        status=trunk.status,
                        port_id=trunk.port_id,
                        project_id=trunk.project_id,
                        project_name=project_map.get(trunk.project_id),
                        sub_ports=trunk.sub_ports,
                        created_at=trunk.created_at
                    )
                except Exception as e:
                    self.logger.error(f"Error processing trunk {trunk.id}: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list trunks: {e}")