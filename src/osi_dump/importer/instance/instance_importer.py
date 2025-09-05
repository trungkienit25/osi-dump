from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.instance import Instance

class InstanceImporter(ABC):
    @abstractmethod
    def import_instances(self) -> Generator[Instance, None, None]:
        pass