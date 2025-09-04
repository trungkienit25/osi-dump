from abc import ABC, abstractmethod

class RoleAssignmentExporter(ABC):
    @abstractmethod
    def export_role_assignments(self, role_data: dict): 
        pass