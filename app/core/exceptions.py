"""
Custom exception classes and error handlers
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Union
import logging

logger = logging.getLogger("vriddhi")

# Custom Exception Classes
class VriddhiException(Exception):
    """Base exception class for Vriddhi application"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code or "VRIDDHI_ERROR"
        super().__init__(message)

class StockNotFoundException(VriddhiException):
    """Raised when a requested stock is not found"""
    def __init__(self, ticker: str):
        super().__init__(f"Stock {ticker} not found", "STOCK_NOT_FOUND")
        self.ticker = ticker

class PortfolioNotFoundException(VriddhiException):
    """Raised when a requested portfolio is not found"""
    def __init__(self, portfolio_id: int):
        super().__init__(f"Portfolio {portfolio_id} not found", "PORTFOLIO_NOT_FOUND")
        self.portfolio_id = portfolio_id

class InsufficientDataException(VriddhiException):
    """Raised when there's insufficient data for analysis"""
    def __init__(self, message: str = "Insufficient data for analysis"):
        super().__init__(message, "INSUFFICIENT_DATA")

class OptimizationFailedException(VriddhiException):
    """Raised when portfolio optimization fails"""
    def __init__(self, message: str = "Portfolio optimization failed"):
        super().__init__(message, "OPTIMIZATION_FAILED")

class InvalidInvestmentParametersException(VriddhiException):
    """Raised when investment parameters are invalid"""
    def __init__(self, message: str):
        super().__init__(message, "INVALID_PARAMETERS")

class DatabaseException(VriddhiException):
    """Raised when database operations fail"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR")

# Error Response Models
def create_error_response(
    error_code: str,
    message: str,
    details: Union[str, dict] = None,
    status_code: int = 400
) -> dict:
    """
    Create standardized error response
    """
    response = {
        "error": True,
        "error_code": error_code,
        "message": message,
        "status_code": status_code
    }

    if details:
        response["details"] = details

    return response

# Exception Handlers
async def vriddhi_exception_handler(request: Request, exc: VriddhiException):
    """
    Handle custom Vriddhi exceptions
    """
    logger.error(f"Vriddhi error: {exc.error_code} - {exc.message}")

    status_code = status.HTTP_400_BAD_REQUEST

    # Map specific exceptions to HTTP status codes
    if isinstance(exc, StockNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, PortfolioNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, InsufficientDataException):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, OptimizationFailedException):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, InvalidInvestmentParametersException):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, DatabaseException):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content=create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=status_code
        )
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors
    """
    logger.error(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details=exc.errors(),
            status_code=422
        )
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle FastAPI HTTP exceptions
    """
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code="HTTP_ERROR",
            message=exc.detail,
            status_code=exc.status_code
        )
    )

async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions
    """
    logger.error(f"Unexpected error: {type(exc).__name__} - {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details=str(exc) if logger.level <= logging.DEBUG else None,
            status_code=500
        )
    )