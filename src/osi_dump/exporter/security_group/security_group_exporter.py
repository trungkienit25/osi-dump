from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.security_group import SecurityGroup

class SecurityGroupExporter(ABC):
    @abstractmethod
    def export_security_groups(self, security_groups: Generator[SecurityGroup, None, None]):
        pass