"""My Account route - user can view their own account info."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from app.presentation.middleware import get_session
from app.presentation.templates import templates
from app.data.oracle.user_dao import user_dao
from app.data.oracle.privilege_dao import privilege_dao

router = APIRouter()


def require_auth(request: Request) -> str:
    """Require authentication and return username."""
    session = get_session(request)
    username = session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username


@router.get("/my-account", response_class=HTMLResponse)
async def my_account_page(request: Request):
    """Display current user's account information."""
    username = require_auth(request)
    
    try:
        # Get user info from Oracle
        user_info = await user_dao.get_user_info(username)
        
        if not user_info:
            return templates.TemplateResponse(
                "my_account/index.html",
                {
                    "request": request,
                    "username": username,
                    "user": None,
                    "roles": [],
                    "system_privs": [],
                    "object_privs": [],
                    "error": "User information not found",
                }
            )
        
        # Get user's quota info
        quota_info = await user_dao.get_user_quota(username)
        
        # Get user's roles
        roles = await privilege_dao.query_grantee_privileges(username)
        user_roles = [r for r in roles if r.get("privilege_type") == "ROLE"]
        system_privs = [r for r in roles if r.get("privilege_type") == "SYSTEM"]
        
        # Get object privileges
        object_privs = await privilege_dao.query_object_privileges(username)
        
        # Get column privileges
        column_privs = await privilege_dao.query_column_privileges(username)
        
        return templates.TemplateResponse(
            "my_account/index.html",
            {
                "request": request,
                "username": username,
                "user": user_info,
                "quota": quota_info,
                "roles": user_roles,
                "system_privs": system_privs,
                "object_privs": object_privs,
                "column_privs": column_privs,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "my_account/index.html",
            {
                "request": request,
                "username": username,
                "user": None,
                "roles": [],
                "system_privs": [],
                "object_privs": [],
                "column_privs": [],
                "error": str(e),
            }
        )
