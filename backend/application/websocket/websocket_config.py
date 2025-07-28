"""
WebSocket Configuration
Manages feature flags for WebSocket message routing
"""

import os
import logging
from enum import Enum
from typing import Set

logger = logging.getLogger(__name__)


class RoutingMode(Enum):
    """Routing mode for WebSocket messages"""
    ADAPTER = "adapter"  # Use legacy adapter system
    USE_CASE = "use_case"  # Use direct use case integration
    MIGRATION = "migration"  # Use both for gradual migration


class WebSocketConfig:
    """
    Configuration for WebSocket routing.
    Controls migration from adapter system to direct use case integration.
    """
    
    def __init__(self):
        # Load routing mode from environment
        mode_str = os.getenv("WEBSOCKET_ROUTING_MODE", "migration").lower()
        try:
            self.routing_mode = RoutingMode(mode_str)
        except ValueError:
            logger.warning(f"Invalid routing mode: {mode_str}, defaulting to migration")
            self.routing_mode = RoutingMode.MIGRATION
        
        # Events to route through use cases (for gradual migration)
        self.use_case_events: Set[str] = set()
        self._load_use_case_events()
        
        # Log configuration
        logger.info(f"WebSocket routing mode: {self.routing_mode.value}")
        if self.routing_mode == RoutingMode.MIGRATION:
            logger.info(f"Events routed to use cases: {len(self.use_case_events)}")
    
    def _load_use_case_events(self):
        """Load events to route through use cases during migration"""
        # Environment variable can contain comma-separated event names
        events_str = os.getenv("USE_CASE_EVENTS", "")
        
        if events_str:
            self.use_case_events = {e.strip() for e in events_str.split(",") if e.strip()}
        else:
            # Default migration order: start with connection and lobby events
            self.use_case_events = {
                # Connection events (simple, stateless)
                "ping", "client_ready", "ack", "sync_request",
                # Lobby events (read-only)
                "request_room_list", "get_rooms"
            }
    
    def should_use_use_case(self, event: str) -> bool:
        """
        Determine if an event should be routed through use case dispatcher.
        
        Args:
            event: The event name
            
        Returns:
            True if should use use case dispatcher, False for adapter system
        """
        if self.routing_mode == RoutingMode.USE_CASE:
            return True
        elif self.routing_mode == RoutingMode.ADAPTER:
            return False
        else:  # MIGRATION mode
            return event in self.use_case_events
    
    def add_use_case_events(self, *events: str):
        """
        Add events to route through use cases (for testing/migration).
        
        Args:
            events: Event names to add
        """
        for event in events:
            self.use_case_events.add(event)
            logger.info(f"Added {event} to use case routing")
    
    def remove_use_case_events(self, *events: str):
        """
        Remove events from use case routing (rollback).
        
        Args:
            events: Event names to remove
        """
        for event in events:
            self.use_case_events.discard(event)
            logger.info(f"Removed {event} from use case routing")
    
    def get_status(self) -> dict:
        """Get current configuration status"""
        return {
            "routing_mode": self.routing_mode.value,
            "use_case_events": sorted(list(self.use_case_events)),
            "use_case_event_count": len(self.use_case_events),
            "total_events": 22  # Total number of WebSocket events
        }


# Global config instance
websocket_config = WebSocketConfig()