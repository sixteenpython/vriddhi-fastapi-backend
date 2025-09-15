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

# Investment planning endpoint
@app.post("/api/v1/investment/plan")
async def investment_plan(request: dict):
    """
    Simple investment planning endpoint
    """
    monthly_investment = request.get("monthly_investment", 50000)
    investment_horizon_months = request.get("investment_horizon_months", 12)

    # Simple mock portfolio for demonstration
    mock_portfolio = [
        {"ticker": "RELIANCE", "allocation": 0.20, "sector": "Energy", "amount": monthly_investment * 0.20},
        {"ticker": "TCS", "allocation": 0.15, "sector": "IT", "amount": monthly_investment * 0.15},
        {"ticker": "HDFC", "allocation": 0.15, "sector": "Banking", "amount": monthly_investment * 0.15},
        {"ticker": "INFY", "allocation": 0.10, "sector": "IT", "amount": monthly_investment * 0.10},
        {"ticker": "ICICIBANK", "allocation": 0.10, "sector": "Banking", "amount": monthly_investment * 0.10},
        {"ticker": "BHARTIARTL", "allocation": 0.10, "sector": "Telecom", "amount": monthly_investment * 0.10},
        {"ticker": "ITC", "allocation": 0.10, "sector": "FMCG", "amount": monthly_investment * 0.10},
        {"ticker": "HDFCBANK", "allocation": 0.10, "sector": "Banking", "amount": monthly_investment * 0.10}
    ]

    # Calculate projections
    final_amount = monthly_investment * investment_horizon_months * 1.15  # 15% CAGR assumption
    total_investment = monthly_investment * investment_horizon_months
    gains = final_amount - total_investment

    return {
        "investment_summary": {
            "monthly_investment": monthly_investment,
            "investment_horizon_months": investment_horizon_months,
            "total_investment": total_investment,
            "final_amount": final_amount,
            "total_gains": gains,
            "cagr": 15.0
        },
        "portfolio_allocation": mock_portfolio,
        "selection_rationale": {
            "algorithm": "Balanced sector allocation with large-cap focus",
            "sectors_selected": ["Energy", "IT", "Banking", "Telecom", "FMCG"],
            "diversification_score": 85,
            "risk_level": "Moderate"
        },
        "projections": {
            "timeline": list(range(1, investment_horizon_months + 1)),
            "portfolio_values": [monthly_investment * i * 1.15 for i in range(1, investment_horizon_months + 1)],
            "invested_amounts": [monthly_investment * i for i in range(1, investment_horizon_months + 1)]
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.simple_main:app", host="0.0.0.0", port=port)