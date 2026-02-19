from pathlib import Path
import logging
from typing import Optional

# Third-party imports (assumed available in environment)
try:
    import requests
except ImportError:
    requests = None

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    boto3 = None
    BotoCoreError = None
    ClientError = None

from osi_dump.core.interfaces import IOutputDestination
from osi_dump.core.config import TelegramConfig, S3Config

# -----------------------------------------------------------------------------
# Telegram Strategy
# -----------------------------------------------------------------------------
class TelegramDeliveryStrategy(IOutputDestination):
    """
    Strategy to deliver files via Telegram Bot API.
    """
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        if not requests:
            self.logger.warning("TelegramDeliveryStrategy initialized but 'requests' library is missing.")

    @property
    def destination_name(self) -> str:
        return "telegram"

    def deliver(self, file_path: Path) -> None:
        if not requests:
            self.logger.error("Cannot deliver to Telegram: 'requests' library not installed.")
            return

        url = f"https://api.telegram.org/bot{self.config.token}/sendDocument"
        data = {"chat_id": self.config.chat_id}
        
        self.logger.info(f"Uploading {file_path.name} to Telegram...")

        try:
            with file_path.open("rb") as f:
                files = {"document": f}
                response = requests.post(url, data=data, files=files, timeout=30)
                response.raise_for_status()
            
            self.logger.info(f"Successfully delivered to Telegram. Response: {response.json().get('ok')}")

        except requests.RequestException as e:
            self.logger.error(f"Failed to upload to Telegram: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error delivering to Telegram: {e}")


# -----------------------------------------------------------------------------
# S3 Strategy
# -----------------------------------------------------------------------------
class S3DeliveryStrategy(IOutputDestination):
    """
    Strategy to upload files to an S3-compatible bucket.
    """
    def __init__(self, config: S3Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        if not boto3:
            self.logger.warning("S3DeliveryStrategy initialized but 'boto3' library is missing.")

    @property
    def destination_name(self) -> str:
        return "s3"

    def deliver(self, file_path: Path) -> None:
        if not boto3:
            self.logger.error("Cannot deliver to S3: 'boto3' library not installed.")
            return

        self.logger.info(f"Uploading {file_path.name} to S3 Bucket '{self.config.bucket_name}'...")

        try:
            # Initialize S3 Client
            s3_client = boto3.client(
                's3',
                endpoint_url=self.config.endpoint_url,
                aws_access_key_id=self.config.access_key,
                aws_secret_access_key=self.config.secret_key
            )

            # Upload File
            # Key will be the filename itself
            s3_client.upload_file(str(file_path), self.config.bucket_name, file_path.name)
            
            self.logger.info(f"Successfully uploaded {file_path.name} to S3.")

        except (BotoCoreError, ClientError) as e:
            self.logger.error(f"AWS S3 Error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error delivering to S3: {e}")
