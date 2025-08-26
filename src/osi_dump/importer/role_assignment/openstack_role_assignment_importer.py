import logging

import concurrent

from openstack.connection import Connection
from openstack.identity.v3.role_assignment import RoleAssignment as OSRoleAssignment
from openstack.identity.v3.user import User as OSUser


from osi_dump.importer.role_assignment.role_assignment_importer import (
    RoleAssignmentImporter,
)
from osi_dump.model.role_assignment import RoleAssignment

from osi_dump.api.keystone import get_role_assignments, get_users

logger = logging.getLogger(__name__)


class OpenStackRoleAssignmentImporter(RoleAssignmentImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

        self.users: dict[str, dict] = {}
        self.roles = {}

    def _get_users(self):
        os_users = get_users(self.connection)

        for os_user in os_users:
            self.users[os_user["id"]] = os_user

    def _get_roles(self):
        os_roles = self.connection.identity.roles()

        for os_role in os_roles:
            self.roles[os_role.id] = os_role.name

    def import_role_assignments(self) -> list[RoleAssignment]:
        """Import role_assignments information from Openstack

        Raises:
            Exception: Raises exception if fetching role_assignment failed

        Returns:
            list[RoleAssignment]: _description_
        """

        logger.info(
            f"Importing role_assignments for {self.connection.auth['auth_url']}"
        )

        try:
            self._get_users()
        except Exception as e:
            logger.info(f"Getting user list failed {e}")

        try:
            self._get_roles()
        except Exception as e:
            logger.info(f"Getting role list failed {e}")

        try:
            osrole_assignments: list[OSRoleAssignment] = list(
                self.connection.identity.role_assignments()
            )

        except Exception as e:
            raise Exception(
                f"Can not fetch role_assignments for {self.connection.auth['auth_url']} {e}"
            ) from e

        role_assignments: list[RoleAssignment] = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._get_role_assignment_info, role_assignment)
                for role_assignment in osrole_assignments
            ]
            for future in concurrent.futures.as_completed(futures):
                role_assignments.append(future.result())

        logger.info(f"Imported role_assignments for {self.connection.auth['auth_url']}")

        return role_assignments

    def _get_role_assignment_info(
        self, role_assignment: OSRoleAssignment
    ) -> RoleAssignment:

        user_id = None
        role_id = None

        try:
            user_id: str = role_assignment["user"]["id"]
        except Exception as e:
            logger.warning(f"Can not get user id: {e}")

        try:
            role_id = role_assignment["role"]["id"]
        except Exception as e:
            logger.warning(f"Can not get role id: {e}")

        user_name = None
        role_name = None

        password_expires_at = None
        options = None

        try:
            user_name = self.users[user_id]["name"]
        except Exception as e:
            logger.warning(f"Can not get user name: {e}")

        try:
            role_name = self.roles[role_id]
        except Exception as e:
            logger.warning(f"Can not get role name: {e}")

        try:
            password_expires_at = self.users[user_id]["password_expires_at"]
        except Exception as e: 
            logger.warning(f"Can not get password expires at: {e}")


        try:
            options = self.users[user_id]["options"]
        except Exception as e:
            logger.warning(f"Can not get option")

        try:
            enabled = self.users[user_id]["enabled"]
        except Exception as e:
            logger.warning(f"Can not get enabled")

        role_assignment_ret = RoleAssignment(
            user_id=user_id,
            user_name=user_name,
            role_id=role_id,
            role_name=role_name,
            enabled=enabled,
            scope=role_assignment["scope"],
            password_expires_at=password_expires_at,
            options=options
        )

        return role_assignment_ret
