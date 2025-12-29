"""Authentication service with bcrypt password verification."""

from typing import Optional
from app.business.models.user import LoginRequest, SessionUser
from app.business.utils.password import hash_password, verify_password
from app.data.oracle.user_dao import user_dao
from app.data.oracle.user_info_dao import user_info_dao


class AuthService:
    """Service for authentication operations."""

    async def login(self, username: str, password: str) -> Optional[SessionUser]:
        """
        Login user by verifying password with bcrypt AND Oracle.
        
        Flow:
        1. Check if user exists in user_info table
        2. If exists: verify bcrypt password hash
        3. Also verify with Oracle (for Oracle-level access)
        4. Return session user if successful
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            SessionUser if login successful, None otherwise
        """
        # Step 1: Check user_info table for bcrypt verification
        user_info = await user_info_dao.get_by_username(username)
        
        if user_info:
            # Verify with bcrypt hash
            if not verify_password(password, user_info.get("password_hash", "")):
                return None
        
        # Step 2: Always verify with Oracle as well (for Oracle-level privileges)
        is_valid = await user_dao.verify_password(username, password)
        
        if not is_valid:
            return None
        
        # Step 3: Get Oracle user info from DBA_USERS
        oracle_user = await user_dao.get_user_info(username)
        
        if not oracle_user:
            return None
        
        return SessionUser(
            username=oracle_user["username"],
            account_status=oracle_user.get("account_status"),
            created=str(oracle_user.get("created")) if oracle_user.get("created") else None,
            default_tablespace=oracle_user.get("default_tablespace"),
            temporary_tablespace=oracle_user.get("temporary_tablespace"),
        )

    async def register_user_info(
        self,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        department: Optional[str] = None,
    ) -> int:
        """
        Register user in user_info table with hashed password.
        
        Args:
            username: Username (must exist in Oracle)
            password: Plain text password (will be hashed)
            full_name: Full name
            email: Email
            phone: Phone
            department: Department
            
        Returns:
            New user_id
        """
        # Hash password with bcrypt
        password_hash = hash_password(password)
        
        # Create user_info record
        return await user_info_dao.create(
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            email=email,
            phone=phone,
            department=department,
        )

    async def update_password(self, username: str, new_password: str) -> None:
        """
        Update password hash in user_info table.
        
        Args:
            username: Username
            new_password: New plain text password (will be hashed)
        """
        password_hash = hash_password(new_password)
        await user_info_dao.update_password_hash(username, password_hash)

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
