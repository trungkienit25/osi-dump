import logging
import pandas as pd
from typing import Generator
from osi_dump import util
from osi_dump.exporter.hypervisor.hypervisor_exporter import HypervisorExporter
from osi_dump.model.hypervisor import Hypervisor

logger = logging.getLogger(__name__)

class ExcelHypervisorExporter(HypervisorExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_hypervisors(self, hypervisors: Generator[Hypervisor, None, None]):
        df = pd.DataFrame(h.model_dump() for h in hypervisors)
        
        if df.empty:
            logger.info(f"No hypervisors to export for {self.sheet_name}")
            return
            
        if 'aggregates' in df.columns:
            df = util.expand_list_column(df, "aggregates")

        if 'name' in df.columns:
            df.sort_values(by='name', inplace=True, na_position='last')

        logger.info(f"Exporting hypervisors for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported hypervisors for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting hypervisors for {self.sheet_name} error: {e}")