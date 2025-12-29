"""
Tiện ích kiểm tra quyền
======================
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


# Ánh xạ hành động -> quyền yêu cầu
REQUIRED_PRIVILEGES: Dict[str, List[str]] = {
    # Quản lý User
    "create_user": ["CREATE USER"],
    "alter_user": ["ALTER USER"],
    "drop_user": ["DROP USER"],
    
    # Quản lý Profile
    "create_profile": ["CREATE PROFILE"],
    "alter_profile": ["ALTER PROFILE"],
    "drop_profile": ["DROP PROFILE"],
    
    # Quản lý Role
    "create_role": ["CREATE ROLE"],
    "alter_role": ["ALTER ANY ROLE"],
    "drop_role": ["DROP ANY ROLE"],
    "grant_role": ["GRANT ANY ROLE"],
    
    # Session
    "login": ["CREATE SESSION"],
    
    # Quyền trên Table
    "select_any_table": ["SELECT ANY TABLE"],
    
    # Cấp quyền
    "grant_system_privilege": ["GRANT ANY PRIVILEGE"],
}


class PermissionChecker:
    """Lớp kiểm tra quyền user trước khi thực hiện hành động."""
    
    async def check_permission(
        self, 
        username: str, 
        action: str,
        raise_error: bool = True,
    ) -> bool:
        """
        Kiểm tra user có quyền thực hiện hành động hay không.
        
        Args:
            username: Tên đăng nhập Oracle
            action: Hành động cần kiểm tra (ví dụ: 'create_user')
            raise_error: Nếu True, raise PermissionError khi không có quyền
            
        Returns:
            True nếu user có quyền
            
        Raises:
            PermissionError: Nếu user không có quyền và raise_error=True
        """
        required_privs = REQUIRED_PRIVILEGES.get(action, [])
        
        if not required_privs:
            # Hành động này không yêu cầu quyền cụ thể
            return True
        
        # User admin bỏ qua kiểm tra
        if username.upper() in ("SYS", "SYSTEM"):
            return True
        
        # Kiểm tra từng quyền yêu cầu
        for priv in required_privs:
            has_priv = await privilege_dao.has_privilege(username, priv)
            if has_priv:
                return True
        
        # User không có quyền
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
        Kiểm tra nhiều quyền cùng lúc.
        
        Returns:
            Dict ánh xạ hành động -> có quyền hay không
        """
        results = {}
        for action in actions:
            results[action] = await self.check_permission(
                username, action, raise_error=False
            )
        return results

    async def get_user_capabilities(self, username: str) -> Dict[str, bool]:
        """
        Lấy tất cả các khả năng (hành động được phép) của user.
        
        Returns:
            Dict ánh xạ hành động -> có thể thực hiện hay không
        """
        return await self.check_multiple_permissions(
            username, 
            list(REQUIRED_PRIVILEGES.keys())
        )


# Instance toàn cục
permission_checker = PermissionChecker()


# Decorator để bảo vệ route
def require_privilege(action: str):
    """
    Decorator yêu cầu quyền cho route handler.
    
    Cách sử dụng:
        @require_privilege("create_user")
        async def create_user_handler(request: Request, ...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Tìm request từ args
            request = None
            for arg in args:
                if hasattr(arg, 'session'):
                    request = arg
                    break
            
            if request is None:
                # Thử tìm trong kwargs
                request = kwargs.get('request')
            
            if request is None:
                raise ValueError("Không tìm thấy request object")
            
            # Lấy username từ session
            from app.presentation.middleware import get_session
            session = get_session(request)
            username = session.get("username")
            
            if not username:
                raise PermissionError("Chưa đăng nhập")
            
            # Kiểm tra quyền
            await permission_checker.check_permission(username, action)
            
            # Thực thi hàm gốc
            return await func(*args, **kwargs)
        
        # Giữ nguyên metadata của hàm
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator
