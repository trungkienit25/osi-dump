import pandas as pd
import logging
from typing import Generator

from osi_dump import util
from osi_dump.exporter.trunk.trunk_exporter import TrunkExporter
from osi_dump.model.trunk import Trunk

logger = logging.getLogger(__name__)

class ExcelTrunkExporter(TrunkExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_trunks(self, trunks: Generator[Trunk, None, None]):
        df = pd.DataFrame(trunk.model_dump() for trunk in trunks)

        if df.empty:
            logger.info(f"No trunks to export for {self.sheet_name}")
            return

        if 'parent_port_id' in df.columns and 'segmentation_id' in df.columns:
            df.sort_values(by=['parent_port_id', 'segmentation_id'], inplace=True, na_position='last')

        logger.info(f"Exporting trunks for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported trunks for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting trunks for {self.sheet_name} error: {e}")