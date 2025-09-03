from abc import ABC, abstractmethod
from osi_dump.model.security_group import SecurityGroup

class SecurityGroupExporter(ABC):
    @abstractmethod
    def export_security_groups(self, security_groups: list[SecurityGroup]):
        pass