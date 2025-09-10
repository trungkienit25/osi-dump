import logging
from openstack.connection import Connection

from osi_dump.exporter.router.router_exporter import RouterExporter
from osi_dump.exporter.router.excel_router_exporter import ExcelRouterExporter
from osi_dump.importer.router.router_importer import RouterImporter
from osi_dump.importer.router.openstack_router_importer import OpenStackRouterImporter
from osi_dump import util

logger = logging.getLogger(__name__)

class RouterBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[tuple[RouterImporter, RouterExporter]] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackRouterImporter(connection)
            sheet_name = f"{util.extract_hostname(connection.auth['auth_url'])}-router"
            exporter = ExcelRouterExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(importer=importer, exporter=exporter)

    def add_importer_exporter(self, importer: RouterImporter, exporter: RouterExporter):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                routers_generator = importer.import_routers()
                exporter.export_routers(routers=routers_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")
