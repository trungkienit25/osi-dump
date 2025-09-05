import logging
from openstack.connection import Connection
from osi_dump import util
from osi_dump.exporter.instance.excel_instance_exporter import ExcelInstanceExporter
from osi_dump.exporter.instance.instance_exporter import InstanceExporter
from osi_dump.importer.instance.instance_importer import InstanceImporter
from osi_dump.importer.instance.openstack_instance_importer import OpenStackInstanceImporter

logger = logging.getLogger(__name__)

class InstanceBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[
            tuple[InstanceImporter, InstanceExporter]
        ] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            instance_importer = OpenStackInstanceImporter(connection)
            sheet_name = (
                f"{util.extract_hostname(connection.auth['auth_url'])}-instance"
            )
            instance_exporter = ExcelInstanceExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(
                importer=instance_importer, exporter=instance_exporter
            )

    def add_importer_exporter(
        self, importer: InstanceImporter, exporter: InstanceExporter
    ):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                # generator importer
                instances_generator = importer.import_instances()
                # generator exporter 
                exporter.export_instances(instances=instances_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")