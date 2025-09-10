from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.router import Router

class RouterExporter(ABC):
    @abstractmethod
    def export_routers(self, routers: Generator[Router, None, None]):
        pass
