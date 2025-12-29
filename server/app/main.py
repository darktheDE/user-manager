"""FastAPI application entry point."""

import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.config import settings
from app.data.oracle.connection import db
from app.presentation.middleware import setup_session_middleware
from app.presentation.routes import auth, users
from app.presentation.templates import templates

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Hệ thống quản lý người dùng Oracle Database",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup session middleware
setup_session_middleware(app)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)

# Static files (skip if directory doesn't exist)
if os.path.exists("app/presentation/static"):
    app.mount("/static", StaticFiles(directory="app/presentation/static"), name="static")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize connection pool on application startup."""
    try:
        await db.create_pool()
        print("Connection pool initialized successfully")
    except Exception as e:
        print(f"Error initializing connection pool: {e}")
        import traceback
        traceback.print_exc()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close connection pool on application shutdown."""
    await db.close_pool()


@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root(request: Request):
    """Root endpoint - Dashboard."""
    from app.presentation.middleware import get_session
    
    session = get_session(request)
    username = session.get("username")
    
    if not username:
        from starlette.responses import RedirectResponse
        from starlette.status import HTTP_303_SEE_OTHER
        return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "username": username}
    )


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME}

