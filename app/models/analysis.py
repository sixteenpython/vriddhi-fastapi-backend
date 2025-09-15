"""
Investment analysis and reporting models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class InvestmentAnalysis(Base):
    """
    Comprehensive investment analysis results
    """
    __tablename__ = "investment_analyses"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)

    # Analysis parameters
    monthly_investment = Column(Float, nullable=False)
    horizon_months = Column(Integer, nullable=False)
    analysis_type = Column(String(50), default="comprehensive")  # comprehensive, quick, custom

    # Financial projections
    projected_values = Column(JSON)  # Monthly projected values array
    cumulative_investment = Column(JSON)  # Monthly cumulative investment array
    monthly_gains = Column(JSON)  # Monthly gains array

    # Key metrics
    final_portfolio_value = Column(Float, nullable=False)
    total_investment = Column(Float, nullable=False)
    total_gains = Column(Float, nullable=False)
    achieved_cagr = Column(Float, nullable=False)
    monthly_avg_gain = Column(Float, nullable=False)
    total_return_percentage = Column(Float, nullable=False)
    money_multiplier = Column(Float, nullable=False)

    # Risk metrics
    portfolio_volatility = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    var_95 = Column(Float)  # Value at Risk (95%)

    # Diversification analysis
    sector_allocation = Column(JSON)  # Sector-wise allocation
    style_allocation = Column(JSON)   # Investment style allocation
    risk_allocation = Column(JSON)    # Risk level allocation

    # Comparison metrics
    inflation_beat_margin = Column(Float)  # How much it beats inflation
    fd_beat_margin = Column(Float)         # How much it beats FD returns
    market_beta = Column(Float)            # Portfolio beta vs market

    # Analysis metadata
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())
    model_version = Column(String(50), default="v1.0")
    confidence_score = Column(Float)  # Overall confidence in analysis

    # Performance tracking
    benchmark_comparison = Column(JSON)  # Comparison with benchmarks
    scenario_analysis = Column(JSON)     # Best/worst/likely scenarios

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    portfolio = relationship("Portfolio")

    def get_year_wise_breakdown(self):
        """
        Calculate year-wise investment breakdown
        """
        if not self.projected_values or not self.cumulative_investment:
            return {}

        year_wise = {}
        for year in range(1, (self.horizon_months // 12) + 1):
            month_index = (year * 12) - 1
            if month_index < len(self.projected_values):
                year_wise[year] = {
                    'invested': self.cumulative_investment[month_index],
                    'projected': self.projected_values[month_index],
                    'gain': self.projected_values[month_index] - self.cumulative_investment[month_index]
                }

        return year_wise

    def __repr__(self):
        return f"<InvestmentAnalysis(id={self.id}, portfolio_id={self.portfolio_id}, cagr={self.achieved_cagr:.2%})>"


class AnalysisSnapshot(Base):
    """
    Periodic snapshots of analysis results for tracking performance
    """
    __tablename__ = "analysis_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("investment_analyses.id"))

    # Snapshot data
    snapshot_date = Column(DateTime(timezone=True), server_default=func.now())
    portfolio_value = Column(Float)
    total_invested = Column(Float)
    current_gain = Column(Float)
    current_return_pct = Column(Float)

    # Market conditions at snapshot
    market_conditions = Column(JSON)  # Market indicators at time of snapshot
    external_factors = Column(JSON)   # Economic/political factors

    # Performance vs expectations
    expected_value = Column(Float)    # What was expected at this point
    variance = Column(Float)          # Actual vs expected variance
    performance_notes = Column(Text)   # Analysis notes

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AnalysisSnapshot(portfolio_id={self.portfolio_id}, date={self.snapshot_date})>"