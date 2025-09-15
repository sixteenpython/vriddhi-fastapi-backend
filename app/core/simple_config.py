"""
Simplified configuration for Railway deployment
This avoids Pydantic BaseSettings validation issues
"""

import os
from typing import List

class SimpleSettings:
    """
    Simplified settings class that won't fail on startup
    """

    # Application settings
    APP_NAME = "Vriddhi Investment API"
    API_V1_STR = "/api/v1"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    DEBUG = False

    # Server settings
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))

    # Database - handle Railway DATABASE_URL
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vriddhi.db")

    # CORS settings
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "https://your-frontend-domain.com",
        "*"  # Allow all for now
    ]

    # Investment algorithm settings
    DEFAULT_EXPECTED_CAGR = 0.15
    MIN_MONTHLY_INVESTMENT = 50000
    MAX_STOCKS_IN_PORTFOLIO = 20
    MIN_STOCKS_IN_PORTFOLIO = 8
    PEG_RATIO_THRESHOLD = 1.0

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Create settings instance
settings = SimpleSettings()