"""Privilege management service."""

import re
from typing import List, Dict, Any
from app.data.oracle.privilege_dao import privilege_dao


class PrivilegeService:
    """Service for privilege management operations."""

    # Common system privileges
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
        """Validate Oracle identifier format."""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_$#]*$', name))

    async def get_all_system_privileges(self) -> List[Dict[str, Any]]:
        """Get list of all system privileges."""
        return await privilege_dao.query_all_system_privileges()

    async def get_common_privileges(self) -> List[str]:
        """Get list of common system privileges for UI."""
        return self.COMMON_SYSTEM_PRIVILEGES

    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all available roles for granting."""
        return await privilege_dao.query_all_roles()

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users for privilege granting."""
        return await privilege_dao.query_all_users()

    async def get_grantee_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """Get all privileges/roles granted to a user or role."""
        return await privilege_dao.query_grantee_privileges(grantee)

    async def grant_system_privilege(
        self,
        privilege: str,
        grantee: str,
        with_admin: bool = False,
    ) -> None:
        """
        Grant system privilege to user/role.
        
        Args:
            privilege: System privilege name
            grantee: User or role name
            with_admin: Grant with ADMIN OPTION
            
        Raises:
            ValueError: If validation fails
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Invalid grantee name.")
        
        if not privilege:
            raise ValueError("Privilege name is required.")
        
        await privilege_dao.grant_system_privilege_ddl(privilege, grantee, with_admin)

    async def revoke_system_privilege(self, privilege: str, grantee: str) -> None:
        """
        Revoke system privilege from user/role.
        
        Args:
            privilege: System privilege name
            grantee: User or role name
            
        Raises:
            ValueError: If validation fails
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Invalid grantee name.")
        
        if not privilege:
            raise ValueError("Privilege name is required.")
        
        await privilege_dao.revoke_system_privilege_ddl(privilege, grantee)

    async def grant_role(
        self,
        role: str,
        grantee: str,
        with_admin: bool = False,
    ) -> None:
        """
        Grant role to user/role.
        
        Args:
            role: Role name
            grantee: User or role name
            with_admin: Grant with ADMIN OPTION
            
        Raises:
            ValueError: If validation fails
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Invalid grantee name.")
        
        if not role or not self._validate_identifier(role):
            raise ValueError("Invalid role name.")
        
        await privilege_dao.grant_role_ddl(role, grantee, with_admin)

    async def revoke_role(self, role: str, grantee: str) -> None:
        """
        Revoke role from user/role.
        
        Args:
            role: Role name
            grantee: User or role name
            
        Raises:
            ValueError: If validation fails
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Invalid grantee name.")
        
        if not role or not self._validate_identifier(role):
            raise ValueError("Invalid role name.")
        
        await privilege_dao.revoke_role_ddl(role, grantee)

    async def check_privilege(self, username: str, privilege: str) -> bool:
        """Check if user has a specific privilege."""
        return await privilege_dao.has_privilege(username, privilege)

    # ==========================================
    # Object Privileges
    # ==========================================

    OBJECT_PRIVILEGES = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    COLUMN_PRIVILEGES = ["SELECT", "INSERT"]

    async def get_all_tables(self, owner: str = None) -> List[Dict[str, Any]]:
        """Get all tables for object privilege granting."""
        return await privilege_dao.query_all_tables(owner)

    async def get_object_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """Get object privileges granted to a grantee."""
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
        Grant object privilege on table to user/role.
        
        Raises:
            ValueError: If validation fails
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Invalid grantee name.")
        
        if privilege.upper() not in self.OBJECT_PRIVILEGES:
            raise ValueError(f"Invalid privilege. Must be one of: {', '.join(self.OBJECT_PRIVILEGES)}")
        
        if not owner or not table_name:
            raise ValueError("Table owner and name are required.")
        
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
        """Revoke object privilege from user/role."""
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Invalid grantee name.")
        
        await privilege_dao.revoke_object_privilege_ddl(
            privilege.upper(), owner, table_name, grantee
        )

    # ==========================================
    # Column Privileges
    # ==========================================

    async def get_table_columns(self, owner: str, table_name: str) -> List[Dict[str, Any]]:
        """Get columns of a table."""
        return await privilege_dao.query_table_columns(owner, table_name)

    async def get_column_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """Get column privileges granted to a grantee."""
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
        Grant column privilege on specific columns to user/role.
        
        Raises:
            ValueError: If validation fails
        """
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Invalid grantee name.")
        
        if privilege.upper() not in self.COLUMN_PRIVILEGES:
            raise ValueError(f"Invalid column privilege. Must be one of: {', '.join(self.COLUMN_PRIVILEGES)}")
        
        if not columns:
            raise ValueError("At least one column is required.")
        
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
        """Revoke column privilege from user/role."""
        if not grantee or not self._validate_identifier(grantee):
            raise ValueError("Invalid grantee name.")
        
        await privilege_dao.revoke_column_privilege_ddl(
            privilege.upper(), owner, table_name, columns, grantee
        )


# Global service instance
privilege_service = PrivilegeService()
