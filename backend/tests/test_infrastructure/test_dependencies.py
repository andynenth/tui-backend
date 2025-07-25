"""
Tests for the dependency injection container.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Protocol

from infrastructure.dependencies import (
    DependencyContainer,
    get_container,
    reset_container,
    get_unit_of_work,
    get_event_publisher,
    get_notification_service,
    get_bot_service,
    get_cache_service,
    get_metrics_collector
)
from application.interfaces import (
    UnitOfWork,
    EventPublisher,
    NotificationService,
    BotService,
    CacheService,
    MetricsCollector
)


class TestDependencyContainer:
    """Test dependency container functionality."""
    
    def test_container_initialization(self):
        """Test that container initializes with defaults."""
        container = DependencyContainer()
        
        # Should have default factories registered
        uow = container.get(UnitOfWork)
        assert uow is not None
        
        publisher = container.get(EventPublisher)
        assert publisher is not None
        
        notification = container.get(NotificationService)
        assert notification is not None
    
    def test_register_factory(self):
        """Test registering custom factories."""
        container = DependencyContainer()
        
        # Define a test interface
        class TestService(Protocol):
            def test_method(self) -> str:
                ...
        
        # Create mock implementation
        mock_service = Mock()
        mock_service.test_method.return_value = "test"
        
        # Register factory
        container.register_factory(
            TestService,
            lambda: mock_service
        )
        
        # Get instance
        service = container.get(TestService)
        assert service is mock_service
        assert service.test_method() == "test"
    
    def test_register_instance(self):
        """Test registering singleton instances."""
        container = DependencyContainer()
        
        # Create singleton instance
        class SingletonService:
            def __init__(self):
                self.value = 42
        
        singleton = SingletonService()
        
        # Register instance
        container.register_instance(SingletonService, singleton)
        
        # Get instance multiple times
        instance1 = container.get(SingletonService)
        instance2 = container.get(SingletonService)
        
        # Should be same instance
        assert instance1 is instance2
        assert instance1 is singleton
        assert instance1.value == 42
    
    def test_factory_creates_new_instances(self):
        """Test that factories create new instances by default."""
        container = DependencyContainer()
        
        # Counter to track creations
        creation_count = 0
        
        class TestService:
            def __init__(self):
                nonlocal creation_count
                creation_count += 1
                self.id = creation_count
        
        # Register factory
        container.register_factory(
            TestService,
            lambda: TestService()
        )
        
        # Get multiple instances
        instance1 = container.get(TestService)
        instance2 = container.get(TestService)
        
        # Should be different instances
        assert instance1 is not instance2
        assert instance1.id == 1
        assert instance2.id == 2
    
    def test_service_singleton_behavior(self):
        """Test that services are cached as singletons."""
        container = DependencyContainer()
        
        # Services (ending with 'Service') should be cached
        service1 = container.get(NotificationService)
        service2 = container.get(NotificationService)
        
        assert service1 is service2
    
    def test_missing_implementation_error(self):
        """Test error when no implementation registered."""
        container = DependencyContainer()
        
        # Clear defaults for test
        container._factories.clear()
        container._instances.clear()
        
        class UnregisteredService:
            pass
        
        with pytest.raises(ValueError, match="No implementation registered"):
            container.get(UnregisteredService)
    
    def test_container_reset(self):
        """Test resetting the container."""
        container = DependencyContainer()
        
        # Add custom instance
        class CustomService:
            pass
        
        custom = CustomService()
        container.register_instance(CustomService, custom)
        
        # Get service to cache it
        notification = container.get(NotificationService)
        
        # Reset container
        container.reset()
        
        # Custom instance should be gone
        with pytest.raises(ValueError):
            container.get(CustomService)
        
        # Default factories should be restored
        new_notification = container.get(NotificationService)
        assert new_notification is not notification  # New instance
    
    def test_event_publisher_creation_with_feature_flags(self):
        """Test event publisher creation based on feature flags."""
        container = DependencyContainer()
        
        # Mock feature flags
        mock_flags = Mock()
        mock_flags.USE_EVENT_SOURCING = 'use_event_sourcing'
        mock_flags.is_enabled.return_value = False
        
        container._feature_flags = mock_flags
        
        # Get publisher - should be WebSocket only
        publisher = container.get(EventPublisher)
        
        # Check it's not composite
        assert not hasattr(publisher, '_publishers')
        
        # Enable event sourcing
        mock_flags.is_enabled.return_value = True
        
        # Reset to clear cache
        container._instances.clear()
        
        # Get publisher - should be composite
        with patch('infrastructure.dependencies.event_store', Mock()):
            publisher = container.get(EventPublisher)
            # Would be CompositeEventPublisher if event store available


class TestGlobalContainer:
    """Test global container functions."""
    
    def test_get_container_singleton(self):
        """Test that get_container returns singleton."""
        container1 = get_container()
        container2 = get_container()
        
        assert container1 is container2
    
    def test_reset_container(self):
        """Test resetting global container."""
        # Get initial container
        container = get_container()
        
        # Add custom registration
        class TestService:
            pass
        
        container.register_instance(TestService, TestService())
        
        # Reset
        reset_container()
        
        # Should still work but custom registration gone
        new_container = get_container()
        assert new_container is container  # Same instance
        
        with pytest.raises(ValueError):
            new_container.get(TestService)
    
    @patch('infrastructure.dependencies.get_container')
    def test_convenience_functions(self, mock_get_container):
        """Test convenience getter functions."""
        mock_container = Mock()
        mock_get_container.return_value = mock_container
        
        # Mock return values
        mock_uow = Mock(spec=UnitOfWork)
        mock_publisher = Mock(spec=EventPublisher)
        mock_notification = Mock(spec=NotificationService)
        mock_bot = Mock(spec=BotService)
        mock_cache = Mock(spec=CacheService)
        mock_metrics = Mock(spec=MetricsCollector)
        
        mock_container.get.side_effect = lambda interface: {
            UnitOfWork: mock_uow,
            EventPublisher: mock_publisher,
            NotificationService: mock_notification,
            BotService: mock_bot,
            CacheService: mock_cache,
            MetricsCollector: mock_metrics
        }[interface]
        
        # Test each convenience function
        assert get_unit_of_work() is mock_uow
        assert get_event_publisher() is mock_publisher
        assert get_notification_service() is mock_notification
        assert get_bot_service() is mock_bot
        assert get_cache_service() is mock_cache
        assert get_metrics_collector() is mock_metrics
        
        # Should use container.get
        assert mock_container.get.call_count == 6
    
    def test_lru_cache_on_getters(self):
        """Test that getters use LRU cache."""
        # Clear any existing cache
        get_unit_of_work.cache_clear()
        
        # First call
        uow1 = get_unit_of_work()
        
        # Second call should return cached instance
        uow2 = get_unit_of_work()
        
        assert uow1 is uow2
        
        # Check cache info
        cache_info = get_unit_of_work.cache_info()
        assert cache_info.hits == 1
        assert cache_info.misses == 1


class TestDependencyIntegration:
    """Test integration of dependencies."""
    
    def test_full_dependency_graph(self):
        """Test that all dependencies can be resolved."""
        container = get_container()
        
        # Get all main dependencies
        uow = container.get(UnitOfWork)
        publisher = container.get(EventPublisher)
        notification = container.get(NotificationService)
        bot = container.get(BotService)
        cache = container.get(CacheService)
        metrics = container.get(MetricsCollector)
        
        # All should be non-null
        assert all([uow, publisher, notification, bot, cache, metrics])
        
        # Test they implement expected interfaces
        # UnitOfWork
        assert hasattr(uow, 'games')
        assert hasattr(uow, 'rooms')
        assert hasattr(uow, 'commit')
        assert hasattr(uow, 'rollback')
        
        # EventPublisher
        assert hasattr(publisher, 'publish')
        
        # NotificationService
        assert hasattr(notification, 'notify_player')
        assert hasattr(notification, 'notify_room')
        
        # BotService
        assert hasattr(bot, 'should_bot_play')
        assert hasattr(bot, 'get_bot_decision')
        
        # CacheService
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        
        # MetricsCollector
        assert hasattr(metrics, 'increment')
        assert hasattr(metrics, 'timing')