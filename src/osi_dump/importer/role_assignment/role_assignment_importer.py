from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.role_assignment import UserRoleAssignment, GroupRoleAssignment, EffectiveUserRole

class RoleAssignmentImporter(ABC):
    @abstractmethod
    def get_user_roles(self) -> Generator[UserRoleAssignment, None, None]:
        pass

    @abstractmethod
    def get_group_roles(self) -> Generator[GroupRoleAssignment, None, None]:
        pass

    @abstractmethod
    def calculate_effective_roles(self) -> Generator[EffectiveUserRole, None, None]:
        pass