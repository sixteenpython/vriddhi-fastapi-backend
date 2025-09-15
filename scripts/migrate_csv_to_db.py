"""
Database migration script to load CSV data into PostgreSQL

This script migrates the grand_table_expanded.csv data into the PostgreSQL database,
populating both the stocks and stock_forecasts tables with all the Vriddhi data.
"""

import asyncio
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import AsyncSessionLocal, create_tables
from app.models.stock import Stock, StockForecast
from app.core.config import settings
from app.core.logging_config import setup_logging

# Setup logging
logger = setup_logging()

async def load_csv_data():
    """
    Load and validate CSV data
    """
    # Try multiple possible locations for the CSV file
    possible_paths = [
        "data/grand_table_expanded.csv",
        "grand_table_expanded.csv",
        "../vriddhi-core/grand_table_expanded.csv",
        "../../vriddhi-core/grand_table_expanded.csv"
    ]

    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break

    if not csv_path:
        logger.error(f"CSV file not found in any of these locations: {possible_paths}")
        raise FileNotFoundError("grand_table_expanded.csv not found")

    logger.info(f"Loading CSV data from: {csv_path}")
    df = pd.read_csv(csv_path)

    logger.info(f"Loaded {len(df)} stocks from CSV")
    logger.info(f"Columns: {df.columns.tolist()}")

    return df

def clean_stock_data(df):
    """
    Clean and validate stock data
    """
    logger.info("Cleaning stock data...")

    # Handle missing values and data types
    numeric_columns = [
        'Current_Price', 'Expected_Returns_12M', 'Expected_Returns_24M',
        'Expected_Returns_36M', 'Expected_Returns_48M', 'Expected_Returns_60M',
        'Forecast_12M', 'Forecast_18M', 'Forecast_24M', 'Forecast_36M',
        'Forecast_48M', 'Forecast_60M', 'Avg_Historical_CAGR',
        'Risk_Adjusted_Return', 'PE_Ratio', 'PB_Ratio'
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill missing values with appropriate defaults
    df['Current_Price'] = df['Current_Price'].fillna(100.0)
    df['PE_Ratio'] = df['PE_Ratio'].fillna(20.0)
    df['PB_Ratio'] = df['PB_Ratio'].fillna(3.0)
    df['Avg_Historical_CAGR'] = df['Avg_Historical_CAGR'].fillna(15.0)
    df['Risk_Adjusted_Return'] = df['Risk_Adjusted_Return'].fillna(12.0)

    # Add derived columns for enhanced functionality
    if 'Investment_Style' not in df.columns:
        # Derive investment style based on PE and PB ratios
        def get_investment_style(row):
            pe = row.get('PE_Ratio', 20)
            pb = row.get('PB_Ratio', 3)
            cagr = row.get('Avg_Historical_CAGR', 15)

            if pe < 15 and pb < 2:
                return 'Deep Value'
            elif pe < 20 and pb < 3:
                return 'Value'
            elif cagr > 25:
                return 'Growth'
            else:
                return 'Balanced'

        df['Investment_Style'] = df.apply(get_investment_style, axis=1)

    if 'Risk_Level' not in df.columns:
        # Derive risk level based on PE ratio and volatility proxy
        def get_risk_level(row):
            pe = row.get('PE_Ratio', 20)
            if pe < 15:
                return 'Low'
            elif pe < 30:
                return 'Medium'
            else:
                return 'High'

        df['Risk_Level'] = df.apply(get_risk_level, axis=1)

    if 'Trend_Direction' not in df.columns:
        # Derive trend direction based on forecasts
        def get_trend_direction(row):
            forecast_12m = row.get('Forecast_12M', 15)
            forecast_24m = row.get('Forecast_24M', 15)

            if forecast_24m > forecast_12m * 1.1:
                return 'Improving'
            elif forecast_24m < forecast_12m * 0.9:
                return 'Declining'
            else:
                return 'Stable'

        df['Trend_Direction'] = df.apply(get_trend_direction, axis=1)

    if 'Momentum_Score' not in df.columns:
        # Create momentum score based on CAGR and trend
        def get_momentum_score(row):
            cagr = row.get('Avg_Historical_CAGR', 15)
            trend = row.get('Trend_Direction', 'Stable')

            base_score = min(cagr * 2, 80)  # Cap at 80

            if trend == 'Improving':
                return min(base_score * 1.2, 95)
            elif trend == 'Declining':
                return max(base_score * 0.8, 20)
            else:
                return base_score

        df['Momentum_Score'] = df.apply(get_momentum_score, axis=1)

    if 'Historical_Volatility' not in df.columns:
        # Create volatility proxy based on PE ratio
        df['Historical_Volatility'] = df['PE_Ratio'].apply(lambda x: min(max(x / 10, 1.0), 5.0))

    # Add company names if not present
    if 'Company_Name' not in df.columns:
        df['Company_Name'] = df['Ticker'] + ' Limited'

    logger.info("Data cleaning completed")
    return df

async def migrate_stocks(df):
    """
    Migrate stock data to the database
    """
    logger.info("Starting stock migration...")

    async with AsyncSessionLocal() as session:
        try:
            # Clear existing data
            logger.info("Clearing existing stock data...")
            await session.execute("DELETE FROM stock_forecasts")
            await session.execute("DELETE FROM stocks")
            await session.commit()

            stocks_to_add = []
            forecasts_to_add = []

            for _, row in df.iterrows():
                # Create Stock object
                stock = Stock(
                    ticker=str(row['Ticker']).upper(),
                    company_name=row.get('Company_Name', f"{row['Ticker']} Limited"),
                    sector=str(row.get('Sector', 'Unknown')),
                    overall_rank=int(row.get('Overall_Rank', 999)),
                    current_price=float(row['Current_Price']),
                    pe_ratio=float(row.get('PE_Ratio', 20.0)),
                    pb_ratio=float(row.get('PB_Ratio', 3.0)),
                    avg_historical_cagr=float(row.get('Avg_Historical_CAGR', 15.0)),
                    risk_adjusted_return=float(row.get('Risk_Adjusted_Return', 12.0)),
                    historical_volatility=float(row.get('Historical_Volatility', 2.5)),
                    investment_style=str(row.get('Investment_Style', 'Balanced')),
                    risk_level=str(row.get('Risk_Level', 'Medium')),
                    trend_direction=str(row.get('Trend_Direction', 'Stable')),
                    momentum_score=float(row.get('Momentum_Score', 50.0)),
                    is_active=True
                )
                stocks_to_add.append(stock)

                # Create StockForecast object
                forecast = StockForecast(
                    ticker=str(row['Ticker']).upper(),
                    expected_returns_6m=row.get('Expected_Returns_6M'),
                    expected_returns_12m=row.get('Expected_Returns_12M'),
                    expected_returns_18m=row.get('Expected_Returns_18M'),
                    expected_returns_24m=row.get('Expected_Returns_24M'),
                    expected_returns_36m=row.get('Expected_Returns_36M'),
                    expected_returns_48m=row.get('Expected_Returns_48M'),
                    expected_returns_60m=row.get('Expected_Returns_60M'),
                    forecast_6m=row.get('Forecast_6M'),
                    forecast_12m=row.get('Forecast_12M'),
                    forecast_18m=row.get('Forecast_18M'),
                    forecast_24m=row.get('Forecast_24M'),
                    forecast_36m=row.get('Forecast_36M'),
                    forecast_48m=row.get('Forecast_48M'),
                    forecast_60m=row.get('Forecast_60M'),
                    model_version="v1.0",
                    confidence_score=0.85
                )
                forecasts_to_add.append(forecast)

            # Bulk insert stocks
            logger.info(f"Inserting {len(stocks_to_add)} stocks...")
            session.add_all(stocks_to_add)
            await session.commit()

            # Update stock_id in forecasts after stocks are committed
            logger.info("Updating forecast stock_ids...")
            stock_id_map = {}
            for stock in stocks_to_add:
                stock_id_map[stock.ticker] = stock.id

            for forecast in forecasts_to_add:
                forecast.stock_id = stock_id_map[forecast.ticker]

            # Bulk insert forecasts
            logger.info(f"Inserting {len(forecasts_to_add)} forecasts...")
            session.add_all(forecasts_to_add)
            await session.commit()

            logger.info("Stock migration completed successfully!")

            # Log summary statistics
            logger.info("Migration Summary:")
            logger.info(f"  - Stocks migrated: {len(stocks_to_add)}")
            logger.info(f"  - Forecasts migrated: {len(forecasts_to_add)}")

            # Sector breakdown
            sectors = df['Sector'].value_counts()
            logger.info("  - Sector breakdown:")
            for sector, count in sectors.head(10).items():
                logger.info(f"    {sector}: {count} stocks")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error during migration: {e}")
            raise

async def verify_migration():
    """
    Verify the migration was successful
    """
    logger.info("Verifying migration...")

    async with AsyncSessionLocal() as session:
        try:
            # Check stock count
            from sqlalchemy import select, func

            stock_count_query = select(func.count(Stock.id))
            stock_result = await session.execute(stock_count_query)
            stock_count = stock_result.scalar()

            forecast_count_query = select(func.count(StockForecast.id))
            forecast_result = await session.execute(forecast_count_query)
            forecast_count = forecast_result.scalar()

            logger.info(f"Verification results:")
            logger.info(f"  - Stocks in database: {stock_count}")
            logger.info(f"  - Forecasts in database: {forecast_count}")

            # Check a few sample stocks
            sample_query = select(Stock).limit(5)
            sample_result = await session.execute(sample_query)
            sample_stocks = sample_result.scalars().all()

            logger.info("Sample stocks:")
            for stock in sample_stocks:
                logger.info(f"  - {stock.ticker} ({stock.sector}): ₹{stock.current_price}, CAGR: {stock.avg_historical_cagr}%")

            return stock_count > 0 and forecast_count > 0

        except Exception as e:
            logger.error(f"Error during verification: {e}")
            return False

async def main():
    """
    Main migration function
    """
    logger.info("Starting CSV to PostgreSQL migration...")

    try:
        # Create database tables
        logger.info("Creating database tables...")
        await create_tables()

        # Load CSV data
        df = await asyncio.to_thread(load_csv_data)

        # Clean data
        df_clean = await asyncio.to_thread(clean_stock_data, df)

        # Migrate to database
        await migrate_stocks(df_clean)

        # Verify migration
        verification_success = await verify_migration()

        if verification_success:
            logger.info("🎉 Migration completed successfully!")
            logger.info("Database is ready for the Vriddhi API")
        else:
            logger.error("❌ Migration verification failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the migration
    asyncio.run(main())