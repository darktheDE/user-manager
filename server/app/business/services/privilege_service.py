"""Dịch vụ quản lý quyền hạn."""

import re
from typing import List, Dict, Any
from app.data.oracle.privilege_dao import privilege_dao


class PrivilegeService:
    """Dịch vụ cho các thao tác quản lý quyền hạn."""

    # Các quyền hệ thống phổ biến
    COMMON_SYSTEM_PRIVILEGES = [
        "CREATE SESSION",
        "CREATE TABLE",
        "CREATE VIEW",
        "CREATE PROCEDURE",
        "CREATE SEQUENCE",
        "CREATE TRIGGER",
        "CREATE TYPE",
        "CREATE SYNONYM",
        "CREATE PUBLIC SYNONYM",
        "DROP ANY TABLE",
        "SELECT ANY TABLE",
        "INSERT ANY TABLE",
        "UPDATE ANY TABLE",
        "DELETE ANY TABLE",
        "ALTER ANY TABLE",
        "CREATE USER",
        "ALTER USER",
        "DROP USER",
        "CREATE ROLE",
        "DROP ANY ROLE",
        "GRANT ANY ROLE",
        "CREATE PROFILE",
        "ALTER PROFILE",
        "DROP PROFILE",
        "UNLIMITED TABLESPACE",
    ]

    def _validate_identifier(self, name: str) -> bool:
        """Kiểm tra định dạng định danh Oracle."""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_$#]*$', name))

    async def get_all_system_privileges(self) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả quyền hệ thống."""
        return await privilege_dao.query_all_system_privileges()

    async def get_common_privileges(self) -> List[str]:
        """Lấy danh sách các quyền hệ thống phổ biến cho UI."""
        return self.COMMON_SYSTEM_PRIVILEGES

    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Lấy tất cả roles có thể cấp."""
        return await privilege_dao.query_all_roles()

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Lấy tất cả users để cấp quyền."""
        return await privilege_dao.query_all_users()

    async def get_grantee_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """Lấy tất cả quyền/roles đã cấp cho user hoặc role."""
        return await privilege_dao.query_grantee_privileges(grantee)

    async def grant_system_privilege(
        self,
        privilege: str,
        grantee: str,
        with_admin: bool = False,
    ) -> None:
        """
        Cấp quyền hệ thống cho user/role.
        
        Args:
            privilege: Tên quyền hệ thống
            grantee: Tên user hoặc role
            with_admin: Cấp kèm ADMIN OPTION
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Tên người được cấp không hợp lệ.")
        
        if not privilege:
            raise ValueError("Tên quyền là bắt buộc.")
        
        await privilege_dao.grant_system_privilege_ddl(privilege, grantee, with_admin)

    async def revoke_system_privilege(self, privilege: str, grantee: str) -> None:
        """
        Thu hồi quyền hệ thống từ user/role.
        
        Args:
            privilege: Tên quyền hệ thống
            grantee: Tên user hoặc role
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Tên người được cấp không hợp lệ.")
        
        if not privilege:
            raise ValueError("Tên quyền là bắt buộc.")
        
        await privilege_dao.revoke_system_privilege_ddl(privilege, grantee)

    async def grant_role(
        self,
        role: str,
        grantee: str,
        with_admin: bool = False,
    ) -> None:
        """
        Cấp role cho user/role.
        
        Args:
            role: Tên role
            grantee: Tên user hoặc role
            with_admin: Cấp kèm ADMIN OPTION
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Tên người được cấp không hợp lệ.")
        
        if not role or not self._validate_identifier(role):
            raise ValueError("Tên role không hợp lệ.")
        
        await privilege_dao.grant_role_ddl(role, grantee, with_admin)

    async def revoke_role(self, role: str, grantee: str) -> None:
        """
        Thu hồi role từ user/role.
        
        Args:
            role: Tên role
            grantee: Tên user hoặc role
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Tên người được cấp không hợp lệ.")
        
        if not role or not self._validate_identifier(role):
            raise ValueError("Tên role không hợp lệ.")
        
        await privilege_dao.revoke_role_ddl(role, grantee)

    async def check_privilege(self, username: str, privilege: str) -> bool:
        """Kiểm tra xem user có quyền cụ thể hay không."""
        return await privilege_dao.has_privilege(username, privilege)

    # ==========================================
    # Quyền trên Đối tượng
    # ==========================================

    OBJECT_PRIVILEGES = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    COLUMN_PRIVILEGES = ["SELECT", "INSERT"]

    async def get_all_tables(self, owner: str = None) -> List[Dict[str, Any]]:
        """Lấy tất cả bảng để cấp quyền đối tượng."""
        return await privilege_dao.query_all_tables(owner)

    async def get_object_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """Lấy các quyền đối tượng đã cấp cho người được cấp."""
        return await privilege_dao.query_object_privileges(grantee)

    async def grant_object_privilege(
        self,
        privilege: str,
        owner: str,
        table_name: str,
        grantee: str,
        with_grant_option: bool = False,
    ) -> None:
        """
        Cấp quyền đối tượng trên bảng cho user/role.
        
        Raises:
            ValueError: Nếu validation thất bại
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Tên người được cấp không hợp lệ.")
        
        if privilege.upper() not in self.OBJECT_PRIVILEGES:
            raise ValueError(f"Quyền không hợp lệ. Phải là một trong: {', '.join(self.OBJECT_PRIVILEGES)}")
        
        if not owner or not table_name:
            raise ValueError("Chủ sở hữu bảng và tên bảng là bắt buộc.")
        
        await privilege_dao.grant_object_privilege_ddl(
            privilege.upper(), owner, table_name, grantee, with_grant_option
        )

    async def revoke_object_privilege(
        self,
        privilege: str,
        owner: str,
        table_name: str,
        grantee: str,
    ) -> None:
        """Thu hồi quyền đối tượng từ user/role."""
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Tên người được cấp không hợp lệ.")
        
        await privilege_dao.revoke_object_privilege_ddl(
            privilege.upper(), owner, table_name, grantee
        )

    # ==========================================
    # Quyền trên Cột
    # ==========================================

    async def get_table_columns(self, owner: str, table_name: str) -> List[Dict[str, Any]]:
        """Lấy danh sách cột của một bảng."""
        return await privilege_dao.query_table_columns(owner, table_name)

    async def get_column_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """Lấy các quyền trên cột đã cấp cho người được cấp."""
        return await privilege_dao.query_column_privileges(grantee)

    async def grant_column_privilege(
        self,
        privilege: str,
        owner: str,
        table_name: str,
        columns: List[str],
        grantee: str,
    ) -> None:
        """
        Cấp quyền trên các cột cụ thể cho user/role.
        
        Raises:
            ValueError: Nếu validation thất bại
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Tên người được cấp không hợp lệ.")
        
        if privilege.upper() not in self.COLUMN_PRIVILEGES:
            raise ValueError(f"Quyền cột không hợp lệ. Phải là một trong: {', '.join(self.COLUMN_PRIVILEGES)}")
        
        if not columns:
            raise ValueError("Cần ít nhất một cột.")
        
        await privilege_dao.grant_column_privilege_ddl(
            privilege.upper(), owner, table_name, columns, grantee
        )

    async def revoke_column_privilege(
        self,
        privilege: str,
        owner: str,
        table_name: str,
        columns: List[str],
        grantee: str,
    ) -> None:
        """Thu hồi quyền trên cột từ user/role."""
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Tên người được cấp không hợp lệ.")
        
        await privilege_dao.revoke_column_privilege_ddl(
            privilege.upper(), owner, table_name, columns, grantee
        )


# Instance dịch vụ toàn cục
privilege_service = PrivilegeService()
