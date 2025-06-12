from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Auto-DJ Backend"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Auto-DJ mixing service backend - Phase 1 MVP"

    # Server Configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Spotify API
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    SPOTIFY_REDIRECT_URI: str

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str
    CLOUDFRONT_DOMAIN: str  # e.g., "d123456abcdef8.cloudfront.net"
    
    # Audio Storage (deprecated, but kept for migration compatibility)
    AUDIO_STORAGE_PATH: str = "./audio"
    MAX_AUDIO_CACHE_GB: int = 50

    # yt-dlp settings
    YTDL_RATE_LIMIT: str = "2.0M"
    YTDL_MAX_DOWNLOADS_PER_MINUTE: int = 49

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @field_validator("AUDIO_STORAGE_PATH")
    def validate_audio_path(cls, v):
        # Only create directory in development or when writable
        if os.getenv("ENVIRONMENT", "development") == "development":
            try:
                os.makedirs(v, exist_ok=True)
            except (OSError, PermissionError):
                # Skip directory creation if path is not writable (e.g., in containers)
                pass
        return v

    @field_validator("DEBUG", mode="before")
    def set_debug_mode(cls, v):
        # Force DEBUG=False in production
        if os.getenv("ENVIRONMENT") == "production":
            return False
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
