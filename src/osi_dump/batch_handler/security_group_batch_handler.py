import logging
from openstack.connection import Connection
from osi_dump import util
from osi_dump.importer.security_group.security_group_importer import SecurityGroupImporter
from osi_dump.importer.security_group.openstack_security_group_importer import OpenStackSecurityGroupImporter
from osi_dump.exporter.security_group.security_group_exporter import SecurityGroupExporter
from osi_dump.exporter.security_group.excel_security_group_exporter import ExcelSecurityGroupExporter

logger = logging.getLogger(__name__)

class SecurityGroupBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[tuple[SecurityGroupImporter, SecurityGroupExporter]] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackSecurityGroupImporter(connection)
            sheet_name = f"{util.extract_hostname(connection.auth['auth_url'])}-sec-group"
            exporter = ExcelSecurityGroupExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                security_groups = importer.import_security_groups()
                exporter.export_security_groups(security_groups=security_groups)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping security group export...")