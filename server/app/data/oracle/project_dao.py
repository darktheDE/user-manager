"""Đối tượng truy cập dữ liệu dự án cho Oracle database."""

import oracledb
from typing import List, Dict, Any, Optional
from app.data.oracle.connection import db


class ProjectDAO:
    """DAO cho các thao tác dự án."""

    async def query_all_projects(self, app_username: str = None) -> List[Dict[str, Any]]:
        """
        Truy vấn tất cả dự án.
        VPD sẽ tự động lọc theo app_username nếu được set.
        
        Args:
            app_username: Username từ session (dùng cho VPD context)
            
        Returns:
            Danh sách dict thông tin dự án
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Set app user context cho VPD
            if app_username:
                await cursor.execute(
                    "BEGIN set_app_user_proc(:username); END;",
                    username=app_username.upper()
                )
            
            # Query - VPD sẽ tự động filter theo app_user_ctx
            await cursor.execute("""
                SELECT project_id, project_name, department, budget, status, 
                       owner_username, created_at, updated_at
                FROM projects
                ORDER BY created_at DESC
            """)
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except oracledb.Error as e:
            print(f"Lỗi truy vấn dự án: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Lấy dự án cụ thể theo ID."""
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT project_id, project_name, department, budget, status, 
                       owner_username, created_at, updated_at
                FROM projects
                WHERE project_id = :project_id
            """, project_id=project_id)
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0].lower() for desc in cursor.description]
            return dict(zip(columns, row))
        except oracledb.Error as e:
            print(f"Lỗi lấy dự án: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def create_project(
        self,
        project_name: str,
        department: str,
        budget: float,
        owner_username: str,
        status: str = "ACTIVE",
    ) -> int:
        """
        Tạo dự án mới.
        
        Returns:
            ID dự án mới
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Insert với RETURNING để lấy ID được tạo
            await cursor.execute("""
                INSERT INTO projects (project_name, department, budget, status, owner_username)
                VALUES (:project_name, :department, :budget, :status, :owner_username)
            """, 
                project_name=project_name,
                department=department.upper(),
                budget=budget,
                status=status,
                owner_username=owner_username.upper()
            )
            
            await conn.commit()
            
            # Lấy ID được thêm vào cuối cùng
            await cursor.execute("SELECT MAX(project_id) FROM projects")
            row = await cursor.fetchone()
            return row[0] if row else 0
            
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi tạo dự án: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def update_project(
        self,
        project_id: int,
        project_name: Optional[str] = None,
        department: Optional[str] = None,
        budget: Optional[float] = None,
        status: Optional[str] = None,
    ) -> None:
        """Cập nhật dự án."""
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            updates = []
            params = {"project_id": project_id}
            
            if project_name is not None:
                updates.append("project_name = :project_name")
                params["project_name"] = project_name
            
            if department is not None:
                updates.append("department = :department")
                params["department"] = department.upper()
            
            if budget is not None:
                updates.append("budget = :budget")
                params["budget"] = budget
            
            if status is not None:
                updates.append("status = :status")
                params["status"] = status
            
            if not updates:
                return
            
            update_clause = ", ".join(updates)
            await cursor.execute(f"""
                UPDATE projects
                SET {update_clause}
                WHERE project_id = :project_id
            """, **params)
            
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi cập nhật dự án: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def delete_project(self, project_id: int) -> None:
        """Xóa dự án."""
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute(
                "DELETE FROM projects WHERE project_id = :project_id",
                project_id=project_id
            )
            await conn.commit()
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Lỗi xóa dự án: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def get_departments(self) -> List[str]:
        """Lấy danh sách các phòng ban khác nhau."""
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            await cursor.execute("""
                SELECT DISTINCT department FROM projects ORDER BY department
            """)
            
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
        except oracledb.Error as e:
            print(f"Lỗi lấy danh sách phòng ban: {e}")
            return []
        finally:
            await db.release_connection(conn)


# Instance DAO toàn cục
project_dao = ProjectDAO()
