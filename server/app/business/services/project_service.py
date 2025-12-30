"""Dịch vụ quản lý dự án."""

from typing import List, Dict, Any, Optional
from app.data.oracle.project_dao import project_dao


class ProjectService:
    """Dịch vụ cho các thao tác quản lý dự án."""

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

    async def get_all_projects(self, app_username: str = None) -> List[Dict[str, Any]]:
        """Lấy tất cả dự án, VPD sẽ tự động lọc theo user."""
        return await project_dao.query_all_projects(app_username)

    async def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Lấy dự án cụ thể theo ID."""
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
        Tạo dự án mới.
        
        Args:
            project_name: Tên dự án
            department: Tên phòng ban
            budget: Ngân sách
            owner_username: Tên đăng nhập Oracle của người sở hữu
            status: Trạng thái dự án
            
        Returns:
            ID dự án mới
            
        Raises:
            ValueError: Nếu validation thất bại
        """
        if not project_name or len(project_name.strip()) == 0:
            raise ValueError("Tên dự án là bắt buộc.")
        
        if not department or len(department.strip()) == 0:
            raise ValueError("Phòng ban là bắt buộc.")
        
        if budget < 0:
            raise ValueError("Ngân sách không được âm.")
        
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Trạng thái không hợp lệ. Phải là một trong: {', '.join(self.VALID_STATUSES)}")
        
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
        Cập nhật dự án.
        
        Raises:
            ValueError: Nếu validation thất bại
        """
        # Kiểm tra dự án tồn tại
        project = await project_dao.get_project_by_id(project_id)
        if not project:
            raise ValueError(f"Không tìm thấy dự án ID {project_id}.")
        
        if budget is not None and budget < 0:
            raise ValueError("Ngân sách không được âm.")
        
        if status is not None and status not in self.VALID_STATUSES:
            raise ValueError(f"Trạng thái không hợp lệ. Phải là một trong: {', '.join(self.VALID_STATUSES)}")
        
        await project_dao.update_project(
            project_id=project_id,
            project_name=project_name.strip() if project_name else None,
            department=department.strip() if department else None,
            budget=budget,
            status=status,
        )

    async def delete_project(self, project_id: int) -> None:
        """
        Xóa dự án.
        
        Raises:
            ValueError: Nếu không tìm thấy dự án
        """
        project = await project_dao.get_project_by_id(project_id)
        if not project:
            raise ValueError(f"Không tìm thấy dự án ID {project_id}.")
        
        await project_dao.delete_project(project_id)

    async def get_departments(self) -> List[str]:
        """Lấy danh sách các phòng ban khả dụng."""
        return self.DEPARTMENTS

    async def get_statuses(self) -> List[str]:
        """Lấy danh sách các trạng thái hợp lệ."""
        return self.VALID_STATUSES


# Instance dịch vụ toàn cục
project_service = ProjectService()
