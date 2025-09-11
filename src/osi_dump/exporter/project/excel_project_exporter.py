import pandas as pd
import logging
from typing import Generator
from osi_dump import util
from osi_dump.exporter.project.project_exporter import ProjectExporter
from osi_dump.model.project import Project

logger = logging.getLogger(__name__)

class ExcelProjectExporter(ProjectExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_projects(self, projects: Generator[Project, None, None]):
        df = pd.DataFrame(p.model_dump() for p in projects)
        
        if df.empty:
            logger.info(f"No projects to export for {self.sheet_name}")
            return
            
        if 'project_name' in df.columns:
            df.sort_values(by='project_name', inplace=True, na_position='last')

        logger.info(f"Exporting projects for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported projects for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting projects for {self.sheet_name} error: {e}")