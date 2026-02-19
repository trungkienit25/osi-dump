from typing import Generator, Any
import logging

class MockExcelExporter:
    """
    A temporary mock exporter to simulate writing data for migration testing.
    """
    def export_data(self, data: Generator[Any, None, None]) -> None:
        count = 0
        for item in data:
            count += 1
        logging.getLogger(__name__).info(f"[MockExporter] Exported {count} items.")
