from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.security_group import SecurityGroup

class SecurityGroupImporter(ABC):
    @abstractmethod
    def import_security_groups(self) -> Generator[SecurityGroup, None, None]: 
        pass