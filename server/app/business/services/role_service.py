"""Dịch vụ quản lý vai trò (Role)."""

import re
from typing import List, Dict, Any, Optional
from app.data.oracle.role_dao import role_dao


class RoleService:
    """Dịch vụ cho các thao tác quản lý role."""

    # Các role Oracle dành riêng không nên sửa đổi
    RESERVED_ROLES = {
        "DBA", "CONNECT", "RESOURCE", "PUBLIC", "SELECT_CATALOG_ROLE",
        "EXECUTE_CATALOG_ROLE", "DELETE_CATALOG_ROLE", "EXP_FULL_DATABASE",
        "IMP_FULL_DATABASE", "RECOVERY_CATALOG_OWNER", "AQ_ADMINISTRATOR_ROLE",
        "AQ_USER_ROLE", "DATAPUMP_EXP_FULL_DATABASE", "DATAPUMP_IMP_FULL_DATABASE",
    }

    def _validate_role_name(self, role_name: str) -> bool:
        """Kiểm tra định dạng tên role (chỉ chứa chữ, số và gạch dưới)."""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', role_name))

    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Lấy tất cả roles từ DBA_ROLES."""
        return await role_dao.query_all_roles()

    async def get_role_detail(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết cho một role cụ thể bao gồm quyền và người được cấp."""
        role = await role_dao.get_role_detail(role_name)
        if not role:
            return None
        
        # Lấy quyền và người được cấp
        role["privileges"] = await role_dao.query_role_privileges(role_name)
        role["grantees"] = await role_dao.query_role_users(role_name)
        
        return role

    async def create_role(
        self,
        role_name: str,
        password: Optional[str] = None,
    ) -> None:
        """
        Tạo role mới với kiểm tra validation.
        
        Args:
            role_name: Tên role
            password: Mật khẩu role (tùy chọn)
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        # Kiểm tra tên role
        if not self._validate_role_name(role_name):
            raise ValueError(
                "Tên role không hợp lệ. Phải bắt đầu bằng chữ cái và chỉ chứa "
                "chữ cái, số và dấu gạch dưới."
            )
        
        # Kiểm tra tên dành riêng
        if role_name.upper() in self.RESERVED_ROLES:
            raise ValueError(f"Không thể tạo role '{role_name}'. Đây là role Oracle dành riêng.")
        
        # Kiểm tra nếu role đã tồn tại
        if await role_dao.role_exists(role_name):
            raise ValueError(f"Role '{role_name}' đã tồn tại.")
        
        await role_dao.create_role_ddl(role_name, password)

    async def update_role(
        self,
        role_name: str,
        password: Optional[str] = None,
        remove_password: bool = False,
    ) -> None:
        """
        Cập nhật mật khẩu role.
        
        Args:
            role_name: Tên role
            password: Mật khẩu mới (tùy chọn)
            remove_password: Nếu True, xóa yêu cầu mật khẩu
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        # Kiểm tra role dành riêng
        if role_name.upper() in self.RESERVED_ROLES:
            raise ValueError(f"Không thể sửa đổi role Oracle dành riêng '{role_name}'.")
        
        # Kiểm tra nếu role tồn tại
        if not await role_dao.role_exists(role_name):
            raise ValueError(f"Role '{role_name}' không tồn tại.")
        
        await role_dao.alter_role_ddl(role_name, password, remove_password)

    async def delete_role(self, role_name: str) -> None:
        """
        Xóa một role.
        
        Args:
            role_name: Tên role
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        # Kiểm tra role dành riêng
        if role_name.upper() in self.RESERVED_ROLES:
            raise ValueError(f"Không thể xóa role Oracle dành riêng '{role_name}'.")
        
        # Kiểm tra nếu role tồn tại
        if not await role_dao.role_exists(role_name):
            raise ValueError(f"Role '{role_name}' không tồn tại.")
        
        await role_dao.drop_role_ddl(role_name)

    async def get_role_privileges(self, role_name: str) -> List[Dict[str, Any]]:
        """Lấy các quyền được cấp cho role."""
        return await role_dao.query_role_privileges(role_name)

    async def get_role_users(self, role_name: str) -> List[Dict[str, Any]]:
        """Lấy danh sách users/roles đã được cấp role này."""
        return await role_dao.query_role_users(role_name)


# Instance dịch vụ toàn cục
role_service = RoleService()
