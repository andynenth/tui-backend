# backend/config/logging_config.py

"""
Logging configuration for Liap Tui backend.

This module provides centralized logging configuration with special
support for rate limiting logs.
"""

import os
import sys
import logging
import logging.config
from typing import Dict, Any


def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration dictionary.

    Returns a configuration suitable for logging.config.dictConfig()
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "json")  # json or text
    rate_limit_debug = os.getenv("RATE_LIMIT_DEBUG", "false").lower() == "true"

    # Check if JSON formatter is available
    json_formatter_available = False
    try:
        import pythonjsonlogger

        json_formatter_available = True
    except ImportError:
        log_format = "text"  # Fall back to text format

    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "text": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": log_format,
                "stream": "ext://sys.stdout",
            },
            "rate_limit_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": log_format,
                "filename": "logs/rate_limit.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            # Rate limiting loggers
            "api.middleware.rate_limit": {
                "level": "DEBUG" if rate_limit_debug else "INFO",
                "handlers": ["console", "rate_limit_file"],
                "propagate": False,
            },
            "api.middleware.websocket_rate_limit": {
                "level": "DEBUG" if rate_limit_debug else "INFO",
                "handlers": ["console", "rate_limit_file"],
                "propagate": False,
            },
            # API routes logger
            "api.routes": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # Game engine logger
            "engine": {"level": log_level, "handlers": ["console"], "propagate": False},
        },
        "root": {"level": log_level, "handlers": ["console"]},
    }

    # Add JSON formatter if available
    if json_formatter_available:
        config["formatters"]["json"] = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    else:
        # Force all handlers to use text formatter
        config["handlers"]["console"]["formatter"] = "text"
        config["handlers"]["rate_limit_file"]["formatter"] = "text"

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    return config


def setup_logging():
    """
    Set up logging configuration for the application.

    This should be called early in the application startup.
    """
    config = get_logging_config()
    logging.config.dictConfig(config)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": config["root"]["level"],
            "rate_limit_debug": os.getenv("RATE_LIMIT_DEBUG", "false"),
        },
    )


def get_rate_limit_logger(name: str = "rate_limit") -> logging.Logger:
    """
    Get a logger configured for rate limiting logs.

    Args:
        name: Logger name suffix (will be prefixed with 'rate_limit.')

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"api.middleware.{name}")


# Custom log filter for rate limit logs
class RateLimitLogFilter(logging.Filter):
    """
    Filter to enrich rate limit logs with additional context.
    """

    def filter(self, record):
        # Add hostname if available
        if not hasattr(record, "hostname"):
            import socket

            record.hostname = socket.gethostname()

        # Add process ID
        if not hasattr(record, "pid"):
            record.pid = os.getpid()

        # Ensure rate_limit_data exists
        if not hasattr(record, "rate_limit_data"):
            record.rate_limit_data = {}

        return True


# Utility functions for structured logging
def log_rate_limit_event(
    logger: logging.Logger, event_type: str, client_id: str, route: str, **kwargs
):
    """
    Log a rate limit event with structured data.

    Args:
        logger: Logger instance
        event_type: Type of event (exceeded, warning, blocked, etc.)
        client_id: Client identifier
        route: Route or event name
        **kwargs: Additional data to log
    """
    level = logging.INFO
    message = f"Rate limit {event_type}"

    if event_type == "exceeded":
        level = logging.WARNING
        message = f"Rate limit exceeded for {route}"
    elif event_type == "blocked":
        level = logging.ERROR
        message = f"Client blocked: {client_id}"
    elif event_type == "warning":
        level = logging.INFO
        message = f"Rate limit warning for {route}"

    logger.log(
        level,
        message,
        extra={
            "rate_limit_data": {
                "event": event_type,
                "client_id": client_id,
                "route": route,
                **kwargs,
            }
        },
    )


# Daily summary generation
def generate_rate_limit_summary(logger: logging.Logger):
    """
    Generate a daily summary of rate limit activity.

    This should be called by a scheduled task.
    """
    # This would typically query the rate limiter for stats
    # For now, just log that a summary was requested
    logger.info(
        "Rate limit daily summary",
        extra={
            "rate_limit_data": {
                "event": "daily_summary",
                "timestamp": os.environ.get("TZ", "UTC"),
            }
        },
    )
