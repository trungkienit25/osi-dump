from typing import Optional, Dict
from pydantic import BaseModel

class FlavorModel(BaseModel):
    id: str
    name: str
    vcpus: int
    ram: int
    disk: int
    is_public: bool
