from typing import Any, Generator
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.project import ProjectModel

class OpenStackProjectImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[ProjectModel, None, None]:
        self.logger.info("Fetching Projects...")
        try:
            projects = self.conn.identity.projects()
            for p in projects:
                try:
                    yield ProjectModel(
                        id=p.id,
                        name=p.name,
                        domain_id=p.domain_id,
                        is_enabled=p.is_enabled,
                        description=p.description
                    )
                except Exception as e:
                    self.logger.error(f"Error processing project {p.id}: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list projects: {e}")