"""User data access object for Oracle database."""

import oracledb
from typing import List, Dict, Any, Optional

from app.data.oracle.connection import db


class UserDAO:
    """Data access object for user operations."""

    async def verify_password(self, username: str, password: str) -> bool:
        """
        Verify password by attempting to connect to Oracle with username/password.
        
        Args:
            username: Oracle username
            password: Oracle password
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            from app.config import settings
            
            dsn = oracledb.makedsn(
                host=settings.ORACLE_HOST,
                port=settings.ORACLE_PORT,
                service_name=settings.ORACLE_SERVICE_NAME,
            )
            test_conn = await oracledb.connect_async(
                user=username,
                password=password,
                dsn=dsn,
            )
            await test_conn.close()
            return True
        except Exception as e:
            print(f"Password verification error: {e}")
            return False

    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from DBA_USERS.
        
        Args:
            username: Oracle username
            
        Returns:
            User information dict or None if not found
        """
        # Ensure pool is initialized
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT username, account_status, created,
                       default_tablespace, temporary_tablespace, profile,
                       lock_date
                FROM dba_users
                WHERE username = :username
            """, username=username.upper())
            
            row = await cursor.fetchone()
            if row:
                columns = [desc[0].lower() for desc in cursor.description]
                return dict(zip(columns, row))
            return None
        finally:
            await db.release_connection(conn)

    async def query_all_users(self) -> List[Dict[str, Any]]:
        """
        Query all users from DBA_USERS.
        
        Returns:
            List of user information dicts
        """
        # Ensure pool is initialized
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT username, account_status, created,
                       default_tablespace, temporary_tablespace, profile,
                       lock_date
                FROM dba_users
                WHERE username NOT IN ('SYS', 'SYSTEM')
                ORDER BY username
            """)
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            await db.release_connection(conn)

    async def create_user_ddl(
        self,
        username: str,
        password: str,
        default_tablespace: str,
        temporary_tablespace: Optional[str] = None,
        quota: Optional[str] = None,
        profile: Optional[str] = None,
    ) -> None:
        """
        Execute CREATE USER DDL statement.
        
        Args:
            username: Oracle username (must be validated before calling)
            password: Oracle password
            default_tablespace: Default tablespace name
            temporary_tablespace: Temporary tablespace name (optional)
            quota: Quota on default tablespace (optional)
            profile: Profile name (optional)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Build CREATE USER statement
            ddl_parts = [f"CREATE USER {username} IDENTIFIED BY \"{password}\""]
            ddl_parts.append(f"DEFAULT TABLESPACE {default_tablespace}")
            
            if temporary_tablespace:
                ddl_parts.append(f"TEMPORARY TABLESPACE {temporary_tablespace}")
            
            if quota:
                ddl_parts.append(f"QUOTA {quota} ON {default_tablespace}")
            
            if profile:
                ddl_parts.append(f"PROFILE {profile}")
            
            ddl = " ".join(ddl_parts)
            await cursor.execute(ddl)
            await conn.commit()
        finally:
            await db.release_connection(conn)

    async def alter_user_ddl(
        self,
        username: str,
        password: Optional[str] = None,
        default_tablespace: Optional[str] = None,
        temporary_tablespace: Optional[str] = None,
        quota: Optional[str] = None,
        profile: Optional[str] = None,
    ) -> None:
        """
        Execute ALTER USER DDL statement.
        
        Args:
            username: Oracle username
            password: New password (optional)
            default_tablespace: New default tablespace (optional)
            temporary_tablespace: New temporary tablespace (optional)
            quota: New quota (optional)
            profile: New profile (optional)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            if password:
                await cursor.execute(f'ALTER USER {username} IDENTIFIED BY "{password}"')
            
            if default_tablespace:
                await cursor.execute(f"ALTER USER {username} DEFAULT TABLESPACE {default_tablespace}")
            
            if temporary_tablespace:
                await cursor.execute(f"ALTER USER {username} TEMPORARY TABLESPACE {temporary_tablespace}")
            
            if quota:
                await cursor.execute(f"ALTER USER {username} QUOTA {quota} ON {default_tablespace or 'USERS'}")
            
            if profile:
                await cursor.execute(f"ALTER USER {username} PROFILE {profile}")
            
            await conn.commit()
        finally:
            await db.release_connection(conn)

    async def drop_user_ddl(self, username: str, cascade: bool = False) -> None:
        """
        Execute DROP USER DDL statement.
        
        Args:
            username: Oracle username
            cascade: Whether to cascade drop (drop user's objects)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            if cascade:
                await cursor.execute(f"DROP USER {username} CASCADE")
            else:
                await cursor.execute(f"DROP USER {username}")
            await conn.commit()
        finally:
            await db.release_connection(conn)

    async def lock_user(self, username: str) -> None:
        """Lock user account."""
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"ALTER USER {username} ACCOUNT LOCK")
            await conn.commit()
        finally:
            await db.release_connection(conn)

    async def unlock_user(self, username: str) -> None:
        """Unlock user account."""
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"ALTER USER {username} ACCOUNT UNLOCK")
            await conn.commit()
        finally:
            await db.release_connection(conn)

    async def query_user_privileges(self, username: str) -> List[Dict[str, Any]]:
        """
        Query user privileges from DBA_SYS_PRIVS and DBA_ROLE_PRIVS.
        
        Args:
            username: Oracle username
            
        Returns:
            List of privilege information dicts
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # System privileges
            await cursor.execute("""
                SELECT privilege, admin_option, 'DIRECT' as grant_type
                FROM dba_sys_privs
                WHERE grantee = :username
            """, username=username.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            privileges = [dict(zip(columns, row)) for row in rows]
            
            # Role privileges
            await cursor.execute("""
                SELECT granted_role as privilege, admin_option, 'ROLE' as grant_type
                FROM dba_role_privs
                WHERE grantee = :username
            """, username=username.upper())
            
            role_columns = [desc[0].lower() for desc in cursor.description]
            role_rows = await cursor.fetchall()
            privileges.extend([dict(zip(role_columns, row)) for row in role_rows])
            
            return privileges
        finally:
            await db.release_connection(conn)

    async def query_user_roles(self, username: str) -> List[Dict[str, Any]]:
        """
        Query user roles from DBA_ROLE_PRIVS.
        
        Args:
            username: Oracle username
            
        Returns:
            List of role information dicts
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT granted_role, admin_option, default_role
                FROM dba_role_privs
                WHERE grantee = :username
            """, username=username.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            await db.release_connection(conn)

    async def get_user_quota(self, username: str) -> List[Dict[str, Any]]:
        """
        Get user quota from DBA_TS_QUOTAS.
        
        Args:
            username: Oracle username
            
        Returns:
            List of quota information dicts
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT tablespace_name, bytes, max_bytes
                FROM dba_ts_quotas
                WHERE username = :username
            """, username=username.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception:
            return []
        finally:
            await db.release_connection(conn)


    async def query_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Query user info from application table user_info.
        
        Args:
            username: Oracle username
            
        Returns:
            User info dict or None if not found
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT username, full_name, email, phone, address, created_at
                FROM user_info
                WHERE username = :username
            """, username=username.upper())
            
            row = await cursor.fetchone()
            if row:
                columns = [desc[0].lower() for desc in cursor.description]
                return dict(zip(columns, row))
            return None
        except oracledb.Error:
            # Table might not exist yet
            return None
        finally:
            await db.release_connection(conn)

    async def create_user_info(
        self,
        username: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
    ) -> None:
        """
        Insert user info into application table user_info.
        
        Args:
            username: Oracle username
            full_name: Full name (optional)
            email: Email (optional)
            phone: Phone (optional)
            address: Address (optional)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                INSERT INTO user_info (username, full_name, email, phone, address)
                VALUES (:username, :full_name, :email, :phone, :address)
            """, username=username.upper(), full_name=full_name, email=email, phone=phone, address=address)
            await conn.commit()
        finally:
            await db.release_connection(conn)

    async def update_user_info(
        self,
        username: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
    ) -> None:
        """
        Update user info in application table user_info.
        
        Args:
            username: Oracle username
            full_name: Full name (optional)
            email: Email (optional)
            phone: Phone (optional)
            address: Address (optional)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            updates = []
            params = {"username": username.upper()}
            
            if full_name is not None:
                updates.append("full_name = :full_name")
                params["full_name"] = full_name
            
            if email is not None:
                updates.append("email = :email")
                params["email"] = email
            
            if phone is not None:
                updates.append("phone = :phone")
                params["phone"] = phone
            
            if address is not None:
                updates.append("address = :address")
                params["address"] = address
            
            if updates:
                update_clause = ", ".join(updates)
                await cursor.execute(f"""
                    UPDATE user_info
                    SET {update_clause}
                    WHERE username = :username
                """, **params)
                await conn.commit()
        finally:
            await db.release_connection(conn)


# Global DAO instance
user_dao = UserDAO()

