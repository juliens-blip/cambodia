"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Cambodia Agri Analytics"
    debug: bool = False

    # Supabase (optional for basic startup)
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_access_token: Optional[str] = None

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_persist_path: str = "chroma_data"

    # Perplexity API (optional)
    perplexity_api_key: str = ""
    perplexity_max_requests_per_month: int = 1000

    # Google Drive API (optional)
    google_drive_api_key: str = ""
    tesseract_cmd: Optional[str] = None
    poppler_path: Optional[str] = None
    tessdata_prefix: Optional[str] = None

    # Claude API (Mock mode by default)
    claude_api_key: Optional[str] = None
    claude_mock_mode: bool = True

    # Data Sources URLs
    mef_api_url: str = "https://data.mef.gov.kh/api/v1/public-datasets/"
    mef_realtime_api_url: str = "https://data.mef.gov.kh/api/v1/realtime-api"
    wits_api_url: str = "https://wits.worldbank.org/API/V1"
    odc_base_url: str = "https://data.opendevelopmentcambodia.net/en/dataset"
    fao_giews_api_base_url: str = "https://fpma.fao.org/giews/v4/global/price_module/api/v1/"
    fao_giews_price_tool_url: str = "https://www.fao.org/giews/food-prices/price-tool/en/"
    fao_giews_csv_urls: str = ""
    fao_giews_country_filter: str = "Cambodia"
    cac_base_url: str = "https://cac-camcashew.org"
    cac_seed_paths: str = "/"
    cac_max_pdfs: int = 25
    cac_max_pages: int = 20

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
