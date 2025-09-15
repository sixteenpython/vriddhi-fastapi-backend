"""
Database session management using SQLAlchemy async
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
import logging

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.ENVIRONMENT == "development",
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Create base for models
Base = declarative_base()
metadata = MetaData()

# Dependency to get DB session
async def get_db() -> AsyncSession:
    """
    Dependency function to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# Function to create tables
async def create_tables():
    """
    Create all database tables
    """
    logger = logging.getLogger("vriddhi")
    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they're registered
            from app.models.stock import Stock, StockForecast
            from app.models.portfolio import Portfolio, PortfolioStock
            from app.models.analysis import InvestmentAnalysis

            await conn.run_sync(Base.metadata.create_all)
            logger.info("All database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise