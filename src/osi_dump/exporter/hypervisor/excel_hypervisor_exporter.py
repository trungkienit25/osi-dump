import pandas as pd
import logging
import re
from typing import Generator

from osi_dump import util
from osi_dump.exporter.hypervisor.hypervisor_exporter import HypervisorExporter
from osi_dump.model.hypervisor import Hypervisor

logger = logging.getLogger(__name__)

def _extract_sort_keys(name):
    """
    Tách tên hypervisor thành phần chữ (prefix) và phần số (suffix).
    Ví dụ: 'hfx0wld01gld01' -> ('hfx0wld01gld', 1)
           'compute-node-no-number' -> ('compute-node-no-number', float('inf'))
    """
    if not isinstance(name, str):
        return (name, float('inf'))

    match = re.search(r'(\d+)$', name)
    if match:
        prefix = name[:match.start()]
        try:
            numeric_suffix = int(match.group(1))
            return (prefix, numeric_suffix)
        except ValueError:
             return (name, float('inf'))
    else:
        return (name, float('inf'))

class ExcelHypervisorExporter(HypervisorExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_hypervisors(self, hypervisors: Generator[Hypervisor, None, None]):
        df = pd.DataFrame(hypervisor.model_dump() for hypervisor in hypervisors)

        if df.empty:
            logger.info(f"No hypervisors to export for {self.sheet_name}")
            return

        if 'aggregates' in df.columns:
            df = util.expand_list_column(df, "aggregates")

        if 'name' in df.columns:
            try:
                sort_keys = df['name'].fillna('').apply(_extract_sort_keys)
                df['_sort_key_prefix'] = sort_keys.apply(lambda x: x[0])
                df['_sort_key_numeric'] = sort_keys.apply(lambda x: x[1])

                df.sort_values(
                    by=['_sort_key_prefix', '_sort_key_numeric'],
                    inplace=True,
                    ascending=[True, True], 
                    na_position='last'
                )

                df.drop(columns=['_sort_key_prefix', '_sort_key_numeric'], inplace=True)
                logger.info(f"Hypervisors sheet '{self.sheet_name}' will be sorted by name prefix and numeric suffix.")

            except Exception as e:
                logger.error(f"Failed to apply custom sort for {self.sheet_name}: {e}. Falling back to default name sort.")
                df.sort_values(by='name', inplace=True, na_position='last')
        else:
             logger.warning(f"Column 'name' not found for {self.sheet_name}. Skipping custom sort.")

        logger.info(f"Exporting hypervisors for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported hypervisors for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting hypervisors for {self.sheet_name} error: {e}")