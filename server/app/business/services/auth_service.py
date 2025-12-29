"""Dịch vụ xác thực với bcrypt để mã hóa mật khẩu."""

from typing import Optional
from app.business.models.user import LoginRequest, SessionUser
from app.business.utils.password import hash_password, verify_password
from app.data.oracle.user_dao import user_dao
from app.data.oracle.user_info_dao import user_info_dao


class AuthService:
    """Dịch vụ xử lý các thao tác xác thực."""

    async def login(self, username: str, password: str) -> Optional[SessionUser]:
        """
        Đăng nhập người dùng bằng cách xác minh mật khẩu với bcrypt VÀ Oracle.
        
        Quy trình:
        1. Kiểm tra user có tồn tại trong bảng user_info không
        2. Nếu có: xác minh mật khẩu với bcrypt hash
        3. Đồng thời xác minh với Oracle (để có quyền truy cập Oracle)
        4. Trả về session user nếu thành công
        
        Args:
            username: Tên đăng nhập
            password: Mật khẩu dạng plain text
            
        Returns:
            SessionUser nếu đăng nhập thành công, None nếu thất bại
        """
        # Bước 1: Kiểm tra bảng user_info để xác minh bcrypt
        user_info = await user_info_dao.get_by_username(username)
        
        if user_info:
            # Xác minh với bcrypt hash
            if not verify_password(password, user_info.get("password_hash", "")):
                return None
        
        # Bước 2: Luôn xác minh với Oracle (để có quyền Oracle-level)
        is_valid = await user_dao.verify_password(username, password)
        
        if not is_valid:
            return None
        
        # Bước 3: Lấy thông tin user Oracle từ DBA_USERS
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
        Đăng ký user vào bảng user_info với mật khẩu đã được hash.
        
        Args:
            username: Tên đăng nhập (phải tồn tại trong Oracle)
            password: Mật khẩu dạng plain text (sẽ được hash)
            full_name: Họ tên đầy đủ
            email: Email
            phone: Số điện thoại
            department: Phòng ban
            
        Returns:
            user_id mới được tạo
        """
        # Hash mật khẩu với bcrypt
        password_hash = hash_password(password)
        
        # Tạo bản ghi user_info
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
        Cập nhật password hash trong bảng user_info.
        
        Args:
            username: Tên đăng nhập
            new_password: Mật khẩu mới dạng plain text (sẽ được hash)
        """
        password_hash = hash_password(new_password)
        await user_info_dao.update_password_hash(username, password_hash)

    async def get_current_user(self, username: str) -> Optional[SessionUser]:
        """
        Lấy thông tin user hiện tại từ session.
        
        Args:
            username: Tên đăng nhập Oracle từ session
            
        Returns:
            SessionUser nếu tìm thấy, None nếu không
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


# Instance dịch vụ toàn cục
auth_service = AuthService()
