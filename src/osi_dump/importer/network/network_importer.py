from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.network import Network

class NetworkImporter(ABC):
    @abstractmethod
    def import_networks(self) -> Generator[Network, None, None]:
        pass