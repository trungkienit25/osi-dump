from typing import Optional
from pydantic import BaseModel

class RoleAssignmentModel(BaseModel):
    id: Optional[str] = None # Assignments often don't have a single ID
    role_id: str
    role_name: Optional[str] = None
    user_id: str
    user_name: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    scope: str # project, domain, or system