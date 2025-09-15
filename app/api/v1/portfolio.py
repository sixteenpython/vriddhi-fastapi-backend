"""
Portfolio management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from typing import List, Optional, Dict, Any
import logging

from app.database.session import get_db
from app.models.portfolio import Portfolio, PortfolioStock
from app.models.analysis import InvestmentAnalysis
from app.schemas.investment import InvestmentSummary, PortfolioAllocation

router = APIRouter()
logger = logging.getLogger("vriddhi")

@router.get("/", response_model=List[Dict[str, Any]])
async def list_portfolios(
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of portfolios to return"),
    offset: int = Query(0, ge=0, description="Number of portfolios to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all portfolios with optional filtering

    Returns a paginated list of portfolios created through the investment planning API.
    Useful for tracking portfolio performance and client management.
    """
    try:
        query = select(Portfolio).order_by(desc(Portfolio.created_at))

        if client_id:
            query = query.where(Portfolio.client_id == client_id)

        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        portfolios = result.scalars().all()

        portfolio_list = []
        for portfolio in portfolios:
            portfolio_data = {
                "id": portfolio.id,
                "monthly_investment": portfolio.monthly_investment,
                "horizon_months": portfolio.horizon_months,
                "expected_cagr": portfolio.expected_cagr,
                "achieved_cagr": portfolio.achieved_cagr,
                "total_investment": portfolio.total_investment,
                "final_value": portfolio.final_value,
                "total_gain": portfolio.total_gain,
                "money_multiplier": portfolio.money_multiplier,
                "num_stocks": portfolio.num_stocks,
                "is_feasible": portfolio.is_feasible,
                "created_at": portfolio.created_at,
                "client_id": portfolio.client_id
            }
            portfolio_list.append(portfolio_data)

        return portfolio_list

    except Exception as e:
        logger.error(f"Error listing portfolios: {e}")
        raise HTTPException(status_code=500, detail="Failed to list portfolios")

@router.get("/{portfolio_id}", response_model=Dict[str, Any])
async def get_portfolio_details(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information for a specific portfolio

    Returns complete portfolio details including stock allocations,
    selection rationale, and performance metrics.
    """
    try:
        # Get portfolio
        portfolio_query = select(Portfolio).where(Portfolio.id == portfolio_id)
        portfolio_result = await db.execute(portfolio_query)
        portfolio = portfolio_result.scalar_one_or_none()

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Get portfolio stocks
        stocks_query = select(PortfolioStock).where(PortfolioStock.portfolio_id == portfolio_id)
        stocks_result = await db.execute(stocks_query)
        portfolio_stocks = stocks_result.scalars().all()

        # Convert portfolio stocks to allocation format
        portfolio_allocations = []
        for stock in portfolio_stocks:
            allocation = PortfolioAllocation(
                ticker=stock.ticker,
                sector=stock.sector,
                weight=stock.weight,
                monthly_allocation=stock.monthly_allocation,
                current_price=stock.current_price,
                pe_ratio=stock.pe_ratio,
                pb_ratio=stock.pb_ratio,
                peg_ratio=stock.peg_ratio,
                expected_cagr=stock.expected_cagr,
                target_shares=stock.target_shares,
                whole_shares=stock.whole_shares,
                share_cost=stock.share_cost,
                actual_weight=stock.actual_weight
            )
            portfolio_allocations.append(allocation)

        # Get investment analysis if available
        analysis_query = select(InvestmentAnalysis).where(
            InvestmentAnalysis.portfolio_id == portfolio_id
        ).order_by(desc(InvestmentAnalysis.created_at)).limit(1)

        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        portfolio_details = {
            "portfolio": {
                "id": portfolio.id,
                "monthly_investment": portfolio.monthly_investment,
                "horizon_months": portfolio.horizon_months,
                "expected_cagr": portfolio.expected_cagr,
                "achieved_cagr": portfolio.achieved_cagr,
                "total_investment": portfolio.total_investment,
                "final_value": portfolio.final_value,
                "total_gain": portfolio.total_gain,
                "money_multiplier": portfolio.money_multiplier,
                "num_stocks": portfolio.num_stocks,
                "is_feasible": portfolio.is_feasible,
                "selection_rationale": portfolio.selection_rationale,
                "created_at": portfolio.created_at,
                "client_id": portfolio.client_id
            },
            "allocations": [allocation.dict() for allocation in portfolio_allocations],
            "analysis": {
                "id": analysis.id if analysis else None,
                "projected_values": analysis.projected_values if analysis else None,
                "sector_allocation": analysis.sector_allocation if analysis else None,
                "style_allocation": analysis.style_allocation if analysis else None,
                "risk_allocation": analysis.risk_allocation if analysis else None,
                "analysis_date": analysis.analysis_date if analysis else None
            } if analysis else None
        }

        return portfolio_details

    except Exception as e:
        logger.error(f"Error getting portfolio details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio details")

@router.get("/{portfolio_id}/performance")
async def get_portfolio_performance(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get portfolio performance metrics and analysis

    Returns detailed performance analysis including risk metrics,
    diversification analysis, and comparison with benchmarks.
    """
    try:
        # Get portfolio
        portfolio_query = select(Portfolio).where(Portfolio.id == portfolio_id)
        portfolio_result = await db.execute(portfolio_query)
        portfolio = portfolio_result.scalar_one_or_none()

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Get latest analysis
        analysis_query = select(InvestmentAnalysis).where(
            InvestmentAnalysis.portfolio_id == portfolio_id
        ).order_by(desc(InvestmentAnalysis.created_at)).limit(1)

        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(status_code=404, detail="No performance analysis available for this portfolio")

        performance_data = {
            "portfolio_id": portfolio_id,
            "basic_metrics": {
                "achieved_cagr": analysis.achieved_cagr,
                "total_return_percentage": analysis.total_return_percentage,
                "money_multiplier": analysis.money_multiplier,
                "monthly_avg_gain": analysis.monthly_avg_gain,
                "final_portfolio_value": analysis.final_portfolio_value,
                "total_investment": analysis.total_investment,
                "total_gains": analysis.total_gains
            },
            "risk_metrics": {
                "portfolio_volatility": analysis.portfolio_volatility,
                "sharpe_ratio": analysis.sharpe_ratio,
                "max_drawdown": analysis.max_drawdown,
                "var_95": analysis.var_95
            },
            "diversification": {
                "sector_allocation": analysis.sector_allocation,
                "style_allocation": analysis.style_allocation,
                "risk_allocation": analysis.risk_allocation
            },
            "market_comparison": {
                "inflation_beat_margin": analysis.inflation_beat_margin,
                "fd_beat_margin": analysis.fd_beat_margin,
                "market_beta": analysis.market_beta
            },
            "projections": {
                "projected_values": analysis.projected_values,
                "cumulative_investment": analysis.cumulative_investment,
                "monthly_gains": analysis.monthly_gains,
                "year_wise_breakdown": analysis.get_year_wise_breakdown()
            },
            "analysis_metadata": {
                "analysis_date": analysis.analysis_date,
                "model_version": analysis.model_version,
                "confidence_score": analysis.confidence_score
            }
        }

        return performance_data

    except Exception as e:
        logger.error(f"Error getting portfolio performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio performance")

@router.get("/{portfolio_id}/allocations")
async def get_portfolio_allocations(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed portfolio stock allocations

    Returns detailed allocation information for each stock in the portfolio
    including weights, monthly allocations, and whole share calculations.
    """
    try:
        # Verify portfolio exists
        portfolio_query = select(Portfolio).where(Portfolio.id == portfolio_id)
        portfolio_result = await db.execute(portfolio_query)
        portfolio = portfolio_result.scalar_one_or_none()

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Get portfolio stocks
        stocks_query = select(PortfolioStock).where(
            PortfolioStock.portfolio_id == portfolio_id
        ).order_by(desc(PortfolioStock.weight))

        stocks_result = await db.execute(stocks_query)
        portfolio_stocks = stocks_result.scalars().all()

        allocations = []
        total_monthly_investment = 0

        for stock in portfolio_stocks:
            allocation_data = {
                "ticker": stock.ticker,
                "sector": stock.sector,
                "weight": stock.weight,
                "monthly_allocation": stock.monthly_allocation,
                "current_price": stock.current_price,
                "pe_ratio": stock.pe_ratio,
                "pb_ratio": stock.pb_ratio,
                "peg_ratio": stock.peg_ratio,
                "expected_cagr": stock.expected_cagr,
                "target_shares": stock.target_shares,
                "whole_shares": stock.whole_shares,
                "share_cost": stock.share_cost,
                "actual_weight": stock.actual_weight,
                "created_at": stock.created_at
            }
            allocations.append(allocation_data)
            total_monthly_investment += stock.monthly_allocation

        # Calculate sector-wise allocation
        sector_allocation = {}
        for stock in portfolio_stocks:
            if stock.sector not in sector_allocation:
                sector_allocation[stock.sector] = 0
            sector_allocation[stock.sector] += stock.weight

        return {
            "portfolio_id": portfolio_id,
            "total_stocks": len(allocations),
            "total_monthly_investment": total_monthly_investment,
            "allocations": allocations,
            "sector_allocation": sector_allocation,
            "summary": {
                "highest_allocation": allocations[0] if allocations else None,
                "most_represented_sector": max(sector_allocation, key=sector_allocation.get) if sector_allocation else None
            }
        }

    except Exception as e:
        logger.error(f"Error getting portfolio allocations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio allocations")

@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a portfolio and all associated data

    Permanently deletes a portfolio including all stock allocations and analysis data.
    This action cannot be undone.
    """
    try:
        # Get portfolio to verify it exists
        portfolio_query = select(Portfolio).where(Portfolio.id == portfolio_id)
        portfolio_result = await db.execute(portfolio_query)
        portfolio = portfolio_result.scalar_one_or_none()

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Delete associated records (cascade should handle this, but being explicit)
        # Delete analysis records
        analysis_query = select(InvestmentAnalysis).where(InvestmentAnalysis.portfolio_id == portfolio_id)
        analysis_result = await db.execute(analysis_query)
        analyses = analysis_result.scalars().all()

        for analysis in analyses:
            await db.delete(analysis)

        # Delete portfolio stocks
        stocks_query = select(PortfolioStock).where(PortfolioStock.portfolio_id == portfolio_id)
        stocks_result = await db.execute(stocks_query)
        stocks = stocks_result.scalars().all()

        for stock in stocks:
            await db.delete(stock)

        # Delete portfolio
        await db.delete(portfolio)
        await db.commit()

        logger.info(f"Deleted portfolio {portfolio_id} and all associated data")

        return {
            "message": f"Portfolio {portfolio_id} deleted successfully",
            "deleted_portfolio_id": portfolio_id,
            "deleted_stocks": len(stocks),
            "deleted_analyses": len(analyses)
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete portfolio")