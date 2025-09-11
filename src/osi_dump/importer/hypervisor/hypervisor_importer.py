from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.hypervisor import Hypervisor

class HypervisorImporter(ABC):
    @abstractmethod
    def import_hypervisors(self) -> Generator[Hypervisor, None, None]:
        pass