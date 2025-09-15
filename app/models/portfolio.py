"""
Portfolio and investment analysis models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Portfolio(Base):
    """
    Portfolio configuration and results
    """
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)

    # Portfolio parameters
    monthly_investment = Column(Float, nullable=False)
    horizon_months = Column(Integer, nullable=False)
    expected_cagr = Column(Float, nullable=False)

    # Portfolio results
    achieved_cagr = Column(Float, nullable=False)
    total_investment = Column(Float, nullable=False)
    final_value = Column(Float, nullable=False)
    total_gain = Column(Float, nullable=False)
    money_multiplier = Column(Float, nullable=False)

    # Portfolio composition
    num_stocks = Column(Integer, nullable=False)
    is_feasible = Column(Boolean, nullable=False)

    # Selection rationale (stored as JSON)
    selection_rationale = Column(JSON)

    # Portfolio metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    client_id = Column(String(100))  # Optional client identifier

    # Relationships
    stocks = relationship("PortfolioStock", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portfolio(id={self.id}, investment={self.monthly_investment}, horizon={self.horizon_months})>"


class PortfolioStock(Base):
    """
    Individual stock allocations within a portfolio
    """
    __tablename__ = "portfolio_stocks"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)

    # Stock allocation details
    ticker = Column(String(50), nullable=False)  # Denormalized for performance
    weight = Column(Float, nullable=False)  # Portfolio weight (0-1)
    monthly_allocation = Column(Float, nullable=False)  # Monthly investment amount

    # Whole share calculation
    target_shares = Column(Float)  # Ideal fractional shares
    whole_shares = Column(Integer)  # Rounded whole shares
    share_cost = Column(Float)  # Cost of whole shares
    actual_weight = Column(Float)  # Actual weight with whole shares

    # Stock metrics at time of selection
    current_price = Column(Float, nullable=False)
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    peg_ratio = Column(Float)
    expected_cagr = Column(Float)
    sector = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="stocks")
    stock = relationship("Stock", back_populates="portfolio_stocks")

    def __repr__(self):
        return f"<PortfolioStock(ticker='{self.ticker}', weight={self.weight:.2%})>"