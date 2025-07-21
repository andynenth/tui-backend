# backend/api/config/rate_limit_config.py

"""
Rate limiting configuration for the Liap Tui API.

This module defines rate limiting rules and settings that can be
customized via environment variables.
"""

import os
from typing import Dict, Optional

from api.middleware.rate_limit import RateLimitRule


def get_rate_limit_rules() -> Dict[str, RateLimitRule]:
    """
    Get rate limit rules from environment variables or use defaults.

    Environment variables follow the pattern:
    RATE_LIMIT_{ENDPOINT}_{METRIC}

    For example:
    - RATE_LIMIT_HEALTH_REQUESTS=60
    - RATE_LIMIT_HEALTH_WINDOW=60
    - RATE_LIMIT_WS_DECLARE_REQUESTS=5
    - RATE_LIMIT_WS_DECLARE_WINDOW=60
    """
    rules = {}

    # REST API endpoints
    rules["/api/health"] = RateLimitRule(
        requests=int(os.getenv("RATE_LIMIT_HEALTH_REQUESTS", "60")),
        window_seconds=int(os.getenv("RATE_LIMIT_HEALTH_WINDOW", "60")),
    )

    rules["/api/health/detailed"] = RateLimitRule(
        requests=int(os.getenv("RATE_LIMIT_HEALTH_DETAILED_REQUESTS", "30")),
        window_seconds=int(os.getenv("RATE_LIMIT_HEALTH_DETAILED_WINDOW", "60")),
    )

    rules["/api/rooms"] = RateLimitRule(
        requests=int(os.getenv("RATE_LIMIT_ROOMS_REQUESTS", "30")),
        window_seconds=int(os.getenv("RATE_LIMIT_ROOMS_WINDOW", "60")),
    )

    rules["/api/recovery"] = RateLimitRule(
        requests=int(os.getenv("RATE_LIMIT_RECOVERY_REQUESTS", "10")),
        window_seconds=int(os.getenv("RATE_LIMIT_RECOVERY_WINDOW", "60")),
    )

    rules["/api/event-store"] = RateLimitRule(
        requests=int(os.getenv("RATE_LIMIT_EVENT_STORE_REQUESTS", "20")),
        window_seconds=int(os.getenv("RATE_LIMIT_EVENT_STORE_WINDOW", "60")),
    )

    # Global default
    rules["global"] = RateLimitRule(
        requests=int(os.getenv("RATE_LIMIT_GLOBAL_REQUESTS", "100")),
        window_seconds=int(os.getenv("RATE_LIMIT_GLOBAL_WINDOW", "60")),
        burst_multiplier=float(os.getenv("RATE_LIMIT_GLOBAL_BURST", "2.0")),
    )

    return rules


def get_websocket_rate_limit_rules() -> Dict[str, RateLimitRule]:
    """
    Get WebSocket-specific rate limit rules from environment variables.

    Environment variables follow the pattern:
    WS_RATE_LIMIT_{EVENT}_{METRIC}

    For example:
    - WS_RATE_LIMIT_DECLARE_REQUESTS=5
    - WS_RATE_LIMIT_DECLARE_WINDOW=60
    - WS_RATE_LIMIT_PLAY_REQUESTS=20
    """
    rules = {}

    # System events
    rules["ping"] = RateLimitRule(
        requests=int(os.getenv("WS_RATE_LIMIT_PING_REQUESTS", "120")),
        window_seconds=int(os.getenv("WS_RATE_LIMIT_PING_WINDOW", "60")),
    )

    rules["ack"] = RateLimitRule(
        requests=int(os.getenv("WS_RATE_LIMIT_ACK_REQUESTS", "200")),
        window_seconds=int(os.getenv("WS_RATE_LIMIT_ACK_WINDOW", "60")),
    )

    # Game events
    rules["declare"] = RateLimitRule(
        requests=int(os.getenv("WS_RATE_LIMIT_DECLARE_REQUESTS", "5")),
        window_seconds=int(os.getenv("WS_RATE_LIMIT_DECLARE_WINDOW", "60")),
        burst_multiplier=float(os.getenv("WS_RATE_LIMIT_DECLARE_BURST", "1.2")),
    )

    rules["play"] = RateLimitRule(
        requests=int(os.getenv("WS_RATE_LIMIT_PLAY_REQUESTS", "20")),
        window_seconds=int(os.getenv("WS_RATE_LIMIT_PLAY_WINDOW", "60")),
    )

    rules["create_room"] = RateLimitRule(
        requests=int(os.getenv("WS_RATE_LIMIT_CREATE_ROOM_REQUESTS", "5")),
        window_seconds=int(os.getenv("WS_RATE_LIMIT_CREATE_ROOM_WINDOW", "60")),
        block_duration_seconds=int(os.getenv("WS_RATE_LIMIT_CREATE_ROOM_BLOCK", "300")),
    )

    rules["start_game"] = RateLimitRule(
        requests=int(os.getenv("WS_RATE_LIMIT_START_GAME_REQUESTS", "3")),
        window_seconds=int(os.getenv("WS_RATE_LIMIT_START_GAME_WINDOW", "60")),
        block_duration_seconds=int(os.getenv("WS_RATE_LIMIT_START_GAME_BLOCK", "600")),
    )

    # Default for unknown events
    rules["default"] = RateLimitRule(
        requests=int(os.getenv("WS_RATE_LIMIT_DEFAULT_REQUESTS", "60")),
        window_seconds=int(os.getenv("WS_RATE_LIMIT_DEFAULT_WINDOW", "60")),
        burst_multiplier=float(os.getenv("WS_RATE_LIMIT_DEFAULT_BURST", "1.5")),
    )

    return rules


# Rate limiting feature flags
RATE_LIMITING_ENABLED = os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true"
RATE_LIMITING_LOG_VIOLATIONS = (
    os.getenv("RATE_LIMITING_LOG_VIOLATIONS", "true").lower() == "true"
)
RATE_LIMITING_REDIS_ENABLED = (
    os.getenv("RATE_LIMITING_REDIS_ENABLED", "false").lower() == "true"
)

# Redis configuration (for distributed rate limiting - future enhancement)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "liap_tui:rate_limit:")
REDIS_TTL_SECONDS = int(os.getenv("REDIS_TTL_SECONDS", "3600"))  # 1 hour
