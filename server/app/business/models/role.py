"""Role Pydantic models."""

from typing import Optional
from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """Base role model."""
    pass


class RoleCreate(RoleBase):
    """Model for creating a new role."""
    role_name: str = Field(..., min_length=1, max_length=30, description="Role name")
    password: Optional[str] = Field(None, description="Role password (optional)")


class RoleUpdate(BaseModel):
    """Model for updating a role."""
    password: Optional[str] = Field(None, description="New password")
    remove_password: bool = Field(False, description="Remove password requirement")


class RoleResponse(BaseModel):
    """Model for role response."""
    role: str = Field(..., description="Role name")
    password_required: str = Field(..., description="Whether password is required (YES/NO)")
    authentication_type: Optional[str] = Field(None, description="Authentication type")
    grantee_count: int = Field(default=0, description="Number of users/roles with this role")
    
    class Config:
        from_attributes = True


class RoleDetail(RoleResponse):
    """Model for detailed role information."""
    privileges: list = Field(default_factory=list, description="Privileges granted to this role")
    grantees: list = Field(default_factory=list, description="Users/roles that have this role")
