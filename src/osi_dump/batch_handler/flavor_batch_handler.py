import logging
from openstack.connection import Connection

from osi_dump.exporter.flavor.flavor_exporter import FlavorExporter
from osi_dump.exporter.flavor.excel_flavor_exporter import ExcelFlavorExporter
from osi_dump.importer.flavor.flavor_importer import FlavorImporter
from osi_dump.importer.flavor.openstack_flavor_importer import OpenStackFlavorImporter
from osi_dump import util

logger = logging.getLogger(__name__)

class FlavorBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[tuple[FlavorImporter, FlavorExporter]] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackFlavorImporter(connection)
            sheet_name = f"{util.extract_hostname(connection.auth['auth_url'])}-flavor"
            exporter = ExcelFlavorExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(importer=importer, exporter=exporter)

    def add_importer_exporter(self, importer: FlavorImporter, exporter: FlavorExporter):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                flavors_generator = importer.import_flavors()
                exporter.export_flavors(flavors=flavors_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")
