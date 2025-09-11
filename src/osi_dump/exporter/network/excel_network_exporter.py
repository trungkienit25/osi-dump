import logging
import pandas as pd
from typing import Generator

from osi_dump.exporter.network.network_exporter import NetworkExporter 
from osi_dump.model.network import Network 
from osi_dump import util

logger = logging.getLogger(__name__)

class ExcelNetworkExporter(NetworkExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_networks(self, networks: Generator[Network, None, None]):
        df = pd.DataFrame(network.model_dump() for network in networks)
        
        if df.empty:
            logger.info(f"No networks to export for {self.sheet_name}")
            return
            
        if 'subnets' in df.columns:
            df = util.expand_list_column(df, "subnets")

        if 'name' in df.columns:
            df.sort_values(by='name', inplace=True, na_position='last')

        logger.info(f"Exporting networks for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported networks for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting networks for {self.sheet_name} error: {e}")