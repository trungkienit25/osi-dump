from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.network import Network

class NetworkExporter(ABC):
    @abstractmethod
    def export_networks(self, networks: Generator[Network, None, None]):
        pass