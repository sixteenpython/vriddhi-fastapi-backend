"""
Stock data models for the database
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Stock(Base):
    """
    Stock master data model
    """
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(50), unique=True, index=True, nullable=False)
    company_name = Column(String(255))
    sector = Column(String(100), index=True)
    overall_rank = Column(Integer, index=True)

    # Current market data
    current_price = Column(Float, nullable=False)

    # Financial metrics
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    avg_historical_cagr = Column(Float)
    risk_adjusted_return = Column(Float)
    historical_volatility = Column(Float)

    # Investment style and risk
    investment_style = Column(String(50))  # Deep Value, Value, Growth, Balanced
    risk_level = Column(String(20))  # Low, Medium, High
    trend_direction = Column(String(20))  # Improving, Declining, Stable
    momentum_score = Column(Float)

    # Status and metadata
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    forecasts = relationship("StockForecast", back_populates="stock", cascade="all, delete-orphan")
    portfolio_stocks = relationship("PortfolioStock", back_populates="stock")

    # Indexes for better query performance
    __table_args__ = (
        Index('idx_stock_sector_rank', 'sector', 'overall_rank'),
        Index('idx_stock_active_sector', 'is_active', 'sector'),
    )

    def __repr__(self):
        return f"<Stock(ticker='{self.ticker}', sector='{self.sector}', rank={self.overall_rank})>"


class StockForecast(Base):
    """
    Stock forecast data for different time horizons
    """
    __tablename__ = "stock_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, index=True, nullable=False)
    ticker = Column(String(50), index=True, nullable=False)  # Denormalized for performance

    # Expected returns for different horizons
    expected_returns_6m = Column(Float)
    expected_returns_12m = Column(Float)
    expected_returns_18m = Column(Float)
    expected_returns_24m = Column(Float)
    expected_returns_36m = Column(Float)
    expected_returns_48m = Column(Float)
    expected_returns_60m = Column(Float)

    # Forecast CAGR for different horizons (%)
    forecast_6m = Column(Float)
    forecast_12m = Column(Float)
    forecast_18m = Column(Float)
    forecast_24m = Column(Float)
    forecast_36m = Column(Float)
    forecast_48m = Column(Float)
    forecast_60m = Column(Float)

    # Forecast metadata
    forecast_date = Column(DateTime(timezone=True), server_default=func.now())
    model_version = Column(String(50), default="v1.0")
    confidence_score = Column(Float)  # 0-1 confidence in forecast

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    stock = relationship("Stock", back_populates="forecasts")

    # Indexes
    __table_args__ = (
        Index('idx_forecast_ticker_date', 'ticker', 'forecast_date'),
        Index('idx_forecast_stock_date', 'stock_id', 'forecast_date'),
    )

    def get_forecast_for_horizon(self, horizon_months: int) -> float:
        """
        Get forecast CAGR for specific horizon
        """
        forecast_mapping = {
            6: self.forecast_6m,
            12: self.forecast_12m,
            18: self.forecast_18m,
            24: self.forecast_24m,
            36: self.forecast_36m,
            48: self.forecast_48m,
            60: self.forecast_60m
        }

        # Find the closest available horizon
        available_horizons = [h for h in forecast_mapping.keys() if forecast_mapping[h] is not None]
        if not available_horizons:
            return None

        closest_horizon = min(available_horizons, key=lambda x: abs(x - horizon_months))
        return forecast_mapping[closest_horizon]

    def __repr__(self):
        return f"<StockForecast(ticker='{self.ticker}', forecast_date='{self.forecast_date}')>"