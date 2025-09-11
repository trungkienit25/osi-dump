import logging
from openstack.connection import Connection

from osi_dump.exporter.project.project_exporter import ProjectExporter
from osi_dump.exporter.project.excel_project_exporter import ExcelProjectExporter
from osi_dump.importer.project.project_importer import ProjectImporter
from osi_dump.importer.project.openstack_project_importer import OpenStackProjectImporter
from osi_dump import util

logger = logging.getLogger(__name__)

class ProjectBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[tuple[ProjectImporter, ProjectExporter]] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackProjectImporter(connection)
            sheet_name = f"{util.extract_hostname(connection.auth['auth_url'])}-project"
            exporter = ExcelProjectExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(importer=importer, exporter=exporter)

    def add_importer_exporter(
        self, importer: ProjectImporter, exporter: ProjectExporter
    ):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                projects_generator = importer.import_projects()
                exporter.export_projects(projects=projects_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")