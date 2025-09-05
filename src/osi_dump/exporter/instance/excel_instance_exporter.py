import pandas as pd
import logging
from typing import Generator

from osi_dump import util
from osi_dump.exporter.instance.instance_exporter import InstanceExporter
from osi_dump.model.instance import Instance

logger = logging.getLogger(__name__)

class ExcelInstanceExporter(InstanceExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_instances(self, instances: Generator[Instance, None, None]):
        df = pd.DataFrame(instance.model_dump() for instance in instances)

        if df.empty:
            logger.info(f"No instances to export for {self.sheet_name}")
            return
        df.sort_values(by='instance_name', inplace=True, na_position='last')

        logger.info(f"Exporting instances for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported instances for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting instances for {self.sheet_name} error: {e}")