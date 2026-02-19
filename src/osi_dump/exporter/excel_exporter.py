from pathlib import Path
from typing import Any, Generator
import logging
import pandas as pd
from osi_dump.core.interfaces import IResourceExporter

class PandasExcelExporter(IResourceExporter):
    """
    Exports resource data to an Excel file using Pandas.
    Append mode is used to add sheets to a single file.
    """
    def __init__(self, file_path: Path, sheet_name: str):
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.logger = logging.getLogger(__name__)

    def export_data(self, data: Generator[Any, None, None]) -> None:
        # 1. Convert Generator to List of Dictionaries
        # Pydantic v2 uses model_dump()
        records = [item.model_dump() for item in data]

        if not records:
            self.logger.warning(f"No data to export for sheet '{self.sheet_name}'. Skipping.")
            return

        # 2. Create DataFrame
        df = pd.DataFrame(records)

        # 3. Write to Excel
        # Use a lock-file or similar mechanism if parallel processes were writing,
        # but for our sequential orchestrator, standard file handles are fine.
        try:
            if self.file_path.exists():
                with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=self.sheet_name, index=False)
            else:
                with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='w') as writer:
                    df.to_excel(writer, sheet_name=self.sheet_name, index=False)
            
            self.logger.info(f"Exported {len(records)} rows to '{self.sheet_name}' in {self.file_path.name}")
        
        except Exception as e:
            self.logger.error(f"Failed to write excel sheet '{self.sheet_name}': {e}")
