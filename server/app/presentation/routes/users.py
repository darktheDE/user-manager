"""User management routes."""

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.presentation.middleware import get_session
from app.business.services.user_service import user_service
from app.presentation.templates import templates

router = APIRouter()


def require_auth(request: Request) -> str:
    """Require authentication and return username."""
    session = get_session(request)
    username = session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")
    return username


@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request):
    """Display list of users."""
    current_user = require_auth(request)
    
    try:
        users = await user_service.get_all_users()
        return templates.TemplateResponse(
            "users/list.html",
            {"request": request, "users": users, "current_user": current_user}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "users/list.html",
            {
                "request": request,
                "users": [],
                "error": str(e),
                "current_user": current_user
            },
            status_code=500,
        )


@router.get("/users/create", response_class=HTMLResponse)
async def create_user_page(request: Request):
    """Display create user form."""
    current_user = require_auth(request)
    
    # Get available tablespaces (hardcoded for now)
    tablespaces = ["USERS", "SYSTEM", "SYSAUX"]
    
    return templates.TemplateResponse(
        "users/create.html",
        {
            "request": request,
            "tablespaces": tablespaces,
            "current_user": current_user
        }
    )


@router.post("/users/create", response_class=HTMLResponse)
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    default_tablespace: str = Form(...),
    temporary_tablespace: str = Form(None),
    quota: str = Form(None),
    profile: str = Form(None),
):
    """Handle create user form submission."""
    current_user = require_auth(request)
    
    try:
        await user_service.create_user(
            username=username,
            password=password,
            default_tablespace=default_tablespace,
            temporary_tablespace=temporary_tablespace or None,
            quota=quota or None,
            profile=profile or None,
            current_user=current_user,
        )
        return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)
    except (ValueError, Exception) as e:
        tablespaces = ["USERS", "SYSTEM", "SYSAUX"]
        return templates.TemplateResponse(
            "users/create.html",
            {
                "request": request,
                "error": str(e),
                "username": username,
                "tablespaces": tablespaces,
                "current_user": current_user
            },
            status_code=400,
        )
    except PermissionError as e:
        return templates.TemplateResponse(
            "users/create.html",
            {
                "request": request,
                "error": str(e),
                "username": username,
                "tablespaces": ["USERS", "SYSTEM", "SYSAUX"],
                "current_user": current_user
            },
            status_code=403,
        )


@router.get("/users/{username}/edit", response_class=HTMLResponse)
async def edit_user_page(request: Request, username: str):
    """Display edit user form."""
    current_user = require_auth(request)
    
    try:
        user_info = await user_service.get_user_detail(username)
        tablespaces = ["USERS", "SYSTEM", "SYSAUX"]
        
        return templates.TemplateResponse(
            "users/edit.html",
            {
                "request": request,
                "user": user_info,
                "tablespaces": tablespaces,
                "current_user": current_user
            }
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "users/list.html",
            {
                "request": request,
                "users": await user_service.get_all_users(),
                "error": str(e),
                "current_user": current_user
            },
            status_code=404,
        )


@router.post("/users/{username}/edit", response_class=HTMLResponse)
async def update_user(
    request: Request,
    username: str,
    password: str = Form(None),
    default_tablespace: str = Form(None),
    temporary_tablespace: str = Form(None),
    quota: str = Form(None),
    profile: str = Form(None),
):
    """Handle update user form submission."""
    current_user = require_auth(request)
    
    try:
        await user_service.update_user(
            username=username,
            password=password or None,
            default_tablespace=default_tablespace or None,
            temporary_tablespace=temporary_tablespace or None,
            quota=quota or None,
            profile=profile or None,
            current_user=current_user,
        )
        return RedirectResponse(url=f"/users/{username}", status_code=HTTP_303_SEE_OTHER)
    except (ValueError, Exception) as e:
        try:
            user_info = await user_service.get_user_detail(username)
        except:
            user_info = {"username": username}
        return templates.TemplateResponse(
            "users/edit.html",
            {
                "request": request,
                "user": user_info,
                "error": str(e),
                "tablespaces": ["USERS", "SYSTEM", "SYSAUX"],
                "current_user": current_user
            },
            status_code=400,
        )
    except PermissionError as e:
        return templates.TemplateResponse(
            "users/edit.html",
            {
                "request": request,
                "user": await user_service.get_user_detail(username),
                "error": str(e),
                "tablespaces": ["USERS", "SYSTEM", "SYSAUX"],
                "current_user": current_user
            },
            status_code=403,
        )


@router.post("/users/{username}/delete", response_class=HTMLResponse)
async def delete_user(request: Request, username: str, cascade: bool = Query(False)):
    """Handle delete user."""
    current_user = require_auth(request)
    
    try:
        await user_service.delete_user(
            username=username,
            cascade=cascade,
            current_user=current_user,
        )
        return RedirectResponse(url="/users", status_code=HTTP_303_SEE_OTHER)
    except PermissionError as e:
        users = await user_service.get_all_users()
        return templates.TemplateResponse(
            "users/list.html",
            {
                "request": request,
                "users": users,
                "error": str(e),
                "current_user": current_user
            },
            status_code=403,
        )


@router.get("/users/{username}", response_class=HTMLResponse)
async def user_detail(request: Request, username: str):
    """Display user detail."""
    current_user = require_auth(request)
    
    try:
        user_detail = await user_service.get_user_detail(username)
        return templates.TemplateResponse(
            "users/detail.html",
            {
                "request": request,
                "user": user_detail,
                "current_user": current_user
            }
        )
    except ValueError as e:
        users = await user_service.get_all_users()
        return templates.TemplateResponse(
            "users/list.html",
            {
                "request": request,
                "users": users,
                "error": str(e),
                "current_user": current_user
            },
            status_code=404,
        )


@router.post("/users/{username}/lock", response_class=HTMLResponse)
async def lock_user(request: Request, username: str):
    """Lock user account."""
    current_user = require_auth(request)
    
    try:
        await user_service.lock_user(username)
        return RedirectResponse(url=f"/users/{username}", status_code=HTTP_303_SEE_OTHER)
    except Exception as e:
        user_detail = await user_service.get_user_detail(username)
        return templates.TemplateResponse(
            "users/detail.html",
            {
                "request": request,
                "user": user_detail,
                "error": str(e),
                "current_user": current_user
            },
            status_code=500,
        )


@router.post("/users/{username}/unlock", response_class=HTMLResponse)
async def unlock_user(request: Request, username: str):
    """Unlock user account."""
    current_user = require_auth(request)
    
    try:
        await user_service.unlock_user(username)
        return RedirectResponse(url=f"/users/{username}", status_code=HTTP_303_SEE_OTHER)
    except Exception as e:
        user_detail = await user_service.get_user_detail(username)
        return templates.TemplateResponse(
            "users/detail.html",
            {
                "request": request,
                "user": user_detail,
                "error": str(e),
                "current_user": current_user
            },
            status_code=500,
        )

