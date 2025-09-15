"""
Configuration settings for the Vriddhi FastAPI application.
Uses Pydantic BaseSettings for environment variable management.
"""

from pydantic import BaseSettings, PostgresDsn, validator
from typing import List, Union, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """

    # Application settings
    APP_NAME: str = "Vriddhi Investment API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8501",  # Streamlit
        "https://your-frontend-domain.com"
    ]

    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "vriddhi_user"
    POSTGRES_PASSWORD: str = "vriddhi_password"
    POSTGRES_DB: str = "vriddhi_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> PostgresDsn:
        """
        Assemble database URL from individual components or use provided URL
        """
        if isinstance(v, str) and v:
            return v

        # For Railway deployment, use DATABASE_URL if available
        railway_db_url = os.getenv("DATABASE_URL")
        if railway_db_url:
            return railway_db_url

        # Fallback to individual components
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=str(values.get("POSTGRES_PORT")),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # Redis settings (optional, for caching)
    REDIS_URL: str = "redis://localhost:6379"

    # Investment algorithm settings
    DEFAULT_EXPECTED_CAGR: float = 0.15  # 15%
    MIN_MONTHLY_INVESTMENT: int = 50000  # ₹50,000
    MAX_STOCKS_IN_PORTFOLIO: int = 20
    MIN_STOCKS_IN_PORTFOLIO: int = 8
    PEG_RATIO_THRESHOLD: float = 1.0

    # Data sources
    STOCK_DATA_CSV_PATH: str = "data/grand_table_expanded.csv"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/vriddhi_api.log"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Monitoring and metrics
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure log directory exists
log_dir = Path(settings.LOG_FILE).parent
log_dir.mkdir(parents=True, exist_ok=True)