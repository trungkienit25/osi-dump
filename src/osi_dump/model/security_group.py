from typing import Optional, List
from pydantic import BaseModel

class SecurityGroupModel(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    created_at: str