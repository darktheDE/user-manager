"""Session middleware for FastAPI."""

from typing import Dict, Any
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from app.config import settings


def get_session(request: Request) -> Dict[str, Any]:
    """Get session from request."""
    return request.session


def setup_session_middleware(app) -> None:
    """Setup session middleware for FastAPI app."""
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        max_age=86400,  # 24 hours
        same_site="lax",
    )

