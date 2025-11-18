from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.trunk import Trunk

class TrunkImporter(ABC):
    @abstractmethod
    def import_trunks(self) -> Generator[Trunk, None, None]:
        pass