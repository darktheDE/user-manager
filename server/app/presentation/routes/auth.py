"""Các route xác thực."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.presentation.middleware import get_session
from app.business.services.auth_service import auth_service
from app.presentation.templates import templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Hiển thị trang đăng nhập."""
    # Nếu đã đăng nhập, chuyển hướng về trang chủ
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
    """Xử lý submit form đăng nhập."""
    try:
        session = get_session(request)
        
        # Thử đăng nhập
        user = await auth_service.login(username, password)
        
        if not user:
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Tên đăng nhập hoặc mật khẩu không đúng",
                    "username": username,
                },
                status_code=401,
            )
        
        # Kiểm tra nếu tài khoản bị khóa
        if user.account_status and "LOCKED" in user.account_status:
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Tài khoản bị khóa. Vui lòng liên hệ quản trị viên.",
                    "username": username,
                },
                status_code=403,
            )
        
        # Thiết lập session
        session["username"] = user.username
        session["account_status"] = user.account_status
        
        # Chuyển hướng về trang chủ
        return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    except Exception as e:
        import traceback
        print(f"Lỗi đăng nhập: {e}")
        print(traceback.format_exc())
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": f"Đã xảy ra lỗi: {str(e)}",
                "username": username,
            },
            status_code=500,
        )


@router.post("/logout")
async def logout(request: Request):
    """Xử lý đăng xuất."""
    session = get_session(request)
    session.clear()
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)
