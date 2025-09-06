import logging
from openstack.connection import Connection
from openstack.identity.v3.role_assignment import RoleAssignment as OSRoleAssignment
from typing import Generator

from .role_assignment_importer import RoleAssignmentImporter
from osi_dump.model.role_assignment import UserRoleAssignment, GroupRoleAssignment
from osi_dump.api.keystone import get_users

logger = logging.getLogger(__name__)

class OpenStackRoleAssignmentImporter(RoleAssignmentImporter):
    def __init__(self, connection: Connection):
        self.connection = connection
        self.users = {}
        self.roles = {}
        self.groups = {}
        self._raw_assignments = None 

    def _fetch_metadata(self):
        """cache metadata"""
        if self._raw_assignments is not None:
            return 

        logger.info(f"Pre-caching metadata for role assignments on {self.connection.auth['auth_url']}")
        
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
            for group in os_groups: self.groups[group.id] = group.name
        except Exception as e:
            logger.error(f"Could not fetch groups: {e}")

        try:
            self._raw_assignments = list(self.connection.identity.role_assignments())
        except Exception as e:
            logger.error(f"Could not fetch role assignments: {e}")
            self._raw_assignments = []

    def get_user_roles(self) -> Generator[UserRoleAssignment, None, None]:
        self._fetch_metadata()
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
        self._fetch_metadata()
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