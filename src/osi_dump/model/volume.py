from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict


class Volume(BaseModel):
    model_config = ConfigDict(strict=True)

    volume_id: str
    project_id: Optional[str]
    user_id: Optional[str]
    volume_name: Optional[str]
    attachments: Optional[list[str]]
    status: str
    type: str
    size: int
    snapshots: Optional[list[str]]

    host: Optional[str]
    image_metadata: Optional[Dict]

    updated_at: Optional[str]
    created_at: Optional[str]