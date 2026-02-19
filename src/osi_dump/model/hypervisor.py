from typing import Optional, Dict
from pydantic import BaseModel

class HypervisorModel(BaseModel):
    id: str
    name: str
    host_ip: Optional[str] = None
    state: str
    status: str
    vcpus: int
    vcpus_used: int
    memory_mb: int
    memory_mb_used: int
   
