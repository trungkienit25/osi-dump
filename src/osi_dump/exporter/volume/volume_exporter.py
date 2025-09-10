from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.volume import Volume

class VolumeExporter(ABC):
    @abstractmethod
    def export_volumes(self, volumes: Generator[Volume, None, None]):
        pass

