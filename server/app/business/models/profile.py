"""Profile Pydantic models."""

from typing import Optional
from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    """Base profile model with common fields."""
    sessions_per_user: str = Field(default="DEFAULT", description="SESSIONS_PER_USER limit")
    connect_time: str = Field(default="DEFAULT", description="CONNECT_TIME limit in minutes")
    idle_time: str = Field(default="DEFAULT", description="IDLE_TIME limit in minutes")


class ProfileCreate(ProfileBase):
    """Model for creating a new profile."""
    profile_name: str = Field(..., min_length=1, max_length=30, description="Profile name")


class ProfileUpdate(BaseModel):
    """Model for updating a profile."""
    sessions_per_user: Optional[str] = Field(None, description="SESSIONS_PER_USER limit")
    connect_time: Optional[str] = Field(None, description="CONNECT_TIME limit in minutes")
    idle_time: Optional[str] = Field(None, description="IDLE_TIME limit in minutes")


class ProfileResponse(ProfileBase):
    """Model for profile response."""
    profile: str = Field(..., description="Profile name")
    user_count: int = Field(default=0, description="Number of users using this profile")
    
    class Config:
        from_attributes = True


class ProfileDetail(ProfileResponse):
    """Model for detailed profile information."""
    resources: dict = Field(default_factory=dict, description="All resource limits")
