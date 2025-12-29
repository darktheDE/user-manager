"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Hệ thống quản lý người dùng Oracle Database",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Templates configuration
templates = Jinja2Templates(directory="app/presentation/templates")

# Static files (skip if directory doesn't exist)
if os.path.exists("app/presentation/static"):
    app.mount("/static", StaticFiles(directory="app/presentation/static"), name="static")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "User Manager API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME}

