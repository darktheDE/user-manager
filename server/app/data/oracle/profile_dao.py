"""Đối tượng truy cập dữ liệu Profile cho Oracle database."""

import oracledb
from typing import List, Dict, Any, Optional

from app.data.oracle.connection import db


class ProfileDAO:
    """DAO cho các thao tác profile."""

    async def query_all_profiles(self) -> List[Dict[str, Any]]:
        """
        Truy vấn tất cả profiles từ DBA_PROFILES nhóm theo tên profile.
        
        Returns:
            Danh sách dict thông tin profile với các resource limits
        """
        # Đảm bảo pool đã được khởi tạo
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            # Truy vấn profiles với resource limits cho 3 resource yêu cầu
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
            print(f"Lỗi truy vấn profiles: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def get_profile_detail(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin chi tiết cho một profile cụ thể.
        
        Args:
            profile_name: Tên profile
            
        Returns:
            Dict chi tiết profile hoặc None nếu không tìm thấy
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
            print(f"Lỗi lấy chi tiết profile: {e}")
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
        Thực thi câu lệnh DDL CREATE PROFILE.
        
        Args:
            profile_name: Tên profile (phải được validate trước)
            sessions_per_user: Giới hạn SESSIONS_PER_USER
            connect_time: Giới hạn CONNECT_TIME
            idle_time: Giới hạn IDLE_TIME
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Xây dựng câu lệnh DDL
            ddl = f"CREATE PROFILE {profile_name.upper()} LIMIT"
            ddl += f" SESSIONS_PER_USER {sessions_per_user}"
            ddl += f" CONNECT_TIME {connect_time}"
            ddl += f" IDLE_TIME {idle_time}"
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi tạo profile: {e}")
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
        Thực thi câu lệnh DDL ALTER PROFILE.
        
        Args:
            profile_name: Tên profile
            sessions_per_user: Giới hạn SESSIONS_PER_USER mới (tùy chọn)
            connect_time: Giới hạn CONNECT_TIME mới (tùy chọn)
            idle_time: Giới hạn IDLE_TIME mới (tùy chọn)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Xây dựng câu lệnh DDL chỉ với các giá trị được cung cấp
            parts = []
            if sessions_per_user is not None:
                parts.append(f"SESSIONS_PER_USER {sessions_per_user}")
            if connect_time is not None:
                parts.append(f"CONNECT_TIME {connect_time}")
            if idle_time is not None:
                parts.append(f"IDLE_TIME {idle_time}")
            
            if not parts:
                return  # Không có gì để update
            
            ddl = f"ALTER PROFILE {profile_name.upper()} LIMIT " + " ".join(parts)
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi sửa profile: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def drop_profile_ddl(self, profile_name: str, cascade: bool = False) -> None:
        """
        Thực thi câu lệnh DDL DROP PROFILE.
        
        Args:
            profile_name: Tên profile
            cascade: Có xóa cascade không (gán lại user về profile DEFAULT)
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
            print(f"Lỗi xóa profile: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_profile_users(self, profile_name: str) -> List[Dict[str, Any]]:
        """
        Truy vấn người dùng được gán vào một profile cụ thể.
        
        Args:
            profile_name: Tên profile
            
        Returns:
            Danh sách dict thông tin user
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
            print(f"Lỗi truy vấn user của profile: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def profile_exists(self, profile_name: str) -> bool:
        """
        Kiểm tra xem profile có tồn tại hay không.
        
        Args:
            profile_name: Tên profile
            
        Returns:
            True nếu profile tồn tại, False nếu không
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
            print(f"Lỗi kiểm tra profile tồn tại: {e}")
            return False
        finally:
            await db.release_connection(conn)


# Instance DAO toàn cục
profile_dao = ProfileDAO()
