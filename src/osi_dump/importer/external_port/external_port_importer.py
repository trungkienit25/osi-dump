from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.external_port import ExternalPort

class ExternalPortImporter(ABC):
    @abstractmethod
    def import_external_ports(self) -> Generator[ExternalPort, None, None]:
        pass