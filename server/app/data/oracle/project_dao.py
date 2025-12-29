"""Project data access object for Oracle database."""

import oracledb
from typing import List, Dict, Any, Optional
from app.data.oracle.connection import db


class ProjectDAO:
    """Data access object for project operations."""

    async def query_all_projects(self, username: str = None) -> List[Dict[str, Any]]:
        """
        Query all projects.
        
        Args:
            username: Optional - filter by owner username
            
        Returns:
            List of project information dicts
        """
        if not db.pool:
            await db.create_pool()
        
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            if username:
                await cursor.execute("""
                    SELECT project_id, project_name, department, budget, status, 
                           owner_username, created_at, updated_at
                    FROM projects
                    WHERE owner_username = :username
                    ORDER BY created_at DESC
                """, username=username.upper())
            else:
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
            print(f"Error querying projects: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID."""
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
            print(f"Error getting project: {e}")
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
        Create a new project.
        
        Returns:
            New project ID
        """
        conn = await db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Insert with RETURNING to get the generated ID
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
            
            # Get the last inserted ID
            await cursor.execute("SELECT MAX(project_id) FROM projects")
            row = await cursor.fetchone()
            return row[0] if row else 0
            
        except oracledb.Error as e:
            await conn.rollback()
            print(f"Error creating project: {e}")
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
        """Update a project."""
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
            print(f"Error updating project: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def delete_project(self, project_id: int) -> None:
        """Delete a project."""
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
            print(f"Error deleting project: {e}")
            raise
        finally:
            await db.release_connection(conn)

    async def get_departments(self) -> List[str]:
        """Get list of distinct departments."""
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
            print(f"Error getting departments: {e}")
            return []
        finally:
            await db.release_connection(conn)


# Global DAO instance
project_dao = ProjectDAO()
