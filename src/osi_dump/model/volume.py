from typing import Optional, List
from pydantic import BaseModel

class VolumeModel(BaseModel):
    """Data model representing an OpenStack Volume (Cinder)."""
    id: str
    name: Optional[str]
    status: str
    size_gb: int
    project_id: str
    project_name: Optional[str] = None
    user_id: Optional[str] = None
    volume_type: Optional[str] = None
    snapshot_ids: List[str] = []
    created_at: str