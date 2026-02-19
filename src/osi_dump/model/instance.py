from typing import Optional
from pydantic import BaseModel

class InstanceModel(BaseModel):
    """Data model representing an OpenStack Instance."""
    id: str
    name: str
    status: str
    flavor_id: str
    flavor_name: str
    project_id: str
    project_name: Optional[str] = None
    availability_zone: Optional[str] = None
    gpu_type: Optional[str] = None
    gpu_count: int = 0
    created_at: str
