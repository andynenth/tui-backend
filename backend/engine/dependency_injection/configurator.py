# backend/engine/dependency_injection/configurator.py

import logging
from typing import Optional, Callable

from .container import DependencyInjectionContainer, ServiceLifetime
from .interfaces import IBroadcaster, IBotNotifier, IEventStore, IGameRepository
from .services import (
    WebSocketBroadcaster,
    BotNotificationService,
    InMemoryEventStore,
    InMemoryGameRepository,
    NullBotNotifier,
    NullBroadcaster
)

logger = logging.getLogger(__name__)


class ServiceConfigurator:
    """
    🎯 **Service Configurator** - Phase 3 Dependency Injection Setup
    
    Configures the dependency injection container with all services
    needed to eliminate circular dependencies.
    
    Provides different configuration profiles:
    - Production: Full services with real implementations
    - Testing: Mock/null services for unit tests
    - Development: Configurable services for development
    """
    
    @staticmethod
    def configure_production_services(
        container: DependencyInjectionContainer,
        broadcast_callback: Optional[Callable] = None
    ) -> DependencyInjectionContainer:
        """
        Configure services for production environment.
        
        Args:
            container: The DI container to configure
            broadcast_callback: WebSocket broadcast callback function
        """
        logger.info("🏭 CONFIGURING production services")
        
        # Broadcaster service (singleton - one instance for entire app)
        container.register_singleton(
            IBroadcaster,
            implementation=WebSocketBroadcaster,
            broadcast_callback=broadcast_callback
        )
        
        # Bot notification service (singleton)
        container.register_singleton(
            IBotNotifier,
            implementation=BotNotificationService
        )
        
        # Event store (singleton - shared across all rooms)
        container.register_singleton(
            IEventStore,
            implementation=InMemoryEventStore
        )
        
        # Game repository (singleton - shared across all rooms)
        container.register_singleton(
            IGameRepository,
            implementation=InMemoryGameRepository
        )
        
        logger.info("✅ Production services configured")
        return container
    
    @staticmethod
    def configure_testing_services(
        container: DependencyInjectionContainer
    ) -> DependencyInjectionContainer:
        """
        Configure services for testing environment.
        
        Uses null/mock implementations that don't have external dependencies.
        """
        logger.info("🧪 CONFIGURING testing services")
        
        # Null broadcaster (no actual broadcasting)
        container.register_singleton(
            IBroadcaster,
            implementation=NullBroadcaster
        )
        
        # Null bot notifier (no actual bot notifications)
        container.register_singleton(
            IBotNotifier,
            implementation=NullBotNotifier
        )
        
        # In-memory event store for testing
        container.register_singleton(
            IEventStore,
            implementation=InMemoryEventStore
        )
        
        # In-memory game repository for testing
        container.register_singleton(
            IGameRepository,
            implementation=InMemoryGameRepository
        )
        
        logger.info("✅ Testing services configured")
        return container
    
    @staticmethod
    def configure_development_services(
        container: DependencyInjectionContainer,
        broadcast_callback: Optional[Callable] = None,
        enable_bots: bool = True
    ) -> DependencyInjectionContainer:
        """
        Configure services for development environment.
        
        Args:
            container: The DI container to configure
            broadcast_callback: WebSocket broadcast callback function
            enable_bots: Whether to enable bot notifications
        """
        logger.info("🔧 CONFIGURING development services")
        
        # Broadcaster service
        if broadcast_callback:
            container.register_singleton(
                IBroadcaster,
                implementation=WebSocketBroadcaster,
                broadcast_callback=broadcast_callback
            )
        else:
            container.register_singleton(
                IBroadcaster,
                implementation=NullBroadcaster
            )
        
        # Bot notification service
        if enable_bots:
            container.register_singleton(
                IBotNotifier,
                implementation=BotNotificationService
            )
        else:
            container.register_singleton(
                IBotNotifier,
                implementation=NullBotNotifier
            )
        
        # Event store (in-memory for development)
        container.register_singleton(
            IEventStore,
            implementation=InMemoryEventStore
        )
        
        # Game repository (in-memory for development)
        container.register_singleton(
            IGameRepository,
            implementation=InMemoryGameRepository
        )
        
        logger.info("✅ Development services configured")
        return container
    
    @staticmethod
    def configure_minimal_services(container: DependencyInjectionContainer) -> DependencyInjectionContainer:
        """
        Configure minimal services for basic functionality.
        
        Uses null implementations for all services. Useful for isolated testing
        or environments where only core game logic is needed.
        """
        logger.info("📦 CONFIGURING minimal services")
        
        container.register_singleton(IBroadcaster, implementation=NullBroadcaster)
        container.register_singleton(IBotNotifier, implementation=NullBotNotifier)
        container.register_singleton(IEventStore, implementation=InMemoryEventStore)
        container.register_singleton(IGameRepository, implementation=InMemoryGameRepository)
        
        logger.info("✅ Minimal services configured")
        return container
    
    @staticmethod
    def get_service_info(container: DependencyInjectionContainer) -> str:
        """Get a formatted string showing all configured services."""
        registration_info = container.get_registration_info()
        
        lines = ["🔧 CONFIGURED SERVICES:"]
        for service_name, info in registration_info.items():
            lines.append(f"   • {service_name}: {info}")
        
        return "\n".join(lines)


def setup_global_container(
    environment: str = "production",
    broadcast_callback: Optional[Callable] = None,
    **kwargs
) -> DependencyInjectionContainer:
    """
    Set up the global dependency injection container.
    
    Args:
        environment: Environment type ("production", "testing", "development", "minimal")
        broadcast_callback: WebSocket broadcast callback for production/development
        **kwargs: Additional configuration options
    
    Returns:
        Configured DI container
    """
    from .container import get_global_container
    
    container = get_global_container()
    
    if environment == "production":
        ServiceConfigurator.configure_production_services(container, broadcast_callback)
    elif environment == "testing":
        ServiceConfigurator.configure_testing_services(container)
    elif environment == "development":
        enable_bots = kwargs.get("enable_bots", True)
        ServiceConfigurator.configure_development_services(container, broadcast_callback, enable_bots)
    elif environment == "minimal":
        ServiceConfigurator.configure_minimal_services(container)
    else:
        raise ValueError(f"Unknown environment: {environment}")
    
    logger.info(f"🚀 Global DI container configured for {environment} environment")
    logger.debug(ServiceConfigurator.get_service_info(container))
    
    return container