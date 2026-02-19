from typing import Optional
from pydantic import BaseModel

class ImageModel(BaseModel):
    id: str
    name: Optional[str] = None
    status: str
    size_bytes: Optional[int] = None
    container_format: Optional[str] = None
    disk_format: Optional[str] = None
    visibility: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    created_at: str
