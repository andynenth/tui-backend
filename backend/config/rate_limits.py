# backend/config/rate_limits.py

"""
Rate limiting configuration module.

This module provides centralized configuration for rate limits across the application,
with support for environment-based configuration and runtime updates.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional
from backend.api.middleware.rate_limit import RateLimitRule


@dataclass
class RateLimitConfig:
    """Main configuration class for rate limits."""

    # Feature flags
    enabled: bool = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "true").lower()
        == "true"
    )
    debug_mode: bool = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_DEBUG", "false").lower() == "true"
    )

    # Global settings
    global_requests_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_GLOBAL_RPM", "100"))
    )
    burst_multiplier: float = field(
        default_factory=lambda: float(os.getenv("RATE_LIMIT_BURST_MULTIPLIER", "1.5"))
    )
    block_duration_seconds: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_BLOCK_DURATION", "300"))
    )

    # REST API limits
    health_endpoint_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_HEALTH_RPM", "60"))
    )
    rooms_endpoint_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_ROOMS_RPM", "30"))
    )
    recovery_endpoint_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_RECOVERY_RPM", "10"))
    )

    # WebSocket limits - System events
    ws_ping_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_PING_RPM", "120"))
    )
    ws_ack_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_ACK_RPM", "200"))
    )
    ws_sync_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_SYNC_RPM", "10"))
    )

    # WebSocket limits - Lobby events
    ws_room_list_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_ROOM_LIST_RPM", "30"))
    )
    ws_create_room_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_CREATE_ROOM_RPM", "5"))
    )
    ws_join_room_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_JOIN_ROOM_RPM", "10"))
    )

    # WebSocket limits - Game events
    ws_declare_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_DECLARE_RPM", "5"))
    )
    ws_play_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_PLAY_RPM", "20"))
    )
    ws_redeal_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_REDEAL_RPM", "3"))
    )
    ws_start_game_rpm: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WS_START_GAME_RPM", "3"))
    )

    # Room flood protection
    room_flood_threshold: int = field(
        default_factory=lambda: int(
            os.getenv("RATE_LIMIT_ROOM_FLOOD_THRESHOLD", "1000")
        )
    )

    # Grace period settings
    grace_warning_threshold: float = field(
        default_factory=lambda: float(os.getenv("RATE_LIMIT_GRACE_WARNING", "0.8"))
    )
    grace_multiplier: float = field(
        default_factory=lambda: float(os.getenv("RATE_LIMIT_GRACE_MULTIPLIER", "1.2"))
    )
    grace_duration_seconds: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_GRACE_DURATION", "30"))
    )

    def get_rest_api_rules(self) -> Dict[str, RateLimitRule]:
        """Get rate limit rules for REST API endpoints."""
        if not self.enabled:
            # Return very high limits when disabled
            return {
                "/api/health": RateLimitRule(requests=99999, window_seconds=60),
                "/api/health/detailed": RateLimitRule(
                    requests=99999, window_seconds=60
                ),
                "/api/rooms": RateLimitRule(requests=99999, window_seconds=60),
                "/api/recovery": RateLimitRule(requests=99999, window_seconds=60),
                "global": RateLimitRule(requests=99999, window_seconds=60),
            }

        return {
            "/api/health": RateLimitRule(
                requests=self.health_endpoint_rpm,
                window_seconds=60,
                burst_multiplier=self.burst_multiplier,
            ),
            "/api/health/detailed": RateLimitRule(
                requests=self.health_endpoint_rpm // 2,
                window_seconds=60,
                burst_multiplier=self.burst_multiplier,
            ),
            "/api/rooms": RateLimitRule(
                requests=self.rooms_endpoint_rpm,
                window_seconds=60,
                burst_multiplier=self.burst_multiplier,
            ),
            "/api/recovery": RateLimitRule(
                requests=self.recovery_endpoint_rpm,
                window_seconds=60,
                burst_multiplier=self.burst_multiplier,
                block_duration_seconds=self.block_duration_seconds,
            ),
            "global": RateLimitRule(
                requests=self.global_requests_per_minute,
                window_seconds=60,
                burst_multiplier=self.burst_multiplier
                * 1.5,  # More lenient global burst
            ),
        }

    def get_websocket_rules(self) -> Dict[str, RateLimitRule]:
        """Get rate limit rules for WebSocket events."""
        if not self.enabled:
            # Return very high limits when disabled
            return {
                event: RateLimitRule(requests=99999, window_seconds=60)
                for event in ["ping", "declare", "play", "create_room", "default"]
            }

        return {
            # System events
            "ping": RateLimitRule(requests=self.ws_ping_rpm, window_seconds=60),
            "ack": RateLimitRule(requests=self.ws_ack_rpm, window_seconds=60),
            "sync_request": RateLimitRule(requests=self.ws_sync_rpm, window_seconds=60),
            # Lobby events
            "request_room_list": RateLimitRule(
                requests=self.ws_room_list_rpm, window_seconds=60
            ),
            "get_rooms": RateLimitRule(
                requests=self.ws_room_list_rpm, window_seconds=60
            ),
            "create_room": RateLimitRule(
                requests=self.ws_create_room_rpm,
                window_seconds=60,
                block_duration_seconds=self.block_duration_seconds,
            ),
            "join_room": RateLimitRule(
                requests=self.ws_join_room_rpm, window_seconds=60
            ),
            # Room management
            "get_room_state": RateLimitRule(
                requests=self.rooms_endpoint_rpm * 2, window_seconds=60
            ),
            "remove_player": RateLimitRule(requests=10, window_seconds=60),
            "add_bot": RateLimitRule(requests=10, window_seconds=60),
            "leave_room": RateLimitRule(requests=5, window_seconds=60),
            "start_game": RateLimitRule(
                requests=self.ws_start_game_rpm,
                window_seconds=60,
                block_duration_seconds=self.block_duration_seconds * 2,
            ),
            # Game events
            "declare": RateLimitRule(
                requests=self.ws_declare_rpm,
                window_seconds=60,
                burst_multiplier=1.2,  # Tight burst control
            ),
            "play": RateLimitRule(requests=self.ws_play_rpm, window_seconds=60),
            "play_pieces": RateLimitRule(requests=self.ws_play_rpm, window_seconds=60),
            "request_redeal": RateLimitRule(
                requests=self.ws_redeal_rpm,
                window_seconds=60,
                block_duration_seconds=self.block_duration_seconds,
            ),
            "accept_redeal": RateLimitRule(requests=5, window_seconds=60),
            "decline_redeal": RateLimitRule(requests=5, window_seconds=60),
            "redeal_decision": RateLimitRule(requests=5, window_seconds=60),
            "player_ready": RateLimitRule(requests=10, window_seconds=60),
            "leave_game": RateLimitRule(requests=3, window_seconds=60),
            # Default for unknown events
            "default": RateLimitRule(
                requests=self.global_requests_per_minute // 2,
                window_seconds=60,
                burst_multiplier=self.burst_multiplier,
            ),
        }

    def validate(self) -> bool:
        """Validate configuration values."""
        errors = []

        # Check that RPM values are reasonable
        if self.global_requests_per_minute < 10:
            errors.append("Global RPM too low (< 10)")

        if self.burst_multiplier < 1.0:
            errors.append("Burst multiplier must be >= 1.0")

        if self.block_duration_seconds < 60:
            errors.append("Block duration too short (< 60s)")

        if self.grace_warning_threshold <= 0 or self.grace_warning_threshold >= 1:
            errors.append("Grace warning threshold must be between 0 and 1")

        if errors:
            print(f"Rate limit configuration errors: {', '.join(errors)}")
            return False

        return True

    def to_dict(self) -> Dict[str, any]:
        """Convert configuration to dictionary for API responses."""
        return {
            "enabled": self.enabled,
            "debug_mode": self.debug_mode,
            "global_settings": {
                "requests_per_minute": self.global_requests_per_minute,
                "burst_multiplier": self.burst_multiplier,
                "block_duration_seconds": self.block_duration_seconds,
            },
            "rest_api_limits": {
                "health": self.health_endpoint_rpm,
                "rooms": self.rooms_endpoint_rpm,
                "recovery": self.recovery_endpoint_rpm,
            },
            "websocket_limits": {
                "system": {
                    "ping": self.ws_ping_rpm,
                    "ack": self.ws_ack_rpm,
                    "sync": self.ws_sync_rpm,
                },
                "lobby": {
                    "room_list": self.ws_room_list_rpm,
                    "create_room": self.ws_create_room_rpm,
                    "join_room": self.ws_join_room_rpm,
                },
                "game": {
                    "declare": self.ws_declare_rpm,
                    "play": self.ws_play_rpm,
                    "redeal": self.ws_redeal_rpm,
                    "start_game": self.ws_start_game_rpm,
                },
            },
            "grace_period": {
                "warning_threshold": self.grace_warning_threshold,
                "multiplier": self.grace_multiplier,
                "duration_seconds": self.grace_duration_seconds,
            },
        }


# Global configuration instance
_config: Optional[RateLimitConfig] = None


def get_rate_limit_config() -> RateLimitConfig:
    """Get the global rate limit configuration instance."""
    global _config
    if _config is None:
        _config = RateLimitConfig()
        if not _config.validate():
            print("Warning: Rate limit configuration validation failed, using defaults")
    return _config


def reload_config():
    """Reload configuration from environment variables."""
    global _config
    _config = RateLimitConfig()
    if not _config.validate():
        print("Warning: Rate limit configuration validation failed after reload")
    return _config
