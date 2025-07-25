"""
Dependency injection configuration for the application.

This module sets up the dependency injection container that provides
concrete implementations for all application interfaces.
"""

import logging
from typing import Dict, Any, Type, TypeVar, Optional
from functools import lru_cache

from application.interfaces import (
    UnitOfWork,
    EventPublisher,
    NotificationService,
    BotService,
    MetricsCollector,
    CacheService
)

from infrastructure.unit_of_work import InMemoryUnitOfWork
from infrastructure.events.application_event_publisher import (
    WebSocketEventPublisher,
    CompositeEventPublisher,
    EventStorePublisher
)
from infrastructure.services import (
    WebSocketNotificationService,
    SimpleBotService,
    InMemoryCacheService,
    ConsoleMetricsCollector
)
from infrastructure.feature_flags import get_feature_flags

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DependencyContainer:
    """
    Simple dependency injection container.
    
    Manages the creation and lifecycle of application dependencies.
    """
    
    def __init__(self):
        """Initialize the container."""
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, Any] = {}
        self._feature_flags = get_feature_flags()
        
        # Register default factories
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default factories for all interfaces."""
        # Unit of Work
        self.register_factory(
            UnitOfWork,
            lambda: InMemoryUnitOfWork()
        )
        
        # Event Publisher - use composite if event sourcing is enabled
        self.register_factory(
            EventPublisher,
            self._create_event_publisher
        )
        
        # Services
        self.register_factory(
            NotificationService,
            lambda: WebSocketNotificationService()
        )
        
        self.register_factory(
            BotService,
            lambda: SimpleBotService()
        )
        
        self.register_factory(
            CacheService,
            lambda: InMemoryCacheService()
        )
        
        self.register_factory(
            MetricsCollector,
            lambda: ConsoleMetricsCollector()
        )
    
    def _create_event_publisher(self) -> EventPublisher:
        """Create the appropriate event publisher based on feature flags."""
        publishers = []
        
        # Always include WebSocket publisher
        publishers.append(WebSocketEventPublisher())
        
        # Add event store publisher if event sourcing is enabled
        if self._feature_flags.is_enabled(
            self._feature_flags.USE_EVENT_SOURCING
        ):
            try:
                from api.services.event_store import event_store
                if event_store:
                    publishers.append(EventStorePublisher(event_store))
            except ImportError:
                logger.warning("Event store not available")
        
        # Return composite if multiple publishers
        if len(publishers) > 1:
            return CompositeEventPublisher(publishers)
        
        return publishers[0]
    
    def register_factory(self, interface: Type[T], factory: Any):
        """
        Register a factory function for an interface.
        
        Args:
            interface: The interface type
            factory: Factory function that creates instances
        """
        self._factories[interface] = factory
        logger.debug(f"Registered factory for {interface.__name__}")
    
    def register_instance(self, interface: Type[T], instance: T):
        """
        Register a singleton instance for an interface.
        
        Args:
            interface: The interface type
            instance: The singleton instance
        """
        self._instances[interface] = instance
        logger.debug(f"Registered instance for {interface.__name__}")
    
    def get(self, interface: Type[T]) -> T:
        """
        Get an instance of the requested interface.
        
        Args:
            interface: The interface type
            
        Returns:
            An instance implementing the interface
            
        Raises:
            ValueError: If no implementation is registered
        """
        # Check for singleton instance
        if interface in self._instances:
            return self._instances[interface]
        
        # Check for factory
        if interface in self._factories:
            instance = self._factories[interface]()
            # Cache as singleton if it's a service
            if interface.__name__.endswith('Service'):
                self._instances[interface] = instance
            return instance
        
        raise ValueError(f"No implementation registered for {interface.__name__}")
    
    def reset(self):
        """Reset the container (mainly for testing)."""
        self._instances.clear()
        self._register_defaults()


# Global container instance
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def reset_container():
    """Reset the global container (mainly for testing)."""
    global _container
    if _container:
        _container.reset()


# Convenience functions for getting dependencies

@lru_cache(maxsize=None)
def get_unit_of_work() -> UnitOfWork:
    """Get a unit of work instance."""
    return get_container().get(UnitOfWork)


@lru_cache(maxsize=None)
def get_event_publisher() -> EventPublisher:
    """Get an event publisher instance."""
    return get_container().get(EventPublisher)


@lru_cache(maxsize=None)
def get_notification_service() -> NotificationService:
    """Get a notification service instance."""
    return get_container().get(NotificationService)


@lru_cache(maxsize=None)
def get_bot_service() -> BotService:
    """Get a bot service instance."""
    return get_container().get(BotService)


@lru_cache(maxsize=None)
def get_cache_service() -> CacheService:
    """Get a cache service instance."""
    return get_container().get(CacheService)


@lru_cache(maxsize=None)
def get_metrics_collector() -> MetricsCollector:
    """Get a metrics collector instance."""
    return get_container().get(MetricsCollector)