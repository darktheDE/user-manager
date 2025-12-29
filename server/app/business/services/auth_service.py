"""Authentication service."""

from typing import Optional
from app.business.models.user import LoginRequest, SessionUser
from app.data.oracle.user_dao import user_dao


class AuthService:
    """Service for authentication operations."""

    async def login(self, username: str, password: str) -> Optional[SessionUser]:
        """
        Login user by verifying password with Oracle.
        
        Args:
            username: Oracle username
            password: Oracle password
            
        Returns:
            SessionUser if login successful, None otherwise
        """
        # Verify password by attempting connection
        is_valid = await user_dao.verify_password(username, password)
        
        if not is_valid:
            return None
        
        # Get user info from DBA_USERS
        user_info = await user_dao.get_user_info(username)
        
        if not user_info:
            return None
        
        return SessionUser(
            username=user_info["username"],
            account_status=user_info.get("account_status"),
            created=str(user_info.get("created")) if user_info.get("created") else None,
            default_tablespace=user_info.get("default_tablespace"),
            temporary_tablespace=user_info.get("temporary_tablespace"),
        )

    async def get_current_user(self, username: str) -> Optional[SessionUser]:
        """
        Get current user information from session.
        
        Args:
            username: Oracle username from session
            
        Returns:
            SessionUser if found, None otherwise
        """
        user_info = await user_dao.get_user_info(username)
        
        if not user_info:
            return None
        
        return SessionUser(
            username=user_info["username"],
            account_status=user_info.get("account_status"),
            created=str(user_info.get("created")) if user_info.get("created") else None,
            default_tablespace=user_info.get("default_tablespace"),
            temporary_tablespace=user_info.get("temporary_tablespace"),
        )


# Global service instance
auth_service = AuthService()

