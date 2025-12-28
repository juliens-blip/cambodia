"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Cambodia Agri Analytics"
    debug: bool = False

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_access_token: Optional[str] = None

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_persist_path: str = "chroma_data"

    # Perplexity API
    perplexity_api_key: str
    perplexity_max_requests_per_month: int = 1000

    # Google Drive API
    google_drive_api_key: str
    tesseract_cmd: Optional[str] = None
    poppler_path: Optional[str] = None
    tessdata_prefix: Optional[str] = None

    # Claude API (Mock mode by default)
    claude_api_key: Optional[str] = None
    claude_mock_mode: bool = True

    # Data Sources URLs
    mef_api_url: str = "https://data.mef.gov.kh/api/v1/public-datasets/"
    wits_api_url: str = "https://wits.worldbank.org/API/V1"
    odc_base_url: str = "https://data.opendevelopmentcambodia.net/en/dataset"

    # Scheduler settings (Cambodia timezone)
    timezone: str = "Asia/Phnom_Penh"
    daily_job_hour: int = 6
    daily_job_minute: int = 0
    weekly_job_day: str = "mon"  # Monday
    weekly_job_hour: int = 6
    weekly_job_minute: int = 0

    # Redis (optional)
    redis_url: Optional[str] = None

    # CORS
    allowed_origins: list[str] = ["http://localhost:8501", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()
