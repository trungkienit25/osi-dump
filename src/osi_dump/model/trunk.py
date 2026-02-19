from typing import Optional, List
from pydantic import BaseModel

class TrunkModel(BaseModel):
    id: str
    name: Optional[str] = None
    status: str
    port_id: str
    project_id: str
    project_name: Optional[str] = None
    sub_ports: List[dict] = []
    created_at: str