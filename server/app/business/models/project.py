"""Project Pydantic models."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base project model."""
    project_name: str = Field(..., min_length=1, max_length=100, description="Project name")
    department: str = Field(..., min_length=1, max_length=50, description="Department")
    budget: float = Field(default=0, ge=0, description="Budget")
    status: str = Field(default="ACTIVE", description="Status: ACTIVE, COMPLETED, CANCELLED")


class ProjectCreate(ProjectBase):
    """Model for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Model for updating a project."""
    project_name: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=50)
    budget: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None)


class ProjectResponse(ProjectBase):
    """Model for project response."""
    project_id: int = Field(..., description="Project ID")
    owner_username: str = Field(..., description="Owner username")
    created_at: Optional[datetime] = Field(None, description="Created timestamp")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp")
    
    class Config:
        from_attributes = True
