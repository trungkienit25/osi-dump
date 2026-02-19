from pathlib import Path
from typing import List
import logging

from osi_dump.core.interfaces import IOutputDestination
from osi_dump.core.config import AppConfig
from osi_dump.delivery.strategies import TelegramDeliveryStrategy, S3DeliveryStrategy

class DeliveryContext:
    """
    Manages the execution of multiple output strategies.
    Ensures that failure in one strategy does not block others.
    """
    def __init__(self, config: AppConfig):
        self.logger = logging.getLogger(__name__)
        self._strategies: List[IOutputDestination] = []

        # Register strategies based on configuration
        if config.output.send_telegram and config.output.telegram:
            self._strategies.append(TelegramDeliveryStrategy(config.output.telegram))
        
        if config.output.send_s3 and config.output.s3:
            self._strategies.append(S3DeliveryStrategy(config.output.s3))

    def execute_delivery(self, file_path: Path) -> None:
        """
        Delivers the file to all configured destinations.
        """
        if not self._strategies:
            self.logger.info("No delivery strategies configured. Skipping delivery.")
            return

        self.logger.info(f"Starting delivery execution for: {file_path.name}")

        for strategy in self._strategies:
            try:
                self.logger.debug(f"Executing strategy: {strategy.destination_name}")
                strategy.deliver(file_path)
            except Exception as e:
                # Robustness: One strategy failing should not stop others
                self.logger.error(f"Critical error in delivery strategy '{strategy.destination_name}': {e}")
        
        self.logger.info("Delivery execution completed.")
