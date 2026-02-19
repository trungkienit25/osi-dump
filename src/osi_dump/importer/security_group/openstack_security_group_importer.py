from typing import Any, Generator, Dict
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.security_group import SecurityGroupModel

class OpenStackSecurityGroupImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[SecurityGroupModel, None, None]:
        # Phase 1: Cache Projects
        project_map: Dict[str, str] = {}
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
        except Exception:
            pass

        # Phase 2: Fetch Security Groups
        try:
            sgs = self.conn.network.security_groups()
            for sg in sgs:
                try:
                    yield SecurityGroupModel(
                        id=sg.id,
                        name=sg.name,
                        description=sg.description,
                        project_id=sg.project_id,
                        project_name=project_map.get(sg.project_id),
                        created_at=sg.created_at
                    )
                except Exception as e:
                    self.logger.error(f"Error processing security group {sg.id}: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list security groups: {e}")