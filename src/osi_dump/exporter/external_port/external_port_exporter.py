from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.external_port import ExternalPort

class ExternalPortExporter(ABC):
    @abstractmethod
    def export_external_ports(self, external_ports: Generator[ExternalPort, None, None]):
        pass