import logging
import pandas as pd
from osi_dump import util
from .role_assignment_exporter import RoleAssignmentExporter

logger = logging.getLogger(__name__)

class ExcelRoleAssignmentExporter(RoleAssignmentExporter):
    def __init__(self, sheet_name_prefix: str, output_file: str):
        self.sheet_name_prefix = sheet_name_prefix
        self.output_file = output_file

    def export_role_assignments(self, role_data: dict):
        user_roles = role_data.get("user_roles", [])
        group_roles = role_data.get("group_roles", [])
        effective_roles = role_data.get("effective_roles", [])

        if effective_roles:
            df_effective = pd.json_normalize(
                [role.model_dump() for role in effective_roles]
            )
            sheet_name = f"{self.sheet_name_prefix}-effective"
            self._export_to_sheet(df_effective, sheet_name)

        if user_roles:
            df_user = pd.json_normalize(
                [role.model_dump() for role in user_roles]
            )
            sheet_name = f"{self.sheet_name_prefix}-user"
            self._export_to_sheet(df_user, sheet_name)
            
        if group_roles:
            df_group = pd.json_normalize(
                [role.model_dump() for role in group_roles]
            )
            sheet_name = f"{self.sheet_name_prefix}-group"
            self._export_to_sheet(df_group, sheet_name)

    def _export_to_sheet(self, df: pd.DataFrame, sheet_name: str):
        logger.info(f"Exporting data to sheet: {sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=sheet_name, df=df)
            logger.info(f"Exported data to sheet: {sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting to {sheet_name} error: {e}")