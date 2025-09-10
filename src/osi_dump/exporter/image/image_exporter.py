from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.image import Image

class ImageExporter(ABC):
    @abstractmethod
    def export_images(self, images: Generator[Image, None, None]):
        pass

