"""Các model Pydantic cho Profile."""

from typing import Optional
from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    """Model profile cơ sở với các trường chung."""
    sessions_per_user: str = Field(default="DEFAULT", description="Giới hạn SESSIONS_PER_USER")
    connect_time: str = Field(default="DEFAULT", description="Giới hạn CONNECT_TIME (phút)")
    idle_time: str = Field(default="DEFAULT", description="Giới hạn IDLE_TIME (phút)")


class ProfileCreate(ProfileBase):
    """Model tạo profile mới."""
    profile_name: str = Field(..., min_length=1, max_length=30, description="Tên profile")


class ProfileUpdate(BaseModel):
    """Model cập nhật profile."""
    sessions_per_user: Optional[str] = Field(None, description="Giới hạn SESSIONS_PER_USER")
    connect_time: Optional[str] = Field(None, description="Giới hạn CONNECT_TIME (phút)")
    idle_time: Optional[str] = Field(None, description="Giới hạn IDLE_TIME (phút)")


class ProfileResponse(ProfileBase):
    """Model phản hồi profile."""
    profile: str = Field(..., description="Tên profile")
    user_count: int = Field(default=0, description="Số lượng user đang sử dụng profile này")
    
    class Config:
        from_attributes = True


class ProfileDetail(ProfileResponse):
    """Model thông tin chi tiết profile."""
    resources: dict = Field(default_factory=dict, description="Tất cả giới hạn tài nguyên")
