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
    CacheService,
)

from infrastructure.unit_of_work import InMemoryUnitOfWork
from infrastructure.events.application_event_publisher import (
    WebSocketEventPublisher,
    CompositeEventPublisher,
    EventStorePublisher,
)
from infrastructure.services import (
    WebSocketNotificationService,
    SimpleBotService,
    InMemoryCacheService,
    ConsoleMetricsCollector,
)
from infrastructure.feature_flags import get_feature_flags
from infrastructure.state_persistence.persistence_manager import (
    StatePersistenceManager,
    PersistenceConfig,
    PersistenceStrategy,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


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
        self.register_factory(UnitOfWork, lambda: InMemoryUnitOfWork())

        # Event Publisher - use composite if event sourcing is enabled
        self.register_factory(EventPublisher, self._create_event_publisher)

        # Services
        self.register_factory(
            NotificationService, lambda: WebSocketNotificationService()
        )

        self.register_factory(BotService, lambda: SimpleBotService())

        self.register_factory(CacheService, lambda: InMemoryCacheService())

        self.register_factory(MetricsCollector, lambda: ConsoleMetricsCollector())
        
        # State Persistence Manager
        self.register_factory(StatePersistenceManager, self._create_state_persistence_manager)

    def _create_event_publisher(self) -> EventPublisher:
        """Create the appropriate event publisher based on feature flags."""
        publishers = []

        # Always include WebSocket publisher
        publishers.append(WebSocketEventPublisher())

        # Add InMemoryEventBus for broadcast handlers
        from infrastructure.events.in_memory_event_bus import get_event_bus

        publishers.append(get_event_bus())

        # Add event store publisher if event sourcing is enabled
        if self._feature_flags.is_enabled(self._feature_flags.USE_EVENT_SOURCING):
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
    
    def _create_state_persistence_manager(self) -> Optional[StatePersistenceManager]:
        """Create state persistence manager if enabled."""
        if not self._feature_flags.is_enabled(self._feature_flags.USE_STATE_PERSISTENCE):
            return None
            
        try:
            from infrastructure.state_persistence.snapshot import StateSnapshotManager, SnapshotConfig
            from infrastructure.state_persistence.transition_log import StateTransitionLogger
            from infrastructure.state_persistence.event_sourcing import StateMachineEventStore
            
            # Configure persistence
            snapshot_enabled = self._feature_flags.is_enabled(self._feature_flags.ENABLE_STATE_SNAPSHOTS)
            recovery_enabled = self._feature_flags.is_enabled(self._feature_flags.ENABLE_STATE_RECOVERY)
            
            logger.info(f"Feature flags - snapshots: {snapshot_enabled}, recovery: {recovery_enabled}")
            
            config = PersistenceConfig(
                strategy=PersistenceStrategy.HYBRID,
                snapshot_enabled=snapshot_enabled,
                event_sourcing_enabled=True,
                recovery_enabled=recovery_enabled,
                cache_enabled=True,
                batch_operations=True,
            )
            
            # Create snapshot stores (in-memory for now)
            snapshot_stores = []
            if config.snapshot_enabled:
                from infrastructure.state_persistence.stores.in_memory import InMemorySnapshotStore
                snapshot_stores.append(InMemorySnapshotStore())
                logger.info(f"Created snapshot stores: {len(snapshot_stores)}")
                
            # Create transition logs
            transition_logs = []
            if config.event_sourcing_enabled:
                from infrastructure.state_persistence.stores.in_memory import InMemoryTransitionLog
                transition_logs.append(InMemoryTransitionLog())
                logger.info(f"Created transition logs: {len(transition_logs)}")
            
            # Create event store if needed
            event_store = None
            if config.event_sourcing_enabled:
                from infrastructure.state_persistence.stores.in_memory import InMemoryEventStore
                event_store = InMemoryEventStore()
                logger.info("Created event store")
            
            return StatePersistenceManager(
                config=config,
                snapshot_stores=snapshot_stores,
                transition_logs=transition_logs,
                event_store=event_store,
            )
            
        except Exception as e:
            logger.error(f"Failed to create StatePersistenceManager: {e}")
            return None

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
            # Cache as singleton if it's a service OR UnitOfWork
            if (
                interface.__name__.endswith("Service")
                or interface.__name__ == "UnitOfWork"
            ):
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


@lru_cache(maxsize=None)
def get_state_persistence_manager() -> Optional[StatePersistenceManager]:
    """Get a state persistence manager instance (if enabled)."""
    return get_container().get(StatePersistenceManager)
