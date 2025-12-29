"""Các route quản lý quyền hạn."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.presentation.middleware import get_session
from app.business.services.privilege_service import privilege_service
from app.presentation.templates import templates

router = APIRouter()


def require_auth(request: Request) -> str:
    """Yêu cầu xác thực và trả về username."""
    session = get_session(request)
    username = session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Chưa xác thực")
    return username


@router.get("/privileges", response_class=HTMLResponse)
async def list_privileges(request: Request, grantee: str = None):
    """Hiển thị trang quyền hạn với bộ lọc grantee tùy chọn."""
    username = require_auth(request)
    
    try:
        privileges = []
        users = await privilege_service.get_all_users()
        roles = await privilege_service.get_all_roles()
        
        if grantee:
            privileges = await privilege_service.get_grantee_privileges(grantee)
        
        return templates.TemplateResponse(
            "privileges/list.html",
            {
                "request": request,
                "username": username,
                "privileges": privileges,
                "selected_grantee": grantee,
                "users": users,
                "roles": roles,
                "error": None,
                "success": request.query_params.get("success"),
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "privileges/list.html",
            {
                "request": request,
                "username": username,
                "privileges": [],
                "selected_grantee": grantee,
                "users": [],
                "roles": [],
                "error": str(e),
                "success": None,
            }
        )


@router.get("/privileges/grant", response_class=HTMLResponse)
async def grant_privilege_page(request: Request, grantee: str = None):
    """Hiển thị form cấp quyền."""
    username = require_auth(request)
    
    try:
        users = await privilege_service.get_all_users()
        roles = await privilege_service.get_all_roles()
        common_privs = await privilege_service.get_common_privileges()
        
        return templates.TemplateResponse(
            "privileges/grant.html",
            {
                "request": request,
                "username": username,
                "users": users,
                "roles": roles,
                "common_privileges": common_privs,
                "selected_grantee": grantee,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "privileges/grant.html",
            {
                "request": request,
                "username": username,
                "users": [],
                "roles": [],
                "common_privileges": [],
                "selected_grantee": grantee,
                "error": str(e),
            }
        )


@router.post("/privileges/grant", response_class=HTMLResponse)
async def grant_privilege(
    request: Request,
    grantee: str = Form(...),
    privilege_type: str = Form(...),
    privilege_or_role: str = Form(...),
    with_admin: bool = Form(False),
):
    """Xử lý submit form cấp quyền/role."""
    username = require_auth(request)
    
    try:
        if privilege_type == "ROLE":
            await privilege_service.grant_role(privilege_or_role, grantee, with_admin)
            msg = f"Role '{privilege_or_role}' đã được cấp cho '{grantee}' thành công"
        else:  # SYSTEM privilege
            await privilege_service.grant_system_privilege(privilege_or_role, grantee, with_admin)
            msg = f"Quyền '{privilege_or_role}' đã được cấp cho '{grantee}' thành công"
        
        return RedirectResponse(
            url=f"/privileges?grantee={grantee}&success={msg}",
            status_code=HTTP_303_SEE_OTHER,
        )
    except (ValueError, Exception) as e:
        users = await privilege_service.get_all_users()
        roles = await privilege_service.get_all_roles()
        common_privs = await privilege_service.get_common_privileges()
        
        return templates.TemplateResponse(
            "privileges/grant.html",
            {
                "request": request,
                "username": username,
                "users": users,
                "roles": roles,
                "common_privileges": common_privs,
                "selected_grantee": grantee,
                "error": str(e),
            },
            status_code=400,
        )


@router.post("/privileges/revoke", response_class=HTMLResponse)
async def revoke_privilege(
    request: Request,
    grantee: str = Form(...),
    privilege_type: str = Form(...),
    privilege_or_role: str = Form(...),
):
    """Xử lý thu hồi quyền/role."""
    username = require_auth(request)
    
    try:
        if privilege_type == "ROLE":
            await privilege_service.revoke_role(privilege_or_role, grantee)
            msg = f"Role '{privilege_or_role}' đã được thu hồi từ '{grantee}' thành công"
        else:  # SYSTEM privilege
            await privilege_service.revoke_system_privilege(privilege_or_role, grantee)
            msg = f"Quyền '{privilege_or_role}' đã được thu hồi từ '{grantee}' thành công"
        
        return RedirectResponse(
            url=f"/privileges?grantee={grantee}&success={msg}",
            status_code=HTTP_303_SEE_OTHER,
        )
    except (ValueError, Exception) as e:
        privileges = await privilege_service.get_grantee_privileges(grantee)
        users = await privilege_service.get_all_users()
        roles = await privilege_service.get_all_roles()
        
        return templates.TemplateResponse(
            "privileges/list.html",
            {
                "request": request,
                "username": username,
                "privileges": privileges,
                "selected_grantee": grantee,
                "users": users,
                "roles": roles,
                "error": str(e),
                "success": None,
            },
            status_code=400,
        )


# ==========================================
# Các route Quyền trên Đối tượng
# ==========================================

@router.get("/privileges/object", response_class=HTMLResponse)
async def object_privileges_page(request: Request, grantee: str = None):
    """Hiển thị trang quyền đối tượng."""
    username = require_auth(request)
    
    try:
        object_privs = []
        users = await privilege_service.get_all_users()
        roles = await privilege_service.get_all_roles()
        
        if grantee:
            object_privs = await privilege_service.get_object_privileges(grantee)
        
        return templates.TemplateResponse(
            "privileges/object_list.html",
            {
                "request": request,
                "username": username,
                "object_privs": object_privs,
                "selected_grantee": grantee,
                "users": users,
                "roles": roles,
                "error": None,
                "success": request.query_params.get("success"),
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "privileges/object_list.html",
            {
                "request": request,
                "username": username,
                "object_privs": [],
                "selected_grantee": grantee,
                "users": [],
                "roles": [],
                "error": str(e),
                "success": None,
            }
        )


@router.get("/privileges/object/grant", response_class=HTMLResponse)
async def grant_object_privilege_page(request: Request, grantee: str = None):
    """Hiển thị form cấp quyền đối tượng."""
    username = require_auth(request)
    
    try:
        users = await privilege_service.get_all_users()
        roles = await privilege_service.get_all_roles()
        tables = await privilege_service.get_all_tables()
        
        return templates.TemplateResponse(
            "privileges/grant_object.html",
            {
                "request": request,
                "username": username,
                "users": users,
                "roles": roles,
                "tables": tables,
                "object_privileges": privilege_service.OBJECT_PRIVILEGES,
                "selected_grantee": grantee,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "privileges/grant_object.html",
            {
                "request": request,
                "username": username,
                "users": [],
                "roles": [],
                "tables": [],
                "object_privileges": [],
                "selected_grantee": grantee,
                "error": str(e),
            }
        )


@router.post("/privileges/object/grant", response_class=HTMLResponse)
async def grant_object_privilege(
    request: Request,
    grantee: str = Form(...),
    privilege: str = Form(...),
    table_owner: str = Form(...),
    table_name: str = Form(...),
    with_grant_option: bool = Form(False),
):
    """Xử lý submit form cấp quyền đối tượng."""
    username = require_auth(request)
    
    try:
        await privilege_service.grant_object_privilege(
            privilege, table_owner, table_name, grantee, with_grant_option
        )
        msg = f"Đã cấp quyền {privilege} trên {table_owner}.{table_name} cho {grantee}"
        
        return RedirectResponse(
            url=f"/privileges/object?grantee={grantee}&success={msg}",
            status_code=HTTP_303_SEE_OTHER,
        )
    except (ValueError, Exception) as e:
        users = await privilege_service.get_all_users()
        roles = await privilege_service.get_all_roles()
        tables = await privilege_service.get_all_tables()
        
        return templates.TemplateResponse(
            "privileges/grant_object.html",
            {
                "request": request,
                "username": username,
                "users": users,
                "roles": roles,
                "tables": tables,
                "object_privileges": privilege_service.OBJECT_PRIVILEGES,
                "selected_grantee": grantee,
                "error": str(e),
            },
            status_code=400,
        )


@router.post("/privileges/object/revoke", response_class=HTMLResponse)
async def revoke_object_privilege(
    request: Request,
    grantee: str = Form(...),
    privilege: str = Form(...),
    table_owner: str = Form(...),
    table_name: str = Form(...),
):
    """Xử lý thu hồi quyền đối tượng."""
    username = require_auth(request)
    
    try:
        await privilege_service.revoke_object_privilege(
            privilege, table_owner, table_name, grantee
        )
        msg = f"Đã thu hồi quyền {privilege} trên {table_owner}.{table_name} từ {grantee}"
        
        return RedirectResponse(
            url=f"/privileges/object?grantee={grantee}&success={msg}",
            status_code=HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/privileges/object?grantee={grantee}&error={str(e)}",
            status_code=HTTP_303_SEE_OTHER,
        )


# ==========================================
# Các route Quyền trên Cột
# ==========================================

@router.get("/privileges/column/grant", response_class=HTMLResponse)
async def grant_column_privilege_page(request: Request, grantee: str = None):
    """Hiển thị form cấp quyền cột."""
    username = require_auth(request)
    
    try:
        users = await privilege_service.get_all_users()
        roles = await privilege_service.get_all_roles()
        tables = await privilege_service.get_all_tables()
        
        return templates.TemplateResponse(
            "privileges/grant_column.html",
            {
                "request": request,
                "username": username,
                "users": users,
                "roles": roles,
                "tables": tables,
                "column_privileges": privilege_service.COLUMN_PRIVILEGES,
                "selected_grantee": grantee,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "privileges/grant_column.html",
            {
                "request": request,
                "username": username,
                "users": [],
                "roles": [],
                "tables": [],
                "column_privileges": [],
                "selected_grantee": grantee,
                "error": str(e),
            }
        )


@router.get("/api/tables/{owner}/{table_name}/columns")
async def get_table_columns_api(request: Request, owner: str, table_name: str):
    """API endpoint để lấy danh sách cột của một bảng."""
    require_auth(request)
    
    try:
        columns = await privilege_service.get_table_columns(owner, table_name)
        return {"columns": columns}
    except Exception as e:
        return {"error": str(e), "columns": []}


@router.post("/privileges/column/grant", response_class=HTMLResponse)
async def grant_column_privilege(
    request: Request,
    grantee: str = Form(...),
    privilege: str = Form(...),
    table_owner: str = Form(...),
    table_name: str = Form(...),
    columns: str = Form(...),  # Tên các cột phân cách bởi dấu phẩy
):
    """Xử lý submit form cấp quyền cột."""
    username = require_auth(request)
    
    try:
        column_list = [c.strip() for c in columns.split(",") if c.strip()]
        
        await privilege_service.grant_column_privilege(
            privilege, table_owner, table_name, column_list, grantee
        )
        msg = f"Đã cấp quyền {privilege}({columns}) trên {table_owner}.{table_name} cho {grantee}"
        
        return RedirectResponse(
            url=f"/privileges/object?grantee={grantee}&success={msg}",
            status_code=HTTP_303_SEE_OTHER,
        )
    except (ValueError, Exception) as e:
        users = await privilege_service.get_all_users()
        roles = await privilege_service.get_all_roles()
        tables = await privilege_service.get_all_tables()
        
        return templates.TemplateResponse(
            "privileges/grant_column.html",
            {
                "request": request,
                "username": username,
                "users": users,
                "roles": roles,
                "tables": tables,
                "column_privileges": privilege_service.COLUMN_PRIVILEGES,
                "selected_grantee": grantee,
                "error": str(e),
            },
            status_code=400,
        )
