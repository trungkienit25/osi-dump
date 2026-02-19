from typing import Optional
from pydantic import BaseModel

class FloatingIPModel(BaseModel):
    id: str
    floating_ip_address: str
    status: str
    router_id: Optional[str] = None
    port_id: Optional[str] = None
    fixed_ip_address: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    created_at: str
