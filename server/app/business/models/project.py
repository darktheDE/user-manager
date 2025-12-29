"""Các model Pydantic cho Project."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Model project cơ sở."""
    project_name: str = Field(..., min_length=1, max_length=100, description="Tên dự án")
    department: str = Field(..., min_length=1, max_length=50, description="Phòng ban")
    budget: float = Field(default=0, ge=0, description="Ngân sách")
    status: str = Field(default="ACTIVE", description="Trạng thái: ACTIVE, COMPLETED, CANCELLED")


class ProjectCreate(ProjectBase):
    """Model tạo dự án mới."""
    pass


class ProjectUpdate(BaseModel):
    """Model cập nhật dự án."""
    project_name: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=50)
    budget: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None)


class ProjectResponse(ProjectBase):
    """Model phản hồi dự án."""
    project_id: int = Field(..., description="ID dự án")
    owner_username: str = Field(..., description="Username người sở hữu")
    created_at: Optional[datetime] = Field(None, description="Thời gian tạo")
    updated_at: Optional[datetime] = Field(None, description="Thời gian cập nhật")
    
    class Config:
        from_attributes = True
