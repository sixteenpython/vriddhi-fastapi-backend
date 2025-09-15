# Vriddhi FastAPI Backend - Deployment Guide

🚀 **Complete deployment guide for the Vriddhi Investment API**

## 🏗️ What You Have

A complete, production-ready FastAPI backend that replicates ALL Vriddhi functionality:

### ✅ Core Features Implemented
- **🎯 PEG-based Stock Selection**: Two-round algorithm with sector diversification
- **📊 Modern Portfolio Theory**: scipy-based optimization
- **💰 SIP Modeling**: Monthly investment projections
- **📈 Multi-horizon Forecasting**: 6M to 60M predictions
- **🏢 Diversification**: Automatic sector and style allocation
- **🔍 Comprehensive Analysis**: Full investment analysis with visualization data

### ✅ Technical Implementation
- **FastAPI**: High-performance async API
- **PostgreSQL**: Production database with proper models
- **Pydantic**: Full request/response validation
- **Error Handling**: Comprehensive error management
- **Health Monitoring**: Built-in health checks and metrics
- **Docker**: Complete containerization
- **Railway**: Ready-to-deploy configuration

## 🚂 Railway Deployment (Recommended)

### Step 1: Prepare for Deployment

```bash
# 1. Navigate to the project directory
cd vriddhi-fastapi-backend

# 2. Install Railway CLI
npm install -g @railway/cli

# 3. Login to Railway
railway login
```

### Step 2: Initialize Railway Project

```bash
# Initialize new Railway project
railway init

# Add PostgreSQL database
railway add --database postgresql
```

### Step 3: Deploy

```bash
# Option A: Use automated script
chmod +x scripts/deploy.sh
./scripts/deploy.sh railway

# Option B: Manual deployment
railway deploy
```

### Step 4: Setup Database

```bash
# After deployment, run the migration
railway run python scripts/migrate_csv_to_db.py

# Check database status
railway run python -c "
from app.database.session import AsyncSessionLocal
from app.models.stock import Stock
from sqlalchemy import select, func
import asyncio

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(Stock.id)))
        count = result.scalar()
        print(f'Stocks in database: {count}')

asyncio.run(check())
"
```

### Step 5: Verify Deployment

```bash
# Get your deployment URL
railway url

# Test the API
curl https://your-app.railway.app/health
curl https://your-app.railway.app/api/v1/stocks/market-summary
```

## 🐳 Docker Deployment

### Local Development with Docker

```bash
# Start all services
docker-compose up -d

# Run migration
docker-compose up migration

# View logs
docker-compose logs -f api

# API will be available at http://localhost:8000
```

### Production Docker

```bash
# Build production image
docker build -t vriddhi-api .

# Run with external PostgreSQL
docker run -d \
  --name vriddhi-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e ENVIRONMENT=production \
  vriddhi-api
```

## 📊 Database Migration

### CSV to PostgreSQL Migration

The migration script automatically:
1. Creates all database tables
2. Loads stock data from CSV
3. Generates derived fields (investment style, risk level, etc.)
4. Creates forecasts for all horizons
5. Verifies data integrity

```bash
# Copy your CSV file
cp path/to/grand_table_expanded.csv data/

# Run migration
python scripts/migrate_csv_to_db.py
```

### Verify Migration

```bash
# Check stock count
curl http://localhost:8000/api/v1/health/detailed

# Test stock endpoints
curl http://localhost:8000/api/v1/stocks/market-summary
curl http://localhost:8000/api/v1/stocks/HDFCLIFE
```

## 🔧 Configuration

### Environment Variables

Key variables to set in Railway/production:

```env
# Database (auto-injected by Railway)
DATABASE_URL=${Postgres.DATABASE_URL}

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Algorithm settings
DEFAULT_EXPECTED_CAGR=0.15
MIN_MONTHLY_INVESTMENT=50000
PEG_RATIO_THRESHOLD=1.0
```

## 🧪 Testing Your Deployment

### 1. Health Checks

```bash
# Basic health
curl https://your-app.railway.app/health

# Detailed health with database status
curl https://your-app.railway.app/api/v1/health/detailed

# Metrics
curl https://your-app.railway.app/api/v1/health/metrics
```

### 2. Stock Data API

```bash
# Market summary
curl https://your-app.railway.app/api/v1/stocks/market-summary

# Search stocks
curl "https://your-app.railway.app/api/v1/stocks/search?q=HDFC"

# Get specific stock
curl https://your-app.railway.app/api/v1/stocks/HDFCLIFE

# Sector analysis
curl https://your-app.railway.app/api/v1/stocks/sectors
```

### 3. Investment Planning API

```bash
# Create investment plan (POST request)
curl -X POST https://your-app.railway.app/api/v1/investment/plan \
  -H "Content-Type: application/json" \
  -d '{
    "monthly_investment": 100000,
    "horizon_months": 36,
    "expected_cagr": 0.18
  }'

# Quick analysis
curl https://your-app.railway.app/api/v1/investment/quick-analysis/100000/36

# SIP projections
curl https://your-app.railway.app/api/v1/investment/projection/100000/36?expected_cagr=0.15
```

## 📈 API Usage Examples

### Complete Investment Analysis

```python
import httpx

# Create comprehensive investment plan
response = httpx.post("https://your-app.railway.app/api/v1/investment/plan", json={
    "monthly_investment": 100000,
    "horizon_months": 36,
    "expected_cagr": 0.18,
    "client_id": "demo_user"
})

if response.status_code == 200:
    plan = response.json()

    print(f"✅ Investment Plan Created")
    print(f"Achieved CAGR: {plan['investment_summary']['achieved_cagr']:.1f}%")
    print(f"Final Value: ₹{plan['investment_summary']['final_value']:,}")
    print(f"Total Gain: ₹{plan['investment_summary']['total_gain']:,}")
    print(f"Stocks Selected: {len(plan['portfolio_allocations'])}")

    # Show top allocations
    allocations = sorted(plan['portfolio_allocations'], key=lambda x: x['weight'], reverse=True)
    print("\nTop 5 Stock Allocations:")
    for stock in allocations[:5]:
        print(f"  {stock['ticker']} ({stock['sector']}): {stock['weight']:.1%} - ₹{stock['monthly_allocation']:,}/month")

    # Show diversification
    print(f"\nSector Diversification:")
    for sector, weight in plan['sector_allocation'].items():
        print(f"  {sector}: {weight:.1%}")
```

### Stock Selection Only

```python
# Run just the stock selection algorithm
response = httpx.post("https://your-app.railway.app/api/v1/investment/select-stocks", json={
    "expected_cagr": 0.18,
    "horizon_months": 36,
    "peg_threshold": 1.0,
    "max_stocks": 15
})

if response.status_code == 200:
    selection = response.json()

    print(f"Stock Selection Results:")
    print(f"Target CAGR: {selection['expected_cagr']:.1%}")
    print(f"Achieved CAGR: {selection['achieved_cagr']:.1%}")
    print(f"Feasible: {selection['feasible']}")
    print(f"Total Stocks: {selection['total_stocks']}")

    print(f"\nSelection Rationale:")
    rationale = selection['selection_rationale']
    print(f"  Universe: {rationale['total_universe']} stocks")
    print(f"  Method: {rationale['selection_method']}")
    print(f"  Sectors: {rationale['sectors_available']}")
```

## 🔗 Frontend Integration

### API Base URL
```javascript
const API_BASE_URL = 'https://your-app.railway.app/api/v1';

// Example API call
const createInvestmentPlan = async (planData) => {
  const response = await fetch(`${API_BASE_URL}/investment/plan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(planData)
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
};
```

### CORS Configuration
Update your Railway environment variables:

```env
ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-domain.com
```

## 📊 Monitoring & Maintenance

### Health Monitoring

Set up monitoring for these endpoints:
- `/health` - Basic health check
- `/api/v1/health/detailed` - Database connectivity
- `/api/v1/health/metrics` - Performance metrics

### Log Analysis

```bash
# View recent logs
railway logs

# Follow logs in real-time
railway logs --follow

# Filter by error level
railway logs | grep ERROR
```

### Database Maintenance

```bash
# Check database performance
railway run python -c "
import asyncio
from app.database.session import AsyncSessionLocal
from sqlalchemy import text

async def check_db():
    async with AsyncSessionLocal() as session:
        # Check table sizes
        result = await session.execute(text('''
            SELECT schemaname,tablename,attname,n_distinct,correlation
            FROM pg_stats
            WHERE tablename IN ('stocks', 'stock_forecasts')
            LIMIT 10
        '''))
        for row in result:
            print(row)

asyncio.run(check_db())
"
```

## 🔧 Troubleshooting

### Common Issues

1. **Migration Fails**
   ```bash
   # Check if CSV file exists
   railway run ls -la data/

   # Run migration with debug logs
   railway run python scripts/migrate_csv_to_db.py --verbose
   ```

2. **API Returns 500 Errors**
   ```bash
   # Check logs
   railway logs | tail -50

   # Test database connection
   railway run python -c "
   from app.database.session import AsyncSessionLocal
   import asyncio

   async def test():
       async with AsyncSessionLocal() as session:
           print('Database connection successful')

   asyncio.run(test())
   "
   ```

3. **Performance Issues**
   ```bash
   # Check health metrics
   curl https://your-app.railway.app/api/v1/health/metrics

   # Monitor response times
   curl -w "@curl-format.txt" -o /dev/null -s https://your-app.railway.app/api/v1/stocks/market-summary
   ```

### Performance Optimization

1. **Database Indexing**: Already optimized with proper indexes
2. **Connection Pooling**: Configured in `database/session.py`
3. **Response Caching**: Add Redis for caching frequent queries
4. **Rate Limiting**: Implement if needed for production

## 🎯 Next Steps

After successful deployment:

1. **Update Frontend**: Point your Streamlit/React app to the new API
2. **SSL Certificate**: Railway provides HTTPS automatically
3. **Custom Domain**: Configure your domain in Railway dashboard
4. **Monitoring**: Set up uptime monitoring
5. **Backup**: Configure database backups in Railway
6. **API Keys**: Add authentication if needed

## 📞 Support

- **API Documentation**: https://your-app.railway.app/docs
- **Health Status**: https://your-app.railway.app/health
- **Railway Dashboard**: https://railway.app/dashboard

---

🎉 **Congratulations!** You now have a complete, production-ready FastAPI backend that replicates all Vriddhi functionality. Your API is ready to power sophisticated investment advisory applications with professional-grade algorithms and infrastructure.

**API URL**: https://your-app.railway.app
**Documentation**: https://your-app.railway.app/docs
**Health Check**: https://your-app.railway.app/health