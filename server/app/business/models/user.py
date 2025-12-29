"""User Pydantic models."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Model for login request."""

    username: str = Field(..., min_length=1, max_length=100, description="Oracle username")
    password: str = Field(..., min_length=1, description="Oracle password")


class SessionUser(BaseModel):
    """Model for session user data."""

    username: str
    account_status: Optional[str] = None
    created: Optional[str] = None
    default_tablespace: Optional[str] = None
    temporary_tablespace: Optional[str] = None


class UserCreate(BaseModel):
    """Model for creating a new user."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)
    default_tablespace: str = Field(..., min_length=1)
    temporary_tablespace: Optional[str] = None
    quota: Optional[str] = None  # e.g., "100M", "UNLIMITED"
    profile: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for updating a user."""

    password: Optional[str] = None
    default_tablespace: Optional[str] = None
    temporary_tablespace: Optional[str] = None
    quota: Optional[str] = None
    profile: Optional[str] = None


class UserResponse(BaseModel):
    """Model for user response."""

    username: str
    account_status: str
    created: Optional[str] = None
    default_tablespace: Optional[str] = None
    temporary_tablespace: Optional[str] = None
    profile: Optional[str] = None
    lock_date: Optional[str] = None


class UserDetail(BaseModel):
    """Model for detailed user information."""

    username: str
    account_status: str
    created: Optional[str] = None
    default_tablespace: Optional[str] = None
    temporary_tablespace: Optional[str] = None
    profile: Optional[str] = None
    lock_date: Optional[str] = None
    roles: list[dict] = []
    privileges: list[dict] = []
    user_info: Optional[dict] = None  # From user_info table

