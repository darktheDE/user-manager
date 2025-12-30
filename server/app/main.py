"""Điểm khởi chạy ứng dụng FastAPI."""

import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.config import settings
from app.data.oracle.connection import db
from app.presentation.middleware import setup_session_middleware
from app.presentation.routes import auth, users, profiles, roles, privileges, projects, my_account, security
from app.presentation.templates import templates

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Hệ thống quản lý người dùng Oracle Database",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Thiết lập middleware session
setup_session_middleware(app)

# Đăng ký các routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(roles.router)
app.include_router(privileges.router)
app.include_router(projects.router)
app.include_router(my_account.router)
app.include_router(security.router)

# Phục vụ static files (bỏ qua nếu thư mục không tồn tại)
if os.path.exists("app/presentation/static"):
    app.mount("/static", StaticFiles(directory="app/presentation/static"), name="static")


@app.on_event("startup")
async def startup_event() -> None:
    """Khởi tạo connection pool khi ứng dụng khởi động."""
    try:
        await db.create_pool()
        print("Khởi tạo connection pool thành công")
    except Exception as e:
        print(f"Lỗi khởi tạo connection pool: {e}")
        import traceback
        traceback.print_exc()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Đóng connection pool khi ứng dụng tắt."""
    await db.close_pool()


@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root(request: Request):
    """Trang chủ - Dashboard (chỉ cho Admin)."""
    from app.presentation.middleware import get_session
    from starlette.responses import RedirectResponse
    from starlette.status import HTTP_303_SEE_OTHER
    
    session = get_session(request)
    username = session.get("username")
    
    if not username:
        return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)
    
    # Redirect user thường đến trang projects, chỉ ADMIN/SYSTEM mới thấy dashboard
    if username.upper() not in ['ADMIN', 'SYSTEM']:
        return RedirectResponse(url="/projects", status_code=HTTP_303_SEE_OTHER)
    
    
    # Lấy thống kê
    try:
        # Count Users
        async with db.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT count(*) FROM dba_users")
                user_count = (await cursor.fetchone())[0]
                
                # Count Projects
                try:
                    await cursor.execute("SELECT count(*) FROM SYSTEM.PROJECTS")
                    project_count = (await cursor.fetchone())[0]
                except:
                    project_count = 0
                    
                # Count Roles
                await cursor.execute("SELECT count(*) FROM dba_roles")
                role_count = (await cursor.fetchone())[0]
                
                # Count Active Sessions
                try:
                    await cursor.execute("SELECT count(*) FROM v$session WHERE type = 'USER'")
                    session_count = (await cursor.fetchone())[0]
                except:
                    session_count = 0
    except Exception as e:
        print(f"Error fetching stats: {e}")
        user_count = 0
        project_count = 0
        role_count = 0
        session_count = 0
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request, 
            "username": username,
            "stats": {
                "users": user_count,
                "projects": project_count,
                "roles": role_count,
                "sessions": session_count
            }
        }
    )


@app.get("/health", tags=["Health"])
async def health():
    """Endpoint kiểm tra tình trạng hệ thống."""
    return {"status": "healthy", "service": settings.APP_NAME}
