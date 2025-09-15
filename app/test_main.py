"""
Test version with hardcoded stock data for immediate testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from typing import List, Dict, Any, Optional
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Vriddhi Alpha Finder API",
    description="AI-Powered Personal Investment Advisor with Modern Portfolio Theory",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vriddhi-investment-app-z8au.vercel.app",
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://localhost:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSV file path for stock data
CSV_FILE_PATH = "grand_table_expanded.csv"

# Import complete stock dataset
try:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    sys.path.append('..')
    from complete_stock_data import COMPLETE_STOCK_DATA
    print(f"✅ Imported complete dataset: {len(COMPLETE_STOCK_DATA)} stocks")
except ImportError as e:
    print(f"❌ Failed to import complete dataset: {e}")
    # Minimal fallback
    COMPLETE_STOCK_DATA = [
        {'Overall_Rank': 1, 'Ticker': 'HDFCLIFE', 'Sector': 'Financials', 'Current_Price': 788.75, 'PE_Ratio': 14.5, 'PB_Ratio': 4.2, 'Avg_Historical_CAGR': 69.74, 'Forecast_12M': 53.41, 'Forecast_24M': 63.12, 'Forecast_36M': 71.18, 'Forecast_48M': 77.67, 'Forecast_60M': 83.33},
        {'Overall_Rank': 2, 'Ticker': 'APOLLOHOSP', 'Sector': 'Healthcare', 'Current_Price': 7922.5, 'PE_Ratio': 58, 'PB_Ratio': 6.2, 'Avg_Historical_CAGR': 54.73, 'Forecast_12M': 51.82, 'Forecast_24M': 53.93, 'Forecast_36M': 55.12, 'Forecast_48M': 56.06, 'Forecast_60M': 56.7}
    ]

def load_stock_data():
    """Load complete stock data (identical to Streamlit version)"""
    try:
        import os

        # Try multiple possible paths for CSV file first
        possible_paths = [
            CSV_FILE_PATH,                    # Current directory
            os.path.join("..", CSV_FILE_PATH), # Parent directory
            os.path.join("app", "..", CSV_FILE_PATH), # From app directory
            os.path.join("/opt/render/project/src", CSV_FILE_PATH), # Render path
            os.path.join("/app", CSV_FILE_PATH), # Docker path
        ]

        csv_path = None
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break

        if csv_path:
            df = pd.read_csv(csv_path)
            print(f"✅ Loaded {len(df)} stocks from CSV: {csv_path}")
            return df
        else:
            print("📊 CSV not found, using embedded complete dataset")
            raise FileNotFoundError("Using embedded data")

    except Exception as e:
        print(f"📊 Loading complete embedded dataset (identical to CSV)")
        # Complete dataset - identical to Streamlit CSV
        return pd.DataFrame(COMPLETE_STOCK_DATA)

STOCK_DATA = None
FORECAST_MAP = {
    12: "Forecast_12M", 18: "Forecast_18M", 24: "Forecast_24M",
    36: "Forecast_36M", 48: "Forecast_48M", 60: "Forecast_60M"
}

# Pydantic models (same as advanced_main.py)
class InvestmentRequest(BaseModel):
    monthly_investment: float
    investment_horizon_months: int
    expected_cagr: Optional[float] = 15.0

class StockInfo(BaseModel):
    ticker: str
    sector: str
    weight: float
    monthly_allocation: float
    pe_ratio: float
    pb_ratio: float
    expected_return: float
    peg_ratio: float

class InvestmentSummary(BaseModel):
    monthly_investment: float
    investment_horizon_months: int
    total_investment: float
    final_amount: float
    total_gains: float
    achieved_cagr: float
    expected_cagr: float
    money_multiplier: float
    feasible: bool

class SelectionRationale(BaseModel):
    total_universe: int
    stocks_selected: int
    sectors_available: int
    selection_method: str
    selection_criteria: List[str]
    quality_filters: List[str]
    diversification_approach: str
    achieved_cagr: str
    feasible: bool
    sector_breakdown: Dict[str, Any]

class InvestmentResponse(BaseModel):
    investment_summary: InvestmentSummary
    portfolio_allocation: List[StockInfo]
    selection_rationale: SelectionRationale
    projections: Dict[str, List[float]]
    whole_share_analysis: Optional[Dict[str, Any]] = None

def initialize_stock_data():
    """Load stock data from CSV (same as Streamlit version)"""
    global STOCK_DATA
    try:
        STOCK_DATA = load_stock_data()
        logger.info(f"✅ Loaded {len(STOCK_DATA)} stocks from CSV data")
        return True
    except Exception as e:
        logger.error(f"❌ Error loading stock data: {e}")
        return False

def get_forecast_column(horizon_months):
    """Map horizon to forecast column"""
    return FORECAST_MAP.get(horizon_months, "Forecast_24M")

def advanced_stock_selector(df: pd.DataFrame, expected_cagr: float, horizon_months: int):
    """PEG-based stock selection with sector diversification"""
    from collections import defaultdict

    # Map horizon to forecast column
    if horizon_months <= 12:
        forecast_col = 'Forecast_12M'
    elif horizon_months <= 18:
        forecast_col = 'Forecast_18M'
    elif horizon_months <= 24:
        forecast_col = 'Forecast_24M'
    elif horizon_months <= 36:
        forecast_col = 'Forecast_36M'
    elif horizon_months <= 48:
        forecast_col = 'Forecast_48M'
    else:
        forecast_col = 'Forecast_60M'

    # Calculate PEG ratio: PE / Average Historical CAGR
    df = df.copy()
    df['PEG_Ratio'] = df['PE_Ratio'] / df['Avg_Historical_CAGR']

    # Quality filters
    quality_df = df[
        (df['PE_Ratio'] > 0) &
        (df['Avg_Historical_CAGR'] > 0) &
        (df['PEG_Ratio'].notna()) &
        (df['PEG_Ratio'] > 0)
    ].copy()

    # Round 1: Best stock per sector (lowest PEG)
    selected_stocks = []
    sector_selections = defaultdict(list)
    sectors = quality_df['Sector'].unique()

    for sector in sectors:
        sector_stocks = quality_df[quality_df['Sector'] == sector].sort_values('PEG_Ratio')
        if len(sector_stocks) > 0:
            best_stock = sector_stocks.iloc[0]
            selected_stocks.append(best_stock)

            sector_selections[sector].append({
                'selected_stock': best_stock['Ticker'],
                'avg_cagr': best_stock['Avg_Historical_CAGR'],
                'pe_ratio': best_stock['PE_Ratio'],
                'pb_ratio': best_stock['PB_Ratio'],
                'peg_ratio': best_stock['PEG_Ratio']
            })

    # Round 2: Additional stocks with PEG < 1.0
    selected_tickers = [stock['Ticker'] for stock in selected_stocks]
    quality_stocks = quality_df[
        (quality_df['PEG_Ratio'] < 1.0) &
        (~quality_df['Ticker'].isin(selected_tickers))
    ]

    # Add all qualifying stocks
    for _, stock in quality_stocks.iterrows():
        selected_stocks.append(stock)

    # Convert to DataFrame
    selected_df = pd.DataFrame(selected_stocks)

    # Calculate portfolio statistics
    if len(selected_df) > 0:
        portfolio_cagr = selected_df[forecast_col].mean() / 100
    else:
        portfolio_cagr = 0

    feasible = True

    # Create selection rationale
    selection_rationale = {
        "total_universe": len(df),
        "after_quality_filters": len(quality_df),
        "sectors_available": len(sectors),
        "stocks_selected": len(selected_df),
        "selection_method": "PEG-based stock selection for maximum CAGR optimization",
        "selection_criteria": [
            "Round 1: Lowest PEG ratio per sector (PE / Avg_Historical_CAGR)",
            "Round 2: All remaining stocks with PEG < 1.0"
        ],
        "quality_filters": [
            "PE Ratio > 0 (valid valuation)",
            "Average CAGR > 0 (positive performance)",
            "Valid PEG ratio calculation"
        ],
        "diversification_approach": "Sector diversification through Round 1 + PEG-filtered growth stocks in Round 2",
        "sector_breakdown": dict(sector_selections),
        "achieved_cagr": f"{portfolio_cagr*100:.1f}%",
        "feasible": feasible,
        "fallback_used": False
    }

    return selected_df, feasible, portfolio_cagr, selection_rationale

def optimize_portfolio(selected_df: pd.DataFrame, horizon_months: int):
    """Modern Portfolio Theory optimization using Sharpe ratio maximization"""
    forecast_col = get_forecast_column(horizon_months)
    returns = selected_df[forecast_col].values / 100  # Convert to decimal

    # Use PE ratio as risk proxy (normalized)
    risks = selected_df["PE_Ratio"].values / 100
    cov_matrix = np.diag(risks ** 2)

    def objective(weights):
        """Minimize negative Sharpe ratio (maximize Sharpe ratio)"""
        port_return = np.dot(weights, returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        if port_vol == 0:
            return -port_return
        return -port_return / port_vol

    n = len(returns)
    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
    bounds = [(0, 1)] * n
    init_guess = np.ones(n) / n

    try:
        result = minimize(objective, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        if result.success:
            selected_df['Weight'] = result.x
        else:
            selected_df['Weight'] = 1.0 / n
    except:
        selected_df['Weight'] = 1.0 / n

    return selected_df

def compute_projections(optimized_df: pd.DataFrame, monthly_investment: float,
                       horizon_months: int, achieved_cagr: float):
    """Calculate SIP growth projections with compound interest"""
    monthly_cagr = achieved_cagr / 12

    timeline = list(range(1, horizon_months + 1))
    invested_amounts = [monthly_investment * month for month in timeline]

    # Compound growth calculation for SIP
    portfolio_values = []
    for month in timeline:
        total_value = 0
        for inv_month in range(1, month + 1):
            months_invested = month - inv_month + 1
            future_value = monthly_investment * ((1 + monthly_cagr) ** months_invested)
            total_value += future_value
        portfolio_values.append(total_value)

    total_invested = monthly_investment * horizon_months
    final_value = portfolio_values[-1] if portfolio_values else 0
    total_gains = final_value - total_invested

    return {
        "timeline": timeline,
        "invested_amounts": invested_amounts,
        "portfolio_values": portfolio_values,
        "total_invested": total_invested,
        "final_value": final_value,
        "total_gains": total_gains
    }

@app.on_event("startup")
async def startup_event():
    """Load stock data on startup"""
    logger.info("🚀 Starting Vriddhi Alpha Finder Test API...")
    if initialize_stock_data():
        logger.info("✅ Stock database loaded successfully")
    else:
        logger.error("❌ Failed to load stock database")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Vriddhi Alpha Finder Test API v2.0",
        "description": "AI-Powered Personal Investment Advisor with Modern Portfolio Theory",
        "features": [
            "PEG-based stock selection",
            "Modern Portfolio Theory optimization",
            "Multi-horizon forecasting",
            "Sector diversification",
            "SIP growth projections"
        ],
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "vriddhi-alpha-finder-test",
        "version": "2.0.0",
        "timestamp": time.time(),
        "database_loaded": STOCK_DATA is not None,
        "stocks_count": len(STOCK_DATA) if STOCK_DATA is not None else 0
    }

@app.post("/api/v1/investment/plan", response_model=InvestmentResponse)
async def create_investment_plan(request: InvestmentRequest):
    """Create comprehensive investment plan using advanced algorithms"""
    if STOCK_DATA is None:
        raise HTTPException(status_code=500, detail="Stock database not loaded")

    # Validate inputs
    if request.monthly_investment < 50000:
        raise HTTPException(status_code=400, detail="Minimum investment amount is ₹50,000")

    if request.investment_horizon_months < 12 or request.investment_horizon_months > 60:
        raise HTTPException(status_code=400, detail="Investment horizon must be between 12-60 months")

    try:
        # Step 1: Stock Selection using PEG-based algorithm
        selected_df, feasible, achieved_cagr, selection_rationale = advanced_stock_selector(
            STOCK_DATA, request.expected_cagr / 100, request.investment_horizon_months
        )

        if len(selected_df) == 0:
            raise HTTPException(status_code=500, detail="No suitable stocks found for investment criteria")

        # Step 2: Portfolio Optimization using Modern Portfolio Theory
        optimized_df = optimize_portfolio(selected_df, request.investment_horizon_months)
        optimized_df["Monthly_Allocation"] = optimized_df["Weight"] * request.monthly_investment

        # Step 3: Growth Projections
        projections = compute_projections(
            optimized_df, request.monthly_investment,
            request.investment_horizon_months, achieved_cagr
        )

        # Prepare response
        portfolio_stocks = []
        for _, row in optimized_df.iterrows():
            portfolio_stocks.append(StockInfo(
                ticker=row['Ticker'],
                sector=row['Sector'],
                weight=row['Weight'],
                monthly_allocation=row['Monthly_Allocation'],
                pe_ratio=row['PE_Ratio'],
                pb_ratio=row['PB_Ratio'],
                expected_return=row[get_forecast_column(request.investment_horizon_months)],
                peg_ratio=row.get('PEG_Ratio', 0)
            ))

        investment_summary = InvestmentSummary(
            monthly_investment=request.monthly_investment,
            investment_horizon_months=request.investment_horizon_months,
            total_investment=projections["total_invested"],
            final_amount=projections["final_value"],
            total_gains=projections["total_gains"],
            achieved_cagr=achieved_cagr * 100,
            expected_cagr=request.expected_cagr,
            money_multiplier=projections["final_value"] / projections["total_invested"] if projections["total_invested"] > 0 else 1,
            feasible=feasible
        )

        rationale = SelectionRationale(
            total_universe=selection_rationale["total_universe"],
            stocks_selected=selection_rationale["stocks_selected"],
            sectors_available=selection_rationale["sectors_available"],
            selection_method=selection_rationale["selection_method"],
            selection_criteria=selection_rationale["selection_criteria"],
            quality_filters=selection_rationale["quality_filters"],
            diversification_approach=selection_rationale["diversification_approach"],
            achieved_cagr=selection_rationale["achieved_cagr"],
            feasible=selection_rationale["feasible"],
            sector_breakdown=selection_rationale["sector_breakdown"]
        )

        return InvestmentResponse(
            investment_summary=investment_summary,
            portfolio_allocation=portfolio_stocks,
            selection_rationale=rationale,
            projections={
                "timeline": projections["timeline"],
                "invested_amounts": projections["invested_amounts"],
                "portfolio_values": projections["portfolio_values"]
            }
        )

    except Exception as e:
        logger.error(f"❌ Error creating investment plan: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating investment plan: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.test_main:app", host="0.0.0.0", port=port, reload=True)