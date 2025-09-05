import logging
import pandas as pd
from osi_dump import util
from .role_assignment_exporter import RoleAssignmentExporter
from osi_dump.importer.role_assignment.role_assignment_importer import RoleAssignmentImporter

logger = logging.getLogger(__name__)

class ExcelRoleAssignmentExporter(RoleAssignmentExporter):
    def __init__(self, sheet_name_prefix: str, output_file: str):
        self.sheet_name_prefix = sheet_name_prefix
        self.output_file = output_file

    def export_role_assignments(self, importer: RoleAssignmentImporter):
        # Sheet 1: User Effective Roles
        df_effective = pd.json_normalize(
            (role.model_dump() for role in importer.calculate_effective_roles())
        )
        if not df_effective.empty:
            df_effective.sort_values(by=['user_name', 'role_name'], inplace=True)
            self._export_to_sheet(df_effective, f"{self.sheet_name_prefix}-effective")

        # Sheet 2: Raw User Roles
        df_user = pd.json_normalize(
            (role.model_dump() for role in importer.get_user_roles())
        )
        if not df_user.empty:
            self._export_to_sheet(df_user, f"{self.sheet_name_prefix}-user")
            
        # Sheet 3: Raw Group Roles
        df_group = pd.json_normalize(
            (role.model_dump() for role in importer.get_group_roles())
        )
        if not df_group.empty:
            self._export_to_sheet(df_group, f"{self.sheet_name_prefix}-group")

    def _export_to_sheet(self, df: pd.DataFrame, sheet_name: str):
        logger.info(f"Exporting data to sheet: {sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=sheet_name, df=df)
            logger.info(f"Exported data to sheet: {sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting to {sheet_name} error: {e}")