"""
API v1 router module
"""

from fastapi import APIRouter
from app.api.v1 import investment, stocks, portfolio, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(investment.router, prefix="/investment", tags=["Investment"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])