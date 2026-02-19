from pathlib import Path
from typing import Any, List
import logging
from osi_dump.core.interfaces import IBatchHandler
from osi_dump.core.config import AppConfig
from osi_dump.services.registry import HandlerRegistry
from osi_dump.importer.router.openstack_router_importer import OpenStackRouterImporter
from osi_dump.exporter.excel_exporter import PandasExcelExporter

@HandlerRegistry.register
class RouterBatchHandler(IBatchHandler):
    @property
    def resource_name(self) -> str:
        return "router"

    def is_enabled(self, config: AppConfig) -> bool:
        return config.resources.router_enabled

    def process(self, connections: List[Any], output_dir: Path) -> Path:
        logger = logging.getLogger(__name__)
        output_file = output_dir / "osi_dump_report.xlsx"
        logger.info(f"Starting batch processing for: {self.resource_name}")
        
        def generator():
            for conn in connections:
                yield from OpenStackRouterImporter(conn).fetch_data()

        exporter = PandasExcelExporter(output_file, sheet_name=self.resource_name)
        exporter.export_data(generator())
        return output_file
