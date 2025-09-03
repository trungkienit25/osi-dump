from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class SecurityGroupRule(BaseModel):
    """Represents a single rule within a security group."""
    rule_id: str
    direction: str
    protocol: Optional[str]
    ethertype: str
    port_range: Optional[str]
    remote_ip_prefix: Optional[str]
    remote_group_id: Optional[str]

class SecurityGroup(BaseModel):
    """Represents an OpenStack Security Group."""
    model_config = ConfigDict(strict=True)

    security_group_id: str
    name: str
    project_id: Optional[str]
    description: Optional[str]
    rules: List[SecurityGroupRule]