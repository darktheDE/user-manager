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


# Global service instance
privilege_service = PrivilegeService()
