from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.hypervisor import Hypervisor

class HypervisorExporter(ABC):
    @abstractmethod
    def export_hypervisors(self, hypervisors: Generator[Hypervisor, None, None]):
        pass