"""Đối tượng truy cập dữ liệu Role cho Oracle database."""

import oracledb
from typing import List, Dict, Any, Optional

from app.data.oracle.connection import db


class RoleDAO:
    """DAO cho các thao tác role."""

    async def query_all_roles(self) -> List[Dict[str, Any]]:
        """
        Truy vấn tất cả roles từ DBA_ROLES.
        
        Returns:
            Danh sách dict thông tin role
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
            print(f"Lỗi truy vấn roles: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def get_role_detail(self, role_name: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin chi tiết cho một role cụ thể.
        
        Args:
            role_name: Tên role
            
        Returns:
            Dict chi tiết role hoặc None nếu không tìm thấy
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
            print(f"Lỗi lấy chi tiết role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def create_role_ddl(
        self,
        role_name: str,
        password: Optional[str] = None,
    ) -> None:
        """
        Thực thi câu lệnh DDL CREATE ROLE.
        
        Args:
            role_name: Tên role (phải được validate trước)
            password: Mật khẩu role (tùy chọn - nếu có, role yêu cầu mật khẩu để kích hoạt)
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
            print(f"Lỗi tạo role: {e}")
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
        Thực thi câu lệnh DDL ALTER ROLE.
        
        Args:
            role_name: Tên role
            password: Mật khẩu mới (tùy chọn)
            remove_password: Nếu True, xóa yêu cầu mật khẩu
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            if remove_password:
                ddl = f"ALTER ROLE {role_name.upper()} NOT IDENTIFIED"
            elif password:
                ddl = f'ALTER ROLE {role_name.upper()} IDENTIFIED BY "{password}"'
            else:
                return  # Không có gì để thay đổi
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi sửa role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def drop_role_ddl(self, role_name: str) -> None:
        """
        Thực thi câu lệnh DDL DROP ROLE.
        
        Args:
            role_name: Tên role
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"DROP ROLE {role_name.upper()}")
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi xóa role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_role_privileges(self, role_name: str) -> List[Dict[str, Any]]:
        """
        Truy vấn các quyền được cấp cho một role.
        
        Args:
            role_name: Tên role
            
        Returns:
            Danh sách dict thông tin quyền
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Quyền hệ thống cấp cho role
            await cursor.execute("""
                SELECT privilege, admin_option, 'SYSTEM' as privilege_type
                FROM dba_sys_privs
                WHERE grantee = :role_name
            """, role_name=role_name.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            privileges = [dict(zip(columns, row)) for row in rows]
            
            # Role khác cấp cho role này
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
            print(f"Lỗi truy vấn quyền của role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_role_users(self, role_name: str) -> List[Dict[str, Any]]:
        """
        Truy vấn users/roles đã được cấp role này.
        
        Args:
            role_name: Tên role
            
        Returns:
            Danh sách dict thông tin người được cấp
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
            print(f"Lỗi truy vấn người dùng dùng role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def role_exists(self, role_name: str) -> bool:
        """
        Kiểm tra xem role có tồn tại hay không.
        
        Args:
            role_name: Tên role
            
        Returns:
            True nếu role tồn tại, False nếu không
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
            print(f"Lỗi kiểm tra role tồn tại: {e}")
            return False
        finally:
            await db.release_connection(conn)


# Instance DAO toàn cục
role_dao = RoleDAO()
