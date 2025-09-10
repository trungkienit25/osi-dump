import logging
from openstack.connection import Connection

from osi_dump.exporter.floating_ip.floating_ip_exporter import FloatingIPExporter
from osi_dump.exporter.floating_ip.excel_floating_ip_exporter import ExcelFloatingIPExporter
from osi_dump.importer.floating_ip.floating_ip_importer import FloatingIPImporter
from osi_dump.importer.floating_ip.openstack_floating_ip_importer import OpenStackFloatingIPImporter
from osi_dump import util

logger = logging.getLogger(__name__)

class FloatingIPBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[
            tuple[FloatingIPImporter, FloatingIPExporter]
        ] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackFloatingIPImporter(connection)
            sheet_name = (
                f"{util.extract_hostname(connection.auth['auth_url'])}-floating-ip"
            )
            exporter = ExcelFloatingIPExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(importer=importer, exporter=exporter)

    def add_importer_exporter(
        self, importer: FloatingIPImporter, exporter: FloatingIPExporter
    ):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                floating_ips_generator = importer.import_floating_ips()
                exporter.export_floating_ips(floating_ips=floating_ips_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")
