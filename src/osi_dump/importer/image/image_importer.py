from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.image import Image

class ImageImporter(ABC):
    @abstractmethod
    def import_images(self) -> Generator[Image, None, None]:
        pass

