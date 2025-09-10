import logging
import pandas as pd
from typing import Generator
import ipaddress

from osi_dump import util
from osi_dump.exporter.floating_ip.floating_ip_exporter import FloatingIPExporter
from osi_dump.model.floating_ip import FloatingIP

logger = logging.getLogger(__name__)

class ExcelFloatingIPExporter(FloatingIPExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_floating_ips(self, floating_ips: Generator[FloatingIP, None, None]):
        df = pd.DataFrame(fip.model_dump() for fip in floating_ips)

        if df.empty:
            logger.info(f"No floating IPs to export for {self.sheet_name}")
            return

        if 'floating_ip_address' in df.columns:
            df['sort_key'] = df['floating_ip_address'].apply(ipaddress.ip_address)
            df.sort_values(by='sort_key', inplace=True)
            df.drop(columns='sort_key', inplace=True)

        logger.info(f"Exporting floating ips for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported floating ips for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting floating ips for {self.sheet_name} error: {e}")
