from abc import ABC, abstractmethod
from osi_dump.model.security_group import SecurityGroup

class SecurityGroupImporter(ABC):
    @abstractmethod
    def import_security_groups(self) -> list[SecurityGroup]:
        pass