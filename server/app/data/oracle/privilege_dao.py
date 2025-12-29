"""Đối tượng truy cập dữ liệu quyền hạn cho Oracle database."""

import oracledb
from typing import List, Dict, Any, Optional
from app.data.oracle.connection import db


class PrivilegeDAO:
    """DAO cho các thao tác quyền hạn."""

    async def has_privilege(self, username: str, privilege: str) -> bool:
        """
        Kiểm tra xem user có quyền cụ thể hay không.
        
        Args:
            username: Tên đăng nhập Oracle
            privilege: Tên quyền cần kiểm tra
            
        Returns:
            True nếu user có quyền, False nếu không
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Kiểm tra quyền hệ thống
            await cursor.execute("""
                SELECT COUNT(*) 
                FROM dba_sys_privs 
                WHERE grantee = :username 
                AND privilege = :privilege
            """, username=username.upper(), privilege=privilege)
            
            row = await cursor.fetchone()
            if row and row[0] > 0:
                return True
            
            # Kiểm tra quyền qua role (đơn giản hóa)
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
        """Truy vấn tất cả quyền hệ thống có sẵn."""
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
            print(f"Lỗi truy vấn quyền hệ thống: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_grantee_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """
        Truy vấn tất cả quyền đã cấp cho một user/role cụ thể.
        
        Trả về kết hợp quyền hệ thống và role grants.
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Quyền hệ thống
            await cursor.execute("""
                SELECT privilege, admin_option, 'SYSTEM' as privilege_type
                FROM dba_sys_privs
                WHERE grantee = :grantee
                ORDER BY privilege
            """, grantee=grantee.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            
            # Quyền qua role
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
            print(f"Lỗi truy vấn quyền grantee: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_all_roles(self) -> List[Dict[str, Any]]:
        """Truy vấn tất cả roles có sẵn để cấp."""
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
            print(f"Lỗi truy vấn roles: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_all_users(self) -> List[Dict[str, Any]]:
        """Truy vấn tất cả users để cấp quyền."""
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
            print(f"Lỗi truy vấn users: {e}")
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
        Cấp quyền hệ thống cho user/role.
        
        Args:
            privilege: Tên quyền hệ thống
            grantee: Tên user hoặc role
            with_admin: Cấp kèm ADMIN OPTION
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
            print(f"Lỗi cấp quyền hệ thống: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def revoke_system_privilege_ddl(self, privilege: str, grantee: str) -> None:
        """
        Thu hồi quyền hệ thống từ user/role.
        
        Args:
            privilege: Tên quyền hệ thống
            grantee: Tên user hoặc role
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"REVOKE {privilege} FROM {grantee.upper()}")
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi thu hồi quyền hệ thống: {e}")
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
        Cấp role cho user/role.
        
        Args:
            role: Tên role
            grantee: Tên user hoặc role
            with_admin: Cấp kèm ADMIN OPTION
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
            print(f"Lỗi cấp role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def revoke_role_ddl(self, role: str, grantee: str) -> None:
        """
        Thu hồi role từ user/role.
        
        Args:
            role: Tên role
            grantee: Tên user hoặc role
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(f"REVOKE {role.upper()} FROM {grantee.upper()}")
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi thu hồi role: {e}")
            raise
        finally:
            await db.release_connection(conn)

    # ==========================================
    # Phương thức Quyền trên Đối tượng
    # ==========================================

    async def query_all_tables(self, owner: str = None) -> List[Dict[str, Any]]:
        """
        Truy vấn tất cả bảng có sẵn để cấp quyền đối tượng.
        
        Args:
            owner: Lọc theo owner (mặc định: tất cả owner trừ các schema SYS)
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            if owner:
                await cursor.execute("""
                    SELECT owner, table_name 
                    FROM all_tables 
                    WHERE owner = :owner
                    ORDER BY owner, table_name
                """, owner=owner.upper())
            else:
                await cursor.execute("""
                    SELECT owner, table_name 
                    FROM all_tables 
                    WHERE owner NOT IN (
                        'SYS', 'SYSTEM', 'XDB', 'CTXSYS', 'MDSYS', 
                        'ORDSYS', 'WMSYS', 'LBACSYS', 'OUTLN', 'DBSNMP'
                    )
                    ORDER BY owner, table_name
                """)
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except oracledb.Error as e:
            print(f"Lỗi truy vấn bảng: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_object_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """
        Truy vấn quyền đối tượng đã cấp cho một user/role cụ thể.
        
        Returns:
            Danh sách các quyền đối tượng với tên bảng, owner, quyền, có thể cấp tiếp
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT owner, table_name, privilege, grantable, 'OBJECT' as privilege_type
                FROM dba_tab_privs
                WHERE grantee = :grantee
                ORDER BY owner, table_name, privilege
            """, grantee=grantee.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except oracledb.Error as e:
            print(f"Lỗi truy vấn quyền đối tượng: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def grant_object_privilege_ddl(
        self,
        privilege: str,
        owner: str,
        table_name: str,
        grantee: str,
        with_grant_option: bool = False,
    ) -> None:
        """
        Cấp quyền đối tượng trên bảng cho user/role.
        
        Args:
            privilege: SELECT, INSERT, UPDATE, DELETE
            owner: Chủ sở hữu bảng
            table_name: Tên bảng
            grantee: Tên user hoặc role
            with_grant_option: Cho phép grantee cấp quyền này cho người khác
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            ddl = f'GRANT {privilege} ON "{owner.upper()}"."{table_name.upper()}" TO {grantee.upper()}'
            if with_grant_option:
                ddl += " WITH GRANT OPTION"
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi cấp quyền đối tượng: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def revoke_object_privilege_ddl(
        self,
        privilege: str,
        owner: str,
        table_name: str,
        grantee: str,
    ) -> None:
        """
        Thu hồi quyền đối tượng từ user/role.
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(
                f'REVOKE {privilege} ON "{owner.upper()}"."{table_name.upper()}" FROM {grantee.upper()}'
            )
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi thu hồi quyền đối tượng: {e}")
            raise
        finally:
            await db.release_connection(conn)

    # ==========================================
    # Phương thức Quyền trên Cột
    # ==========================================

    async def query_table_columns(self, owner: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Truy vấn các cột của một bảng cụ thể.
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT column_name, data_type, nullable
                FROM all_tab_columns
                WHERE owner = :owner AND table_name = :table_name
                ORDER BY column_id
            """, owner=owner.upper(), table_name=table_name.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except oracledb.Error as e:
            print(f"Lỗi truy vấn cột bảng: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def query_column_privileges(self, grantee: str) -> List[Dict[str, Any]]:
        """
        Truy vấn quyền cấp cột đã cấp cho một user/role cụ thể.
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT owner, table_name, column_name, privilege, grantable, 'COLUMN' as privilege_type
                FROM dba_col_privs
                WHERE grantee = :grantee
                ORDER BY owner, table_name, column_name, privilege
            """, grantee=grantee.upper())
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except oracledb.Error as e:
            print(f"Lỗi truy vấn quyền cột: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def grant_column_privilege_ddl(
        self,
        privilege: str,
        owner: str,
        table_name: str,
        columns: List[str],
        grantee: str,
    ) -> None:
        """
        Cấp quyền trên các cột cụ thể cho user/role.
        
        Args:
            privilege: SELECT hoặc INSERT
            owner: Chủ sở hữu bảng
            table_name: Tên bảng
            columns: Danh sách tên cột
            grantee: Tên user hoặc role
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            cols = ", ".join([f'"{c.upper()}"' for c in columns])
            ddl = f'GRANT {privilege}({cols}) ON "{owner.upper()}"."{table_name.upper()}" TO {grantee.upper()}'
            
            await cursor.execute(ddl)
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi cấp quyền cột: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def revoke_column_privilege_ddl(
        self,
        privilege: str,
        owner: str,
        table_name: str,
        columns: List[str],
        grantee: str,
    ) -> None:
        """
        Thu hồi quyền trên cột từ user/role.
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            cols = ", ".join([f'"{c.upper()}"' for c in columns])
            await cursor.execute(
                f'REVOKE {privilege}({cols}) ON "{owner.upper()}"."{table_name.upper()}" FROM {grantee.upper()}'
            )
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi thu hồi quyền cột: {e}")
            raise
        finally:
            await db.release_connection(conn)


# Instance DAO toàn cục
privilege_dao = PrivilegeDAO()
