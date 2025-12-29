"""Role data access object for Oracle database."""

import oracledb
from typing import List, Dict, Any, Optional

from app.data.oracle.connection import db


class RoleDAO:
    """Data access object for role operations."""

    async def query_all_roles(self) -> List[Dict[str, Any]]:
        """
        Query all roles from DBA_ROLES.
        
        Returns:
            List of role information dicts
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT 
                    r.role,
                    r.password_required,
                    r.authentication_type,
                    (SELECT COUNT(*) FROM dba_role_privs rp WHERE rp.granted_role = r.role) AS grantee_count
                FROM dba_roles r
                ORDER BY r.role
            """)
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except oracledb.Error as e:
            print(f"Error querying roles: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def get_role_detail(self, role_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific role.
        
        Args:
            role_name: Role name
            
        Returns:
            Role detail dict or None if not found
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT role, password_required, authentication_type
                FROM dba_roles
                WHERE role = :role_name
            """, role_name=role_name.upper())
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0].lower() for desc in cursor.description]
            return dict(zip(columns, row))
        except oracledb.Error as e:
            print(f"Error getting role detail: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def create_role_ddl(
        self,
        role_name: str,
        password: Optional[str] = None,
    ) -> None:
        """
        Execute CREATE ROLE DDL statement.
        
        Args:
            role_name: Role name (must be validated before calling)
            password: Role password (optional - if provided, role requires password to enable)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            if password:
                ddl = f'CREATE ROLE {role_name.upper()} IDENTIFIED BY "{password}"'
            else:
                ddl = f"CREATE ROLE {role_name.upper()} NOT IDENTIFIED"
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error creating role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def alter_role_ddl(
        self,
        role_name: str,
        password: Optional[str] = None,
        remove_password: bool = False,
    ) -> None:
        """
        Execute ALTER ROLE DDL statement.
        
        Args:
            role_name: Role name
            password: New password (optional)
            remove_password: If True, remove password requirement
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            if remove_password:
                ddl = f"ALTER ROLE {role_name.upper()} NOT IDENTIFIED"
            elif password:
                ddl = f'ALTER ROLE {role_name.upper()} IDENTIFIED BY "{password}"'
            else:
                return  # Nothing to change
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error altering role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def drop_role_ddl(self, role_name: str) -> None:
        """
        Execute DROP ROLE DDL statement.
        
        Args:
            role_name: Role name
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"DROP ROLE {role_name.upper()}")
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error dropping role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_role_privileges(self, role_name: str) -> List[Dict[str, Any]]:
        """
        Query privileges granted to a role.
        
        Args:
            role_name: Role name
            
        Returns:
            List of privilege information dicts
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # System privileges granted to role
            await cursor.execute("""
                SELECT privilege, admin_option, 'SYSTEM' as privilege_type
                FROM dba_sys_privs
                WHERE grantee = :role_name
            """, role_name=role_name.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            privileges = [dict(zip(columns, row)) for row in rows]
            
            # Roles granted to role
            await cursor.execute("""
                SELECT granted_role as privilege, admin_option, 'ROLE' as privilege_type
                FROM dba_role_privs
                WHERE grantee = :role_name
            """, role_name=role_name.upper())
            
            role_columns = [desc[0].lower() for desc in cursor.description]
            role_rows = await cursor.fetchall()
            privileges.extend([dict(zip(role_columns, row)) for row in role_rows])
            
            return privileges
        except oracledb.Error as e:
            print(f"Error querying role privileges: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_role_users(self, role_name: str) -> List[Dict[str, Any]]:
        """
        Query users/roles that have been granted this role.
        
        Args:
            role_name: Role name
            
        Returns:
            List of grantee information dicts
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT grantee, admin_option, default_role
                FROM dba_role_privs
                WHERE granted_role = :role_name
                ORDER BY grantee
            """, role_name=role_name.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except oracledb.Error as e:
            print(f"Error querying role users: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def role_exists(self, role_name: str) -> bool:
        """
        Check if a role exists.
        
        Args:
            role_name: Role name
            
        Returns:
            True if role exists, False otherwise
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT COUNT(*) FROM dba_roles
                WHERE role = :role_name
            """, role_name=role_name.upper())
            
            row = await cursor.fetchone()
            count = row[0] if row else 0
            return count > 0
        except oracledb.Error as e:
            print(f"Error checking role existence: {e}")
            return False
        finally:
            await db.release_connection(conn)


# Global DAO instance
role_dao = RoleDAO()
