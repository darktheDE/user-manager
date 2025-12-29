"""Script để chạy ứng dụng FastAPI trong môi trường phát triển."""

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,  # Auto-reload khi code thay đổi
        log_level="info",
    )

