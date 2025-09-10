import logging
from openstack.connection import Connection

from osi_dump.exporter.volume.excel_volume_exporter import ExcelVolumeExporter
from osi_dump.exporter.volume.volume_exporter import VolumeExporter
from osi_dump import util
from osi_dump.importer.volume.openstack_volume_importer import OpenStackVolumeImporter
from osi_dump.importer.volume.volume_importer import VolumeImporter

logger = logging.getLogger(__name__)

class VolumeBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[tuple[VolumeImporter, VolumeExporter]] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackVolumeImporter(connection)
            sheet_name = f"{util.extract_hostname(connection.auth['auth_url'])}-volume"
            exporter = ExcelVolumeExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(importer=importer, exporter=exporter)

    def add_importer_exporter(self, importer: VolumeImporter, exporter: VolumeExporter):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                volumes_generator = importer.import_volumes()
                exporter.export_volumes(volumes=volumes_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")
