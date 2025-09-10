from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.router import Router

class RouterImporter(ABC):
    @abstractmethod
    def import_routers(self) -> Generator[Router, None, None]:
        pass
