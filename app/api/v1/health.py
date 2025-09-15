"""
Health check and monitoring endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime
import psutil
import os
import logging

from app.database.session import get_db
from app.models.stock import Stock
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger("vriddhi")

@router.get("/")
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "service": "vriddhi-investment-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": settings.ENVIRONMENT
    }

@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check including database and system metrics
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": {
            "name": "vriddhi-investment-api",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": psutil.Process(os.getpid()).create_time()
        },
        "database": {},
        "system": {},
        "dependencies": {}
    }

    # Database health check
    try:
        # Test basic connection
        result = await db.execute(text("SELECT 1"))
        result.fetchone()

        # Get stock count
        stock_count_query = select(func.count(Stock.id))
        stock_result = await db.execute(stock_count_query)
        stock_count = stock_result.scalar()

        # Get active stock count
        active_stock_query = select(func.count(Stock.id)).where(Stock.is_active == True)
        active_result = await db.execute(active_stock_query)
        active_count = active_result.scalar()

        health_status["database"] = {
            "status": "connected",
            "total_stocks": stock_count,
            "active_stocks": active_count
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # System metrics
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        }
    except Exception as e:
        logger.error(f"System metrics collection failed: {e}")
        health_status["system"] = {
            "status": "error",
            "error": str(e)
        }

    # Dependencies check
    try:
        import scipy
        import numpy
        import pandas

        health_status["dependencies"] = {
            "scipy": scipy.__version__,
            "numpy": numpy.__version__,
            "pandas": pandas.__version__,
            "status": "available"
        }
    except Exception as e:
        health_status["dependencies"] = {
            "status": "error",
            "error": str(e)
        }

    return health_status

@router.get("/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check for Kubernetes/Railway deployments
    """
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        result.fetchone()

        # Verify we have stock data
        stock_count_query = select(func.count(Stock.id))
        stock_result = await db.execute(stock_count_query)
        stock_count = stock_result.scalar()

        if stock_count == 0:
            raise HTTPException(status_code=503, detail="No stock data available")

        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "stock_count": stock_count
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/liveness")
async def liveness_check():
    """
    Liveness check for Kubernetes/Railway deployments
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "pid": os.getpid()
    }

@router.get("/metrics")
async def metrics_endpoint(db: AsyncSession = Depends(get_db)):
    """
    Prometheus-style metrics endpoint
    """
    try:
        # Database metrics
        total_stocks_query = select(func.count(Stock.id))
        total_result = await db.execute(total_stocks_query)
        total_stocks = total_result.scalar()

        active_stocks_query = select(func.count(Stock.id)).where(Stock.is_active == True)
        active_result = await db.execute(active_stocks_query)
        active_stocks = active_result.scalar()

        # System metrics
        memory = psutil.virtual_memory()

        metrics = {
            "vriddhi_stocks_total": total_stocks,
            "vriddhi_stocks_active": active_stocks,
            "vriddhi_memory_usage_bytes": memory.used,
            "vriddhi_memory_total_bytes": memory.total,
            "vriddhi_cpu_usage_percent": psutil.cpu_percent(),
            "vriddhi_uptime_seconds": psutil.Process(os.getpid()).create_time()
        }

        return metrics

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics collection failed")