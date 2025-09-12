"""
Application configuration using Pydantic Settings
"""

from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    """Application settings"""
    
    # Project info
    PROJECT_NAME: str = "Video Jockey"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/video_jockey.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # External APIs
    IMVDB_API_KEY: Optional[str] = None
    IMVDB_BASE_URL: str = "https://imvdb.com/api/v1"
    
    YOUTUBE_API_KEY: Optional[str] = None
    YOUTUBE_BASE_URL: str = "https://www.googleapis.com/youtube/v3"
    
    # File storage
    UPLOAD_DIR: str = "/data/uploads"
    DOWNLOAD_DIR: str = "/data/downloads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024 * 1024  # 5GB
    
    # Queue settings
    MAX_CONCURRENT_DOWNLOADS: int = 3
    DOWNLOAD_TIMEOUT: int = 3600  # 1 hour
    
    # Environment
    ENVIRONMENT: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create settings instance
settings = Settings()