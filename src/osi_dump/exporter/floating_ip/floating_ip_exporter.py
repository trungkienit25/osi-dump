from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.floating_ip import FloatingIP

class FloatingIPExporter(ABC):
    @abstractmethod
    def export_floating_ips(self, floating_ips: Generator[FloatingIP, None, None]):
        pass

