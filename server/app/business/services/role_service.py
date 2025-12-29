"""Role management service."""

import re
from typing import List, Dict, Any, Optional
from app.data.oracle.role_dao import role_dao


class RoleService:
    """Service for role management operations."""

    # Reserved Oracle roles that should not be modified
    RESERVED_ROLES = {
        "DBA", "CONNECT", "RESOURCE", "PUBLIC", "SELECT_CATALOG_ROLE",
        "EXECUTE_CATALOG_ROLE", "DELETE_CATALOG_ROLE", "EXP_FULL_DATABASE",
        "IMP_FULL_DATABASE", "RECOVERY_CATALOG_OWNER", "AQ_ADMINISTRATOR_ROLE",
        "AQ_USER_ROLE", "DATAPUMP_EXP_FULL_DATABASE", "DATAPUMP_IMP_FULL_DATABASE",
    }

    def _validate_role_name(self, role_name: str) -> bool:
        """Validate role name format (alphanumeric and underscore only)."""
        return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', role_name))

    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all roles from DBA_ROLES."""
        return await role_dao.query_all_roles()

    async def get_role_detail(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific role including privileges and grantees."""
        role = await role_dao.get_role_detail(role_name)
        if not role:
            return None
        
        # Get privileges and grantees
        role["privileges"] = await role_dao.query_role_privileges(role_name)
        role["grantees"] = await role_dao.query_role_users(role_name)
        
        return role

    async def create_role(
        self,
        role_name: str,
        password: Optional[str] = None,
    ) -> None:
        """
        Create a new role with validation.
        
        Args:
            role_name: Role name
            password: Role password (optional)
            
        Raises:
            ValueError: If validation fails
        """
        # Validate role name
        if not self._validate_role_name(role_name):
            raise ValueError(
                "Invalid role name. Must start with a letter and contain only "
                "alphanumeric characters and underscores."
            )
        
        # Check reserved names
        if role_name.upper() in self.RESERVED_ROLES:
            raise ValueError(f"Cannot create role '{role_name}'. It is a reserved Oracle role.")
        
        # Check if role already exists
        if await role_dao.role_exists(role_name):
            raise ValueError(f"Role '{role_name}' already exists.")
        
        await role_dao.create_role_ddl(role_name, password)

    async def update_role(
        self,
        role_name: str,
        password: Optional[str] = None,
        remove_password: bool = False,
    ) -> None:
        """
        Update role password.
        
        Args:
            role_name: Role name
            password: New password (optional)
            remove_password: If True, remove password requirement
            
        Raises:
            ValueError: If validation fails
        """
        # Check reserved roles
        if role_name.upper() in self.RESERVED_ROLES:
            raise ValueError(f"Cannot modify reserved Oracle role '{role_name}'.")
        
        # Check if role exists
        if not await role_dao.role_exists(role_name):
            raise ValueError(f"Role '{role_name}' does not exist.")
        
        await role_dao.alter_role_ddl(role_name, password, remove_password)

    async def delete_role(self, role_name: str) -> None:
        """
        Delete a role.
        
        Args:
            role_name: Role name
            
        Raises:
            ValueError: If validation fails
        """
        # Check reserved roles
        if role_name.upper() in self.RESERVED_ROLES:
            raise ValueError(f"Cannot delete reserved Oracle role '{role_name}'.")
        
        # Check if role exists
        if not await role_dao.role_exists(role_name):
            raise ValueError(f"Role '{role_name}' does not exist.")
        
        await role_dao.drop_role_ddl(role_name)

    async def get_role_privileges(self, role_name: str) -> List[Dict[str, Any]]:
        """Get privileges granted to a role."""
        return await role_dao.query_role_privileges(role_name)

    async def get_role_users(self, role_name: str) -> List[Dict[str, Any]]:
        """Get users/roles that have been granted this role."""
        return await role_dao.query_role_users(role_name)


# Global service instance
role_service = RoleService()
