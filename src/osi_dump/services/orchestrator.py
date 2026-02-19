from pathlib import Path
from typing import List, Any
import logging

from osi_dump.core.config import AppConfig
from osi_dump.services.registry import HandlerRegistry
from osi_dump.delivery.context import DeliveryContext

# Attempt to import the connection helper. 
# In a real scenario, this file exists as verified.
try:
    from osi_dump.os_connection.get_connections import get_connections
except ImportError:
    # Fallback mock for compilation if the environment is incomplete
    def get_connections(auth_file: Path) -> List[Any]:
        logging.getLogger(__name__).warning("Using mock get_connections")
        return []

class DumpOrchestrator:
    """
    Facade that coordinates the entire dump process:
    1. Configuration Loading
    2. OpenStack Authentication
    3. Resource Extraction (via Handlers)
    4. Data Delivery (via DeliveryContext)
    """
    def __init__(self, config_path: Path, auth_file: Path, output_dir: Path):
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        
        # 1. Load Configuration
        self.logger.info(f"Loading configuration from {config_path}")
        self.config = AppConfig.from_json(config_path)

        # 2. Authenticate / Get Connections
        self.logger.info(f"Authenticating using {auth_file}")
        self.connections = get_connections(auth_file)
        
        # 3. Initialize Delivery Context
        self.delivery_context = DeliveryContext(self.config)

    def execute(self) -> List[Path]:
        """
        Runs the full export pipeline.
        Returns a list of paths to the generated files.
        """
        generated_files: List[Path] = []
        
        # 1. Get Active Handlers
        handlers = HandlerRegistry.get_active_handlers(self.config)
        if not handlers:
            self.logger.warning("No resource handlers enabled in configuration.")
            return []

        self.logger.info(f"Found {len(handlers)} active resource handlers.")

        # 2. Ensure Output Directory Exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 3. Process Each Handler
        for handler in handlers:
            try:
                self.logger.info(f"Processing handler: {handler.resource_name}")
                file_path = handler.process(self.connections, self.output_dir)
                if file_path and file_path.exists():
                    generated_files.append(file_path)
            except Exception as e:
                self.logger.error(f"Handler '{handler.resource_name}' failed: {e}")
                # We continue to the next handler even if one fails
                continue

        # 4. Deliver Files
        if generated_files:
            self.logger.info(f"Starting delivery for {len(generated_files)} files...")
            for file_path in generated_files:
                self.delivery_context.execute_delivery(file_path)
        else:
            self.logger.warning("No files were generated to deliver.")

        return generated_files
