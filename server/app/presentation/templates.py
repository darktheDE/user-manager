"""Cấu hình template Jinja2."""

from fastapi.templating import Jinja2Templates

# Cấu hình templates
templates = Jinja2Templates(directory="app/presentation/templates")
