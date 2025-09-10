import logging
from openstack.connection import Connection

from osi_dump.exporter.image.image_exporter import ImageExporter
from osi_dump.exporter.image.excel_image_exporter import ExcelImageExporter
from osi_dump.importer.image.image_importer import ImageImporter
from osi_dump.importer.image.openstack_image_importer import OpenStackImageImporter
from osi_dump import util

logger = logging.getLogger(__name__)

class ImageBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[tuple[ImageImporter, ImageExporter]] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackImageImporter(connection)
            sheet_name = f"{util.extract_hostname(connection.auth['auth_url'])}-image"
            exporter = ExcelImageExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(importer=importer, exporter=exporter)

    def add_importer_exporter(self, importer: ImageImporter, exporter: ImageExporter):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                images_generator = importer.import_images()
                exporter.export_images(images=images_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")
