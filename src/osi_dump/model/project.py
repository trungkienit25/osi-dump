from typing import Optional
from pydantic import BaseModel

class ProjectModel(BaseModel):
    id: str
    name: str
    domain_id: str
    is_enabled: bool
    description: Optional[str] = None