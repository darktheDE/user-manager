"""Profile management routes."""

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.presentation.middleware import get_session
from app.business.services.profile_service import profile_service
from app.presentation.templates import templates

router = APIRouter()


def require_auth(request: Request) -> str:
    """Require authentication and return username."""
    session = get_session(request)
    username = session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username


@router.get("/profiles", response_class=HTMLResponse)
async def list_profiles(request: Request):
    """Display list of profiles."""
    username = require_auth(request)
    
    try:
        profiles = await profile_service.get_all_profiles()
        return templates.TemplateResponse(
            "profiles/list.html",
            {
                "request": request,
                "username": username,
                "profiles": profiles,
                "error": None,
                "success": request.query_params.get("success"),
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "profiles/list.html",
            {
                "request": request,
                "username": username,
                "profiles": [],
                "error": str(e),
                "success": None,
            }
        )


@router.get("/profiles/create", response_class=HTMLResponse)
async def create_profile_page(request: Request):
    """Display create profile form."""
    username = require_auth(request)
    
    return templates.TemplateResponse(
        "profiles/create.html",
        {
            "request": request,
            "username": username,
            "error": None,
        }
    )


@router.post("/profiles/create", response_class=HTMLResponse)
async def create_profile(
    request: Request,
    profile_name: str = Form(...),
    sessions_per_user: str = Form("DEFAULT"),
    connect_time: str = Form("DEFAULT"),
    idle_time: str = Form("DEFAULT"),
):
    """Handle create profile form submission."""
    username = require_auth(request)
    
    try:
        await profile_service.create_profile(
            profile_name=profile_name,
            sessions_per_user=sessions_per_user,
            connect_time=connect_time,
            idle_time=idle_time,
        )
        return RedirectResponse(
            url=f"/profiles?success=Profile '{profile_name}' created successfully",
            status_code=HTTP_303_SEE_OTHER,
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "profiles/create.html",
            {
                "request": request,
                "username": username,
                "error": str(e),
                "profile_name": profile_name,
                "sessions_per_user": sessions_per_user,
                "connect_time": connect_time,
                "idle_time": idle_time,
            },
            status_code=400,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "profiles/create.html",
            {
                "request": request,
                "username": username,
                "error": f"Error creating profile: {str(e)}",
                "profile_name": profile_name,
                "sessions_per_user": sessions_per_user,
                "connect_time": connect_time,
                "idle_time": idle_time,
            },
            status_code=500,
        )


@router.get("/profiles/{profile_name}/edit", response_class=HTMLResponse)
async def edit_profile_page(request: Request, profile_name: str):
    """Display edit profile form."""
    username = require_auth(request)
    
    try:
        profile = await profile_service.get_profile_detail(profile_name)
        
        if not profile:
            return templates.TemplateResponse(
                "profiles/list.html",
                {
                    "request": request,
                    "username": username,
                    "profiles": await profile_service.get_all_profiles(),
                    "error": f"Profile '{profile_name}' not found",
                    "success": None,
                }
            )
        
        # Get users using this profile
        users = await profile_service.get_profile_users(profile_name)
        
        return templates.TemplateResponse(
            "profiles/edit.html",
            {
                "request": request,
                "username": username,
                "profile": profile,
                "users": users,
                "error": None,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "profiles/list.html",
            {
                "request": request,
                "username": username,
                "profiles": [],
                "error": str(e),
                "success": None,
            }
        )


@router.post("/profiles/{profile_name}/edit", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    profile_name: str,
    sessions_per_user: str = Form(...),
    connect_time: str = Form(...),
    idle_time: str = Form(...),
):
    """Handle update profile form submission."""
    username = require_auth(request)
    
    try:
        await profile_service.update_profile(
            profile_name=profile_name,
            sessions_per_user=sessions_per_user,
            connect_time=connect_time,
            idle_time=idle_time,
        )
        return RedirectResponse(
            url=f"/profiles?success=Profile '{profile_name}' updated successfully",
            status_code=HTTP_303_SEE_OTHER,
        )
    except ValueError as e:
        profile = await profile_service.get_profile_detail(profile_name)
        users = await profile_service.get_profile_users(profile_name) if profile else []
        
        return templates.TemplateResponse(
            "profiles/edit.html",
            {
                "request": request,
                "username": username,
                "profile": profile or {
                    "profile": profile_name,
                    "sessions_per_user": sessions_per_user,
                    "connect_time": connect_time,
                    "idle_time": idle_time,
                },
                "users": users,
                "error": str(e),
            },
            status_code=400,
        )
    except Exception as e:
        profile = await profile_service.get_profile_detail(profile_name)
        users = await profile_service.get_profile_users(profile_name) if profile else []
        
        return templates.TemplateResponse(
            "profiles/edit.html",
            {
                "request": request,
                "username": username,
                "profile": profile or {
                    "profile": profile_name,
                    "sessions_per_user": sessions_per_user,
                    "connect_time": connect_time,
                    "idle_time": idle_time,
                },
                "users": users,
                "error": f"Error updating profile: {str(e)}",
            },
            status_code=500,
        )


@router.post("/profiles/{profile_name}/delete", response_class=HTMLResponse)
async def delete_profile(
    request: Request,
    profile_name: str,
    cascade: bool = Query(False),
):
    """Handle delete profile."""
    username = require_auth(request)
    
    try:
        await profile_service.delete_profile(profile_name, cascade=cascade)
        return RedirectResponse(
            url=f"/profiles?success=Profile '{profile_name}' deleted successfully",
            status_code=HTTP_303_SEE_OTHER,
        )
    except ValueError as e:
        profiles = await profile_service.get_all_profiles()
        return templates.TemplateResponse(
            "profiles/list.html",
            {
                "request": request,
                "username": username,
                "profiles": profiles,
                "error": str(e),
                "success": None,
            },
            status_code=400,
        )
    except Exception as e:
        profiles = await profile_service.get_all_profiles()
        return templates.TemplateResponse(
            "profiles/list.html",
            {
                "request": request,
                "username": username,
                "profiles": profiles,
                "error": f"Error deleting profile: {str(e)}",
                "success": None,
            },
            status_code=500,
        )
