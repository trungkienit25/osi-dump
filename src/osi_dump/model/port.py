from typing import Optional, List
from pydantic import BaseModel

class PortModel(BaseModel):
    id: str
    name: Optional[str] = None
    status: str
    mac_address: str
    network_id: str
    network_name: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    device_id: str
    device_owner: str
    fixed_ips: List[dict] = []
    created_at: str
