from typing import Optional
from pydantic import BaseModel

class LoadBalancerModel(BaseModel):
    id: str
    name: Optional[str] = None
    provisioning_status: str
    operating_status: str
    vip_address: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    created_at: str
