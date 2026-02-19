from typing import Optional, List
from pydantic import BaseModel

class NetworkModel(BaseModel):
    id: str
    name: Optional[str] = None
    status: str
    is_shared: bool
    is_admin_state_up: bool
    is_router_external: bool
    project_id: str
    project_name: Optional[str] = None
    subnets: List[str] = []
    created_at: str