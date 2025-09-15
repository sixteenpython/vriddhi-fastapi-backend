"""
Vriddhi FastAPI Backend
AI-Powered Personal Investment Advisor

A comprehensive FastAPI backend that replicates all Vriddhi functionality including:
- PEG-based stock selection algorithm
- Modern Portfolio Theory optimization
- SIP (Systematic Investment Plan) modeling
- Multi-horizon forecasting
- Investment analysis with comprehensive data
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.exceptions import (
    VriddhiException,
    vriddhi_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.database.session import engine, create_tables
from app.api.v1 import api_router

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events
    """
    # Startup
    logger.info("Starting Vriddhi FastAPI Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")

    # Create database tables
    try:
        await create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Vriddhi FastAPI Backend...")

# Create FastAPI application
app = FastAPI(
    title="Vriddhi Investment API",
    description="""
    🌟 **Vriddhi Alpha Finder API**

    Professional AI-Powered Investment Advisory Backend

    ## Features

    - 🔬 **ML-Powered Forecasting**: Advanced Prophet + LSTM + XGBoost ensemble predictions
    - 🎯 **PEG-Based Selection**: Intelligent growth-at-reasonable-price algorithm
    - 📊 **Modern Portfolio Theory**: Professional MPT optimization with risk-adjusted returns
    - 🏢 **Automatic Diversification**: Balanced exposure across industries
    - 📈 **Multi-Horizon Analysis**: 6M/12M/18M/24M/36M/48M/60M CAGR forecasts
    - 💰 **SIP Optimization**: Systematic monthly investment modeling

    ## Investment Process

    1. **Stock Selection**: PEG-based two-round selection with sector diversification
    2. **Portfolio Optimization**: Modern Portfolio Theory with scipy optimization
    3. **SIP Modeling**: Monthly investment projections and growth scenarios
    4. **Analysis**: Comprehensive investment analysis with visualization data

    Built with FastAPI, PostgreSQL, and advanced financial algorithms.
    """,
    version="1.0.0",
    contact={
        "name": "Vriddhi Team",
        "email": "support@vriddhi.ai",
    },
    license_info={
        "name": "Educational Use Only",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Add exception handlers
from fastapi.exceptions import RequestValidationError
app.add_exception_handler(VriddhiException, vriddhi_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    """
    return {
        "status": "healthy",
        "service": "vriddhi-investment-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Vriddhi Investment API - Professional AI-Powered Investment Advisory Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_prefix": settings.API_V1_STR
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )