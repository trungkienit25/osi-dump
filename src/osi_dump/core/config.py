from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

import json

class ResourceConfig(BaseModel):
    """Configuration for enabling/disabling resource extraction."""
    instance_enabled: bool = True
    volume_enabled: bool = True
    hypervisor_enabled: bool = True
    flavor_enabled: bool = True
    image_enabled: bool = True
    network_enabled: bool = True
    port_enabled: bool = True
    router_enabled: bool = True
    floating_ip_enabled: bool = True
    security_group_enabled: bool = True
    load_balancer_enabled: bool = True
    trunk_enabled: bool = True
    project_enabled: bool = True
    role_assignment_enabled: bool = True
    # Can add more resources here or use extra='allow' if dynamic fields are needed

class TelegramConfig(BaseModel):
    """Configuration for Telegram output."""
    token: str
    chat_id: str

class S3Config(BaseModel):
    """Configuration for S3 output."""
    bucket_name: str
    access_key: str
    secret_key: str
    endpoint_url: str

class OutputConfig(BaseModel):
    """Configuration for output destinations."""
    send_telegram: bool = False
    send_s3: bool = False
    telegram: Optional[TelegramConfig] = None
    s3: Optional[S3Config] = None

class AppConfig(BaseModel):
    """Root application configuration."""
    resources: ResourceConfig = Field(default_factory=ResourceConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @classmethod
    def from_json(cls, file_path: Path) -> "AppConfig":
        """Load configuration from a JSON file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls.model_validate(data)
