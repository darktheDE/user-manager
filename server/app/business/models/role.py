"""Các model Pydantic cho Role."""

from typing import Optional
from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """Model role cơ sở."""
    pass


class RoleCreate(RoleBase):
    """Model tạo role mới."""
    role_name: str = Field(..., min_length=1, max_length=30, description="Tên role")
    password: Optional[str] = Field(None, description="Mật khẩu role (tùy chọn)")


class RoleUpdate(BaseModel):
    """Model cập nhật role."""
    password: Optional[str] = Field(None, description="Mật khẩu mới")
    remove_password: bool = Field(False, description="Gỡ bỏ yêu cầu mật khẩu")


class RoleResponse(BaseModel):
    """Model phản hồi role."""
    role: str = Field(..., description="Tên role")
    password_required: str = Field(..., description="Có yêu cầu mật khẩu không (YES/NO)")
    authentication_type: Optional[str] = Field(None, description="Loại xác thực")
    grantee_count: int = Field(default=0, description="Số lượng user/role có role này")
    
    class Config:
        from_attributes = True


class RoleDetail(RoleResponse):
    """Model thông tin chi tiết role."""
    privileges: list = Field(default_factory=list, description="Các quyền được cấp cho role này")
    grantees: list = Field(default_factory=list, description="Các user/role sở hữu role này")
