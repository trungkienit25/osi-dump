from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.flavor import Flavor

class FlavorExporter(ABC):
    @abstractmethod
    def export_flavors(self, flavors: Generator[Flavor, None, None]):
        pass

