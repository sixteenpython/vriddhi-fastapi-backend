"""
Investment planning and analysis API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from app.database.session import get_db
from app.services.investment_engine import VriddhiInvestmentEngine
from app.services.stock_service import StockService
from app.schemas.investment import (
    InvestmentPlanRequest,
    InvestmentPlanResponse,
    PortfolioOptimizationRequest,
    WholeShareAllocation,
    PortfolioAllocation,
    InvestmentSummary,
    FinancialProjection,
    SelectionRationale
)
from app.schemas.stock import StockSelectionRequest, StockSelectionResponse
from app.core.config import settings
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("vriddhi")

@router.post("/plan", response_model=InvestmentPlanResponse)
async def create_investment_plan(
    request: InvestmentPlanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a comprehensive investment plan using Vriddhi algorithms

    This is the main endpoint that replicates the full Vriddhi functionality:

    **Process:**
    1. **Stock Selection**: PEG-based two-round selection with sector diversification
    2. **Portfolio Optimization**: Modern Portfolio Theory optimization using scipy
    3. **SIP Modeling**: Monthly investment projections and growth scenarios
    4. **Analysis**: Comprehensive investment analysis with visualization data

    **Features:**
    - 🎯 PEG-based selection (PE/CAGR ratio optimization)
    - 🏢 Automatic sector diversification
    - 📊 Modern Portfolio Theory weight optimization
    - 💰 SIP (Systematic Investment Plan) calculations
    - 📈 Multi-horizon forecasting (12M-60M)
    - 🔍 Detailed selection rationale

    **Returns:**
    Complete investment plan with portfolio allocations, financial projections,
    selection rationale, and diversification analysis.
    """
    try:
        logger.info(f"Creating investment plan: {request.monthly_investment}/month, {request.horizon_months}m horizon")

        # Initialize investment engine
        investment_engine = VriddhiInvestmentEngine(db)

        # Convert expected CAGR to decimal
        expected_cagr_decimal = request.expected_cagr

        # Run complete analysis
        analysis_results = await investment_engine.run_complete_analysis(
            monthly_investment=request.monthly_investment,
            horizon_months=request.horizon_months,
            expected_cagr=expected_cagr_decimal,
            client_id=request.client_id
        )

        # Convert results to response format
        portfolio_allocations = []
        for allocation in analysis_results['portfolio_allocations']:
            stock = allocation['stock']
            portfolio_allocation = PortfolioAllocation(
                ticker=stock.ticker,
                sector=stock.sector,
                weight=allocation['weight'],
                monthly_allocation=allocation['monthly_allocation'],
                current_price=stock.current_price,
                pe_ratio=stock.pe_ratio,
                pb_ratio=stock.pb_ratio,
                peg_ratio=stock.pe_ratio / stock.avg_historical_cagr if stock.pe_ratio and stock.avg_historical_cagr else None,
                expected_cagr=stock.avg_historical_cagr
            )
            portfolio_allocations.append(portfolio_allocation)

        # Create financial projection
        financial_projection = FinancialProjection(
            projected_values=analysis_results['financial_projection']['projected_values'],
            cumulative_investment=analysis_results['financial_projection']['cumulative_investment'],
            monthly_gains=analysis_results['financial_projection']['monthly_gains'],
            total_investment=analysis_results['financial_projection']['total_investment'],
            final_value=analysis_results['financial_projection']['final_value'],
            total_gain=analysis_results['financial_projection']['total_gain'],
            money_multiplier=analysis_results['financial_projection']['money_multiplier'],
            monthly_avg_gain=analysis_results['financial_projection']['monthly_avg_gain'],
            total_return_percentage=analysis_results['financial_projection']['total_return_percentage']
        )

        # Create investment summary
        investment_summary = InvestmentSummary(
            **analysis_results['investment_summary']
        )

        # Create selection rationale
        selection_rationale = SelectionRationale(
            **analysis_results['selection_rationale']
        )

        # Create response
        response = InvestmentPlanResponse(
            portfolio_id=None,  # Would be set if saved to database
            portfolio_allocations=portfolio_allocations,
            investment_summary=investment_summary,
            financial_projection=financial_projection,
            selection_rationale=selection_rationale,
            sector_allocation=analysis_results['sector_allocation'],
            style_allocation=analysis_results.get('style_allocation'),
            risk_allocation=analysis_results.get('risk_allocation'),
            analysis_date=analysis_results['analysis_date'],
            model_version=analysis_results['model_version']
        )

        logger.info("Investment plan created successfully")
        return response

    except Exception as e:
        logger.error(f"Error creating investment plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create investment plan: {str(e)}")

@router.post("/select-stocks", response_model=StockSelectionResponse)
async def select_stocks(
    request: StockSelectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run the PEG-based stock selection algorithm

    This endpoint runs only the stock selection part of the Vriddhi algorithm:

    **Algorithm:**
    1. **Round 1**: Best stock from each sector (lowest PEG ratio)
    2. **Round 2**: All remaining stocks with PEG < threshold
    3. **Quality filters**: PE > 0, CAGR > 0, valid PEG ratio

    **Parameters:**
    - `expected_cagr`: Target CAGR (8%-50%)
    - `horizon_months`: Investment horizon (12-60 months)
    - `peg_threshold`: PEG ratio threshold for Round 2 (default: 1.0)
    - `max_stocks`: Maximum stocks in selection (default: 20)

    Useful for understanding stock selection logic before portfolio optimization.
    """
    try:
        logger.info(f"Running stock selection: CAGR={request.expected_cagr:.1%}, horizon={request.horizon_months}m")

        investment_engine = VriddhiInvestmentEngine(db)

        selected_stocks, feasible, achieved_cagr, selection_rationale = await investment_engine.advanced_stock_selector(
            expected_cagr=request.expected_cagr,
            horizon_months=request.horizon_months,
            max_stocks=request.max_stocks,
            min_stocks=request.min_stocks,
            peg_threshold=request.peg_threshold
        )

        # Convert Stock objects to StockDetail format
        from app.schemas.stock import StockDetail
        stock_details = [StockDetail.from_orm(stock) for stock in selected_stocks]

        response = StockSelectionResponse(
            selected_stocks=stock_details,
            selection_rationale=selection_rationale,
            feasible=feasible,
            achieved_cagr=achieved_cagr,
            total_stocks=len(selected_stocks)
        )

        logger.info(f"Stock selection complete: {len(selected_stocks)} stocks selected")
        return response

    except Exception as e:
        logger.error(f"Error in stock selection: {e}")
        raise HTTPException(status_code=500, detail=f"Stock selection failed: {str(e)}")

@router.post("/optimize-portfolio")
async def optimize_portfolio(
    request: PortfolioOptimizationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Optimize portfolio weights for given stocks

    Takes a list of stock tickers and applies Modern Portfolio Theory optimization
    to determine optimal weights based on risk-adjusted returns.

    **Features:**
    - Modern Portfolio Theory (Markowitz optimization)
    - Risk-adjusted weight allocation
    - Sector diversification constraints
    - Monthly allocation calculations

    Returns optimized weights and monthly allocation amounts for each stock.
    """
    try:
        logger.info(f"Optimizing portfolio for {len(request.tickers)} stocks")

        investment_engine = VriddhiInvestmentEngine(db)
        stock_service = StockService(db)

        # Get stocks by tickers
        selected_stocks = []
        for ticker in request.tickers:
            stock = await stock_service.get_stock_by_ticker(ticker.upper())
            if not stock:
                raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
            selected_stocks.append(stock)

        # Run portfolio optimization
        portfolio_allocations = investment_engine.optimize_portfolio(
            selected_stocks=selected_stocks,
            monthly_investment=request.monthly_investment,
            horizon_months=request.horizon_months
        )

        # Convert to response format
        allocations = []
        for allocation in portfolio_allocations:
            stock = allocation['stock']
            portfolio_allocation = PortfolioAllocation(
                ticker=stock.ticker,
                sector=stock.sector,
                weight=allocation['weight'],
                monthly_allocation=allocation['monthly_allocation'],
                current_price=stock.current_price,
                pe_ratio=stock.pe_ratio,
                pb_ratio=stock.pb_ratio,
                peg_ratio=stock.pe_ratio / stock.avg_historical_cagr if stock.pe_ratio and stock.avg_historical_cagr else None,
                expected_cagr=stock.avg_historical_cagr
            )
            allocations.append(portfolio_allocation)

        return {
            "portfolio_allocations": allocations,
            "total_monthly_investment": request.monthly_investment,
            "optimization_method": request.optimization_method,
            "message": "Portfolio optimization completed successfully"
        }

    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Portfolio optimization failed: {str(e)}")

@router.post("/whole-shares")
async def calculate_whole_shares(
    request: PortfolioOptimizationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate whole share allocation for portfolio

    Converts fractional share allocations to whole shares and calculates
    the actual investment required for whole share purchases.

    **Process:**
    1. Takes optimal portfolio weights
    2. Calculates ideal fractional shares for each stock
    3. Rounds to whole shares (minimum 1 per stock)
    4. Recalculates actual weights and total investment required

    Useful for investors who can only buy whole shares (most retail investors).
    """
    try:
        logger.info(f"Calculating whole share allocation for {len(request.tickers)} stocks")

        investment_engine = VriddhiInvestmentEngine(db)
        stock_service = StockService(db)

        # Get stocks and optimize portfolio
        selected_stocks = []
        for ticker in request.tickers:
            stock = await stock_service.get_stock_by_ticker(ticker.upper())
            if not stock:
                raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
            selected_stocks.append(stock)

        portfolio_allocations = investment_engine.optimize_portfolio(
            selected_stocks=selected_stocks,
            monthly_investment=request.monthly_investment,
            horizon_months=request.horizon_months
        )

        # Calculate whole share allocations
        whole_share_allocations = investment_engine.calculate_whole_share_allocation(portfolio_allocations)

        # Convert to response format
        allocations = [WholeShareAllocation(**allocation) for allocation in whole_share_allocations]

        total_investment = allocations[0].total_monthly_investment if allocations else 0
        difference = total_investment - request.monthly_investment

        return {
            "whole_share_allocations": allocations,
            "original_monthly_investment": request.monthly_investment,
            "required_monthly_investment": total_investment,
            "investment_difference": difference,
            "message": f"Whole share calculation complete. {'Additional' if difference > 0 else 'Saved'} ₹{abs(difference):,.0f}/month {'needed' if difference > 0 else 'compared to target'}"
        }

    except Exception as e:
        logger.error(f"Error calculating whole shares: {e}")
        raise HTTPException(status_code=500, detail=f"Whole share calculation failed: {str(e)}")

@router.get("/projection/{monthly_investment}/{horizon_months}")
async def calculate_sip_projection(
    monthly_investment: float,
    horizon_months: int,
    expected_cagr: float = Query(0.15, ge=0.08, le=0.50, description="Expected CAGR (decimal)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate SIP (Systematic Investment Plan) projections

    Calculates month-by-month projections for a systematic investment plan
    without running the full stock selection algorithm.

    **Parameters:**
    - `monthly_investment`: Monthly investment amount (₹)
    - `horizon_months`: Investment horizon (months)
    - `expected_cagr`: Expected annual return rate (decimal, e.g., 0.15 for 15%)

    Returns detailed monthly projections, total investment, final value, and gains.
    """
    try:
        if monthly_investment < settings.MIN_MONTHLY_INVESTMENT:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum monthly investment is ₹{settings.MIN_MONTHLY_INVESTMENT:,}"
            )

        if not (12 <= horizon_months <= 60):
            raise HTTPException(
                status_code=400,
                detail="Investment horizon must be between 12 and 60 months"
            )

        investment_engine = VriddhiInvestmentEngine(db)

        # Calculate projections
        financial_projections = investment_engine.calculate_financial_projections(
            monthly_investment=monthly_investment,
            horizon_months=horizon_months,
            achieved_cagr=expected_cagr
        )

        return {
            **financial_projections,
            "parameters": {
                "monthly_investment": monthly_investment,
                "horizon_months": horizon_months,
                "horizon_years": horizon_months / 12,
                "expected_cagr": expected_cagr * 100  # Convert to percentage for display
            },
            "analysis_date": datetime.now(),
            "message": "SIP projection calculated successfully"
        }

    except Exception as e:
        logger.error(f"Error calculating SIP projection: {e}")
        raise HTTPException(status_code=500, detail=f"SIP projection calculation failed: {str(e)}")

@router.get("/quick-analysis/{monthly_investment}/{horizon_months}")
async def quick_investment_analysis(
    monthly_investment: float,
    horizon_months: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick investment analysis with default parameters

    Provides a fast investment analysis using default settings:
    - Expected CAGR: 15%
    - Standard stock selection algorithm
    - Basic portfolio optimization

    Useful for quick estimates and API testing.
    """
    try:
        request = InvestmentPlanRequest(
            monthly_investment=monthly_investment,
            horizon_months=horizon_months,
            expected_cagr=settings.DEFAULT_EXPECTED_CAGR
        )

        # Use the main investment plan endpoint
        return await create_investment_plan(request, BackgroundTasks(), db)

    except Exception as e:
        logger.error(f"Error in quick analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Quick analysis failed: {str(e)}")