"""Profile data access object for Oracle database."""

import oracledb
from typing import List, Dict, Any, Optional

from app.data.oracle.connection import db


class ProfileDAO:
    """Data access object for profile operations."""

    async def query_all_profiles(self) -> List[Dict[str, Any]]:
        """
        Query all profiles from DBA_PROFILES grouped by profile name.
        
        Returns:
            List of profile information dicts with resource limits
        """
        # Ensure pool is initialized
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            # Query profiles with their resource limits for the 3 required resources
            await cursor.execute("""
                SELECT 
                    p.profile,
                    MAX(CASE WHEN p.resource_name = 'SESSIONS_PER_USER' THEN p.limit END) AS sessions_per_user,
                    MAX(CASE WHEN p.resource_name = 'CONNECT_TIME' THEN p.limit END) AS connect_time,
                    MAX(CASE WHEN p.resource_name = 'IDLE_TIME' THEN p.limit END) AS idle_time,
                    (SELECT COUNT(*) FROM dba_users u WHERE u.profile = p.profile) AS user_count
                FROM dba_profiles p
                WHERE p.resource_name IN ('SESSIONS_PER_USER', 'CONNECT_TIME', 'IDLE_TIME')
                GROUP BY p.profile
                ORDER BY p.profile
            """)
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except oracledb.Error as e:
            print(f"Error querying profiles: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def get_profile_detail(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific profile.
        
        Args:
            profile_name: Profile name
            
        Returns:
            Profile detail dict or None if not found
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT resource_name, resource_type, limit
                FROM dba_profiles
                WHERE profile = :profile_name
                ORDER BY resource_name
            """, profile_name=profile_name.upper())
            
            rows = await cursor.fetchall()
            if not rows:
                return None
            
            resources = {}
            for row in rows:
                resources[row[0].lower()] = {
                    "type": row[1],
                    "limit": row[2]
                }
            
            return {
                "profile": profile_name.upper(),
                "resources": resources,
                "sessions_per_user": resources.get("sessions_per_user", {}).get("limit", "DEFAULT"),
                "connect_time": resources.get("connect_time", {}).get("limit", "DEFAULT"),
                "idle_time": resources.get("idle_time", {}).get("limit", "DEFAULT"),
            }
        except oracledb.Error as e:
            print(f"Error getting profile detail: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def create_profile_ddl(
        self,
        profile_name: str,
        sessions_per_user: str = "DEFAULT",
        connect_time: str = "DEFAULT",
        idle_time: str = "DEFAULT",
    ) -> None:
        """
        Execute CREATE PROFILE DDL statement.
        
        Args:
            profile_name: Profile name (must be validated before calling)
            sessions_per_user: SESSIONS_PER_USER limit (UNLIMITED, DEFAULT, or integer)
            connect_time: CONNECT_TIME limit (UNLIMITED, DEFAULT, or integer in minutes)
            idle_time: IDLE_TIME limit (UNLIMITED, DEFAULT, or integer in minutes)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Build DDL statement
            ddl = f"CREATE PROFILE {profile_name.upper()} LIMIT"
            ddl += f" SESSIONS_PER_USER {sessions_per_user}"
            ddl += f" CONNECT_TIME {connect_time}"
            ddl += f" IDLE_TIME {idle_time}"
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error creating profile: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def alter_profile_ddl(
        self,
        profile_name: str,
        sessions_per_user: Optional[str] = None,
        connect_time: Optional[str] = None,
        idle_time: Optional[str] = None,
    ) -> None:
        """
        Execute ALTER PROFILE DDL statement.
        
        Args:
            profile_name: Profile name
            sessions_per_user: New SESSIONS_PER_USER limit (optional)
            connect_time: New CONNECT_TIME limit (optional)
            idle_time: New IDLE_TIME limit (optional)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Build DDL statement with only provided values
            parts = []
            if sessions_per_user is not None:
                parts.append(f"SESSIONS_PER_USER {sessions_per_user}")
            if connect_time is not None:
                parts.append(f"CONNECT_TIME {connect_time}")
            if idle_time is not None:
                parts.append(f"IDLE_TIME {idle_time}")
            
            if not parts:
                return  # Nothing to update
            
            ddl = f"ALTER PROFILE {profile_name.upper()} LIMIT " + " ".join(parts)
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error altering profile: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def drop_profile_ddl(self, profile_name: str, cascade: bool = False) -> None:
        """
        Execute DROP PROFILE DDL statement.
        
        Args:
            profile_name: Profile name
            cascade: Whether to cascade drop (reassign users to DEFAULT profile)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            ddl = f"DROP PROFILE {profile_name.upper()}"
            if cascade:
                ddl += " CASCADE"
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error dropping profile: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_profile_users(self, profile_name: str) -> List[Dict[str, Any]]:
        """
        Query users assigned to a specific profile.
        
        Args:
            profile_name: Profile name
            
        Returns:
            List of user information dicts
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT username, account_status, created
                FROM dba_users
                WHERE profile = :profile_name
                ORDER BY username
            """, profile_name=profile_name.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except oracledb.Error as e:
            print(f"Error querying profile users: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def profile_exists(self, profile_name: str) -> bool:
        """
        Check if a profile exists.
        
        Args:
            profile_name: Profile name
            
        Returns:
            True if profile exists, False otherwise
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT COUNT(*) FROM dba_profiles
                WHERE profile = :profile_name
            """, profile_name=profile_name.upper())
            
            row = await cursor.fetchone()
            count = row[0] if row else 0
            return count > 0
        except oracledb.Error as e:
            print(f"Error checking profile existence: {e}")
            return False
        finally:
            await db.release_connection(conn)


# Global DAO instance
profile_dao = ProfileDAO()
