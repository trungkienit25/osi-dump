from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.trunk import Trunk

class TrunkExporter(ABC):
    @abstractmethod
    def export_trunks(self, trunks: Generator[Trunk, None, None]):
        pass