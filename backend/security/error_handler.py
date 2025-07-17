"""
Enhanced Error Handling System
Comprehensive error handling with logging, monitoring, and user-friendly responses
"""
import logging
import traceback
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
import uuid

# Configure secure logging
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO for production
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/gaming_platform.log"),
        logging.StreamHandler()
    ]
)

class ErrorTracker:
    """
    Track and monitor errors for system health
    """
    
    def __init__(self):
        self.error_counts = {}
        self.recent_errors = []
        self.max_recent_errors = 100
    
    def record_error(self, error_type: str, error_message: str, endpoint: str = None):
        """Record error for monitoring"""
        error_key = f"{error_type}_{endpoint}" if endpoint else error_type
        
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": error_type,
            "message": error_message,
            "endpoint": endpoint,
            "count": self.error_counts[error_key]
        }
        
        self.recent_errors.append(error_record)
        
        # Keep only recent errors
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_error_types": len(self.error_counts),
            "error_counts": self.error_counts,
            "recent_errors": self.recent_errors[-10:]  # Last 10 errors
        }

class GameError(Exception):
    """Base class for game-specific errors"""
    def __init__(self, message: str, code: str = "GAME_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ValidationError(GameError):
    """Validation error"""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")

class WalletError(GameError):
    """Wallet-related error"""
    def __init__(self, message: str):
        super().__init__(message, "WALLET_ERROR")

class TransactionError(GameError):
    """Transaction-related error"""
    def __init__(self, message: str):
        super().__init__(message, "TRANSACTION_ERROR")

class GameLogicError(GameError):
    """Game logic error"""
    def __init__(self, message: str):
        super().__init__(message, "GAME_LOGIC_ERROR")

class PayoutError(GameError):
    """Payout-related error"""
    def __init__(self, message: str):
        super().__init__(message, "PAYOUT_ERROR")

class ErrorHandler:
    """
    Centralized error handling system
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_tracker = ErrorTracker()
        
        # User-friendly error messages
        self.error_messages = {
            "VALIDATION_ERROR": "Invalid input provided. Please check your data and try again.",
            "WALLET_ERROR": "Wallet connection issue. Please check your wallet and try again.",
            "TRANSACTION_ERROR": "Transaction failed. Please check your balance and try again.",
            "GAME_LOGIC_ERROR": "Game temporarily unavailable. Please try again later.",
            "PAYOUT_ERROR": "Payout processing failed. Please contact support.",
            "RATE_LIMIT_ERROR": "Too many requests. Please wait and try again.",
            "DATABASE_ERROR": "Service temporarily unavailable. Please try again later.",
            "INTERNAL_ERROR": "Internal server error. Please try again later."
        }
    
    def handle_error(self, error: Exception, request: Request = None) -> JSONResponse:
        """
        Handle different types of errors and return appropriate responses
        """
        error_id = str(uuid.uuid4())
        endpoint = request.url.path if request else "unknown"
        
        # Log error with unique ID
        self.logger.error(f"Error ID: {error_id} | Endpoint: {endpoint} | Error: {str(error)}")
        
        if isinstance(error, GameError):
            return self._handle_game_error(error, error_id, endpoint)
        elif isinstance(error, HTTPException):
            return self._handle_http_error(error, error_id, endpoint)
        elif isinstance(error, ValueError):
            return self._handle_validation_error(error, error_id, endpoint)
        else:
            return self._handle_unexpected_error(error, error_id, endpoint)
    
    def _handle_game_error(self, error: GameError, error_id: str, endpoint: str) -> JSONResponse:
        """Handle game-specific errors"""
        self.error_tracker.record_error(error.code, error.message, endpoint)
        
        user_message = self.error_messages.get(error.code, "Game error occurred")
        
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": user_message,
                "error_code": error.code,
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _handle_http_error(self, error: HTTPException, error_id: str, endpoint: str) -> JSONResponse:
        """Handle HTTP errors"""
        self.error_tracker.record_error("HTTP_ERROR", str(error.detail), endpoint)
        
        return JSONResponse(
            status_code=error.status_code,
            content={
                "success": False,
                "error": str(error.detail),
                "error_code": "HTTP_ERROR",
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _handle_validation_error(self, error: ValueError, error_id: str, endpoint: str) -> JSONResponse:
        """Handle validation errors"""
        self.error_tracker.record_error("VALIDATION_ERROR", str(error), endpoint)
        
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": self.error_messages["VALIDATION_ERROR"],
                "error_code": "VALIDATION_ERROR",
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _handle_unexpected_error(self, error: Exception, error_id: str, endpoint: str) -> JSONResponse:
        """Handle unexpected errors"""
        # Log full traceback for debugging
        self.logger.error(f"Unexpected error ID: {error_id} | Traceback: {traceback.format_exc()}")
        
        self.error_tracker.record_error("INTERNAL_ERROR", str(error), endpoint)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": self.error_messages["INTERNAL_ERROR"],
                "error_code": "INTERNAL_ERROR",
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def safe_execute(self, func, *args, **kwargs):
        """
        Safely execute a function with error handling
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Safe execution failed: {str(e)}")
            raise GameLogicError("Operation failed")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return self.error_tracker.get_error_stats()

# Global error handler instance
error_handler = ErrorHandler()

# Decorator for safe function execution
def safe_endpoint(func):
    """
    Decorator to wrap endpoints with error handling
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            request = kwargs.get('request') or (args[0] if args and hasattr(args[0], 'url') else None)
            return error_handler.handle_error(e, request)
    
    return wrapper

# Database connection error handler
class DatabaseErrorHandler:
    """
    Handle database connection and query errors
    """
    
    def __init__(self):
        self.logger = logging.getLogger("database")
        self.retry_count = 3
        self.retry_delay = 1.0
    
    async def safe_db_operation(self, operation, *args, **kwargs):
        """
        Safely execute database operation with retries
        """
        for attempt in range(self.retry_count):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f"Database operation failed (attempt {attempt + 1}): {str(e)}")
                
                if attempt == self.retry_count - 1:
                    raise GameError("Database temporarily unavailable", "DATABASE_ERROR")
                
                await asyncio.sleep(self.retry_delay * (attempt + 1))

# Global database error handler
db_error_handler = DatabaseErrorHandler()

# Utility functions
def log_security_event(event_type: str, details: str, request: Request = None):
    """Log security-related events"""
    security_logger = logging.getLogger("security")
    
    client_ip = request.client.host if request else "unknown"
    endpoint = request.url.path if request else "unknown"
    
    security_logger.warning(f"SECURITY EVENT: {event_type} | IP: {client_ip} | Endpoint: {endpoint} | Details: {details}")

def sanitize_for_logging(data: Any) -> Any:
    """Sanitize sensitive data for logging"""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in ['password', 'key', 'secret', 'signature']):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = sanitize_for_logging(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_for_logging(item) for item in data]
    else:
        return data