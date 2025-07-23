# infrastructure/events/event_bus_adapter.py
"""
Adapter that bridges the domain event publisher with the application event bus.
"""

import logging
from typing import Optional

from domain.interfaces.event_publisher import EventPublisher
from domain.events.base import DomainEvent
from application.events.event_bus import EventBus

logger = logging.getLogger(__name__)


class EventBusAdapter(EventPublisher):
    """
    Adapter that implements the domain EventPublisher interface
    by delegating to the application EventBus.
    
    This allows the domain to publish events without knowing
    about the specific event bus implementation.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize with event bus.
        
        Args:
            event_bus: The application event bus to delegate to
        """
        self._event_bus = event_bus
        self._enabled = True
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish event through the event bus.
        
        Args:
            event: Domain event to publish
        """
        if not self._enabled:
            logger.debug(f"Event publishing disabled, skipping: {event}")
            return
        
        try:
            logger.debug(
                f"Publishing {event.__class__.__name__} "
                f"for aggregate {event.aggregate_id}"
            )
            
            # Delegate to event bus
            await self._event_bus.publish(event)
            
        except Exception as e:
            logger.error(
                f"Error publishing event {event.__class__.__name__}: {str(e)}",
                exc_info=True
            )
            # Don't re-raise - event publishing should not break domain operations
    
    def enable(self) -> None:
        """Enable event publishing."""
        self._enabled = True
        logger.info("Event publishing enabled")
    
    def disable(self) -> None:
        """Disable event publishing (useful for testing)."""
        self._enabled = False
        logger.info("Event publishing disabled")