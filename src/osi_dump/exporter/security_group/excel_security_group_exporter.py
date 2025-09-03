import logging
import pandas as pd
from osi_dump import util
from osi_dump.exporter.security_group.security_group_exporter import SecurityGroupExporter
from osi_dump.model.security_group import SecurityGroup

logger = logging.getLogger(__name__)

class ExcelSecurityGroupExporter(SecurityGroupExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_security_groups(self, security_groups: list[SecurityGroup]):
        if not security_groups:
            logger.info(f"No security groups to export for {self.sheet_name}")
            return

        df = pd.json_normalize(
            [sg.model_dump() for sg in security_groups],
            record_path='rules',
            meta=['security_group_id', 'name', 'project_id', 'description'],
            record_prefix='rule.'
        )

        logger.info(f"Exporting security groups for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported security groups for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting security groups for {self.sheet_name} error: {e}")