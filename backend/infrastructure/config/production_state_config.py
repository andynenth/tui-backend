"""
Production configuration for state persistence.

This module defines production-ready settings for the state management system,
including persistence strategies, retention policies, and performance optimizations.
"""

import os
from datetime import timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from infrastructure.state_persistence.persistence_manager import (
    PersistenceConfig,
    PersistenceStrategy,
    AutoPersistencePolicy,
)
from infrastructure.state_persistence.recovery import RecoveryMode
from infrastructure.state_persistence.snapshot import SnapshotConfig


@dataclass
class ProductionStateConfig:
    """Production configuration for state persistence."""
    
    # Environment-based configuration
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "production"))
    
    # Storage backend configuration
    storage_backend: str = field(default_factory=lambda: os.getenv("STATE_STORAGE_BACKEND", "redis"))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    dynamodb_table: str = field(default_factory=lambda: os.getenv("DYNAMODB_STATE_TABLE", "game-states"))
    
    # Performance settings
    connection_pool_size: int = field(default_factory=lambda: int(os.getenv("STATE_POOL_SIZE", "20")))
    connection_timeout: int = field(default_factory=lambda: int(os.getenv("STATE_CONN_TIMEOUT", "5")))
    operation_timeout: int = field(default_factory=lambda: int(os.getenv("STATE_OP_TIMEOUT", "30")))
    
    # Retention policies
    snapshot_retention_days: int = field(default_factory=lambda: int(os.getenv("SNAPSHOT_RETENTION_DAYS", "7")))
    event_retention_days: int = field(default_factory=lambda: int(os.getenv("EVENT_RETENTION_DAYS", "30")))
    completed_game_retention_hours: int = field(default_factory=lambda: int(os.getenv("COMPLETED_GAME_RETENTION_HOURS", "24")))
    
    # Feature flags
    enable_compression: bool = field(default_factory=lambda: os.getenv("STATE_COMPRESSION", "true").lower() == "true")
    enable_encryption: bool = field(default_factory=lambda: os.getenv("STATE_ENCRYPTION", "false").lower() == "true")
    enable_async_snapshots: bool = field(default_factory=lambda: os.getenv("ASYNC_SNAPSHOTS", "true").lower() == "true")


def get_production_persistence_config() -> PersistenceConfig:
    """
    Get production persistence configuration.
    
    Returns optimized settings for production use with:
    - Hybrid persistence strategy for reliability and performance
    - Appropriate snapshot intervals
    - Memory-efficient settings
    - Production-ready timeouts
    """
    prod_config = ProductionStateConfig()
    
    return PersistenceConfig(
        # Use hybrid strategy for production (best of both worlds)
        strategy=PersistenceStrategy.HYBRID,
        
        # Snapshot configuration
        snapshot_enabled=True,
        snapshot_interval=timedelta(minutes=5),  # Snapshot every 5 minutes
        max_snapshots_per_state=5,  # Keep last 5 snapshots per game
        snapshot_on_shutdown=True,  # Always snapshot on graceful shutdown
        
        # Event sourcing configuration
        event_sourcing_enabled=True,
        max_events_per_state=5000,  # Limit events to prevent unbounded growth
        compact_events_after=1000,  # Compact after 1000 events
        
        # Recovery configuration
        recovery_enabled=True,
        recovery_mode=RecoveryMode.LATEST,  # Always recover from latest state
        auto_recovery=True,  # Automatically recover on startup
        
        # Performance configuration
        cache_enabled=True,
        cache_size=500,  # Cache last 500 active games
        batch_operations=True,
        batch_size=50,  # Batch up to 50 operations
        
        # Archival configuration
        archive_completed_states=True,
        archive_after=timedelta(hours=prod_config.completed_game_retention_hours),
        compression_enabled=prod_config.enable_compression,
    )


def get_production_persistence_policy() -> AutoPersistencePolicy:
    """
    Get production auto-persistence policy.
    
    Returns a policy optimized for production with:
    - Persistence on all significant events
    - Reasonable intervals to prevent excessive writes
    """
    return AutoPersistencePolicy(
        persist_on_transition=True,  # Persist all state transitions
        persist_on_update=False,  # Don't persist every update (too frequent)
        persist_on_error=True,  # Always persist on errors for debugging
        persist_interval=timedelta(seconds=30),  # Auto-persist every 30 seconds
        persist_on_phase_change=True,  # Always persist phase changes
    )


def get_production_snapshot_config() -> SnapshotConfig:
    """
    Get production snapshot configuration.
    
    Returns settings optimized for production snapshots.
    """
    prod_config = ProductionStateConfig()
    
    return SnapshotConfig(
        max_snapshots=5,  # Keep 5 snapshots per game
        snapshot_interval=timedelta(minutes=5),
        compression_enabled=prod_config.enable_compression,
        encryption_enabled=prod_config.enable_encryption,
        auto_snapshot=True,
        snapshot_on_error=True,  # Always snapshot on errors
        async_snapshots=prod_config.enable_async_snapshots,
    )


def get_state_validation_rules() -> Dict[str, Any]:
    """
    Get production state validation rules.
    
    Returns validation rules to ensure state integrity.
    """
    return {
        "max_players_per_game": 8,
        "min_players_per_game": 2,
        "valid_game_phases": [
            "NOT_STARTED", "PREPARATION", "DECLARATION", 
            "TURN", "SCORING", "GAME_OVER"
        ],
        "max_game_duration_hours": 4,
        "require_player_ids": True,
        "require_room_id": True,
        "require_timestamps": True,
        "validate_phase_transitions": True,
        "allowed_phase_transitions": {
            "NOT_STARTED": ["PREPARATION"],
            "PREPARATION": ["DECLARATION"],
            "DECLARATION": ["TURN"],
            "TURN": ["SCORING", "TURN"],  # Turn can repeat
            "SCORING": ["TURN", "GAME_OVER"],
            "GAME_OVER": [],  # Terminal state
        }
    }


def get_connection_pool_config() -> Dict[str, Any]:
    """
    Get connection pool configuration for state storage.
    
    Returns settings for efficient connection management.
    """
    prod_config = ProductionStateConfig()
    
    if prod_config.storage_backend == "redis":
        return {
            "max_connections": prod_config.connection_pool_size,
            "min_connections": 5,
            "connection_timeout": prod_config.connection_timeout,
            "socket_timeout": prod_config.operation_timeout,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "decode_responses": True,
        }
    elif prod_config.storage_backend == "dynamodb":
        return {
            "max_pool_connections": prod_config.connection_pool_size,
            "read_timeout": prod_config.operation_timeout,
            "connect_timeout": prod_config.connection_timeout,
            "retries": {
                "max_attempts": 3,
                "mode": "adaptive"
            }
        }
    else:
        # In-memory fallback (for testing)
        return {
            "max_connections": 1,
            "connection_timeout": 1,
        }


def get_monitoring_config() -> Dict[str, Any]:
    """
    Get monitoring configuration for state persistence.
    
    Returns settings for metrics and alerting.
    """
    return {
        "metrics_enabled": True,
        "metrics_interval": 60,  # Collect metrics every minute
        "alert_thresholds": {
            "snapshot_failure_rate": 0.05,  # Alert if > 5% failures
            "recovery_failure_rate": 0.01,  # Alert if > 1% recovery failures
            "operation_latency_p99_ms": 100,  # Alert if p99 > 100ms
            "cache_hit_rate_min": 0.8,  # Alert if cache hit rate < 80%
            "storage_connection_errors": 5,  # Alert after 5 connection errors
        },
        "metrics_to_track": [
            "state_transitions_total",
            "state_snapshots_total",
            "state_recoveries_total",
            "state_errors_total",
            "state_operation_duration_ms",
            "state_cache_hits",
            "state_cache_misses",
            "state_storage_size_bytes",
        ]
    }


# Production presets for different deployment scenarios
PRODUCTION_PRESETS = {
    "high_reliability": {
        "strategy": PersistenceStrategy.HYBRID,
        "snapshot_interval": timedelta(minutes=2),
        "max_snapshots": 10,
        "event_sourcing": True,
        "auto_recovery": True,
    },
    "high_performance": {
        "strategy": PersistenceStrategy.SNAPSHOT_ONLY,
        "snapshot_interval": timedelta(minutes=10),
        "max_snapshots": 3,
        "event_sourcing": False,
        "cache_size": 1000,
    },
    "cost_optimized": {
        "strategy": PersistenceStrategy.EVENT_SOURCED,
        "snapshot_interval": timedelta(minutes=30),
        "max_snapshots": 2,
        "compression": True,
        "archive_after": timedelta(hours=12),
    }
}


def get_production_preset(preset_name: str = "high_reliability") -> Dict[str, Any]:
    """Get a production configuration preset."""
    return PRODUCTION_PRESETS.get(preset_name, PRODUCTION_PRESETS["high_reliability"])