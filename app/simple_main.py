"""
Simplified FastAPI main application for Railway deployment
This version prioritizes starting successfully over full functionality
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import logging

# Create simple logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Vriddhi Investment API",
    description="Vriddhi Alpha Finder - AI-Powered Investment Advisory Backend",
    version="1.0.0"
)

# Simple CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Simple startup event"""
    logger.info("🚀 Vriddhi FastAPI Backend Starting...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    logger.info(f"Port: {os.getenv('PORT', '8000')}")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')}")

# Health check endpoint - CRITICAL for Railway
@app.get("/health")
async def health_check():
    """
    Health check endpoint for Railway monitoring
    """
    return {
        "status": "healthy",
        "service": "vriddhi-investment-api",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "timestamp": time.time(),
        "message": "Service is running successfully"
    }

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Vriddhi Investment API is running!",
        "version": "1.0.0",
        "health": "/health",
        "docs": "/docs",
        "status": "operational"
    }

# Simple test endpoint
@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "message": "API test successful",
        "timestamp": time.time(),
        "environment": os.getenv("ENVIRONMENT", "production")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.simple_main:app", host="0.0.0.0", port=port)