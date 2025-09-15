"""
Pydantic schemas for investment-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal

# ===== REQUEST SCHEMAS =====

class InvestmentPlanRequest(BaseModel):
    """
    Request schema for creating an investment plan
    """
    monthly_investment: float = Field(
        ...,
        ge=50000,
        le=10000000,
        description="Monthly investment amount in INR (minimum ₹50,000)"
    )
    horizon_months: int = Field(
        ...,
        ge=12,
        le=60,
        description="Investment horizon in months (12-60)"
    )
    expected_cagr: Optional[float] = Field(
        0.15,
        ge=0.08,
        le=0.50,
        description="Expected CAGR (8%-50%, default 15%)"
    )
    client_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional client identifier"
    )

    @validator("horizon_months")
    def validate_horizon(cls, v):
        """Ensure horizon is in supported values"""
        supported_horizons = [12, 18, 24, 36, 48, 60]
        closest = min(supported_horizons, key=lambda x: abs(x - v))
        return closest

    class Config:
        schema_extra = {
            "example": {
                "monthly_investment": 100000,
                "horizon_months": 36,
                "expected_cagr": 0.18,
                "client_id": "client123"
            }
        }


class PortfolioOptimizationRequest(BaseModel):
    """
    Request schema for portfolio optimization
    """
    tickers: List[str] = Field(..., description="List of stock tickers")
    monthly_investment: float = Field(..., ge=50000)
    horizon_months: int = Field(..., ge=12, le=60)
    optimization_method: str = Field("mpt", description="Optimization method: 'mpt', 'equal_weight', 'risk_parity'")

    class Config:
        schema_extra = {
            "example": {
                "tickers": ["HDFCLIFE", "APOLLOHOSP", "HEROMOTOCO"],
                "monthly_investment": 100000,
                "horizon_months": 24,
                "optimization_method": "mpt"
            }
        }


# ===== RESPONSE SCHEMAS =====

class StockInfo(BaseModel):
    """
    Basic stock information schema
    """
    ticker: str
    company_name: Optional[str]
    sector: str
    current_price: float
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    avg_historical_cagr: Optional[float]
    investment_style: Optional[str]
    risk_level: Optional[str]


class StockForecastInfo(BaseModel):
    """
    Stock forecast information schema
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


class PortfolioAllocation(BaseModel):
    """
    Individual stock allocation in portfolio
    """
    ticker: str
    sector: str
    weight: float = Field(..., description="Portfolio weight (0-1)")
    monthly_allocation: float = Field(..., description="Monthly investment amount")
    current_price: float
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    peg_ratio: Optional[float]
    expected_cagr: Optional[float]

    # Whole share calculation
    target_shares: Optional[float] = Field(None, description="Ideal fractional shares")
    whole_shares: Optional[int] = Field(None, description="Rounded whole shares")
    share_cost: Optional[float] = Field(None, description="Cost of whole shares")
    actual_weight: Optional[float] = Field(None, description="Actual weight with whole shares")

    class Config:
        schema_extra = {
            "example": {
                "ticker": "HDFCLIFE",
                "sector": "Financials",
                "weight": 0.25,
                "monthly_allocation": 25000.0,
                "current_price": 788.75,
                "pe_ratio": 14.5,
                "pb_ratio": 4.2,
                "peg_ratio": 0.21,
                "expected_cagr": 53.41,
                "target_shares": 31.7,
                "whole_shares": 32,
                "share_cost": 25240.0,
                "actual_weight": 0.252
            }
        }


class SelectionRationale(BaseModel):
    """
    Stock selection rationale and methodology
    """
    total_universe: int
    after_quality_filters: int
    stocks_selected: int
    selection_method: str
    selection_criteria: List[str]
    quality_filters: List[str]
    diversification_approach: str
    sector_breakdown: Dict[str, Any]
    achieved_cagr: str
    feasible: bool
    fallback_used: bool


class FinancialProjection(BaseModel):
    """
    Financial projection data
    """
    projected_values: List[float] = Field(..., description="Monthly projected portfolio values")
    cumulative_investment: List[float] = Field(..., description="Monthly cumulative investment")
    monthly_gains: List[float] = Field(..., description="Monthly gains")

    # Key metrics
    total_investment: float
    final_value: float
    total_gain: float
    money_multiplier: float
    monthly_avg_gain: float
    total_return_percentage: float


class InvestmentSummary(BaseModel):
    """
    Investment plan summary
    """
    feasible: bool
    horizon_years: float
    horizon_months: int
    expected_cagr: float = Field(..., description="Expected CAGR (%)")
    achieved_cagr: float = Field(..., description="Achieved CAGR (%)")
    total_investment: float
    final_value: float
    total_gain: float
    money_multiplier: float
    monthly_avg_gain: float
    total_return_percentage: float
    inflation_beat_margin: Optional[float]


class InvestmentPlanResponse(BaseModel):
    """
    Complete investment plan response
    """
    # Portfolio information
    portfolio_id: Optional[int]
    portfolio_allocations: List[PortfolioAllocation]

    # Financial projections
    investment_summary: InvestmentSummary
    financial_projection: FinancialProjection

    # Analysis details
    selection_rationale: SelectionRationale

    # Diversification analysis
    sector_allocation: Dict[str, float]
    style_allocation: Optional[Dict[str, float]]
    risk_allocation: Optional[Dict[str, float]]

    # Metadata
    analysis_date: datetime
    model_version: str = "v1.0"

    class Config:
        schema_extra = {
            "example": {
                "portfolio_id": 123,
                "portfolio_allocations": [
                    {
                        "ticker": "HDFCLIFE",
                        "sector": "Financials",
                        "weight": 0.25,
                        "monthly_allocation": 25000.0,
                        "current_price": 788.75,
                        "pe_ratio": 14.5,
                        "pb_ratio": 4.2,
                        "peg_ratio": 0.21,
                        "expected_cagr": 53.41
                    }
                ],
                "investment_summary": {
                    "feasible": True,
                    "horizon_years": 3.0,
                    "horizon_months": 36,
                    "expected_cagr": 15.0,
                    "achieved_cagr": 18.2,
                    "total_investment": 3600000,
                    "final_value": 5200000,
                    "total_gain": 1600000,
                    "money_multiplier": 1.44,
                    "monthly_avg_gain": 44444.44,
                    "total_return_percentage": 44.44
                },
                "sector_allocation": {
                    "Financials": 0.30,
                    "Healthcare": 0.25,
                    "Technology": 0.20,
                    "Consumer": 0.25
                },
                "analysis_date": "2024-01-01T10:00:00Z",
                "model_version": "v1.0"
            }
        }


class WholeShareAllocation(BaseModel):
    """
    Whole share allocation response
    """
    ticker: str
    current_price: float
    weight: float
    whole_shares: int
    share_cost: float
    actual_weight: float
    total_monthly_investment: float

    class Config:
        schema_extra = {
            "example": {
                "ticker": "HDFCLIFE",
                "current_price": 788.75,
                "weight": 0.25,
                "whole_shares": 32,
                "share_cost": 25240.0,
                "actual_weight": 0.252,
                "total_monthly_investment": 100000.0
            }
        }