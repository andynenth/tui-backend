# backend/api/middleware/logging_middleware.py
"""
Structured logging middleware for API requests.
"""

import time
import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import uuid

logger = logging.getLogger(__name__)

# Import monitoring service for metrics collection
try:
    from backend.services.monitoring_service import metrics_collector
except ImportError:
    metrics_collector = None


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add structured logging for all API requests.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID if not already present
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            "API Request",
            extra={
                "event": "api_request_start",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
            }
        )
        
        # Process request
        response = None
        error = None
        try:
            response = await call_next(request)
        except Exception as e:
            error = str(e)
            logger.error(
                f"Request failed: {error}",
                extra={
                    "event": "api_request_error",
                    "request_id": request_id,
                    "error": error,
                    "method": request.method,
                    "path": request.url.path,
                },
                exc_info=True
            )
            raise
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            log_data = {
                "event": "api_request_complete",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code if response else 500,
                "duration_ms": round(duration_ms, 2),
                "client_host": request.client.host if request.client else None,
            }
            
            # Add performance warnings
            if duration_ms > 1000:  # Slow request (>1s)
                log_data["performance_warning"] = "slow_request"
            elif duration_ms > 500:  # Medium slow (>500ms)
                log_data["performance_warning"] = "medium_slow_request"
            
            # Log based on status code
            if response and response.status_code >= 500:
                logger.error("Server error response", extra=log_data)
            elif response and response.status_code >= 400:
                logger.warning("Client error response", extra=log_data)
            else:
                logger.info("Request completed", extra=log_data)
            
            # Record metrics if collector is available
            if metrics_collector and response:
                metrics_collector.record_request(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=response.status_code,
                    duration_ms=duration_ms
                )
        
        # Add request ID to response headers
        if response:
            response.headers["X-Request-ID"] = request_id
        
        return response


class PlayHistoryLoggingMiddleware:
    """
    Specialized logging for play history endpoints.
    """
    
    @staticmethod
    def log_play_history_request(
        room_id: str,
        rounds: str = None,
        include_hands: bool = True,
        include_ai_analysis: bool = True,
        format: str = None,
        request_id: str = None
    ):
        """Log play history request details."""
        logger.info(
            "Play history request",
            extra={
                "event": "play_history_request",
                "request_id": request_id,
                "room_id": room_id,
                "rounds": rounds,
                "include_hands": include_hands,
                "include_ai_analysis": include_ai_analysis,
                "format": format,
            }
        )
    
    @staticmethod
    def log_play_history_response(
        room_id: str,
        total_rounds: int,
        response_size: int,
        build_time_ms: float,
        request_id: str = None
    ):
        """Log play history response metrics."""
        logger.info(
            "Play history response",
            extra={
                "event": "play_history_response",
                "request_id": request_id,
                "room_id": room_id,
                "total_rounds": total_rounds,
                "response_size_bytes": response_size,
                "build_time_ms": round(build_time_ms, 2),
            }
        )
    
    @staticmethod
    def log_performance_warning(
        warning_type: str,
        details: dict,
        request_id: str = None
    ):
        """Log performance warnings."""
        logger.warning(
            f"Performance warning: {warning_type}",
            extra={
                "event": "performance_warning",
                "request_id": request_id,
                "warning_type": warning_type,
                "details": details,
            }
        )
    
    @staticmethod
    def log_cache_hit(
        cache_key: str,
        cache_type: str = "redis",
        request_id: str = None
    ):
        """Log cache hit."""
        logger.info(
            "Cache hit",
            extra={
                "event": "cache_hit",
                "request_id": request_id,
                "cache_key": cache_key,
                "cache_type": cache_type,
            }
        )
    
    @staticmethod
    def log_cache_miss(
        cache_key: str,
        cache_type: str = "redis",
        request_id: str = None
    ):
        """Log cache miss."""
        logger.info(
            "Cache miss",
            extra={
                "event": "cache_miss",
                "request_id": request_id,
                "cache_key": cache_key,
                "cache_type": cache_type,
            }
        )


def setup_structured_logging():
    """
    Configure structured logging with JSON formatter.
    """
    import logging.config
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "json_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/api_structured.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "backend.api": {
                "level": "INFO",
                "handlers": ["console", "json_file"],
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(config)