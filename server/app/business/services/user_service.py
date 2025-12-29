"""Dịch vụ quản lý User."""

import re
from typing import List, Dict, Any, Optional
from app.business.models.user import UserCreate, UserUpdate
from app.data.oracle.user_dao import user_dao
from app.data.oracle.privilege_dao import privilege_dao


class UserService:
    """Dịch vụ xử lý các thao tác quản lý user."""

    def _validate_username(self, username: str) -> bool:
        """Kiểm tra định dạng username (chỉ chứa chữ, số và dấu gạch dưới)."""
        return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

    async def check_privilege(self, username: str, privilege: str) -> bool:
        """Kiểm tra user có quyền yêu cầu hay không."""
        try:
            return await privilege_dao.has_privilege(username, privilege)
        except Exception:
            # Nếu kiểm tra quyền thất bại, giả sử user có quyền (cho SYSTEM user)
            return True

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Lấy tất cả users từ DBA_USERS."""
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
        Tạo user mới với kiểm tra validation và quyền.
        
        Args:
            username: Tên đăng nhập Oracle
            password: Mật khẩu Oracle
            default_tablespace: Tablespace mặc định
            temporary_tablespace: Tablespace tạm (tùy chọn)
            quota: Hạn mức trên tablespace mặc định (tùy chọn)
            profile: Tên profile (tùy chọn)
            current_user: User đang đăng nhập để kiểm tra quyền
        """
        # Kiểm tra định dạng username
        if not self._validate_username(username):
            raise ValueError("Username chỉ được chứa chữ cái, số và dấu gạch dưới")
        
        # Kiểm tra tablespaces - không được trùng nhau
        if temporary_tablespace and default_tablespace == temporary_tablespace:
            raise ValueError("Tablespace mặc định và tablespace tạm không được giống nhau")
        
        # Kiểm tra quyền CREATE USER
        if current_user:
            has_privilege = await self.check_privilege(current_user, "CREATE USER")
            if not has_privilege:
                raise PermissionError(f"User {current_user} không có quyền CREATE USER")
        
        # Tạo user
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
            # Chuyển đổi lỗi Oracle thành thông báo thân thiện
            error_msg = str(e)
            if "ORA-12911" in error_msg:
                raise ValueError("Tablespace vĩnh viễn không thể dùng làm tablespace tạm. Vui lòng chọn tablespace khác.")
            elif "ORA-01920" in error_msg:
                raise ValueError(f"User {username} đã tồn tại")
            elif "ORA-00959" in error_msg:
                raise ValueError("Tablespace không tồn tại")
            else:
                raise ValueError(f"Lỗi database: {error_msg}")

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
        Cập nhật user với kiểm tra validation và quyền.
        
        Args:
            username: Tên đăng nhập Oracle
            password: Mật khẩu mới (tùy chọn)
            default_tablespace: Tablespace mặc định mới (tùy chọn)
            temporary_tablespace: Tablespace tạm mới (tùy chọn)
            quota: Hạn mức mới (tùy chọn)
            profile: Profile mới (tùy chọn)
            current_user: User đang đăng nhập để kiểm tra quyền
        """
        # Kiểm tra tablespaces - không được trùng nhau
        if temporary_tablespace and default_tablespace and default_tablespace == temporary_tablespace:
            raise ValueError("Tablespace mặc định và tablespace tạm không được giống nhau")
        
        # Kiểm tra quyền ALTER USER
        if current_user:
            has_privilege = await self.check_privilege(current_user, "ALTER USER")
            if not has_privilege:
                raise PermissionError(f"User {current_user} không có quyền ALTER USER")
        
        # Cập nhật user
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
            # Chuyển đổi lỗi Oracle thành thông báo thân thiện
            error_msg = str(e)
            if "ORA-12911" in error_msg:
                raise ValueError("Tablespace vĩnh viễn không thể dùng làm tablespace tạm. Vui lòng chọn tablespace khác.")
            elif "ORA-00959" in error_msg:
                raise ValueError("Tablespace không tồn tại")
            else:
                raise ValueError(f"Lỗi database: {error_msg}")

    async def delete_user(
        self,
        username: str,
        cascade: bool = False,
        current_user: Optional[str] = None,
    ) -> None:
        """
        Xóa user với kiểm tra quyền.
        
        Args:
            username: Tên đăng nhập Oracle
            cascade: Có xóa cascade không (xóa cả objects của user)
            current_user: User đang đăng nhập để kiểm tra quyền
        """
        # Kiểm tra quyền DROP USER
        if current_user:
            has_privilege = await self.check_privilege(current_user, "DROP USER")
            if not has_privilege:
                raise PermissionError(f"User {current_user} không có quyền DROP USER")
        
        # Xóa user
        await user_dao.drop_user_ddl(username.upper(), cascade=cascade)

    async def lock_user(self, username: str) -> None:
        """Khóa tài khoản user."""
        await user_dao.lock_user(username.upper())

    async def unlock_user(self, username: str) -> None:
        """Mở khóa tài khoản user."""
        await user_dao.unlock_user(username.upper())

    async def update_quota(
        self,
        username: str,
        tablespace: str,
        quota: str,
    ) -> None:
        """Cập nhật hạn mức quota của user trên tablespace."""
        await user_dao.alter_user_ddl(
            username=username.upper(),
            quota=quota,
        )

    async def get_user_privileges(self, username: str) -> List[Dict[str, Any]]:
        """Lấy quyền của user từ DBA_SYS_PRIVS và DBA_ROLE_PRIVS."""
        return await user_dao.query_user_privileges(username.upper())

    async def get_user_roles(self, username: str) -> List[Dict[str, Any]]:
        """Lấy roles của user từ DBA_ROLE_PRIVS."""
        return await user_dao.query_user_roles(username.upper())

    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin user từ bảng ứng dụng user_info."""
        return await user_dao.query_user_info(username.upper())

    async def get_user_detail(self, username: str) -> Dict[str, Any]:
        """Lấy thông tin chi tiết user bao gồm privileges, roles, và info."""
        user_info = await user_dao.get_user_info(username.upper())
        if not user_info:
            raise ValueError(f"Không tìm thấy user {username}")
        
        privileges = await self.get_user_privileges(username)
        roles = await self.get_user_roles(username)
        app_info = await self.get_user_info(username)
        
        return {
            **user_info,
            "privileges": privileges,
            "roles": roles,
            "user_info": app_info,
        }


# Instance dịch vụ toàn cục
user_service = UserService()
