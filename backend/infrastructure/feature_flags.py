"""
Feature flags system for gradual rollout of new architecture.

This module provides a centralized way to control which features
use the new clean architecture vs the legacy implementation.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class FeatureFlagType(Enum):
    """Types of feature flags."""

    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    LIST = "list"
    JSON = "json"


class FeatureFlags:
    """
    Centralized feature flags management.

    Controls the rollout of new architecture components and features.
    """

    # Feature flag definitions
    USE_CLEAN_ARCHITECTURE = "use_clean_architecture"
    USE_DOMAIN_EVENTS = "use_domain_events"
    USE_APPLICATION_LAYER = "use_application_layer"
    USE_NEW_REPOSITORIES = "use_new_repositories"
    USE_EVENT_SOURCING = "use_event_sourcing"

    # Specific feature flags for each adapter
    USE_CONNECTION_ADAPTERS = "use_connection_adapters"
    USE_ROOM_ADAPTERS = "use_room_adapters"
    USE_GAME_ADAPTERS = "use_game_adapters"
    USE_LOBBY_ADAPTERS = "use_lobby_adapters"

    # Performance and monitoring flags
    ENABLE_PERFORMANCE_MONITORING = "enable_performance_monitoring"
    ENABLE_SHADOW_MODE = "enable_shadow_mode"
    LOG_ADAPTER_CALLS = "log_adapter_calls"
    
    # State management flags
    USE_STATE_PERSISTENCE = "use_state_persistence"
    ENABLE_STATE_SNAPSHOTS = "enable_state_snapshots"
    ENABLE_STATE_RECOVERY = "enable_state_recovery"

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize feature flags.

        Args:
            config_file: Path to JSON config file (optional)
        """
        self._flags: Dict[str, Any] = {}
        self._overrides: Dict[str, Any] = {}

        # Load defaults
        self._load_defaults()

        # Load from environment
        self._load_from_env()

        # Load from config file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)

    def _load_defaults(self):
        """Load default flag values."""
        self._flags = {
            # Main architecture flags - start disabled
            self.USE_CLEAN_ARCHITECTURE: False,
            self.USE_DOMAIN_EVENTS: False,
            self.USE_APPLICATION_LAYER: False,
            self.USE_NEW_REPOSITORIES: False,
            self.USE_EVENT_SOURCING: True,
            # Individual adapter flags - can be enabled independently
            self.USE_CONNECTION_ADAPTERS: False,
            self.USE_ROOM_ADAPTERS: False,
            self.USE_GAME_ADAPTERS: False,
            self.USE_LOBBY_ADAPTERS: False,
            # Monitoring and debugging
            self.ENABLE_PERFORMANCE_MONITORING: True,
            self.ENABLE_SHADOW_MODE: True,
            self.LOG_ADAPTER_CALLS: True,
            # State management - start disabled
            self.USE_STATE_PERSISTENCE: False,
            self.ENABLE_STATE_SNAPSHOTS: False,
            self.ENABLE_STATE_RECOVERY: False,
        }

    def _load_from_env(self):
        """Load flag values from environment variables."""
        for flag_name in self._flags:
            env_name = f"FF_{flag_name.upper()}"
            env_value = os.environ.get(env_name)

            if env_value is not None:
                # Parse boolean values
                if env_value.lower() in ("true", "1", "yes", "on"):
                    self._flags[flag_name] = True
                elif env_value.lower() in ("false", "0", "no", "off"):
                    self._flags[flag_name] = False
                else:
                    # Try to parse as JSON for complex values
                    try:
                        self._flags[flag_name] = json.loads(env_value)
                    except json.JSONDecodeError:
                        self._flags[flag_name] = env_value

    def _load_from_file(self, config_file: str):
        """Load flag values from a JSON file."""
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                self._flags.update(config)
                logger.info(f"Loaded feature flags from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load feature flags from {config_file}: {e}")

    def is_enabled(
        self, flag_name: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_name: Name of the feature flag
            context: Optional context for percentage-based flags

        Returns:
            True if the feature is enabled
        """
        # Check overrides first
        if flag_name in self._overrides:
            return self._overrides[flag_name]

        # Get flag value
        value = self._flags.get(flag_name, False)

        # Handle different flag types
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)) and 0 <= value <= 100:
            # Percentage-based rollout
            if context and "user_id" in context:
                # Use consistent hashing for gradual rollout
                hash_value = hash(f"{flag_name}:{context['user_id']}") % 100
                return hash_value < value
            else:
                # Random rollout if no user context
                import random

                return random.randint(0, 99) < value
        elif isinstance(value, list) and context:
            # List-based flags (e.g., enabled for specific users/rooms)
            return any(
                context.get(key) in value for key in ["user_id", "room_id", "player_id"]
            )

        return False

    def override(self, flag_name: str, value: bool):
        """
        Override a feature flag value (useful for testing).

        Args:
            flag_name: Name of the feature flag
            value: Override value
        """
        self._overrides[flag_name] = value
        logger.info(f"Feature flag '{flag_name}' overridden to {value}")

    def clear_override(self, flag_name: str):
        """
        Clear an override for a feature flag.

        Args:
            flag_name: Name of the feature flag
        """
        if flag_name in self._overrides:
            del self._overrides[flag_name]
            logger.info(f"Override cleared for feature flag '{flag_name}'")

    def get_all_flags(self) -> Dict[str, Any]:
        """Get all current flag values including overrides."""
        result = self._flags.copy()
        result.update(self._overrides)
        return result

    def enable_clean_architecture(self, percentage: int = 100):
        """
        Enable clean architecture features.

        Args:
            percentage: Percentage of traffic to route to new architecture
        """
        if percentage == 100:
            # Full rollout
            self._flags[self.USE_CLEAN_ARCHITECTURE] = True
            self._flags[self.USE_DOMAIN_EVENTS] = True
            self._flags[self.USE_APPLICATION_LAYER] = True
            self._flags[self.USE_NEW_REPOSITORIES] = True

            # Enable all adapters
            self._flags[self.USE_CONNECTION_ADAPTERS] = True
            self._flags[self.USE_ROOM_ADAPTERS] = True
            self._flags[self.USE_GAME_ADAPTERS] = True
            self._flags[self.USE_LOBBY_ADAPTERS] = True
        else:
            # Gradual rollout
            self._flags[self.USE_CLEAN_ARCHITECTURE] = percentage
            self._flags[self.USE_DOMAIN_EVENTS] = percentage
            self._flags[self.USE_APPLICATION_LAYER] = percentage
            self._flags[self.USE_NEW_REPOSITORIES] = percentage

            # Adapters follow main flag
            self._flags[self.USE_CONNECTION_ADAPTERS] = percentage
            self._flags[self.USE_ROOM_ADAPTERS] = percentage
            self._flags[self.USE_GAME_ADAPTERS] = percentage
            self._flags[self.USE_LOBBY_ADAPTERS] = percentage

        logger.info(f"Clean architecture enabled at {percentage}% rollout")

    def disable_clean_architecture(self):
        """Disable all clean architecture features."""
        self.enable_clean_architecture(0)
        logger.info("Clean architecture disabled")


# Global feature flags instance
_feature_flags = None


def get_feature_flags() -> FeatureFlags:
    """Get the global feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        # Check for config file in environment
        config_file = os.environ.get("FEATURE_FLAGS_CONFIG")
        _feature_flags = FeatureFlags(config_file)
    return _feature_flags


def reset_feature_flags():
    """Reset the global feature flags instance (mainly for testing)."""
    global _feature_flags
    _feature_flags = None
