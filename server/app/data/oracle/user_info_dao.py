"""User Info data access object for Oracle database."""

import oracledb
from typing import Optional, Dict, Any
from app.data.oracle.connection import db


class UserInfoDAO:
    """Data access object for user_info table operations."""

    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user_info by username.
        
        Returns:
            User info dict or None if not found
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT user_id, username, password_hash, full_name, 
                       email, phone, department, notes, created_at, updated_at
                FROM user_info
                WHERE UPPER(username) = :username
            """, username=username.upper())
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0].lower() for desc in cursor.description]
            return dict(zip(columns, row))
        except oracledb.Error as e:
            print(f"Error getting user info: {e}")
            return None
        finally:
            await db.release_connection(conn)

    async def create(
        self,
        username: str,
        password_hash: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        department: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> int:
        """
        Create new user_info record.
        
        Returns:
            New user_id
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                INSERT INTO user_info (username, password_hash, full_name, email, phone, department, notes)
                VALUES (:username, :password_hash, :full_name, :email, :phone, :department, :notes)
            """,
                username=username.upper(),
                password_hash=password_hash,
                full_name=full_name,
                email=email,
                phone=phone,
                department=department,
                notes=notes
            )
            await conn.commit()
            
            # Get the new ID
            await cursor.execute(
                "SELECT user_id FROM user_info WHERE username = :username",
                username=username.upper()
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error creating user info: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def update_password_hash(self, username: str, password_hash: str) -> None:
        """Update password hash for a user."""
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                UPDATE user_info
                SET password_hash = :password_hash
                WHERE UPPER(username) = :username
            """, password_hash=password_hash, username=username.upper())
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error updating password hash: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def update(
        self,
        username: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        department: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Update user_info fields."""
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
            if department is not None:
                updates.append("department = :department")
                params["department"] = department
            if notes is not None:
                updates.append("notes = :notes")
                params["notes"] = notes
            
            if not updates:
                return
            
            update_clause = ", ".join(updates)
            await cursor.execute(f"""
                UPDATE user_info
                SET {update_clause}
                WHERE UPPER(username) = :username
            """, **params)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error updating user info: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def delete(self, username: str) -> None:
        """Delete user_info record."""
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(
                "DELETE FROM user_info WHERE UPPER(username) = :username",
                username=username.upper()
            )
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error deleting user info: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def exists(self, username: str) -> bool:
        """Check if username exists in user_info."""
        user = await self.get_by_username(username)
        return user is not None


# Global DAO instance
user_info_dao = UserInfoDAO()
