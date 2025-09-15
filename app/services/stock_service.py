"""
Stock data service for managing stock information and forecasts
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from app.models.stock import Stock, StockForecast
from app.schemas.stock import (
    StockFilterRequest,
    StockDetail,
    StockListResponse,
    SectorSummary,
    MarketSummary,
    InvestmentStyle,
    RiskLevel,
    TrendDirection
)
import logging

logger = logging.getLogger("vriddhi")

class StockService:
    """
    Service class for stock-related operations
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stock_by_ticker(self, ticker: str) -> Optional[Stock]:
        """
        Get stock by ticker symbol
        """
        query = select(Stock).where(Stock.ticker == ticker)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_stocks_with_filters(
        self,
        filters: StockFilterRequest
    ) -> StockListResponse:
        """
        Get stocks with filtering and pagination
        """
        query = select(Stock).where(Stock.is_active == True)

        # Apply filters
        conditions = []

        if filters.sectors:
            conditions.append(Stock.sector.in_(filters.sectors))

        if filters.min_cagr is not None:
            conditions.append(Stock.avg_historical_cagr >= filters.min_cagr)

        if filters.max_cagr is not None:
            conditions.append(Stock.avg_historical_cagr <= filters.max_cagr)

        if filters.min_pe is not None:
            conditions.append(Stock.pe_ratio >= filters.min_pe)

        if filters.max_pe is not None:
            conditions.append(Stock.pe_ratio <= filters.max_pe)

        if filters.min_pb is not None:
            conditions.append(Stock.pb_ratio >= filters.min_pb)

        if filters.max_pb is not None:
            conditions.append(Stock.pb_ratio <= filters.max_pb)

        if filters.investment_styles:
            style_conditions = [Stock.investment_style == style.value for style in filters.investment_styles]
            conditions.append(or_(*style_conditions))

        if filters.risk_levels:
            risk_conditions = [Stock.risk_level == risk.value for risk in filters.risk_levels]
            conditions.append(or_(*risk_conditions))

        if filters.trend_direction:
            conditions.append(Stock.trend_direction == filters.trend_direction.value)

        if filters.min_momentum_score is not None:
            conditions.append(Stock.momentum_score >= filters.min_momentum_score)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await self.db.execute(count_query)
        total_count = total_count_result.scalar()

        # Apply ordering, limit and offset
        query = query.order_by(Stock.overall_rank.asc().nullslast(), Stock.ticker.asc())
        query = query.offset(filters.offset).limit(filters.limit)

        # Execute query
        result = await self.db.execute(query)
        stocks = result.scalars().all()

        return StockListResponse(
            stocks=[StockDetail.from_orm(stock) for stock in stocks],
            total_count=total_count,
            offset=filters.offset,
            limit=filters.limit,
            has_more=(filters.offset + len(stocks)) < total_count
        )

    async def get_stock_with_forecast(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get stock with its latest forecast
        """
        # Get stock
        stock_query = select(Stock).where(
            and_(Stock.ticker == ticker, Stock.is_active == True)
        )
        stock_result = await self.db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()

        if not stock:
            return None

        # Get latest forecast
        forecast_query = select(StockForecast).where(
            StockForecast.ticker == ticker
        ).order_by(desc(StockForecast.forecast_date)).limit(1)

        forecast_result = await self.db.execute(forecast_query)
        forecast = forecast_result.scalar_one_or_none()

        return {
            'stock': StockDetail.from_orm(stock),
            'forecast': forecast
        }

    async def get_sector_summaries(self) -> List[SectorSummary]:
        """
        Get sector-wise summary statistics
        """
        query = select(
            Stock.sector,
            func.count(Stock.id).label('stock_count'),
            func.avg(Stock.avg_historical_cagr).label('avg_cagr'),
            func.avg(Stock.pe_ratio).label('avg_pe_ratio'),
            func.avg(Stock.pb_ratio).label('avg_pb_ratio')
        ).where(
            Stock.is_active == True
        ).group_by(Stock.sector)

        result = await self.db.execute(query)
        sector_data = result.all()

        summaries = []
        for row in sector_data:
            # Get top performing stock in sector
            top_stock_query = select(Stock.ticker).where(
                and_(
                    Stock.sector == row.sector,
                    Stock.is_active == True
                )
            ).order_by(Stock.overall_rank.asc().nullslast()).limit(1)

            top_stock_result = await self.db.execute(top_stock_query)
            top_stock = top_stock_result.scalar()

            summary = SectorSummary(
                sector=row.sector,
                stock_count=row.stock_count,
                avg_cagr=round(row.avg_cagr or 0, 2),
                avg_pe_ratio=round(row.avg_pe_ratio or 0, 2),
                avg_pb_ratio=round(row.avg_pb_ratio or 0, 2),
                top_performing_stock=top_stock or "N/A"
            )
            summaries.append(summary)

        return sorted(summaries, key=lambda x: x.avg_cagr, reverse=True)

    async def get_market_summary(self) -> MarketSummary:
        """
        Get overall market summary
        """
        # Basic counts
        total_stocks_query = select(func.count(Stock.id))
        total_result = await self.db.execute(total_stocks_query)
        total_stocks = total_result.scalar()

        active_stocks_query = select(func.count(Stock.id)).where(Stock.is_active == True)
        active_result = await self.db.execute(active_stocks_query)
        active_stocks = active_result.scalar()

        # Market averages
        market_stats_query = select(
            func.avg(Stock.avg_historical_cagr).label('avg_cagr'),
            func.avg(Stock.pe_ratio).label('avg_pe'),
            func.avg(Stock.pb_ratio).label('avg_pb')
        ).where(Stock.is_active == True)

        stats_result = await self.db.execute(market_stats_query)
        stats = stats_result.first()

        # Unique sectors
        sectors_query = select(Stock.sector).where(Stock.is_active == True).distinct()
        sectors_result = await self.db.execute(sectors_query)
        sectors = [row[0] for row in sectors_result.all()]

        # Get sector summaries
        sector_summaries = await self.get_sector_summaries()

        # Last updated (use the most recent stock update)
        last_updated_query = select(func.max(Stock.updated_at))
        last_updated_result = await self.db.execute(last_updated_query)
        last_updated = last_updated_result.scalar()

        return MarketSummary(
            total_stocks=total_stocks,
            active_stocks=active_stocks,
            sectors=sorted(sectors),
            avg_market_cagr=round(stats.avg_cagr or 0, 2),
            market_pe_ratio=round(stats.avg_pe or 0, 2),
            market_pb_ratio=round(stats.avg_pb or 0, 2),
            sector_summaries=sector_summaries,
            last_updated=last_updated
        )

    async def get_top_performing_stocks(
        self,
        limit: int = 10,
        sector: Optional[str] = None
    ) -> List[StockDetail]:
        """
        Get top performing stocks by CAGR
        """
        query = select(Stock).where(
            and_(
                Stock.is_active == True,
                Stock.avg_historical_cagr.isnot(None)
            )
        )

        if sector:
            query = query.where(Stock.sector == sector)

        query = query.order_by(desc(Stock.avg_historical_cagr)).limit(limit)

        result = await self.db.execute(query)
        stocks = result.scalars().all()

        return [StockDetail.from_orm(stock) for stock in stocks]

    async def search_stocks(self, search_term: str, limit: int = 20) -> List[StockDetail]:
        """
        Search stocks by ticker or company name
        """
        search_pattern = f"%{search_term}%"

        query = select(Stock).where(
            and_(
                Stock.is_active == True,
                or_(
                    Stock.ticker.ilike(search_pattern),
                    Stock.company_name.ilike(search_pattern)
                )
            )
        ).order_by(Stock.overall_rank.asc().nullslast()).limit(limit)

        result = await self.db.execute(query)
        stocks = result.scalars().all()

        return [StockDetail.from_orm(stock) for stock in stocks]

    async def get_stocks_by_investment_style(
        self,
        style: InvestmentStyle,
        limit: int = 50
    ) -> List[StockDetail]:
        """
        Get stocks by investment style
        """
        query = select(Stock).where(
            and_(
                Stock.is_active == True,
                Stock.investment_style == style.value
            )
        ).order_by(Stock.overall_rank.asc().nullslast()).limit(limit)

        result = await self.db.execute(query)
        stocks = result.scalars().all()

        return [StockDetail.from_orm(stock) for stock in stocks]

    async def get_stocks_by_risk_level(
        self,
        risk_level: RiskLevel,
        limit: int = 50
    ) -> List[StockDetail]:
        """
        Get stocks by risk level
        """
        query = select(Stock).where(
            and_(
                Stock.is_active == True,
                Stock.risk_level == risk_level.value
            )
        ).order_by(Stock.overall_rank.asc().nullslast()).limit(limit)

        result = await self.db.execute(query)
        stocks = result.scalars().all()

        return [StockDetail.from_orm(stock) for stock in stocks]