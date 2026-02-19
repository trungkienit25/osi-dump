from typing import Any, Generator, Protocol, runtime_checkable
from pathlib import Path

@runtime_checkable
class IResourceImporter(Protocol):
    """Protocol for fetching resource data from a source."""
    def fetch_data(self) -> Generator[Any, None, None]:
        ...

@runtime_checkable
class IResourceExporter(Protocol):
    """Protocol for exporting fetched resource data."""
    def export_data(self, data: Generator[Any, None, None]) -> None:
        ...

@runtime_checkable
class IOutputDestination(Protocol):
    """Protocol for delivering exported files to a destination."""
    
    @property
    def destination_name(self) -> str:
        ...

    def deliver(self, file_path: Path) -> None:
        ...

@runtime_checkable
class IBatchHandler(Protocol):
    """Protocol for processing a batch of resources."""
    
    @property
    def resource_name(self) -> str:
        ...

    def is_enabled(self, config: Any) -> bool:
        ...

    def process(self, connections: list[Any], output_dir: Path) -> Path:
        ...
