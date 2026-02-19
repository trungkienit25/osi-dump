from pathlib import Path
from typing import Any, Generator, List
import logging

from osi_dump.core.interfaces import IBatchHandler
from osi_dump.core.config import AppConfig
from osi_dump.services.registry import HandlerRegistry
from osi_dump.importer.instance.openstack_instance_importer import OpenStackInstanceImporter
from osi_dump.model.instance import InstanceModel

# -----------------------------------------------------------------------------
# Mock Exporter (Internal for this step)
# -----------------------------------------------------------------------------
class MockExcelExporter:
    """
    A temporary mock exporter to simulate writing data.
    """
    def export_data(self, data: Generator[Any, None, None]) -> None:
        count = 0
        for item in data:
            count += 1
            # In a real exporter, we would write 'item' to a file.
        logging.getLogger(__name__).info(f"[MockExporter] Exported {count} items.")

# -----------------------------------------------------------------------------
# Batch Handler
# -----------------------------------------------------------------------------
@HandlerRegistry.register
class InstanceBatchHandler(IBatchHandler):
    """
    Orchestrates the extraction and export of OpenStack Instances.
    """
    
    @property
    def resource_name(self) -> str:
        return "instance"

    def is_enabled(self, config: AppConfig) -> bool:
        return config.resources.instance_enabled

    def process(self, connections: List[Any], output_dir: Path) -> Path:
        """
        Processes instances across multiple OpenStack connections.
        """
        logger = logging.getLogger(__name__)
        output_file = output_dir / f"instances_dump.xlsx" # Dummy filename
        
        logger.info(f"Starting batch processing for: {self.resource_name}")
        
        # In a real scenario, we might merge data from all connections.
        # For simplicity in this step, we just iterate them.
        
        all_instances_generator = self._merge_generators(connections)
        
        exporter = MockExcelExporter()
        exporter.export_data(all_instances_generator)
        
        logger.info(f"Finished processing {self.resource_name}. Output: {output_file}")
        return output_file

    def _merge_generators(self, connections: List[Any]) -> Generator[InstanceModel, None, None]:
        """
        Helper to yield instances from all connections sequentially.
        """
        for conn in connections:
            importer = OpenStackInstanceImporter(conn)
            yield from importer.fetch_data()