import pandas as pd
import logging
import ipaddress
from typing import Generator

from osi_dump import util
from osi_dump.exporter.external_port.external_port_exporter import ExternalPortExporter
from osi_dump.model.external_port import ExternalPort

logger = logging.getLogger(__name__)

class ExcelExternalPortExporter(ExternalPortExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_external_ports(self, external_ports: Generator[ExternalPort, None, None]):
        df = util.panda_excel.expand_list_column(
            pd.DataFrame(port.model_dump() for port in external_ports),
            "allowed_address_pairs"
        )

        if df.empty:
            logger.info(f"No external ports to export for {self.sheet_name}")
            return

        if 'network_id' in df.columns and 'ip_address' in df.columns:
            df['ip_sort_key'] = df['ip_address'].apply(
                lambda ip: ipaddress.ip_address(ip) if ip else ipaddress.ip_address('0.0.0.0')
            )
            df.sort_values(by=['network_id', 'ip_sort_key'], inplace=True, na_position='last')
            df.drop(columns=['ip_sort_key'], inplace=True)

        logger.info(f"Exporting external_ports for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported external_ports for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting external_ports for {self.sheet_name} error: {e}")
