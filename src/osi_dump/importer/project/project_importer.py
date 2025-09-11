from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.project import Project

class ProjectImporter(ABC):
    @abstractmethod
    def import_projects(self) -> Generator[Project, None, None]:
        pass