"""
Ultra-minimal FastAPI app for debugging Railway deployment
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Minimal Test")

# Add CORS middleware
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

@app.get("/")
def root():
    return {"status": "ok", "message": "Minimal app working"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Investment endpoint
@app.post("/api/v1/investment/plan")
async def investment_plan(request: dict = None):
    """Simple investment planning"""
    if not request:
        request = {}

    monthly_investment = request.get("monthly_investment", 50000)
    investment_horizon_months = request.get("investment_horizon_months", 12)

    # Simple mock data
    portfolio = [
        {"ticker": "RELIANCE", "allocation": 0.25, "sector": "Energy", "amount": monthly_investment * 0.25},
        {"ticker": "TCS", "allocation": 0.25, "sector": "IT", "amount": monthly_investment * 0.25},
        {"ticker": "HDFC", "allocation": 0.25, "sector": "Banking", "amount": monthly_investment * 0.25},
        {"ticker": "INFY", "allocation": 0.25, "sector": "IT", "amount": monthly_investment * 0.25}
    ]

    total_investment = monthly_investment * investment_horizon_months
    final_amount = total_investment * 1.15  # 15% growth
    gains = final_amount - total_investment

    return {
        "investment_summary": {
            "monthly_investment": monthly_investment,
            "investment_horizon_months": investment_horizon_months,
            "total_investment": total_investment,
            "final_amount": final_amount,
            "total_gains": gains,
            "cagr": 15.0
        },
        "portfolio_allocation": portfolio,
        "selection_rationale": {
            "algorithm": "Simple balanced allocation",
            "sectors_selected": ["Energy", "IT", "Banking"],
            "diversification_score": 80,
            "risk_level": "Moderate"
        },
        "projections": {
            "timeline": list(range(1, investment_horizon_months + 1)),
            "portfolio_values": [monthly_investment * i * 1.15 for i in range(1, investment_horizon_months + 1)],
            "invested_amounts": [monthly_investment * i for i in range(1, investment_horizon_months + 1)]
        }
    }