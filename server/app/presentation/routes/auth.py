"""Authentication routes."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.presentation.middleware import get_session
from app.business.services.auth_service import auth_service
from app.presentation.templates import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page."""
    # If already logged in, redirect to home
    session = get_session(request)
    if session.get("username"):
        return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "error": None}
    )


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Handle login form submission."""
    try:
        session = get_session(request)
        
        # Attempt login
        user = await auth_service.login(username, password)
        
        if not user:
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Invalid username or password",
                    "username": username,
                },
                status_code=401,
            )
        
        # Check if account is locked
        if user.account_status and "LOCKED" in user.account_status:
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Account is locked. Please contact administrator.",
                    "username": username,
                },
                status_code=403,
            )
        
        # Set session
        session["username"] = user.username
        session["account_status"] = user.account_status
        
        # Redirect to home
        return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    except Exception as e:
        import traceback
        print(f"Login error: {e}")
        print(traceback.format_exc())
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": f"An error occurred: {str(e)}",
                "username": username,
            },
            status_code=500,
        )


@router.post("/logout")
async def logout(request: Request):
    """Handle logout."""
    session = get_session(request)
    session.clear()
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

