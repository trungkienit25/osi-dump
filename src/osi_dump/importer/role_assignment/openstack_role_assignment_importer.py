import logging
from openstack.connection import Connection
from openstack.identity.v3.role_assignment import RoleAssignment as OSRoleAssignment

from .role_assignment_importer import RoleAssignmentImporter
from osi_dump.model.role_assignment import UserRoleAssignment, GroupRoleAssignment, EffectiveUserRole
from osi_dump.api.keystone import get_users

logger = logging.getLogger(__name__)

class OpenStackRoleAssignmentImporter(RoleAssignmentImporter):
    def __init__(self, connection: Connection):
        self.connection = connection
        self.users = {}
        self.roles = {}
        self.groups = {}
        self.group_members = {}  

    def _get_users(self):
        os_users = get_users(self.connection)
        for os_user in os_users:
            self.users[os_user["id"]] = os_user

    def _get_roles(self):
        os_roles = self.connection.identity.roles()
        for os_role in os_roles:
            self.roles[os_role.id] = os_role.name

    def _get_groups_and_members(self):
        """Lấy tất cả group và thành viên của chúng."""
        try:
            os_groups = list(self.connection.identity.groups())
            for group in os_groups:
                self.groups[group.id] = group.name
                try:
                    members = list(self.connection.identity.group_users(group))
                    self.group_members[group.id] = [user.id for user in members]
                except Exception as e:
                    logger.warning(f"Could not fetch members for group {group.name}: {e}")
                    self.group_members[group.id] = []
        except Exception as e:
            logger.error(f"Could not fetch groups: {e}")

    def import_role_assignments(self) -> dict:
        logger.info(f"Importing role assignments for {self.connection.auth['auth_url']}")

        self._get_users()
        self._get_roles()
        self._get_groups_and_members()

        try:
            os_role_assignments = list(self.connection.identity.role_assignments())
        except Exception as e:
            raise Exception(f"Can not fetch role_assignments for {self.connection.auth['auth_url']} {e}") from e

        raw_user_roles = []
        raw_group_roles = []

        for assignment in os_role_assignments:
            role_id = assignment.role.get('id') if assignment.role else None
            role_name = self.roles.get(role_id)
            scope = assignment.scope

            if assignment.user:
                user_id = assignment.user.get('id')
                user_info = self.users.get(user_id, {})
                raw_user_roles.append(UserRoleAssignment(
                    user_id=user_id,
                    user_name=user_info.get('name'),
                    role_id=role_id,
                    role_name=role_name,
                    scope=scope,
                    enabled=user_info.get('enabled'),
                    password_expires_at=user_info.get('password_expires_at'),
                    options=user_info.get('options')
                ))

            elif assignment.group:
                group_id = assignment.group.get('id')
                raw_group_roles.append(GroupRoleAssignment(
                    group_id=group_id,
                    group_name=self.groups.get(group_id),
                    role_id=role_id,
                    role_name=role_name,
                    scope=scope
                ))

        effective_roles = []
        
        for user_role in raw_user_roles:
            effective_roles.append(EffectiveUserRole(
                user_id=user_role.user_id,
                user_name=user_role.user_name,
                role_id=user_role.role_id,
                role_name=user_role.role_name,
                scope=user_role.scope,
                inherited_from_group='[Direct]'
            ))

        for group_role in raw_group_roles:
            group_id = group_role.group_id
            if group_id in self.group_members:
                for user_id in self.group_members[group_id]:
                    user_info = self.users.get(user_id, {})
                    effective_roles.append(EffectiveUserRole(
                        user_id=user_id,
                        user_name=user_info.get('name'),
                        role_id=group_role.role_id,
                        role_name=group_role.role_name,
                        scope=group_role.scope,
                        inherited_from_group=group_role.group_name
                    ))
        
        effective_roles.sort(key=lambda x: (x.user_name or "", x.role_name or ""))

        return {
            "user_roles": raw_user_roles,
            "group_roles": raw_group_roles,
            "effective_roles": effective_roles
        }