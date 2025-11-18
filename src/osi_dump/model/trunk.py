from typing import Optional
from pydantic import BaseModel, ConfigDict

class Trunk(BaseModel):
    model_config = ConfigDict(strict=True)
    trunk_id: str
    trunk_name: Optional[str]
    trunk_status: str
    project_id: Optional[str]
    parent_port_id: str

    # sub-port
    sub_port_id: str
    segmentation_type: str
    segmentation_id: int # VLAN ID