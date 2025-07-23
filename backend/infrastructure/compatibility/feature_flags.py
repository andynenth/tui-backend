# infrastructure/compatibility/feature_flags.py
"""
Feature flags for controlling migration rollout.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlag:
    """Represents a single feature flag."""
    name: str
    enabled: bool
    description: str
    rollout_percentage: int = 100  # For gradual rollout
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeatureFlags:
    """
    Manages feature flags for the migration.
    
    Supports environment variables, config files, and runtime updates.
    """
    
    def __init__(self):
        """Initialize with default flags."""
        self._flags: Dict[str, FeatureFlag] = {
            "use_clean_architecture": FeatureFlag(
                name="use_clean_architecture",
                enabled=True,
                description="Use new clean architecture for request handling",
                rollout_percentage=100
            ),
            "use_event_system": FeatureFlag(
                name="use_event_system",
                enabled=True,
                description="Use event-driven architecture for notifications",
                rollout_percentage=100
            ),
            "use_new_state_machine": FeatureFlag(
                name="use_new_state_machine",
                enabled=False,
                description="Use refactored state machine (gradual rollout)",
                rollout_percentage=0
            ),
            "use_new_bot_system": FeatureFlag(
                name="use_new_bot_system",
                enabled=True,
                description="Use new bot strategy system",
                rollout_percentage=100
            ),
            "enable_event_sourcing": FeatureFlag(
                name="enable_event_sourcing",
                enabled=False,
                description="Store and replay events for debugging",
                rollout_percentage=0
            ),
            "enable_legacy_compatibility": FeatureFlag(
                name="enable_legacy_compatibility",
                enabled=True,
                description="Maintain backward compatibility with old API",
                rollout_percentage=100
            )
        }
        
        # Load from environment
        self._load_from_env()
        
        # Load from config file if exists
        self._load_from_file()
        
        logger.info(f"Feature flags initialized: {self.get_all_flags()}")
    
    def is_enabled(self, flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            context: Optional context for percentage rollout (e.g., user_id)
            
        Returns:
            True if enabled, False otherwise
        """
        if flag_name not in self._flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False
        
        flag = self._flags[flag_name]
        
        # Check if globally disabled
        if not flag.enabled:
            return False
        
        # Check percentage rollout if applicable
        if flag.rollout_percentage < 100 and context:
            return self._check_rollout(flag, context)
        
        return flag.enabled
    
    def _check_rollout(self, flag: FeatureFlag, context: Dict[str, Any]) -> bool:
        """Check if feature should be enabled based on rollout percentage."""
        # Simple hash-based rollout
        identifier = context.get("user_id") or context.get("room_id") or "default"
        hash_value = hash(f"{flag.name}:{identifier}") % 100
        return hash_value < flag.rollout_percentage
    
    def set_flag(self, flag_name: str, enabled: bool, rollout_percentage: int = 100):
        """
        Update a feature flag at runtime.
        
        Args:
            flag_name: Name of the flag
            enabled: Whether to enable the flag
            rollout_percentage: Percentage of users to roll out to
        """
        if flag_name in self._flags:
            self._flags[flag_name].enabled = enabled
            self._flags[flag_name].rollout_percentage = rollout_percentage
            logger.info(
                f"Feature flag updated: {flag_name} = {enabled} "
                f"(rollout: {rollout_percentage}%)"
            )
        else:
            logger.warning(f"Attempted to set unknown flag: {flag_name}")
    
    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get a specific feature flag."""
        return self._flags.get(flag_name)
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags and their states."""
        return {
            name: flag.enabled
            for name, flag in self._flags.items()
        }
    
    def _load_from_env(self):
        """Load feature flags from environment variables."""
        for flag_name in self._flags:
            env_var = f"FEATURE_{flag_name.upper()}"
            if env_var in os.environ:
                value = os.environ[env_var].lower() in ('true', '1', 'yes', 'on')
                self._flags[flag_name].enabled = value
                logger.info(f"Loaded {flag_name} from env: {value}")
    
    def _load_from_file(self, filepath: str = "feature_flags.json"):
        """Load feature flags from JSON file."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    for flag_name, config in data.items():
                        if flag_name in self._flags:
                            if isinstance(config, bool):
                                self._flags[flag_name].enabled = config
                            elif isinstance(config, dict):
                                self._flags[flag_name].enabled = config.get("enabled", False)
                                self._flags[flag_name].rollout_percentage = config.get(
                                    "rollout_percentage", 100
                                )
                logger.info(f"Loaded feature flags from {filepath}")
        except Exception as e:
            logger.error(f"Error loading feature flags from file: {e}")
    
    def save_to_file(self, filepath: str = "feature_flags.json"):
        """Save current feature flags to JSON file."""
        try:
            data = {
                name: {
                    "enabled": flag.enabled,
                    "rollout_percentage": flag.rollout_percentage,
                    "description": flag.description
                }
                for name, flag in self._flags.items()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved feature flags to {filepath}")
        except Exception as e:
            logger.error(f"Error saving feature flags: {e}")


# Global instance
_feature_flags = None


def get_feature_flags() -> FeatureFlags:
    """Get the global feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def is_feature_enabled(flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to check if a feature is enabled."""
    return get_feature_flags().is_enabled(flag_name, context)