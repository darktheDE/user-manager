"""Các model Pydantic cho Privilege."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PrivilegeType(str, Enum):
    """Các loại quyền."""
    SYSTEM = "SYSTEM"
    ROLE = "ROLE"
    OBJECT = "OBJECT"


class GrantRequest(BaseModel):
    """Model yêu cầu cấp quyền/role."""
    grantee: str = Field(..., min_length=1, description="User hoặc role được cấp")
    privilege_or_role: str = Field(..., min_length=1, description="Tên quyền hoặc role")
    privilege_type: PrivilegeType = Field(..., description="Loại: SYSTEM, ROLE, hoặc OBJECT")
    with_admin: bool = Field(False, description="Cấp quyền với tùy chọn admin")


class RevokeRequest(BaseModel):
    """Model yêu cầu thu hồi quyền/role."""
    grantee: str = Field(..., min_length=1, description="User hoặc role bị thu hồi")
    privilege_or_role: str = Field(..., min_length=1, description="Tên quyền hoặc role")
    privilege_type: PrivilegeType = Field(..., description="Loại: SYSTEM, ROLE, hoặc OBJECT")


class PrivilegeResponse(BaseModel):
    """Model phản hồi quyền."""
    privilege: str = Field(..., description="Tên quyền hoặc role")
    privilege_type: str = Field(..., description="SYSTEM hoặc ROLE")
    admin_option: Optional[str] = Field(None, description="YES/NO cho tùy chọn admin")
    
    class Config:
        from_attributes = True
