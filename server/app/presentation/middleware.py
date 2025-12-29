"""Middleware phiên làm việc cho FastAPI."""

from typing import Dict, Any
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from app.config import settings


def get_session(request: Request) -> Dict[str, Any]:
    """Lấy session từ request."""
    return request.session


def setup_session_middleware(app) -> None:
    """Cài đặt middleware phiên làm việc cho ứng dụng FastAPI."""
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        max_age=86400,  # 24 giờ
        same_site="lax",
    )
