"""
Configuration for state machine event integration.

This module controls whether the state machine publishes domain events
when phase data changes occur through the enterprise architecture.
"""

import os
import logging

logger = logging.getLogger(__name__)


class StateEventConfig:
    """
    Configuration for state machine event publishing.
    
    Controls whether update_phase_data() and broadcast_custom_event()
    automatically publish domain events.
    """
    
    def __init__(self):
        # Check environment variable for enabling events
        self.events_enabled = self._get_bool_env("STATE_EVENTS_ENABLED", False)
        
        # Specific event types to enable/disable
        self.phase_change_events = self._get_bool_env("STATE_PHASE_CHANGE_EVENTS", True)
        self.turn_events = self._get_bool_env("STATE_TURN_EVENTS", True)
        self.scoring_events = self._get_bool_env("STATE_SCORING_EVENTS", True)
        self.custom_events = self._get_bool_env("STATE_CUSTOM_EVENTS", True)
        
        # Log configuration
        if self.events_enabled:
            logger.info("State machine event publishing ENABLED")
            logger.info(f"  Phase changes: {self.phase_change_events}")
            logger.info(f"  Turn events: {self.turn_events}")
            logger.info(f"  Scoring events: {self.scoring_events}")
            logger.info(f"  Custom events: {self.custom_events}")
        else:
            logger.info("State machine event publishing DISABLED")
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean from environment."""
        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        return default
    
    def enable(self):
        """Enable all event publishing."""
        self.events_enabled = True
        logger.info("State machine event publishing enabled")
    
    def disable(self):
        """Disable all event publishing."""
        self.events_enabled = False
        logger.info("State machine event publishing disabled")


# Global configuration instance
state_event_config = StateEventConfig()


def initialize_state_event_system():
    """
    Initialize the state machine event system.
    
    This should be called during application startup to:
    1. Enable the event publisher if configured
    2. Initialize the broadcast handler
    3. Set up event-to-broadcast mappings
    """
    if state_event_config.events_enabled:
        # Enable the state event publisher
        from .event_integration import get_state_event_publisher
        publisher = get_state_event_publisher()
        publisher.enable()
        
        # Initialize the broadcast handler
        try:
            from backend.infrastructure.events.integrated_broadcast_handler import (
                get_broadcast_handler
            )
            # This will initialize the broadcast handler and subscribe to events
            handler = get_broadcast_handler()
            logger.info("Broadcast handler initialized for state events")
        except Exception as e:
            logger.error(f"Failed to initialize broadcast handler: {e}")
        
        logger.info("State machine event system initialized")
    else:
        logger.info("State machine event system not enabled")


def is_state_events_enabled() -> bool:
    """Check if state event publishing is enabled."""
    return state_event_config.events_enabled