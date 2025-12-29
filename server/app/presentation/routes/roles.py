"""Các route quản lý role."""

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.presentation.middleware import get_session
from app.business.services.role_service import role_service
from app.presentation.templates import templates

router = APIRouter()


def require_auth(request: Request) -> str:
    """Yêu cầu xác thực và trả về username."""
    session = get_session(request)
    username = session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Chưa xác thực")
    return username


@router.get("/roles", response_class=HTMLResponse)
async def list_roles(request: Request):
    """Hiển thị danh sách role."""
    username = require_auth(request)
    
    try:
        roles = await role_service.get_all_roles()
        return templates.TemplateResponse(
            "roles/list.html",
            {
                "request": request,
                "username": username,
                "roles": roles,
                "error": None,
                "success": request.query_params.get("success"),
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "roles/list.html",
            {
                "request": request,
                "username": username,
                "roles": [],
                "error": str(e),
                "success": None,
            }
        )


@router.get("/roles/create", response_class=HTMLResponse)
async def create_role_page(request: Request):
    """Hiển thị form tạo role."""
    username = require_auth(request)
    
    return templates.TemplateResponse(
        "roles/create.html",
        {
            "request": request,
            "username": username,
            "error": None,
        }
    )


@router.post("/roles/create", response_class=HTMLResponse)
async def create_role(
    request: Request,
    role_name: str = Form(...),
    password: str = Form(None),
):
    """Xử lý submit form tạo role."""
    username = require_auth(request)
    
    # Convert empty string to None
    if password == "":
        password = None
    
    try:
        await role_service.create_role(role_name=role_name, password=password)
        return RedirectResponse(
            url=f"/roles?success=Role '{role_name}' đã được tạo thành công",
            status_code=HTTP_303_SEE_OTHER,
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "roles/create.html",
            {
                "request": request,
                "username": username,
                "error": str(e),
                "role_name": role_name,
            },
            status_code=400,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "roles/create.html",
            {
                "request": request,
                "username": username,
                "error": f"Lỗi khi tạo role: {str(e)}",
                "role_name": role_name,
            },
            status_code=500,
        )


@router.get("/roles/{role_name}/edit", response_class=HTMLResponse)
async def edit_role_page(request: Request, role_name: str):
    """Hiển thị form sửa role."""
    username = require_auth(request)
    
    try:
        role = await role_service.get_role_detail(role_name)
        
        if not role:
            return templates.TemplateResponse(
                "roles/list.html",
                {
                    "request": request,
                    "username": username,
                    "roles": await role_service.get_all_roles(),
                    "error": f"Không tìm thấy role '{role_name}'",
                    "success": None,
                }
            )
        
        return templates.TemplateResponse(
            "roles/edit.html",
            {
                "request": request,
                "username": username,
                "role": role,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "roles/list.html",
            {
                "request": request,
                "username": username,
                "roles": [],
                "error": str(e),
                "success": None,
            }
        )


@router.post("/roles/{role_name}/edit", response_class=HTMLResponse)
async def update_role(
    request: Request,
    role_name: str,
    password: str = Form(None),
    remove_password: bool = Form(False),
):
    """Xử lý submit form cập nhật role."""
    username = require_auth(request)
    
    # Convert empty string to None
    if password == "":
        password = None
    
    try:
        await role_service.update_role(
            role_name=role_name,
            password=password,
            remove_password=remove_password,
        )
        return RedirectResponse(
            url=f"/roles?success=Role '{role_name}' đã được cập nhật thành công",
            status_code=HTTP_303_SEE_OTHER,
        )
    except ValueError as e:
        role = await role_service.get_role_detail(role_name)
        return templates.TemplateResponse(
            "roles/edit.html",
            {
                "request": request,
                "username": username,
                "role": role or {"role": role_name},
                "error": str(e),
            },
            status_code=400,
        )
    except Exception as e:
        role = await role_service.get_role_detail(role_name)
        return templates.TemplateResponse(
            "roles/edit.html",
            {
                "request": request,
                "username": username,
                "role": role or {"role": role_name},
                "error": f"Lỗi khi cập nhật role: {str(e)}",
            },
            status_code=500,
        )


@router.post("/roles/{role_name}/delete", response_class=HTMLResponse)
async def delete_role(request: Request, role_name: str):
    """Xử lý xóa role."""
    username = require_auth(request)
    
    try:
        await role_service.delete_role(role_name)
        return RedirectResponse(
            url=f"/roles?success=Role '{role_name}' đã được xóa thành công",
            status_code=HTTP_303_SEE_OTHER,
        )
    except ValueError as e:
        roles = await role_service.get_all_roles()
        return templates.TemplateResponse(
            "roles/list.html",
            {
                "request": request,
                "username": username,
                "roles": roles,
                "error": str(e),
                "success": None,
            },
            status_code=400,
        )
    except Exception as e:
        roles = await role_service.get_all_roles()
        return templates.TemplateResponse(
            "roles/list.html",
            {
                "request": request,
                "username": username,
                "roles": roles,
                "error": f"Lỗi khi xóa role: {str(e)}",
                "success": None,
            },
            status_code=500,
        )
