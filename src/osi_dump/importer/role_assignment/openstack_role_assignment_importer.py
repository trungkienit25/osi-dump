from typing import Any, Generator, Dict
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.role_assignment import RoleAssignmentModel

class OpenStackRoleAssignmentImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[RoleAssignmentModel, None, None]:
        # Phase 1: Cache Projects, Users, Roles
        project_map: Dict[str, str] = {}
        user_map: Dict[str, str] = {}
        role_map: Dict[str, str] = {}
        
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
            for user in self.conn.identity.users():
                user_map[user.id] = user.name
            for role in self.conn.identity.roles():
                role_map[role.id] = role.name
        except Exception as e:
            self.logger.warning(f"Failed to fully cache identity resources: {e}")

        # Phase 2: Fetch Role Assignments
        try:
            assignments = self.conn.identity.role_assignments()
            for ra in assignments:
                try:
                    scope = "unknown"
                    pid = None
                    pname = None

                    if ra.scope:
                        if 'project' in ra.scope:
                            scope = 'project'
                            pid = ra.scope['project']['id']
                            pname = project_map.get(pid)
                        elif 'domain' in ra.scope:
                            scope = 'domain'
                        elif 'system' in ra.scope:
                            scope = 'system'

                    uid = ra.user['id'] if ra.user else "N/A"
                    uname = user_map.get(uid)
                    
                    rid = ra.role['id']
                    rname = role_map.get(rid)

                    yield RoleAssignmentModel(
                        role_id=rid,
                        role_name=rname,
                        user_id=uid,
                        user_name=uname,
                        project_id=pid,
                        project_name=pname,
                        scope=scope
                    )
                except Exception as e:
                    self.logger.error(f"Error processing assignment: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list role assignments: {e}")