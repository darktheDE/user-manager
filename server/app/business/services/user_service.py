"""User management service."""

import re
from typing import List, Dict, Any, Optional
from app.business.models.user import UserCreate, UserUpdate
from app.data.oracle.user_dao import user_dao
from app.data.oracle.privilege_dao import privilege_dao


class UserService:
    """Service for user management operations."""

    def _validate_username(self, username: str) -> bool:
        """Validate username format (alphanumeric and underscore only)."""
        return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

    async def check_privilege(self, username: str, privilege: str) -> bool:
        """Check if user has required privilege."""
        try:
            return await privilege_dao.has_privilege(username, privilege)
        except Exception:
            # If privilege checking fails, assume user has privilege (for SYSTEM user)
            return True

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users from DBA_USERS."""
        return await user_dao.query_all_users()

    async def create_user(
        self,
        username: str,
        password: str,
        default_tablespace: str,
        temporary_tablespace: Optional[str] = None,
        quota: Optional[str] = None,
        profile: Optional[str] = None,
        current_user: Optional[str] = None,
    ) -> None:
        """
        Create a new user with validation and privilege checking.
        
        Args:
            username: Oracle username
            password: Oracle password
            default_tablespace: Default tablespace
            temporary_tablespace: Temporary tablespace (optional)
            quota: Quota on default tablespace (optional)
            profile: Profile name (optional)
            current_user: Current logged-in user for privilege checking
        """
        # Validate username
        if not self._validate_username(username):
            raise ValueError("Username must contain only alphanumeric characters and underscores")
        
        # Validate tablespaces - cannot be the same
        if temporary_tablespace and default_tablespace == temporary_tablespace:
            raise ValueError("Default tablespace and temporary tablespace cannot be the same")
        
        # Check CREATE USER privilege
        if current_user:
            has_privilege = await self.check_privilege(current_user, "CREATE USER")
            if not has_privilege:
                raise PermissionError(f"User {current_user} does not have CREATE USER privilege")
        
        # Create user
        try:
            await user_dao.create_user_ddl(
                username=username.upper(),
                password=password,
                default_tablespace=default_tablespace,
                temporary_tablespace=temporary_tablespace,
                quota=quota,
                profile=profile,
            )
        except Exception as e:
            # Convert Oracle errors to user-friendly messages
            error_msg = str(e)
            if "ORA-12911" in error_msg:
                raise ValueError("Permanent tablespace cannot be used as temporary tablespace. Please select different tablespaces.")
            elif "ORA-01920" in error_msg:
                raise ValueError(f"User {username} already exists")
            elif "ORA-00959" in error_msg:
                raise ValueError("Tablespace does not exist")
            else:
                raise ValueError(f"Database error: {error_msg}")

    async def update_user(
        self,
        username: str,
        password: Optional[str] = None,
        default_tablespace: Optional[str] = None,
        temporary_tablespace: Optional[str] = None,
        quota: Optional[str] = None,
        profile: Optional[str] = None,
        current_user: Optional[str] = None,
    ) -> None:
        """
        Update user with validation and privilege checking.
        
        Args:
            username: Oracle username
            password: New password (optional)
            default_tablespace: New default tablespace (optional)
            temporary_tablespace: New temporary tablespace (optional)
            quota: New quota (optional)
            profile: New profile (optional)
            current_user: Current logged-in user for privilege checking
        """
        # Validate tablespaces - cannot be the same
        if temporary_tablespace and default_tablespace and default_tablespace == temporary_tablespace:
            raise ValueError("Default tablespace and temporary tablespace cannot be the same")
        
        # Check ALTER USER privilege
        if current_user:
            has_privilege = await self.check_privilege(current_user, "ALTER USER")
            if not has_privilege:
                raise PermissionError(f"User {current_user} does not have ALTER USER privilege")
        
        # Update user
        try:
            await user_dao.alter_user_ddl(
                username=username.upper(),
                password=password,
                default_tablespace=default_tablespace,
                temporary_tablespace=temporary_tablespace,
                quota=quota,
                profile=profile,
            )
        except Exception as e:
            # Convert Oracle errors to user-friendly messages
            error_msg = str(e)
            if "ORA-12911" in error_msg:
                raise ValueError("Permanent tablespace cannot be used as temporary tablespace. Please select different tablespaces.")
            elif "ORA-00959" in error_msg:
                raise ValueError("Tablespace does not exist")
            else:
                raise ValueError(f"Database error: {error_msg}")

    async def delete_user(
        self,
        username: str,
        cascade: bool = False,
        current_user: Optional[str] = None,
    ) -> None:
        """
        Delete user with privilege checking.
        
        Args:
            username: Oracle username
            cascade: Whether to cascade drop (drop user's objects)
            current_user: Current logged-in user for privilege checking
        """
        # Check DROP USER privilege
        if current_user:
            has_privilege = await self.check_privilege(current_user, "DROP USER")
            if not has_privilege:
                raise PermissionError(f"User {current_user} does not have DROP USER privilege")
        
        # Delete user
        await user_dao.drop_user_ddl(username.upper(), cascade=cascade)

    async def lock_user(self, username: str) -> None:
        """Lock user account."""
        await user_dao.lock_user(username.upper())

    async def unlock_user(self, username: str) -> None:
        """Unlock user account."""
        await user_dao.unlock_user(username.upper())

    async def update_quota(
        self,
        username: str,
        tablespace: str,
        quota: str,
    ) -> None:
        """Update user quota on tablespace."""
        await user_dao.alter_user_ddl(
            username=username.upper(),
            quota=quota,
        )

    async def get_user_privileges(self, username: str) -> List[Dict[str, Any]]:
        """Get user privileges from DBA_SYS_PRIVS and DBA_ROLE_PRIVS."""
        return await user_dao.query_user_privileges(username.upper())

    async def get_user_roles(self, username: str) -> List[Dict[str, Any]]:
        """Get user roles from DBA_ROLE_PRIVS."""
        return await user_dao.query_user_roles(username.upper())

    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user info from application table user_info."""
        return await user_dao.query_user_info(username.upper())

    async def get_user_detail(self, username: str) -> Dict[str, Any]:
        """Get complete user detail including privileges, roles, and info."""
        user_info = await user_dao.get_user_info(username.upper())
        if not user_info:
            raise ValueError(f"User {username} not found")
        
        privileges = await self.get_user_privileges(username)
        roles = await self.get_user_roles(username)
        app_info = await self.get_user_info(username)
        
        return {
            **user_info,
            "privileges": privileges,
            "roles": roles,
            "user_info": app_info,
        }


# Global service instance
user_service = UserService()

