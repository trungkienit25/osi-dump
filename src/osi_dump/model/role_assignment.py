from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserRoleAssignment(BaseModel):
    model_config = ConfigDict(strict=True)
    user_id: str
    user_name: Optional[str]
    role_id: str
    role_name: Optional[str]
    scope: dict
    enabled: Optional[bool]
    password_expires_at: Optional[str]
    options: Optional[dict]

class GroupRoleAssignment(BaseModel):
    model_config = ConfigDict(strict=True)
    group_id: str
    group_name: Optional[str]
    role_id: str
    role_name: Optional[str]
    scope: dict

#class EffectiveUserRole(BaseModel):
#    model_config = ConfigDict(strict=True)
#    user_id: str
#    user_name: Optional[str]
#    role_id: str
#    role_name: Optional[str]
#    scope: dict
#    inherited_from_group: Optional[str]