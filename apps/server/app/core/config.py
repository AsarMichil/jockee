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

    # Audio Storage
    AUDIO_STORAGE_PATH: str = "./audio"
    MAX_AUDIO_CACHE_GB: int = 50

    # yt-dlp settings
    YTDL_RATE_LIMIT: str = "50K"
    YTDL_MAX_DOWNLOADS_PER_MINUTE: int = 10

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
        # Ensure the audio storage directory exists (only if writable)
        try:
            os.makedirs(v, exist_ok=True)
        except (OSError, PermissionError):
            # Skip directory creation if path is not writable (e.g., in containers)
            pass
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
