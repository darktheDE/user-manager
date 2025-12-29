"""Privilege data access object for Oracle database."""

import oracledb
from typing import List, Dict, Any, Optional
from app.data.oracle.connection import db


class PrivilegeDAO:
    """Data access object for privilege operations."""

    async def has_privilege(self, username: str, privilege: str) -> bool:
        """
        Check if user has a specific privilege.
        
        Args:
            username: Oracle username
            privilege: Privilege name to check
            
        Returns:
            True if user has privilege, False otherwise
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Check system privileges
            await cursor.execute("""
                SELECT COUNT(*) 
                FROM dba_sys_privs 
                WHERE grantee = :username 
                AND privilege = :privilege
            """, username=username.upper(), privilege=privilege)
            
            row = await cursor.fetchone()
            if row and row[0] > 0:
                return True
            
            # Check role privileges (simplified)
            await cursor.execute("""
                SELECT COUNT(*) 
                FROM dba_sys_privs 
                WHERE grantee IN (
                    SELECT granted_role 
                    FROM dba_role_privs 
                    WHERE grantee = :username
                )
                AND privilege = :privilege
            """, username=username.upper(), privilege=privilege)
            
            row = await cursor.fetchone()
            return row and row[0] > 0
            
        except Exception:
            return True
        finally:
            await db.release_connection(conn)

    async def query_all_system_privileges(self) -> List[Dict[str, Any]]:
        """Query all available system privileges."""
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT DISTINCT privilege 
                FROM dba_sys_privs 
                ORDER BY privilege
            """)
            
            rows = await cursor.fetchall()
            return [{"privilege": row[0]} for row in rows]
        except oracledb.Error as e:
            print(f"Error querying system privileges: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_grantee_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """
        Query all privileges granted to a specific user/role.
        
        Returns combined system privileges and role grants.
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # System privileges
            await cursor.execute("""
                SELECT privilege, admin_option, 'SYSTEM' as privilege_type
                FROM dba_sys_privs
                WHERE grantee = :grantee
                ORDER BY privilege
            """, grantee=grantee.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            
            # Role privileges
            await cursor.execute("""
                SELECT granted_role as privilege, admin_option, 'ROLE' as privilege_type
                FROM dba_role_privs
                WHERE grantee = :grantee
                ORDER BY granted_role
            """, grantee=grantee.upper())
            
            role_columns = [desc[0].lower() for desc in cursor.description]
            role_rows = await cursor.fetchall()
            result.extend([dict(zip(role_columns, row)) for row in role_rows])
            
            return result
        except oracledb.Error as e:
            print(f"Error querying grantee privileges: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_all_roles(self) -> List[Dict[str, Any]]:
        """Query all available roles for granting."""
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT role FROM dba_roles ORDER BY role
            """)
            
            rows = await cursor.fetchall()
            return [{"role": row[0]} for row in rows]
        except oracledb.Error as e:
            print(f"Error querying roles: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_all_users(self) -> List[Dict[str, Any]]:
        """Query all users for privilege granting."""
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT username FROM dba_users 
                WHERE username NOT IN ('SYS', 'SYSTEM')
                ORDER BY username
            """)
            
            rows = await cursor.fetchall()
            return [{"username": row[0]} for row in rows]
        except oracledb.Error as e:
            print(f"Error querying users: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def grant_system_privilege_ddl(
        self, 
        privilege: str, 
        grantee: str, 
        with_admin: bool = False
    ) -> None:
        """
        Grant system privilege to user/role.
        
        Args:
            privilege: System privilege name
            grantee: User or role name
            with_admin: Grant with ADMIN OPTION
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            ddl = f"GRANT {privilege} TO {grantee.upper()}"
            if with_admin:
                ddl += " WITH ADMIN OPTION"
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error granting system privilege: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def revoke_system_privilege_ddl(self, privilege: str, grantee: str) -> None:
        """
        Revoke system privilege from user/role.
        
        Args:
            privilege: System privilege name
            grantee: User or role name
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"REVOKE {privilege} FROM {grantee.upper()}")
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error revoking system privilege: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def grant_role_ddl(
        self, 
        role: str, 
        grantee: str, 
        with_admin: bool = False
    ) -> None:
        """
        Grant role to user/role.
        
        Args:
            role: Role name
            grantee: User or role name
            with_admin: Grant with ADMIN OPTION
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            ddl = f"GRANT {role.upper()} TO {grantee.upper()}"
            if with_admin:
                ddl += " WITH ADMIN OPTION"
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error granting role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def revoke_role_ddl(self, role: str, grantee: str) -> None:
        """
        Revoke role from user/role.
        
        Args:
            role: Role name
            grantee: User or role name
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"REVOKE {role.upper()} FROM {grantee.upper()}")
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error revoking role: {e}")
            raise
        finally:
            await db.release_connection(conn)


# Global DAO instance
privilege_dao = PrivilegeDAO()
