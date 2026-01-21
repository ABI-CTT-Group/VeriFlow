from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://veriflow:veriflow_dev@localhost:5432/veriflow"
    
    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "veriflow"
    minio_secret_key: str = "veriflow_dev"
    minio_bucket: str = "veriflow"
    minio_secure: bool = False
    
    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
