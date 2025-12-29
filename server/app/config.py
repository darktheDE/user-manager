"""Cấu hình ứng dụng."""


class Settings:
    """Các thiết lập của ứng dụng."""

    # Cấu hình Oracle Database
    ORACLE_HOST: str = "localhost"
    ORACLE_PORT: int = 1521
    ORACLE_SERVICE_NAME: str = "FREEPDB1"  # Oracle 23ai Free sử dụng FREEPDB1 mặc định
    ORACLE_USER: str = "system"
    ORACLE_PASSWORD: str = "oracle123"

    # Cấu hình ứng dụng
    APP_NAME: str = "User Manager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Cấu hình server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Cấu hình session
    SESSION_SECRET_KEY: str = "change-me-in-production"


settings = Settings()
