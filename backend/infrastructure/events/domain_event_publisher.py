# infrastructure/events/domain_event_publisher.py
"""
Enhanced domain event publisher that integrates with event bus.
"""

import logging
from typing import Optional, List, Dict, Any
from collections import defaultdict

from domain.interfaces.event_publisher import EventPublisher, EventSubscriber
from domain.events.base import DomainEvent
from application.events.event_bus import EventBus
from infrastructure.persistence.event_publisher_impl import InMemoryEventPublisher

logger = logging.getLogger(__name__)


class DomainEventPublisher(EventPublisher):
    """
    Enhanced event publisher that combines in-memory publishing
    with event bus integration.
    
    This provides both synchronous (in-process) and asynchronous
    (event bus) event handling.
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        enable_sync: bool = True,
        enable_async: bool = True
    ):
        """
        Initialize publisher.
        
        Args:
            event_bus: Optional event bus for async publishing
            enable_sync: Enable synchronous subscribers
            enable_async: Enable async event bus publishing
        """
        self._in_memory_publisher = InMemoryEventPublisher()
        self._event_bus = event_bus
        self._enable_sync = enable_sync
        self._enable_async = enable_async
        self._metrics = PublisherMetrics()
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish event to both sync subscribers and event bus.
        
        Args:
            event: Event to publish
        """
        logger.debug(
            f"Publishing {event.__class__.__name__} "
            f"(sync={self._enable_sync}, async={self._enable_async})"
        )
        
        errors = []
        
        # Synchronous publishing (in-process)
        if self._enable_sync:
            try:
                await self._in_memory_publisher.publish(event)
                self._metrics.sync_published += 1
            except Exception as e:
                logger.error(f"Sync publishing failed: {str(e)}", exc_info=True)
                errors.append(e)
                self._metrics.sync_errors += 1
        
        # Asynchronous publishing (event bus)
        if self._enable_async and self._event_bus:
            try:
                await self._event_bus.publish(event)
                self._metrics.async_published += 1
            except Exception as e:
                logger.error(f"Async publishing failed: {str(e)}", exc_info=True)
                errors.append(e)
                self._metrics.async_errors += 1
        
        # If all publishing methods failed, log but don't raise
        if errors and len(errors) == (int(self._enable_sync) + int(self._enable_async)):
            logger.error(
                f"All publishing methods failed for {event.__class__.__name__}",
                extra={"errors": errors}
            )
    
    def subscribe(self, event_type: type, subscriber: EventSubscriber) -> None:
        """
        Subscribe to synchronous events.
        
        Args:
            event_type: Type of events to subscribe to
            subscriber: Subscriber to notify
        """
        self._in_memory_publisher.subscribe(event_type, subscriber)
    
    def unsubscribe(self, event_type: type, subscriber: EventSubscriber) -> None:
        """
        Unsubscribe from synchronous events.
        
        Args:
            event_type: Type of events to unsubscribe from
            subscriber: Subscriber to remove
        """
        self._in_memory_publisher.unsubscribe(event_type, subscriber)
    
    def enable_sync_publishing(self) -> None:
        """Enable synchronous publishing."""
        self._enable_sync = True
        logger.info("Synchronous publishing enabled")
    
    def disable_sync_publishing(self) -> None:
        """Disable synchronous publishing."""
        self._enable_sync = False
        logger.info("Synchronous publishing disabled")
    
    def enable_async_publishing(self) -> None:
        """Enable asynchronous publishing."""
        self._enable_async = True
        logger.info("Asynchronous publishing enabled")
    
    def disable_async_publishing(self) -> None:
        """Disable asynchronous publishing."""
        self._enable_async = False
        logger.info("Asynchronous publishing disabled")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get publishing metrics."""
        return {
            "sync_published": self._metrics.sync_published,
            "sync_errors": self._metrics.sync_errors,
            "async_published": self._metrics.async_published,
            "async_errors": self._metrics.async_errors,
            "total_published": self._metrics.sync_published + self._metrics.async_published,
            "total_errors": self._metrics.sync_errors + self._metrics.async_errors
        }


class PublisherMetrics:
    """Metrics for event publisher."""
    
    def __init__(self):
        self.sync_published = 0
        self.sync_errors = 0
        self.async_published = 0
        self.async_errors = 0