from typing import Any, Generator
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.flavor import FlavorModel

class OpenStackFlavorImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[FlavorModel, None, None]:
        self.logger.info("Fetching Flavors...")
        try:
            # Flavors are usually global, no complex dependencies
            flavors = self.conn.compute.flavors(details=True)
            for f in flavors:
                try:
                    yield FlavorModel(
                        id=f.id,
                        name=f.name,
                        vcpus=f.vcpus,
                        ram=f.ram,
                        disk=f.disk,
                        is_public=f.is_public
                    )
                except Exception as e:
                    self.logger.error(f"Error processing flavor {f.id}: {e}")
                    continue
        except Exception as e:
            self.logger.critical(f"Failed to list flavors: {e}")
