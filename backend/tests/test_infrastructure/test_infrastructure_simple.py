"""
Simple infrastructure tests that don't require WebSocket initialization.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from infrastructure.feature_flags import FeatureFlags
from infrastructure.services.console_metrics_collector import ConsoleMetricsCollector
from infrastructure.services.in_memory_cache_service import InMemoryCacheService
from infrastructure.repositories.in_memory_room_repository import InMemoryRoomRepository
from infrastructure.repositories.in_memory_game_repository import InMemoryGameRepository
from domain.entities import Room, Game, Player
from domain.value_objects import RoomId, GameId, PlayerId


class TestFeatureFlagsSimple:
    """Test feature flags without complex dependencies."""
    
    def test_boolean_flag(self):
        """Test simple boolean feature flag."""
        flags = FeatureFlags()
        
        # Test default flags
        assert flags.is_enabled(FeatureFlags.USE_CLEAN_ARCHITECTURE) is False
        
        # Test override
        flags.override(FeatureFlags.USE_CLEAN_ARCHITECTURE, True)
        assert flags.is_enabled(FeatureFlags.USE_CLEAN_ARCHITECTURE) is True
    
    def test_percentage_rollout(self):
        """Test percentage-based rollout."""
        flags = FeatureFlags()
        
        # Set up percentage-based flag
        flags._flags['test_percentage'] = 50
        
        # Test with multiple users
        enabled_count = 0
        for i in range(100):
            if flags.is_enabled('test_percentage', {'user_id': f'user_{i}'}):
                enabled_count += 1
        
        # Should be roughly 50% (with some variance)
        assert 30 <= enabled_count <= 70
    
    def test_list_based_flags(self):
        """Test list-based flags."""
        flags = FeatureFlags()
        
        # Set up list-based flag
        flags._flags['test_list'] = ['user1', 'user2', 'user3']
        
        # Users in list
        assert flags.is_enabled('test_list', {'user_id': 'user1'}) is True
        assert flags.is_enabled('test_list', {'user_id': 'user2'}) is True
        
        # User not in list
        assert flags.is_enabled('test_list', {'user_id': 'user4'}) is False


class TestConsoleMetrics:
    """Test console metrics collector."""
    
    def test_counter_metrics(self):
        """Test counter metric collection."""
        collector = ConsoleMetricsCollector()
        
        # Increment counter
        collector.increment('test_counter')
        collector.increment('test_counter', value=5)
        
        stats = collector.get_stats()
        assert stats['counters']['test_counter'] == 6
    
    def test_gauge_metrics(self):
        """Test gauge metric collection."""
        collector = ConsoleMetricsCollector()
        
        # Set gauge
        collector.gauge('cpu_usage', 45.5)
        collector.gauge('memory_usage', 1024.0)
        
        stats = collector.get_stats()
        assert stats['gauges']['cpu_usage']['value'] == 45.5
        assert stats['gauges']['memory_usage']['value'] == 1024.0
    
    def test_timing_metrics(self):
        """Test timing metric collection."""
        collector = ConsoleMetricsCollector()
        
        # Record timings
        collector.timing('api_call', 100.5)
        collector.timing('api_call', 200.3)
        collector.timing('api_call', 150.7)
        
        stats = collector.get_stats()
        timing = stats['timings']['api_call']
        assert timing['count'] == 3
        assert timing['min_ms'] == 100.5
        assert timing['max_ms'] == 200.3


class TestInMemoryCache:
    """Test in-memory cache service."""
    
    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Test basic cache operations."""
        cache = InMemoryCacheService()
        
        try:
            # Set and get
            await cache.set('key1', 'value1')
            value = await cache.get('key1')
            assert value == 'value1'
            
            # Exists
            assert await cache.exists('key1') is True
            assert await cache.exists('nonexistent') is False
            
            # Delete
            assert await cache.delete('key1') is True
            assert await cache.exists('key1') is False
            
        finally:
            # Cleanup
            await cache.close()
    
    @pytest.mark.asyncio
    async def test_ttl_functionality(self):
        """Test TTL functionality."""
        cache = InMemoryCacheService()
        
        try:
            # Set with very short TTL
            await cache.set('expire_key', 'expire_value', ttl=0)
            
            # Should be expired immediately
            import asyncio
            await asyncio.sleep(0.1)
            
            value = await cache.get('expire_key')
            assert value is None
            
        finally:
            await cache.close()


class TestInMemoryRepositories:
    """Test in-memory repository implementations."""
    
    @pytest.mark.asyncio
    async def test_room_repository(self):
        """Test room repository operations."""
        storage = {}
        repo = InMemoryRoomRepository(storage)
        
        # Create and add room
        room = Room(
            room_id=RoomId('room1'),
            room_code='ABC123',
            name='Test Room'
        )
        await repo.add(room)
        
        # Get by ID
        retrieved = await repo.get_by_id(RoomId('room1'))
        assert retrieved is not None
        assert retrieved.room_code == 'ABC123'
        
        # Get by code
        retrieved = await repo.get_by_code('ABC123')
        assert retrieved is not None
        assert retrieved.room_id == RoomId('room1')
        
        # Update
        room.name = 'Updated Room'
        await repo.update(room)
        
        updated = await repo.get_by_id(RoomId('room1'))
        assert updated.name == 'Updated Room'
        
        # Delete
        await repo.delete(RoomId('room1'))
        assert await repo.get_by_id(RoomId('room1')) is None
    
    @pytest.mark.asyncio
    async def test_game_repository(self):
        """Test game repository operations."""
        storage = {}
        repo = InMemoryGameRepository(storage)
        
        # Create and add game
        game = Game(
            game_id=GameId('game1'),
            room_id=RoomId('room1')
        )
        await repo.add(game)
        
        # Get by ID
        retrieved = await repo.get_by_id(GameId('game1'))
        assert retrieved is not None
        assert retrieved.room_id == RoomId('room1')
        
        # Get by room
        games = await repo.get_by_room(RoomId('room1'))
        assert len(games) == 1
        assert games[0].game_id == GameId('game1')
        
        # Get active game
        active = await repo.get_active_by_room(RoomId('room1'))
        assert active is not None
        assert active.game_id == GameId('game1')
    
    @pytest.mark.asyncio
    async def test_repository_snapshot_restore(self):
        """Test repository snapshot/restore functionality."""
        storage = {}
        repo = InMemoryRoomRepository(storage)
        
        # Add initial data
        room1 = Room(room_id=RoomId('r1'), room_code='ABC1', name='Room 1')
        room2 = Room(room_id=RoomId('r2'), room_code='ABC2', name='Room 2')
        await repo.add(room1)
        await repo.add(room2)
        
        # Take snapshot
        snapshot = repo.snapshot()
        
        # Modify data
        await repo.delete(RoomId('r1'))
        room3 = Room(room_id=RoomId('r3'), room_code='ABC3', name='Room 3')
        await repo.add(room3)
        
        # Verify modifications
        assert await repo.get_by_id(RoomId('r1')) is None
        assert await repo.get_by_id(RoomId('r3')) is not None
        
        # Restore snapshot
        repo.restore(snapshot)
        
        # Verify original state
        assert await repo.get_by_id(RoomId('r1')) is not None
        assert await repo.get_by_id(RoomId('r3')) is None


class TestDependencyInjection:
    """Test dependency injection without WebSocket dependencies."""
    
    def test_container_registration(self):
        """Test basic container registration."""
        from infrastructure.dependencies import DependencyContainer
        
        container = DependencyContainer()
        
        # Define test interface
        class TestService:
            def get_value(self):
                return 42
        
        # Register factory
        container.register_factory(TestService, lambda: TestService())
        
        # Get instance
        service = container.get(TestService)
        assert service.get_value() == 42
    
    def test_singleton_behavior(self):
        """Test singleton behavior for services."""
        from infrastructure.dependencies import DependencyContainer
        
        container = DependencyContainer()
        
        # Services should be cached
        from application.interfaces import MetricsCollector
        
        # Get multiple times
        metrics1 = container.get(MetricsCollector)
        metrics2 = container.get(MetricsCollector)
        
        # Should be same instance
        assert metrics1 is metrics2