"""
Stock data API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.session import get_db
from app.services.stock_service import StockService
from app.schemas.stock import (
    StockFilterRequest,
    StockDetail,
    StockListResponse,
    SectorSummary,
    MarketSummary,
    StockSelectionRequest,
    StockSelectionResponse,
    InvestmentStyle,
    RiskLevel
)

router = APIRouter()

@router.get("/", response_model=StockListResponse)
async def get_stocks(
    sectors: Optional[List[str]] = Query(None, description="Filter by sectors"),
    min_cagr: Optional[float] = Query(None, ge=0, le=100, description="Minimum CAGR %"),
    max_cagr: Optional[float] = Query(None, ge=0, le=100, description="Maximum CAGR %"),
    min_pe: Optional[float] = Query(None, ge=0, description="Minimum PE ratio"),
    max_pe: Optional[float] = Query(None, ge=0, description="Maximum PE ratio"),
    investment_styles: Optional[List[InvestmentStyle]] = Query(None, description="Investment styles"),
    risk_levels: Optional[List[RiskLevel]] = Query(None, description="Risk levels"),
    limit: int = Query(50, ge=1, le=500, description="Number of results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get stocks with optional filtering and pagination

    Returns a paginated list of stocks matching the specified criteria.
    Use this endpoint to explore the stock universe and filter by various parameters.
    """
    stock_service = StockService(db)

    filters = StockFilterRequest(
        sectors=sectors,
        min_cagr=min_cagr,
        max_cagr=max_cagr,
        min_pe=min_pe,
        max_pe=max_pe,
        investment_styles=investment_styles,
        risk_levels=risk_levels,
        limit=limit,
        offset=offset
    )

    return await stock_service.get_stocks_with_filters(filters)

@router.get("/search")
async def search_stocks(
    q: str = Query(..., min_length=2, description="Search term for ticker or company name"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
) -> List[StockDetail]:
    """
    Search stocks by ticker symbol or company name

    Performs a case-insensitive search across stock tickers and company names.
    """
    stock_service = StockService(db)
    return await stock_service.search_stocks(q, limit)

@router.get("/sectors", response_model=List[SectorSummary])
async def get_sector_summaries(db: AsyncSession = Depends(get_db)):
    """
    Get sector-wise summary statistics

    Returns aggregated statistics for each sector including average CAGR,
    PE ratios, and the top performing stock in each sector.
    """
    stock_service = StockService(db)
    return await stock_service.get_sector_summaries()

@router.get("/market-summary", response_model=MarketSummary)
async def get_market_summary(db: AsyncSession = Depends(get_db)):
    """
    Get overall market summary and statistics

    Provides a comprehensive overview of the entire stock universe including
    market averages, sector breakdowns, and key statistics.
    """
    stock_service = StockService(db)
    return await stock_service.get_market_summary()

@router.get("/top-performers")
async def get_top_performing_stocks(
    limit: int = Query(10, ge=1, le=50, description="Number of top stocks"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    db: AsyncSession = Depends(get_db)
) -> List[StockDetail]:
    """
    Get top performing stocks by CAGR

    Returns the highest performing stocks ranked by historical CAGR.
    Optionally filter by sector to see top performers in specific industries.
    """
    stock_service = StockService(db)
    return await stock_service.get_top_performing_stocks(limit, sector)

@router.get("/by-style/{investment_style}")
async def get_stocks_by_investment_style(
    investment_style: InvestmentStyle,
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
) -> List[StockDetail]:
    """
    Get stocks by investment style

    Filter stocks by investment style: Deep Value, Value, Growth, or Balanced.
    Useful for building style-specific portfolios.
    """
    stock_service = StockService(db)
    return await stock_service.get_stocks_by_investment_style(investment_style, limit)

@router.get("/by-risk/{risk_level}")
async def get_stocks_by_risk_level(
    risk_level: RiskLevel,
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    db: AsyncSession = Depends(get_db)
) -> List[StockDetail]:
    """
    Get stocks by risk level

    Filter stocks by risk level: Low, Medium, or High.
    Helps in building risk-appropriate portfolios based on investor profile.
    """
    stock_service = StockService(db)
    return await stock_service.get_stocks_by_risk_level(risk_level, limit)

@router.get("/{ticker}", response_model=StockDetail)
async def get_stock_by_ticker(
    ticker: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information for a specific stock

    Returns comprehensive stock information including financial metrics,
    investment style, risk level, and current market data.
    """
    stock_service = StockService(db)
    stock_data = await stock_service.get_stock_with_forecast(ticker.upper())

    if not stock_data:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    return stock_data['stock']

@router.get("/{ticker}/forecast")
async def get_stock_forecast(
    ticker: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get forecast data for a specific stock

    Returns multi-horizon forecast data (6M, 12M, 18M, 24M, 36M, 48M, 60M)
    with confidence scores and model version information.
    """
    stock_service = StockService(db)
    stock_data = await stock_service.get_stock_with_forecast(ticker.upper())

    if not stock_data:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    if not stock_data['forecast']:
        raise HTTPException(status_code=404, detail=f"No forecast data available for {ticker}")

    return stock_data['forecast']

@router.get("/{ticker}/complete")
async def get_complete_stock_info(
    ticker: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete stock information including forecast

    Returns both stock details and forecast data in a single response.
    Most comprehensive endpoint for individual stock analysis.
    """
    stock_service = StockService(db)
    stock_data = await stock_service.get_stock_with_forecast(ticker.upper())

    if not stock_data:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    return {
        "stock": stock_data['stock'],
        "forecast": stock_data['forecast'],
        "has_forecast": stock_data['forecast'] is not None
    }