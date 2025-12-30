"""Các route quản lý dự án."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.presentation.middleware import get_session
from app.business.services.project_service import project_service
from app.presentation.templates import templates

router = APIRouter()


def require_auth(request: Request) -> str:
    """Yêu cầu xác thực và trả về username."""
    session = get_session(request)
    username = session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Chưa xác thực")
    return username


@router.get("/projects", response_class=HTMLResponse)
async def list_projects(request: Request):
    """Hiển thị danh sách dự án."""
    username = require_auth(request)
    
    try:
        # Truyền username để VPD context được set
        projects = await project_service.get_all_projects(app_username=username)
        return templates.TemplateResponse(
            "projects/list.html",
            {
                "request": request,
                "username": username,
                "projects": projects,
                "error": None,
                "success": request.query_params.get("success"),
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "projects/list.html",
            {
                "request": request,
                "username": username,
                "projects": [],
                "error": str(e),
                "success": None,
            }
        )


@router.get("/projects/create", response_class=HTMLResponse)
async def create_project_page(request: Request):
    """Hiển thị form tạo dự án."""
    username = require_auth(request)
    
    departments = await project_service.get_departments()
    statuses = await project_service.get_statuses()
    
    return templates.TemplateResponse(
        "projects/create.html",
        {
            "request": request,
            "username": username,
            "departments": departments,
            "statuses": statuses,
            "error": None,
        }
    )


@router.post("/projects/create", response_class=HTMLResponse)
async def create_project(
    request: Request,
    project_name: str = Form(...),
    department: str = Form(...),
    budget: float = Form(0),
    status: str = Form("ACTIVE"),
):
    """Xử lý submit form tạo dự án."""
    username = require_auth(request)
    
    try:
        project_id = await project_service.create_project(
            project_name=project_name,
            department=department,
            budget=budget,
            owner_username=username,
            status=status,
        )
        return RedirectResponse(
            url=f"/projects?success=Dự án '{project_name}' đã được tạo thành công (ID: {project_id})",
            status_code=HTTP_303_SEE_OTHER,
        )
    except ValueError as e:
        departments = await project_service.get_departments()
        statuses = await project_service.get_statuses()
        
        return templates.TemplateResponse(
            "projects/create.html",
            {
                "request": request,
                "username": username,
                "departments": departments,
                "statuses": statuses,
                "error": str(e),
                "project_name": project_name,
                "department": department,
                "budget": budget,
                "status": status,
            },
            status_code=400,
        )
    except Exception as e:
        departments = await project_service.get_departments()
        statuses = await project_service.get_statuses()
        
        return templates.TemplateResponse(
            "projects/create.html",
            {
                "request": request,
                "username": username,
                "departments": departments,
                "statuses": statuses,
                "error": f"Lỗi khi tạo dự án: {str(e)}",
                "project_name": project_name,
                "department": department,
                "budget": budget,
                "status": status,
            },
            status_code=500,
        )


@router.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def edit_project_page(request: Request, project_id: int):
    """Hiển thị form sửa dự án."""
    username = require_auth(request)
    
    try:
        project = await project_service.get_project_by_id(project_id)
        
        if not project:
            return templates.TemplateResponse(
                "projects/list.html",
                {
                    "request": request,
                    "username": username,
                    "projects": await project_service.get_all_projects(),
                    "error": f"Không tìm thấy dự án ID {project_id}",
                    "success": None,
                }
            )
        
        departments = await project_service.get_departments()
        statuses = await project_service.get_statuses()
        
        return templates.TemplateResponse(
            "projects/edit.html",
            {
                "request": request,
                "username": username,
                "project": project,
                "departments": departments,
                "statuses": statuses,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "projects/list.html",
            {
                "request": request,
                "username": username,
                "projects": [],
                "error": str(e),
                "success": None,
            }
        )


@router.post("/projects/{project_id}/edit", response_class=HTMLResponse)
async def update_project(
    request: Request,
    project_id: int,
    project_name: str = Form(...),
    department: str = Form(...),
    budget: float = Form(0),
    status: str = Form("ACTIVE"),
):
    """Xử lý submit form cập nhật dự án."""
    username = require_auth(request)
    
    try:
        await project_service.update_project(
            project_id=project_id,
            project_name=project_name,
            department=department,
            budget=budget,
            status=status,
        )
        return RedirectResponse(
            url=f"/projects?success=Dự án ID {project_id} đã được cập nhật thành công",
            status_code=HTTP_303_SEE_OTHER,
        )
    except ValueError as e:
        project = await project_service.get_project_by_id(project_id)
        departments = await project_service.get_departments()
        statuses = await project_service.get_statuses()
        
        return templates.TemplateResponse(
            "projects/edit.html",
            {
                "request": request,
                "username": username,
                "project": project or {
                    "project_id": project_id,
                    "project_name": project_name,
                    "department": department,
                    "budget": budget,
                    "status": status,
                },
                "departments": departments,
                "statuses": statuses,
                "error": str(e),
            },
            status_code=400,
        )
    except Exception as e:
        project = await project_service.get_project_by_id(project_id)
        departments = await project_service.get_departments()
        statuses = await project_service.get_statuses()
        
        return templates.TemplateResponse(
            "projects/edit.html",
            {
                "request": request,
                "username": username,
                "project": project or {"project_id": project_id},
                "departments": departments,
                "statuses": statuses,
                "error": f"Lỗi khi cập nhật dự án: {str(e)}",
            },
            status_code=500,
        )


@router.post("/projects/{project_id}/delete", response_class=HTMLResponse)
async def delete_project(request: Request, project_id: int):
    """Xử lý xóa dự án."""
    username = require_auth(request)
    
    try:
        await project_service.delete_project(project_id)
        return RedirectResponse(
            url=f"/projects?success=Dự án ID {project_id} đã được xóa thành công",
            status_code=HTTP_303_SEE_OTHER,
        )
    except ValueError as e:
        projects = await project_service.get_all_projects()
        return templates.TemplateResponse(
            "projects/list.html",
            {
                "request": request,
                "username": username,
                "projects": projects,
                "error": str(e),
                "success": None,
            },
            status_code=400,
        )
    except Exception as e:
        projects = await project_service.get_all_projects()
        return templates.TemplateResponse(
            "projects/list.html",
            {
                "request": request,
                "username": username,
                "projects": projects,
                "error": f"Lỗi khi xóa dự án: {str(e)}",
                "success": None,
            },
            status_code=500,
        )
