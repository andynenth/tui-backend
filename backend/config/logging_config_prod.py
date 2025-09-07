# backend/config/logging_config_prod.py
"""
Production logging configuration that only uses console output.
File logging is handled by Docker's logging driver.
"""

import logging
import sys


def setup_logging():
    """Setup production logging configuration."""
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": sys.stdout,
            }
        },
        "loggers": {
            "": {"level": "INFO", "handlers": ["console"]},
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "backend": {"level": "INFO", "handlers": ["console"], "propagate": False},
        },
    }

    logging.config.dictConfig(config)
    logger = logging.getLogger(__name__)
    logger.info("Production logging configured (console only)")
