from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.volume import Volume

class VolumeImporter(ABC):
    @abstractmethod
    def import_volumes(self) -> Generator[Volume, None, None]:
        pass