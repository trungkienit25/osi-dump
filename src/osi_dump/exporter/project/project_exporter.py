from abc import ABC, abstractmethod
from typing import Generator
from osi_dump.model.project import Project

class ProjectExporter(ABC):
    @abstractmethod
    def export_projects(self, projects: Generator[Project, None, None]):
        pass