import logging
from openstack.connection import Connection
from osi_dump import util
from osi_dump.importer.external_port.openstack_external_port_importer import (
    OpenStackExternalPortImporter,
)
from osi_dump.exporter.external_port.excel_external_port_exporter import (
    ExcelExternalPortExporter,
)
logger = logging.getLogger(__name__)

class ExternalPortBatchHandler:
    def __init__(self):
        self._importer_exporter_list = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackExternalPortImporter(connection)
            sheet_name = f"{util.extract_hostname(connection.auth['auth_url'])}-ex-port"
            exporter = ExcelExternalPortExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(importer=importer, exporter=exporter)

    def add_importer_exporter(self, importer, exporter):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                ports_generator = importer.import_external_ports()
                exporter.export_external_ports(external_ports=ports_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")
