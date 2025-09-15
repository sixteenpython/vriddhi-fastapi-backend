"""
Vriddhi Investment Engine - Core algorithms ported to FastAPI

This module contains the core investment algorithms from the original Vriddhi application:
- PEG-based stock selection with sector diversification
- Modern Portfolio Theory optimization
- SIP (Systematic Investment Plan) modeling
- Multi-horizon forecasting and analysis
"""

import pandas as pd
import numpy as np
from scipy.optimize import minimize
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Any
import logging
from datetime import datetime

from app.models.stock import Stock, StockForecast
from app.models.portfolio import Portfolio, PortfolioStock
from app.models.analysis import InvestmentAnalysis
from app.schemas.investment import SelectionRationale
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger("vriddhi")

class VriddhiInvestmentEngine:
    """
    Core investment engine implementing Vriddhi algorithms
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.forecast_map = {
            6: 'forecast_6m',
            12: 'forecast_12m',
            18: 'forecast_18m',
            24: 'forecast_24m',
            36: 'forecast_36m',
            48: 'forecast_48m',
            60: 'forecast_60m'
        }

    async def get_active_stocks(self) -> List[Stock]:
        """
        Get all active stocks with their forecasts
        """
        query = select(Stock).where(Stock.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    def get_forecast_column(self, horizon_months: int) -> str:
        """
        Map horizon to forecast column
        """
        return self.forecast_map.get(horizon_months, 'forecast_24m')

    async def advanced_stock_selector(
        self,
        expected_cagr: float,
        horizon_months: int,
        max_stocks: int = 20,
        min_stocks: int = 8,
        peg_threshold: float = 1.0
    ) -> Tuple[List[Stock], bool, float, Dict[str, Any]]:
        """
        Enhanced PEG-based stock selection algorithm with sector diversification

        Args:
            expected_cagr: Target CAGR (decimal format, e.g., 0.15 for 15%)
            horizon_months: Investment horizon in months
            max_stocks: Maximum stocks in portfolio
            min_stocks: Minimum stocks in portfolio
            peg_threshold: PEG ratio threshold for Round 2 selection

        Returns:
            Tuple of (selected_stocks, feasible, achieved_cagr, selection_rationale)
        """
        logger.info(f"Starting stock selection: CAGR={expected_cagr:.1%}, horizon={horizon_months}m")

        # Get all active stocks with forecasts
        stocks = await self.get_active_stocks()

        if not stocks:
            raise ValueError("No active stocks found in database")

        # Convert to DataFrame for algorithm processing
        stock_data = []
        forecast_col = self.get_forecast_column(horizon_months)

        for stock in stocks:
            # Get latest forecast
            forecast_query = select(StockForecast).where(
                StockForecast.ticker == stock.ticker
            ).order_by(StockForecast.forecast_date.desc()).limit(1)

            forecast_result = await self.db.execute(forecast_query)
            forecast = forecast_result.scalar_one_or_none()

            if forecast and stock.pe_ratio and stock.avg_historical_cagr:
                forecast_value = getattr(forecast, forecast_col)
                if forecast_value and stock.pe_ratio > 0 and stock.avg_historical_cagr > 0:
                    stock_data.append({
                        'stock': stock,
                        'ticker': stock.ticker,
                        'sector': stock.sector,
                        'pe_ratio': stock.pe_ratio,
                        'pb_ratio': stock.pb_ratio or 0,
                        'avg_historical_cagr': stock.avg_historical_cagr,
                        'current_price': stock.current_price,
                        'forecast_cagr': forecast_value,
                        'peg_ratio': stock.pe_ratio / stock.avg_historical_cagr,
                        'investment_style': stock.investment_style,
                        'risk_level': stock.risk_level,
                        'overall_rank': stock.overall_rank or 999
                    })

        if not stock_data:
            raise ValueError("No stocks with valid data found")

        df = pd.DataFrame(stock_data)

        # Filter out invalid PEG ratios and negative CAGR stocks
        df = df[(df['pe_ratio'] > 0) & (df['avg_historical_cagr'] > 0)].copy()

        # Get unique sectors
        sectors = df['sector'].unique()
        logger.info(f"Processing {len(df)} stocks across {len(sectors)} sectors")

        # Round 1: Select best stock from each sector with lowest PEG ratio
        selected_stocks = []
        sector_selections = {}
        used_tickers = set()

        for sector in sectors:
            sector_stocks = df[df['sector'] == sector].copy()

            # Sort by PEG ratio (lowest first - best value)
            sector_stocks = sector_stocks.sort_values('peg_ratio', ascending=True)

            # Select the stock with lowest PEG ratio from this sector
            best_stock_data = sector_stocks.iloc[0]
            selected_stocks.append(best_stock_data)
            used_tickers.add(best_stock_data['ticker'])

            sector_selections[sector] = {
                'selected_stock': best_stock_data['ticker'],
                'avg_cagr': best_stock_data['avg_historical_cagr'],
                'pe_ratio': best_stock_data['pe_ratio'],
                'pb_ratio': best_stock_data['pb_ratio'],
                'peg_ratio': best_stock_data['peg_ratio'],
                'total_in_sector': len(sector_stocks)
            }

        # Round 2: Select all remaining stocks with PEG < threshold
        remaining_stocks = df[~df['ticker'].isin(used_tickers)].copy()

        # Apply PEG filter for additional selection
        quality_stocks = remaining_stocks[remaining_stocks['peg_ratio'] < peg_threshold].copy()

        # Sort by PEG ratio and select all qualifying stocks (up to max_stocks limit)
        if len(quality_stocks) > 0:
            quality_stocks = quality_stocks.sort_values('peg_ratio', ascending=True)

            # Add qualifying stocks up to max_stocks limit
            remaining_slots = max_stocks - len(selected_stocks)
            for _, stock_data in quality_stocks.head(remaining_slots).iterrows():
                selected_stocks.append(stock_data)

                # Update sector selections to track additional picks
                sector = stock_data['sector']
                if f"{sector}_additional" not in sector_selections:
                    sector_selections[f"{sector}_additional"] = []

                sector_selections[f"{sector}_additional"].append({
                    'selected_stock': stock_data['ticker'],
                    'avg_cagr': stock_data['avg_historical_cagr'],
                    'pe_ratio': stock_data['pe_ratio'],
                    'pb_ratio': stock_data['pb_ratio'],
                    'peg_ratio': stock_data['peg_ratio']
                })

        # Calculate portfolio statistics using forecast CAGR
        if len(selected_stocks) > 0:
            portfolio_cagr = np.mean([s['forecast_cagr'] for s in selected_stocks]) / 100
        else:
            portfolio_cagr = 0

        # Check feasibility
        feasible = portfolio_cagr >= expected_cagr and len(selected_stocks) >= min_stocks

        # Create selection rationale
        selection_rationale = {
            "total_universe": len(df),
            "after_quality_filters": len(df),
            "sectors_available": len(sectors),
            "stocks_selected": len(selected_stocks),
            "selection_method": "PEG-based stock selection for maximum CAGR optimization",
            "selection_criteria": [
                "Round 1: Lowest PEG ratio per sector (PE / Avg_Historical_CAGR)",
                f"Round 2: All remaining stocks with PEG < {peg_threshold}"
            ],
            "quality_filters": [
                "PE Ratio > 0 (valid valuation)",
                "Average CAGR > 0 (positive performance - no negative CAGR stocks)",
                "Valid PEG ratio calculation"
            ],
            "diversification_approach": f"Sector diversification through Round 1 + PEG-filtered growth stocks in Round 2",
            "sector_breakdown": sector_selections,
            "achieved_cagr": f"{portfolio_cagr*100:.1f}%",
            "feasible": feasible,
            "fallback_used": False
        }

        if not feasible:
            selection_rationale["feasibility_note"] = f"Target {expected_cagr*100:.1f}% CAGR not achieved with sector diversification approach. Best achievable: {portfolio_cagr*100:.1f}%"

        # Convert back to Stock objects
        selected_stock_objects = [s['stock'] for s in selected_stocks]

        logger.info(f"Stock selection complete: {len(selected_stock_objects)} stocks, {portfolio_cagr:.1%} CAGR")

        return selected_stock_objects, feasible, portfolio_cagr, selection_rationale

    def optimize_portfolio(
        self,
        selected_stocks: List[Stock],
        monthly_investment: float,
        horizon_months: int
    ) -> List[Dict[str, Any]]:
        """
        Modern Portfolio Theory optimization

        Args:
            selected_stocks: List of selected Stock objects
            monthly_investment: Monthly investment amount
            horizon_months: Investment horizon in months

        Returns:
            List of portfolio allocations with weights
        """
        logger.info(f"Starting portfolio optimization for {len(selected_stocks)} stocks")

        forecast_col = self.get_forecast_column(horizon_months)

        # Extract returns and create risk matrix
        returns = []
        risks = []
        stock_data = []

        for stock in selected_stocks:
            # For now, we'll use a simplified approach since we don't have historical volatility
            # In the original code, it used PE ratio as risk proxy
            returns.append(stock.avg_historical_cagr or 20.0)  # Use historical CAGR as return proxy
            risks.append(stock.pe_ratio / 100 if stock.pe_ratio else 0.25)  # PE ratio as risk proxy

            stock_data.append({
                'stock': stock,
                'ticker': stock.ticker,
                'sector': stock.sector,
                'current_price': stock.current_price,
                'pe_ratio': stock.pe_ratio,
                'pb_ratio': stock.pb_ratio,
                'expected_return': stock.avg_historical_cagr or 20.0
            })

        returns = np.array(returns)
        risks = np.array(risks)
        cov_matrix = np.diag(risks ** 2)

        # Objective function: maximize Sharpe ratio (return/risk)
        def objective(weights):
            port_return = np.dot(weights, returns)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -port_return / port_vol  # Negative for minimization

        n = len(returns)
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = [(0, 1)] * n
        init_guess = np.ones(n) / n

        # Run optimization
        try:
            result = minimize(objective, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)

            if result.success:
                weights = result.x
            else:
                logger.warning("Portfolio optimization failed, using equal weights")
                weights = np.ones(n) / n
        except Exception as e:
            logger.error(f"Portfolio optimization error: {e}")
            weights = np.ones(n) / n

        # Create optimized portfolio allocations
        portfolio_allocations = []
        for i, stock_info in enumerate(stock_data):
            allocation = {
                **stock_info,
                'weight': weights[i],
                'monthly_allocation': weights[i] * monthly_investment
            }
            portfolio_allocations.append(allocation)

        logger.info("Portfolio optimization complete")
        return portfolio_allocations

    def compute_projection(
        self,
        monthly_investment: float,
        horizon_months: int,
        horizon_cagr: float
    ) -> Tuple[float, float, float]:
        """
        Compute SIP projections

        Args:
            monthly_investment: Monthly investment amount
            horizon_months: Investment horizon in months
            horizon_cagr: Achieved CAGR (decimal format)

        Returns:
            Tuple of (total_investment, future_value, gain)
        """
        monthly_cagr = horizon_cagr / 12
        total_investment = monthly_investment * horizon_months

        if monthly_cagr > 0:
            future_value = monthly_investment * (((1 + monthly_cagr) ** horizon_months - 1) / monthly_cagr)
        else:
            future_value = total_investment

        gain = future_value - total_investment

        return round(total_investment), round(future_value), round(gain)

    def calculate_financial_projections(
        self,
        monthly_investment: float,
        horizon_months: int,
        achieved_cagr: float
    ) -> Dict[str, Any]:
        """
        Calculate detailed financial projections for visualization

        Args:
            monthly_investment: Monthly investment amount
            horizon_months: Investment horizon in months
            achieved_cagr: Achieved CAGR (decimal format)

        Returns:
            Dictionary with projection data
        """
        months = list(range(1, horizon_months + 1))
        monthly_cagr = achieved_cagr / 12

        # Calculate month-by-month projections
        cumulative_invested = [monthly_investment * month for month in months]
        projected_values = []

        for month in months:
            if monthly_cagr > 0:
                fv = monthly_investment * (((1 + monthly_cagr) ** month - 1) / monthly_cagr)
            else:
                fv = monthly_investment * month
            projected_values.append(round(fv))

        monthly_gains = [projected_values[i] - cumulative_invested[i] for i in range(len(months))]

        # Calculate key metrics
        final_value = projected_values[-1]
        total_investment = cumulative_invested[-1]
        total_gain = final_value - total_investment

        return {
            'projected_values': projected_values,
            'cumulative_investment': cumulative_invested,
            'monthly_gains': monthly_gains,
            'total_investment': total_investment,
            'final_value': final_value,
            'total_gain': total_gain,
            'money_multiplier': final_value / total_investment,
            'monthly_avg_gain': total_gain / horizon_months,
            'total_return_percentage': (total_gain / total_investment) * 100
        }

    def calculate_whole_share_allocation(
        self,
        portfolio_allocations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate whole share allocation based on optimal weights

        Args:
            portfolio_allocations: List of portfolio allocations

        Returns:
            List of whole share allocations
        """
        whole_share_allocations = []
        total_share_cost = 0

        for allocation in portfolio_allocations:
            current_price = allocation['current_price']
            target_allocation = allocation['monthly_allocation']

            # Calculate ideal number of shares (fractional)
            ideal_shares = target_allocation / current_price

            # Round to nearest whole number, but ensure minimum 1 share
            whole_shares = max(1, round(ideal_shares))

            share_cost = whole_shares * current_price
            total_share_cost += share_cost

            whole_share_allocations.append({
                'ticker': allocation['ticker'],
                'current_price': current_price,
                'weight': allocation['weight'],
                'target_shares': ideal_shares,
                'whole_shares': whole_shares,
                'share_cost': share_cost
            })

        # Calculate actual weights based on share costs
        for allocation in whole_share_allocations:
            allocation['actual_weight'] = allocation['share_cost'] / total_share_cost
            allocation['total_monthly_investment'] = total_share_cost

        return whole_share_allocations

    async def run_complete_analysis(
        self,
        monthly_investment: float,
        horizon_months: int,
        expected_cagr: float,
        client_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete Vriddhi investment analysis

        Args:
            monthly_investment: Monthly investment amount
            horizon_months: Investment horizon in months
            expected_cagr: Expected CAGR (decimal format)
            client_id: Optional client identifier

        Returns:
            Complete analysis results
        """
        logger.info(f"Starting complete analysis: investment={monthly_investment}, horizon={horizon_months}, cagr={expected_cagr:.1%}")

        # Step 1: Stock Selection
        selected_stocks, feasible, achieved_cagr, selection_rationale = await self.advanced_stock_selector(
            expected_cagr, horizon_months
        )

        # Step 2: Portfolio Optimization
        portfolio_allocations = self.optimize_portfolio(
            selected_stocks, monthly_investment, horizon_months
        )

        # Step 3: Financial Projections
        financial_projections = self.calculate_financial_projections(
            monthly_investment, horizon_months, achieved_cagr
        )

        # Step 4: Whole Share Allocation
        whole_share_allocations = self.calculate_whole_share_allocation(portfolio_allocations)

        # Step 5: Calculate diversification metrics
        sector_allocation = defaultdict(float)
        style_allocation = defaultdict(float)
        risk_allocation = defaultdict(float)

        for allocation in portfolio_allocations:
            stock = allocation['stock']
            weight = allocation['weight']

            sector_allocation[stock.sector] += weight
            if stock.investment_style:
                style_allocation[stock.investment_style] += weight
            if stock.risk_level:
                risk_allocation[stock.risk_level] += weight

        # Create summary
        investment_summary = {
            'feasible': feasible,
            'horizon_years': horizon_months / 12,
            'horizon_months': horizon_months,
            'expected_cagr': expected_cagr * 100,
            'achieved_cagr': achieved_cagr * 100,
            'total_investment': financial_projections['total_investment'],
            'final_value': financial_projections['final_value'],
            'total_gain': financial_projections['total_gain'],
            'money_multiplier': financial_projections['money_multiplier'],
            'monthly_avg_gain': financial_projections['monthly_avg_gain'],
            'total_return_percentage': financial_projections['total_return_percentage'],
            'inflation_beat_margin': (achieved_cagr * 100) - 6  # Assuming 6% inflation
        }

        results = {
            'portfolio_allocations': portfolio_allocations,
            'whole_share_allocations': whole_share_allocations,
            'investment_summary': investment_summary,
            'financial_projection': financial_projections,
            'selection_rationale': selection_rationale,
            'sector_allocation': dict(sector_allocation),
            'style_allocation': dict(style_allocation) if style_allocation else None,
            'risk_allocation': dict(risk_allocation) if risk_allocation else None,
            'analysis_date': datetime.now(),
            'model_version': 'v1.0'
        }

        logger.info("Complete analysis finished successfully")
        return results