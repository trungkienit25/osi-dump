from abc import ABC, abstractmethod

class RoleAssignmentImporter(ABC):
    @abstractmethod
    def import_role_assignments(self) -> dict: 
        pass