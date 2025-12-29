"""Privilege management routes."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.presentation.middleware import get_session
from app.business.services.privilege_service import privilege_service
from app.presentation.templates import templates

router = APIRouter()


def require_auth(request: Request) -> str:
    """Require authentication and return username."""
    session = get_session(request)
    username = session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username


@router.get("/privileges", response_class=HTMLResponse)
async def list_privileges(request: Request, grantee: str = None):
    """Display privileges page with optional grantee filter."""
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
    """Display grant privilege form."""
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
    """Handle grant privilege/role form submission."""
    username = require_auth(request)
    
    try:
        if privilege_type == "ROLE":
            await privilege_service.grant_role(privilege_or_role, grantee, with_admin)
            msg = f"Role '{privilege_or_role}' granted to '{grantee}' successfully"
        else:  # SYSTEM privilege
            await privilege_service.grant_system_privilege(privilege_or_role, grantee, with_admin)
            msg = f"Privilege '{privilege_or_role}' granted to '{grantee}' successfully"
        
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
    """Handle revoke privilege/role."""
    username = require_auth(request)
    
    try:
        if privilege_type == "ROLE":
            await privilege_service.revoke_role(privilege_or_role, grantee)
            msg = f"Role '{privilege_or_role}' revoked from '{grantee}' successfully"
        else:  # SYSTEM privilege
            await privilege_service.revoke_system_privilege(privilege_or_role, grantee)
            msg = f"Privilege '{privilege_or_role}' revoked from '{grantee}' successfully"
        
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
# Object Privileges Routes
# ==========================================

@router.get("/privileges/object", response_class=HTMLResponse)
async def object_privileges_page(request: Request, grantee: str = None):
    """Display object privileges page."""
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
    """Display grant object privilege form."""
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
    """Handle grant object privilege form submission."""
    username = require_auth(request)
    
    try:
        await privilege_service.grant_object_privilege(
            privilege, table_owner, table_name, grantee, with_grant_option
        )
        msg = f"{privilege} on {table_owner}.{table_name} granted to {grantee}"
        
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
    """Handle revoke object privilege."""
    username = require_auth(request)
    
    try:
        await privilege_service.revoke_object_privilege(
            privilege, table_owner, table_name, grantee
        )
        msg = f"{privilege} on {table_owner}.{table_name} revoked from {grantee}"
        
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
# Column Privileges Routes
# ==========================================

@router.get("/privileges/column/grant", response_class=HTMLResponse)
async def grant_column_privilege_page(request: Request, grantee: str = None):
    """Display grant column privilege form."""
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
    """API endpoint to get columns of a table."""
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
    columns: str = Form(...),  # Comma-separated column names
):
    """Handle grant column privilege form submission."""
    username = require_auth(request)
    
    try:
        column_list = [c.strip() for c in columns.split(",") if c.strip()]
        
        await privilege_service.grant_column_privilege(
            privilege, table_owner, table_name, column_list, grantee
        )
        msg = f"{privilege}({columns}) on {table_owner}.{table_name} granted to {grantee}"
        
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

