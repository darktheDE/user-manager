"""Application configuration."""


class Settings:
    """Application settings."""

    # Oracle Database Configuration
    ORACLE_HOST: str = "localhost"
    ORACLE_PORT: int = 1521
    ORACLE_SERVICE_NAME: str = "FREEPDB1"  # Oracle 23ai Free uses FREEPDB1 by default
    ORACLE_USER: str = "system"
    ORACLE_PASSWORD: str = "oracle123"

    # Application Configuration
    APP_NAME: str = "User Manager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Session Configuration
    SESSION_SECRET_KEY: str = "change-me-in-production"


settings = Settings()

