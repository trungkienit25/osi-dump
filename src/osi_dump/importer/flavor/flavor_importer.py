from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.flavor import Flavor

class FlavorImporter(ABC):
    @abstractmethod
    def import_flavors(self) -> Generator[Flavor, None, None]:
        pass

