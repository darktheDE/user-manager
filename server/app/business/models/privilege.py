"""Privilege Pydantic models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PrivilegeType(str, Enum):
    """Types of privileges."""
    SYSTEM = "SYSTEM"
    ROLE = "ROLE"
    OBJECT = "OBJECT"


class GrantRequest(BaseModel):
    """Model for grant privilege/role request."""
    grantee: str = Field(..., min_length=1, description="User or role to grant to")
    privilege_or_role: str = Field(..., min_length=1, description="Privilege or role name")
    privilege_type: PrivilegeType = Field(..., description="Type: SYSTEM, ROLE, or OBJECT")
    with_admin: bool = Field(False, description="Grant with admin option")


class RevokeRequest(BaseModel):
    """Model for revoke privilege/role request."""
    grantee: str = Field(..., min_length=1, description="User or role to revoke from")
    privilege_or_role: str = Field(..., min_length=1, description="Privilege or role name")
    privilege_type: PrivilegeType = Field(..., description="Type: SYSTEM, ROLE, or OBJECT")


class PrivilegeResponse(BaseModel):
    """Model for privilege response."""
    privilege: str = Field(..., description="Privilege or role name")
    privilege_type: str = Field(..., description="SYSTEM or ROLE")
    admin_option: Optional[str] = Field(None, description="YES/NO for admin option")
    
    class Config:
        from_attributes = True
