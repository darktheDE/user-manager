"""Dịch vụ quản lý Profile."""

import re
from typing import List, Dict, Any, Optional
from app.data.oracle.profile_dao import profile_dao


class ProfileService:
    """Dịch vụ cho các thao tác quản lý profile."""

    def _validate_profile_name(self, profile_name: str) -> bool:
        """Kiểm tra định dạng tên profile (chỉ chứa chữ, số và gạch dưới)."""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', profile_name))

    def _validate_resource_limit(self, value: str) -> bool:
        """
        Kiểm tra giá trị giới hạn tài nguyên.
        Giá trị hợp lệ: UNLIMITED, DEFAULT, hoặc số nguyên dương.
        """
        if value.upper() in ("UNLIMITED", "DEFAULT"):
            return True
        try:
            int_val = int(value)
            return int_val > 0
        except ValueError:
            return False

    def _normalize_resource_limit(self, value: str) -> str:
        """Chuẩn hóa giá trị giới hạn tài nguyên về chữ hoa hoặc chuỗi số nguyên."""
        upper_val = value.upper().strip()
        if upper_val in ("UNLIMITED", "DEFAULT"):
            return upper_val
        return value.strip()

    async def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Lấy tất cả profiles từ DBA_PROFILES."""
        return await profile_dao.query_all_profiles()

    async def get_profile_detail(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết cho một profile cụ thể."""
        return await profile_dao.get_profile_detail(profile_name)

    async def create_profile(
        self,
        profile_name: str,
        sessions_per_user: str = "DEFAULT",
        connect_time: str = "DEFAULT",
        idle_time: str = "DEFAULT",
    ) -> None:
        """
        Tạo profile mới với kiểm tra validation.
        
        Args:
            profile_name: Tên profile
            sessions_per_user: Giới hạn SESSIONS_PER_USER
            connect_time: Giới hạn CONNECT_TIME
            idle_time: Giới hạn IDLE_TIME
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        # Kiểm tra tên profile
        if not self._validate_profile_name(profile_name):
            raise ValueError(
                "Tên profile không hợp lệ. Phải bắt đầu bằng chữ cái và chỉ chứa "
                "chữ cái, số và dấu gạch dưới."
            )
        
        # Kiểm tra tên dành riêng
        if profile_name.upper() == "DEFAULT":
            raise ValueError("Không được tạo profile tên 'DEFAULT'. Đây là tên dành riêng.")
        
        # Kiểm tra nếu profile đã tồn tại
        if await profile_dao.profile_exists(profile_name):
            raise ValueError(f"Profile '{profile_name}' đã tồn tại.")
        
        # Kiểm tra giới hạn tài nguyên
        for name, value in [
            ("SESSIONS_PER_USER", sessions_per_user),
            ("CONNECT_TIME", connect_time),
            ("IDLE_TIME", idle_time),
        ]:
            if not self._validate_resource_limit(value):
                raise ValueError(
                    f"Giá trị {name} không hợp lệ: '{value}'. "
                    "Phải là UNLIMITED, DEFAULT, hoặc một số nguyên dương."
                )
        
        # Chuẩn hóa và tạo
        await profile_dao.create_profile_ddl(
            profile_name=profile_name,
            sessions_per_user=self._normalize_resource_limit(sessions_per_user),
            connect_time=self._normalize_resource_limit(connect_time),
            idle_time=self._normalize_resource_limit(idle_time),
        )

    async def update_profile(
        self,
        profile_name: str,
        sessions_per_user: Optional[str] = None,
        connect_time: Optional[str] = None,
        idle_time: Optional[str] = None,
    ) -> None:
        """
        Cập nhật giới hạn tài nguyên profile.
        
        Args:
            profile_name: Tên profile
            sessions_per_user: Giới hạn SESSIONS_PER_USER mới (tùy chọn)
            connect_time: Giới hạn CONNECT_TIME mới (tùy chọn)
            idle_time: Giới hạn IDLE_TIME mới (tùy chọn)
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        # Kiểm tra nếu profile tồn tại
        if not await profile_dao.profile_exists(profile_name):
            raise ValueError(f"Profile '{profile_name}' không tồn tại.")
        
        # Validate các giá trị giới hạn được cung cấp
        normalized_values = {}
        
        if sessions_per_user is not None:
            if not self._validate_resource_limit(sessions_per_user):
                raise ValueError(
                    f"Giá trị SESSIONS_PER_USER không hợp lệ: '{sessions_per_user}'. "
                    "Phải là UNLIMITED, DEFAULT, hoặc một số nguyên dương."
                )
            normalized_values["sessions_per_user"] = self._normalize_resource_limit(sessions_per_user)
        
        if connect_time is not None:
            if not self._validate_resource_limit(connect_time):
                raise ValueError(
                    f"Giá trị CONNECT_TIME không hợp lệ: '{connect_time}'. "
                    "Phải là UNLIMITED, DEFAULT, hoặc một số nguyên dương."
                )
            normalized_values["connect_time"] = self._normalize_resource_limit(connect_time)
        
        if idle_time is not None:
            if not self._validate_resource_limit(idle_time):
                raise ValueError(
                    f"Giá trị IDLE_TIME không hợp lệ: '{idle_time}'. "
                    "Phải là UNLIMITED, DEFAULT, hoặc một số nguyên dương."
                )
            normalized_values["idle_time"] = self._normalize_resource_limit(idle_time)
        
        if not normalized_values:
            return  # Không có gì để update
        
        await profile_dao.alter_profile_ddl(profile_name, **normalized_values)

    async def delete_profile(self, profile_name: str, cascade: bool = False) -> None:
        """
        Xóa một profile.
        
        Args:
            profile_name: Tên profile
            cascade: Có xóa cascade không (gán lại user về profile DEFAULT)
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        # Kiểm tra profile dành riêng
        if profile_name.upper() == "DEFAULT":
            raise ValueError("Không được xóa profile DEFAULT.")
        
        # Kiểm tra nếu profile tồn tại
        if not await profile_dao.profile_exists(profile_name):
            raise ValueError(f"Profile '{profile_name}' không tồn tại.")
        
        # Kiểm tra user đang dùng profile nếu không cascade
        if not cascade:
            users = await profile_dao.query_profile_users(profile_name)
            if users:
                raise ValueError(
                    f"Profile '{profile_name}' đang được gán cho {len(users)} user(s). "
                    "Sử dụng tùy chọn cascade để gán lại họ về profile DEFAULT."
                )
        
        await profile_dao.drop_profile_ddl(profile_name, cascade=cascade)

    async def get_profile_users(self, profile_name: str) -> List[Dict[str, Any]]:
        """Lấy danh sách người dùng được gán vào profile."""
        return await profile_dao.query_profile_users(profile_name)


# Instance dịch vụ toàn cục
profile_service = ProfileService()
