from abc import ABC, abstractmethod
from osi_dump.importer.role_assignment.role_assignment_importer import RoleAssignmentImporter

class RoleAssignmentExporter(ABC):
    @abstractmethod
    def export_role_assignments(self, importer: RoleAssignmentImporter):
        pass