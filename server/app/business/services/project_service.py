"""Project management service."""

from typing import List, Dict, Any, Optional
from app.data.oracle.project_dao import project_dao


class ProjectService:
    """Service for project management operations."""

    VALID_STATUSES = ["ACTIVE", "COMPLETED", "CANCELLED"]
    
    DEPARTMENTS = [
        "IT",
        "HR",
        "FINANCE", 
        "MARKETING",
        "OPERATIONS",
        "SALES",
        "LEGAL",
        "R&D",
    ]

    async def get_all_projects(self, username: str = None) -> List[Dict[str, Any]]:
        """Get all projects, optionally filtered by owner."""
        return await project_dao.query_all_projects(username)

    async def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID."""
        return await project_dao.get_project_by_id(project_id)

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
        
        Args:
            project_name: Project name
            department: Department name
            budget: Budget amount
            owner_username: Owner's Oracle username
            status: Project status
            
        Returns:
            New project ID
            
        Raises:
            ValueError: If validation fails
        """
        if not project_name or len(project_name.strip()) == 0:
            raise ValueError("Project name is required.")
        
        if not department or len(department.strip()) == 0:
            raise ValueError("Department is required.")
        
        if budget < 0:
            raise ValueError("Budget cannot be negative.")
        
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        
        return await project_dao.create_project(
            project_name=project_name.strip(),
            department=department.strip(),
            budget=budget,
            owner_username=owner_username,
            status=status,
        )

    async def update_project(
        self,
        project_id: int,
        project_name: Optional[str] = None,
        department: Optional[str] = None,
        budget: Optional[float] = None,
        status: Optional[str] = None,
    ) -> None:
        """
        Update a project.
        
        Raises:
            ValueError: If validation fails
        """
        # Check project exists
        project = await project_dao.get_project_by_id(project_id)
        if not project:
            raise ValueError(f"Project ID {project_id} not found.")
        
        if budget is not None and budget < 0:
            raise ValueError("Budget cannot be negative.")
        
        if status is not None and status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        
        await project_dao.update_project(
            project_id=project_id,
            project_name=project_name.strip() if project_name else None,
            department=department.strip() if department else None,
            budget=budget,
            status=status,
        )

    async def delete_project(self, project_id: int) -> None:
        """
        Delete a project.
        
        Raises:
            ValueError: If project not found
        """
        project = await project_dao.get_project_by_id(project_id)
        if not project:
            raise ValueError(f"Project ID {project_id} not found.")
        
        await project_dao.delete_project(project_id)

    async def get_departments(self) -> List[str]:
        """Get list of available departments."""
        return self.DEPARTMENTS

    async def get_statuses(self) -> List[str]:
        """Get list of valid statuses."""
        return self.VALID_STATUSES


# Global service instance
project_service = ProjectService()
