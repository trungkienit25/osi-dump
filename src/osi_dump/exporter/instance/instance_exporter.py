from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.instance import Instance

class InstanceExporter(ABC):
    @abstractmethod
    def export_instances(self, instances: Generator[Instance, None, None]):
        pass