"""
Permission Checker Utility
==========================
Kiểm tra quyền của user trước khi thực hiện action theo yêu cầu đề tài.

Các quyền đánh dấu (*) trong đề tài cần được kiểm tra:
- CREATE USER*, ALTER USER*, DROP USER*
- CREATE PROFILE*, ALTER PROFILE*, DROP PROFILE*
- CREATE ROLE*, ALTER ANY ROLE*, DROP ANY ROLE*, GRANT ANY ROLE*
- CREATE SESSION*
- SELECT ANY TABLE*
"""

from typing import Dict, List, Optional
from app.data.oracle.privilege_dao import privilege_dao


# Mapping action -> required privileges
REQUIRED_PRIVILEGES: Dict[str, List[str]] = {
    # User Management
    "create_user": ["CREATE USER"],
    "alter_user": ["ALTER USER"],
    "drop_user": ["DROP USER"],
    
    # Profile Management
    "create_profile": ["CREATE PROFILE"],
    "alter_profile": ["ALTER PROFILE"],
    "drop_profile": ["DROP PROFILE"],
    
    # Role Management
    "create_role": ["CREATE ROLE"],
    "alter_role": ["ALTER ANY ROLE"],
    "drop_role": ["DROP ANY ROLE"],
    "grant_role": ["GRANT ANY ROLE"],
    
    # Session
    "login": ["CREATE SESSION"],
    
    # Table privileges
    "select_any_table": ["SELECT ANY TABLE"],
    
    # Grant privileges
    "grant_system_privilege": ["GRANT ANY PRIVILEGE"],
}


class PermissionChecker:
    """Check user permissions before executing actions."""
    
    async def check_permission(
        self, 
        username: str, 
        action: str,
        raise_error: bool = True,
    ) -> bool:
        """
        Check if user has required privilege for an action.
        
        Args:
            username: Oracle username
            action: Action to check (e.g., 'create_user')
            raise_error: If True, raise PermissionError on failure
            
        Returns:
            True if user has permission
            
        Raises:
            PermissionError: If user lacks permission and raise_error=True
        """
        required_privs = REQUIRED_PRIVILEGES.get(action, [])
        
        if not required_privs:
            # No specific privilege required for this action
            return True
        
        # Admin users bypass check
        if username.upper() in ("SYS", "SYSTEM"):
            return True
        
        # Check each required privilege
        for priv in required_privs:
            has_priv = await privilege_dao.has_privilege(username, priv)
            if has_priv:
                return True
        
        # User lacks permission
        if raise_error:
            raise PermissionError(
                f"Bạn không có quyền thực hiện hành động này. "
                f"Yêu cầu quyền: {', '.join(required_privs)}"
            )
        
        return False

    async def check_multiple_permissions(
        self, 
        username: str, 
        actions: List[str],
    ) -> Dict[str, bool]:
        """
        Check multiple permissions at once.
        
        Returns:
            Dict mapping action -> has_permission
        """
        results = {}
        for action in actions:
            results[action] = await self.check_permission(
                username, action, raise_error=False
            )
        return results

    async def get_user_capabilities(self, username: str) -> Dict[str, bool]:
        """
        Get all capabilities (allowed actions) for a user.
        
        Returns:
            Dict mapping action -> can_perform
        """
        return await self.check_multiple_permissions(
            username, 
            list(REQUIRED_PRIVILEGES.keys())
        )


# Global instance
permission_checker = PermissionChecker()


# Decorator for route protection
def require_privilege(action: str):
    """
    Decorator to require privilege for a route handler.
    
    Usage:
        @require_privilege("create_user")
        async def create_user_handler(request: Request, ...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get request from args
            request = None
            for arg in args:
                if hasattr(arg, 'session'):
                    request = arg
                    break
            
            if request is None:
                # Try kwargs
                request = kwargs.get('request')
            
            if request is None:
                raise ValueError("Could not find request object")
            
            # Get username from session
            from app.presentation.middleware import get_session
            session = get_session(request)
            username = session.get("username")
            
            if not username:
                raise PermissionError("Not authenticated")
            
            # Check permission
            await permission_checker.check_permission(username, action)
            
            # Execute original function
            return await func(*args, **kwargs)
        
        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator
