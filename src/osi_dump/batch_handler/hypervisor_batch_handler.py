import logging
from openstack.connection import Connection

from osi_dump.exporter.hypervisor.hypervisor_exporter import HypervisorExporter
from osi_dump.exporter.hypervisor.excel_hypervisor_exporter import ExcelHypervisorExporter
from osi_dump.importer.hypervisor.hypervisor_importer import HypervisorImporter
from osi_dump.importer.hypervisor.openstack_hypervisor_importer import OpenStackHypervisorImporter
from osi_dump import util

logger = logging.getLogger(__name__)

class HypervisorBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[
            tuple[HypervisorImporter, HypervisorExporter]
        ] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackHypervisorImporter(connection)
            sheet_name = (
                f"{util.extract_hostname(connection.auth['auth_url'])}-hypervisor"
            )
            exporter = ExcelHypervisorExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(importer=importer, exporter=exporter)

    def add_importer_exporter(
        self, importer: HypervisorImporter, exporter: HypervisorExporter
    ):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                hypervisors_generator = importer.import_hypervisors()
                exporter.export_hypervisors(hypervisors=hypervisors_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")