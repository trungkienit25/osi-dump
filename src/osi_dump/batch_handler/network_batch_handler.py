import logging
from openstack.connection import Connection

from osi_dump.exporter.network.network_exporter import NetworkExporter
from osi_dump.exporter.network.excel_network_exporter import ExcelNetworkExporter
from osi_dump.importer.network.network_importer import NetworkImporter
from osi_dump.importer.network.openstack_network_importer import OpenStackNetworkImporter
from osi_dump import util

logger = logging.getLogger(__name__)

class NetworkBatchHandler:
    def __init__(self):
        self._importer_exporter_list: list[tuple[NetworkImporter, NetworkExporter]] = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list[Connection], output_file: str
    ):
        for connection in connections:
            importer = OpenStackNetworkImporter(connection)
            sheet_name = f"{util.extract_hostname(connection.auth['auth_url'])}-network"
            exporter = ExcelNetworkExporter(
                sheet_name=sheet_name, output_file=output_file
            )
            self.add_importer_exporter(importer=importer, exporter=exporter)

    def add_importer_exporter(self, importer: NetworkImporter, exporter: NetworkExporter):
        self._importer_exporter_list.append((importer, exporter))

    def process(self):
        for importer, exporter in self._importer_exporter_list:
            try:
                networks_generator = importer.import_networks()
                exporter.export_networks(networks=networks_generator)
            except Exception as e:
                logger.warning(e)
                logger.warning("Skipping...")