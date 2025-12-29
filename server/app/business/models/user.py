"""Các model Pydantic cho User."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Model yêu cầu đăng nhập."""

    username: str = Field(..., min_length=1, max_length=100, description="Username Oracle")
    password: str = Field(..., min_length=1, description="Mật khẩu Oracle")


class SessionUser(BaseModel):
    """Model dữ liệu user trong session."""

    username: str
    account_status: Optional[str] = None
    created: Optional[str] = None
    default_tablespace: Optional[str] = None
    temporary_tablespace: Optional[str] = None


class UserCreate(BaseModel):
    """Model tạo user mới."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)
    default_tablespace: str = Field(..., min_length=1)
    temporary_tablespace: Optional[str] = None
    quota: Optional[str] = None  # e.g., "100M", "UNLIMITED"
    profile: Optional[str] = None


class UserUpdate(BaseModel):
    """Model cập nhật user."""

    password: Optional[str] = None
    default_tablespace: Optional[str] = None
    temporary_tablespace: Optional[str] = None
    quota: Optional[str] = None
    profile: Optional[str] = None


class UserResponse(BaseModel):
    """Model phản hồi user."""

    username: str
    account_status: str
    created: Optional[str] = None
    default_tablespace: Optional[str] = None
    temporary_tablespace: Optional[str] = None
    profile: Optional[str] = None
    lock_date: Optional[str] = None


class UserDetail(BaseModel):
    """Model thông tin chi tiết user."""

    username: str
    account_status: str
    created: Optional[str] = None
    default_tablespace: Optional[str] = None
    temporary_tablespace: Optional[str] = None
    profile: Optional[str] = None
    lock_date: Optional[str] = None
    roles: list[dict] = []
    privileges: list[dict] = []
    user_info: Optional[dict] = None  # Từ bảng user_info
