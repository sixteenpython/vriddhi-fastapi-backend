"""
Pydantic schemas for API request/response validation

This module contains all Pydantic schemas for:
- Investment planning and portfolio optimization
- Stock data and filtering
- Response formatting and validation
"""

from app.schemas.investment import (
    InvestmentPlanRequest,
    PortfolioOptimizationRequest,
    StockInfo,
    StockForecastInfo,
    PortfolioAllocation,
    SelectionRationale,
    FinancialProjection,
    InvestmentSummary,
    InvestmentPlanResponse,
    WholeShareAllocation
)

from app.schemas.stock import (
    StockFilterRequest,
    StockSelectionRequest,
    StockBase,
    StockDetail,
    StockForecast,
    StockWithForecast,
    StockListResponse,
    SectorSummary,
    StockSelectionResponse,
    MarketSummary,
    InvestmentStyle,
    RiskLevel,
    TrendDirection
)

__all__ = [
    # Investment schemas
    "InvestmentPlanRequest",
    "PortfolioOptimizationRequest",
    "StockInfo",
    "StockForecastInfo",
    "PortfolioAllocation",
    "SelectionRationale",
    "FinancialProjection",
    "InvestmentSummary",
    "InvestmentPlanResponse",
    "WholeShareAllocation",

    # Stock schemas
    "StockFilterRequest",
    "StockSelectionRequest",
    "StockBase",
    "StockDetail",
    "StockForecast",
    "StockWithForecast",
    "StockListResponse",
    "SectorSummary",
    "StockSelectionResponse",
    "MarketSummary",
    "InvestmentStyle",
    "RiskLevel",
    "TrendDirection"
]