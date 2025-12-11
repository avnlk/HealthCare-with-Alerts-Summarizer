from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service info
    service_name: str = "auth-service"
    service_version: str = "1.0.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = Field(default=8004, env="PORT")

    # MongoDB settings
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "healthcare_aiops"

    # JWT settings
    jwt_secret_key: str = "healthcare-aiops-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours

    # Default admin (for initial setup)
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
