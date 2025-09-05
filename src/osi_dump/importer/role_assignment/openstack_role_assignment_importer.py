import logging
from openstack.connection import Connection
from openstack.identity.v3.role_assignment import RoleAssignment as OSRoleAssignment
from typing import Generator

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
        self.group_members = {}  # group_id -> [user_id_1, user_id_2]
        self._raw_assignments = None # Cache 

    def _fetch_all_data(self):
        """pre-cache for metadata."""
        if self._raw_assignments is not None:
            return

        logger.info(f"Pre-caching all role assignment metadata for {self.connection.auth['auth_url']}")
        
        try:
            os_users = get_users(self.connection)
            for os_user in os_users: self.users[os_user["id"]] = os_user
        except Exception as e:
            logger.error(f"Could not fetch users: {e}")

        try:
            os_roles = self.connection.identity.roles()
            for os_role in os_roles: self.roles[os_role.id] = os_role.name
        except Exception as e:
            logger.error(f"Could not fetch roles: {e}")
            
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

        try:
            self._raw_assignments = list(self.connection.identity.role_assignments())
        except Exception as e:
            logger.error(f"Could not fetch role assignments: {e}")
            self._raw_assignments = []

    def get_user_roles(self) -> Generator[UserRoleAssignment, None, None]:
        self._fetch_all_data()
        for assignment in self._raw_assignments:
            if assignment.user:
                user_id = assignment.user.get('id')
                user_info = self.users.get(user_id, {})
                role_id = assignment.role.get('id') if assignment.role else None
                yield UserRoleAssignment(
                    user_id=user_id,
                    user_name=user_info.get('name'),
                    role_id=role_id,
                    role_name=self.roles.get(role_id),
                    scope=assignment.scope,
                    enabled=user_info.get('enabled'),
                    password_expires_at=user_info.get('password_expires_at'),
                    options=user_info.get('options')
                )

    def get_group_roles(self) -> Generator[GroupRoleAssignment, None, None]:
        self._fetch_all_data()
        for assignment in self._raw_assignments:
            if assignment.group:
                group_id = assignment.group.get('id')
                role_id = assignment.role.get('id') if assignment.role else None
                yield GroupRoleAssignment(
                    group_id=group_id,
                    group_name=self.groups.get(group_id),
                    role_id=role_id,
                    role_name=self.roles.get(role_id),
                    scope=assignment.scope
                )

    def calculate_effective_roles(self) -> Generator[EffectiveUserRole, None, None]:
        # generator
        # direct role
        for user_role in self.get_user_roles():
            yield EffectiveUserRole(
                user_id=user_role.user_id,
                user_name=user_role.user_name,
                role_id=user_role.role_id,
                role_name=user_role.role_name,
                scope=user_role.scope,
                inherited_from_group='[Direct]'
            )
        
        # inherited_from_group
        for group_role in self.get_group_roles():
            group_id = group_role.group_id
            if group_id in self.group_members:
                for user_id in self.group_members[group_id]:
                    user_info = self.users.get(user_id, {})
                    yield EffectiveUserRole(
                        user_id=user_id,
                        user_name=user_info.get('name'),
                        role_id=group_role.role_id,
                        role_name=group_role.role_name,
                        scope=group_role.scope,
                        inherited_from_group=group_role.group_name
                    )