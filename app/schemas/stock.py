"""
Pydantic schemas for stock-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# ===== ENUMS =====

class InvestmentStyle(str, Enum):
    DEEP_VALUE = "Deep Value"
    VALUE = "Value"
    GROWTH = "Growth"
    BALANCED = "Balanced"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TrendDirection(str, Enum):
    IMPROVING = "Improving"
    DECLINING = "Declining"
    STABLE = "Stable"


# ===== REQUEST SCHEMAS =====

class StockFilterRequest(BaseModel):
    """
    Request schema for filtering stocks
    """
    sectors: Optional[List[str]] = Field(None, description="Filter by sectors")
    min_cagr: Optional[float] = Field(None, ge=0, le=100, description="Minimum CAGR %")
    max_cagr: Optional[float] = Field(None, ge=0, le=100, description="Maximum CAGR %")
    min_pe: Optional[float] = Field(None, ge=0, description="Minimum PE ratio")
    max_pe: Optional[float] = Field(None, ge=0, description="Maximum PE ratio")
    min_pb: Optional[float] = Field(None, ge=0, description="Minimum PB ratio")
    max_pb: Optional[float] = Field(None, ge=0, description="Maximum PB ratio")
    investment_styles: Optional[List[InvestmentStyle]] = Field(None, description="Investment styles")
    risk_levels: Optional[List[RiskLevel]] = Field(None, description="Risk levels")
    trend_direction: Optional[TrendDirection] = Field(None, description="Trend direction")
    min_momentum_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum momentum score")
    limit: int = Field(50, ge=1, le=500, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")

    @validator("max_cagr")
    def validate_cagr_range(cls, v, values):
        if v is not None and "min_cagr" in values and values["min_cagr"] is not None:
            if v < values["min_cagr"]:
                raise ValueError("max_cagr must be greater than or equal to min_cagr")
        return v

    class Config:
        schema_extra = {
            "example": {
                "sectors": ["Financials", "Technology"],
                "min_cagr": 10.0,
                "max_cagr": 50.0,
                "max_pe": 25.0,
                "investment_styles": ["Growth", "Balanced"],
                "risk_levels": ["Low", "Medium"],
                "trend_direction": "Improving",
                "min_momentum_score": 40.0,
                "limit": 20
            }
        }


class StockSelectionRequest(BaseModel):
    """
    Request schema for stock selection algorithm
    """
    expected_cagr: float = Field(..., ge=0.08, le=0.50, description="Expected CAGR (8%-50%)")
    horizon_months: int = Field(..., ge=12, le=60, description="Investment horizon in months")
    max_stocks: int = Field(20, ge=5, le=50, description="Maximum stocks in portfolio")
    min_stocks: int = Field(8, ge=5, le=20, description="Minimum stocks in portfolio")
    peg_threshold: float = Field(1.0, ge=0.1, le=5.0, description="PEG ratio threshold")
    diversification_mode: str = Field("enhanced", description="Diversification mode: 'basic', 'enhanced'")

    class Config:
        schema_extra = {
            "example": {
                "expected_cagr": 0.18,
                "horizon_months": 36,
                "max_stocks": 15,
                "min_stocks": 8,
                "peg_threshold": 1.0,
                "diversification_mode": "enhanced"
            }
        }


# ===== RESPONSE SCHEMAS =====

class StockBase(BaseModel):
    """
    Base stock information
    """
    ticker: str
    company_name: Optional[str]
    sector: str
    current_price: float
    overall_rank: Optional[int]


class StockDetail(StockBase):
    """
    Detailed stock information
    """
    # Financial metrics
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    avg_historical_cagr: Optional[float]
    risk_adjusted_return: Optional[float]
    historical_volatility: Optional[float]

    # Investment characteristics
    investment_style: Optional[InvestmentStyle]
    risk_level: Optional[RiskLevel]
    trend_direction: Optional[TrendDirection]
    momentum_score: Optional[float]

    # Metadata
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "ticker": "HDFCLIFE",
                "company_name": "HDFC Life Insurance Company Limited",
                "sector": "Financials",
                "current_price": 788.75,
                "overall_rank": 1,
                "pe_ratio": 14.5,
                "pb_ratio": 4.2,
                "avg_historical_cagr": 69.74,
                "risk_adjusted_return": 55.79,
                "historical_volatility": 2.5,
                "investment_style": "Growth",
                "risk_level": "Low",
                "trend_direction": "Improving",
                "momentum_score": 85.5,
                "is_active": True,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            }
        }


class StockForecast(BaseModel):
    """
    Stock forecast data
    """
    ticker: str
    forecast_6m: Optional[float]
    forecast_12m: Optional[float]
    forecast_18m: Optional[float]
    forecast_24m: Optional[float]
    forecast_36m: Optional[float]
    forecast_48m: Optional[float]
    forecast_60m: Optional[float]
    confidence_score: Optional[float]
    forecast_date: datetime
    model_version: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "ticker": "HDFCLIFE",
                "forecast_6m": 45.2,
                "forecast_12m": 53.41,
                "forecast_18m": 58.7,
                "forecast_24m": 63.12,
                "forecast_36m": 71.18,
                "forecast_48m": 77.67,
                "forecast_60m": 83.33,
                "confidence_score": 0.85,
                "forecast_date": "2024-01-01T10:00:00Z",
                "model_version": "v1.0"
            }
        }


class StockWithForecast(StockDetail):
    """
    Stock with forecast information
    """
    forecast: Optional[StockForecast]


class StockListResponse(BaseModel):
    """
    Paginated stock list response
    """
    stocks: List[StockDetail]
    total_count: int
    offset: int
    limit: int
    has_more: bool

    class Config:
        schema_extra = {
            "example": {
                "stocks": [
                    {
                        "ticker": "HDFCLIFE",
                        "company_name": "HDFC Life Insurance Company Limited",
                        "sector": "Financials",
                        "current_price": 788.75,
                        "overall_rank": 1,
                        "pe_ratio": 14.5,
                        "pb_ratio": 4.2,
                        "avg_historical_cagr": 69.74,
                        "investment_style": "Growth",
                        "risk_level": "Low",
                        "is_active": True,
                        "created_at": "2024-01-01T10:00:00Z"
                    }
                ],
                "total_count": 150,
                "offset": 0,
                "limit": 50,
                "has_more": True
            }
        }


class SectorSummary(BaseModel):
    """
    Sector-wise summary statistics
    """
    sector: str
    stock_count: int
    avg_cagr: float
    avg_pe_ratio: float
    avg_pb_ratio: float
    top_performing_stock: str

    class Config:
        schema_extra = {
            "example": {
                "sector": "Financials",
                "stock_count": 25,
                "avg_cagr": 45.2,
                "avg_pe_ratio": 18.5,
                "avg_pb_ratio": 3.2,
                "top_performing_stock": "HDFCLIFE"
            }
        }


class StockSelectionResponse(BaseModel):
    """
    Response for stock selection algorithm
    """
    selected_stocks: List[StockDetail]
    selection_rationale: Dict[str, Any]
    feasible: bool
    achieved_cagr: float
    total_stocks: int

    class Config:
        schema_extra = {
            "example": {
                "selected_stocks": [
                    {
                        "ticker": "HDFCLIFE",
                        "sector": "Financials",
                        "current_price": 788.75,
                        "pe_ratio": 14.5,
                        "pb_ratio": 4.2,
                        "avg_historical_cagr": 69.74
                    }
                ],
                "selection_rationale": {
                    "total_universe": 150,
                    "after_quality_filters": 75,
                    "stocks_selected": 12,
                    "selection_method": "PEG-based with sector diversification",
                    "achieved_cagr": "18.2%"
                },
                "feasible": True,
                "achieved_cagr": 0.182,
                "total_stocks": 12
            }
        }


class MarketSummary(BaseModel):
    """
    Overall market summary
    """
    total_stocks: int
    active_stocks: int
    sectors: List[str]
    avg_market_cagr: float
    market_pe_ratio: float
    market_pb_ratio: float
    sector_summaries: List[SectorSummary]
    last_updated: datetime

    class Config:
        schema_extra = {
            "example": {
                "total_stocks": 150,
                "active_stocks": 145,
                "sectors": ["Financials", "Technology", "Healthcare", "Consumer", "Automobile"],
                "avg_market_cagr": 35.5,
                "market_pe_ratio": 22.3,
                "market_pb_ratio": 4.1,
                "sector_summaries": [
                    {
                        "sector": "Financials",
                        "stock_count": 25,
                        "avg_cagr": 45.2,
                        "avg_pe_ratio": 18.5,
                        "avg_pb_ratio": 3.2,
                        "top_performing_stock": "HDFCLIFE"
                    }
                ],
                "last_updated": "2024-01-01T10:00:00Z"
            }
        }