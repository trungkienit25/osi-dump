from typing import Any, Generator, Dict
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.image import ImageModel

class OpenStackImageImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[ImageModel, None, None]:
        # Phase 1: Cache Projects
        project_map: Dict[str, str] = {}
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
        except Exception:
            pass

        # Phase 2: Fetch Images
        try:
            images = self.conn.image.images()
            for img in images:
                try:
                    yield ImageModel(
                        id=img.id,
                        name=img.name,
                        status=img.status,
                        size_bytes=img.size,
                        container_format=img.container_format,
                        disk_format=img.disk_format,
                        visibility=img.visibility,
                        project_id=img.owner or "",
                        project_name=project_map.get(img.owner),
                        created_at=img.created_at
                    )
                except Exception as e:
                    self.logger.error(f"Error processing image {img.id}: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list images: {e}")
