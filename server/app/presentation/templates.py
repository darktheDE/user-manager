"""Jinja2 templates configuration."""

from fastapi.templating import Jinja2Templates

# Templates configuration
templates = Jinja2Templates(directory="app/presentation/templates")

