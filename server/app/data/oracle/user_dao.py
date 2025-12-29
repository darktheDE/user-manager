"""Đối tượng truy cập dữ liệu User cho Oracle Database."""

import oracledb
from typing import List, Dict, Any, Optional

from app.data.oracle.connection import db


class UserDAO:
    """Lớp truy cập dữ liệu cho các thao tác với user."""

    async def verify_password(self, username: str, password: str) -> bool:
        """
        Xác minh mật khẩu bằng cách thử kết nối Oracle với username/password.
        
        Args:
            username: Tên đăng nhập Oracle
            password: Mật khẩu Oracle
            
        Returns:
            True nếu kết nối thành công, False nếu thất bại
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
            print(f"Lỗi xác minh mật khẩu: {e}")
            return False

    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user từ DBA_USERS.
        
        Args:
            username: Tên đăng nhập Oracle
            
        Returns:
            Dict thông tin user hoặc None nếu không tìm thấy
        """
        # Đảm bảo pool đã được khởi tạo
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
        Truy vấn tất cả users từ DBA_USERS.
        
        Returns:
            Danh sách các dict chứa thông tin user
        """
        # Đảm bảo pool đã được khởi tạo
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
        Thực thi câu lệnh DDL CREATE USER.
        
        Args:
            username: Tên đăng nhập Oracle (phải được validate trước)
            password: Mật khẩu Oracle
            default_tablespace: Tên tablespace mặc định
            temporary_tablespace: Tên tablespace tạm (tùy chọn)
            quota: Hạn mức trên tablespace mặc định (tùy chọn)
            profile: Tên profile (tùy chọn)
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Xây dựng câu lệnh CREATE USER
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
        Thực thi câu lệnh DDL ALTER USER.
        
        Args:
            username: Tên đăng nhập Oracle
            password: Mật khẩu mới (tùy chọn)
            default_tablespace: Tablespace mặc định mới (tùy chọn)
            temporary_tablespace: Tablespace tạm mới (tùy chọn)
            quota: Hạn mức mới (tùy chọn)
            profile: Profile mới (tùy chọn)
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
        Thực thi câu lệnh DDL DROP USER.
        
        Args:
            username: Tên đăng nhập Oracle
            cascade: Có xóa cascade không (xóa cả objects của user)
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
        """Khóa tài khoản user."""
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"ALTER USER {username} ACCOUNT LOCK")
            await conn.commit()
        finally:
            await db.release_connection(conn)

    async def unlock_user(self, username: str) -> None:
        """Mở khóa tài khoản user."""
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"ALTER USER {username} ACCOUNT UNLOCK")
            await conn.commit()
        finally:
            await db.release_connection(conn)

    async def query_user_privileges(self, username: str) -> List[Dict[str, Any]]:
        """
        Truy vấn quyền của user từ DBA_SYS_PRIVS và DBA_ROLE_PRIVS.
        
        Args:
            username: Tên đăng nhập Oracle
            
        Returns:
            Danh sách các dict chứa thông tin quyền
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Quyền hệ thống
            await cursor.execute("""
                SELECT privilege, admin_option, 'DIRECT' as grant_type
                FROM dba_sys_privs
                WHERE grantee = :username
            """, username=username.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            privileges = [dict(zip(columns, row)) for row in rows]
            
            # Quyền qua role
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
        Truy vấn roles của user từ DBA_ROLE_PRIVS.
        
        Args:
            username: Tên đăng nhập Oracle
            
        Returns:
            Danh sách các dict chứa thông tin role
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
        Lấy hạn mức (quota) của user từ DBA_TS_QUOTAS.
        
        Args:
            username: Tên đăng nhập Oracle
            
        Returns:
            Danh sách các dict chứa thông tin quota
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
        Truy vấn thông tin user từ bảng ứng dụng user_info.
        
        Args:
            username: Tên đăng nhập Oracle
            
        Returns:
            Dict thông tin user hoặc None nếu không tìm thấy
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
            # Bảng có thể chưa tồn tại
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
        Thêm thông tin user vào bảng ứng dụng user_info.
        
        Args:
            username: Tên đăng nhập Oracle
            full_name: Họ tên đầy đủ (tùy chọn)
            email: Email (tùy chọn)
            phone: Số điện thoại (tùy chọn)
            address: Địa chỉ (tùy chọn)
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
        Cập nhật thông tin user trong bảng ứng dụng user_info.
        
        Args:
            username: Tên đăng nhập Oracle
            full_name: Họ tên đầy đủ (tùy chọn)
            email: Email (tùy chọn)
            phone: Số điện thoại (tùy chọn)
            address: Địa chỉ (tùy chọn)
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


# Instance DAO toàn cục
user_dao = UserDAO()
