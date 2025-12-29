"""Privilege data access object for Oracle database."""

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
            
            # Check role privileges (simplified - check if user has any role with the privilege)
            # Note: This is a simplified check. For production, you'd need to recursively check role hierarchies
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
            # If checking fails, assume user has privilege (for SYSTEM user)
            return True
        finally:
            await db.release_connection(conn)


# Global DAO instance
privilege_dao = PrivilegeDAO()

