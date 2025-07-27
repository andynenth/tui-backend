"""
Tests for the persistence abstraction layer.

Tests the adapter pattern, hybrid repository, and factory implementation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

from backend.infrastructure.persistence.base import (
    IPersistenceAdapter,
    PersistenceConfig,
    PersistenceBackend
)
from backend.infrastructure.persistence.memory_adapter import MemoryAdapter
from backend.infrastructure.persistence.hybrid_repository import (
    HybridRepository,
    TimeBasedArchivalPolicy,
    CompletionBasedArchivalPolicy
)
from backend.infrastructure.persistence.repository_factory import (
    RepositoryFactory,
    RepositoryConfig,
    RepositoryStrategy,
    get_repository_factory
)


# Test entity classes

@dataclass
class TestEntity:
    """Simple test entity."""
    id: str
    name: str
    value: int
    created_at: datetime = None
    is_completed: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class GameEntity:
    """Test entity that simulates a game."""
    id: str
    room_id: str
    players: list
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    
    def complete(self):
        """Mark game as completed."""
        self.is_completed = True
        self.completed_at = datetime.utcnow()


# Mock persistent adapter for testing

class MockPersistentAdapter(IPersistenceAdapter[TestEntity]):
    """Mock adapter that simulates persistent storage."""
    
    def __init__(self, config: PersistenceConfig):
        self.config = config
        self._storage: Dict[str, TestEntity] = {}
        self._save_count = 0
        self._get_count = 0
        self._delete_count = 0
    
    async def get(self, key: str) -> Optional[TestEntity]:
        self._get_count += 1
        # Simulate network delay
        await asyncio.sleep(0.001)
        return self._storage.get(key)
    
    async def get_many(self, keys: list) -> Dict[str, TestEntity]:
        self._get_count += len(keys)
        await asyncio.sleep(0.001 * len(keys))
        return {k: v for k, v in self._storage.items() if k in keys}
    
    async def save(self, key: str, entity: TestEntity) -> None:
        self._save_count += 1
        await asyncio.sleep(0.002)
        self._storage[key] = entity
    
    async def save_many(self, entities: Dict[str, TestEntity]) -> None:
        self._save_count += len(entities)
        await asyncio.sleep(0.002 * len(entities))
        self._storage.update(entities)
    
    async def delete(self, key: str) -> bool:
        self._delete_count += 1
        await asyncio.sleep(0.001)
        if key in self._storage:
            del self._storage[key]
            return True
        return False
    
    async def delete_many(self, keys: list) -> int:
        self._delete_count += len(keys)
        await asyncio.sleep(0.001 * len(keys))
        deleted = 0
        for key in keys:
            if key in self._storage:
                del self._storage[key]
                deleted += 1
        return deleted
    
    async def exists(self, key: str) -> bool:
        return key in self._storage
    
    async def list_keys(self, prefix: Optional[str] = None) -> list:
        if prefix:
            return [k for k in self._storage.keys() if k.startswith(prefix)]
        return list(self._storage.keys())
    
    async def clear(self) -> None:
        self._storage.clear()
    
    async def get_metrics(self) -> Dict[str, Any]:
        return {
            'total_items': len(self._storage),
            'save_count': self._save_count,
            'get_count': self._get_count,
            'delete_count': self._delete_count
        }


# Tests for MemoryAdapter

class TestMemoryAdapter:
    """Test the in-memory persistence adapter."""
    
    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Test basic CRUD operations."""
        config = PersistenceConfig(
            backend=PersistenceBackend.MEMORY,
            options={'max_items': 100}
        )
        adapter = MemoryAdapter[TestEntity](config)
        
        # Test save and get
        entity = TestEntity(id="1", name="test", value=42)
        await adapter.save("1", entity)
        
        retrieved = await adapter.get("1")
        assert retrieved is not None
        assert retrieved.id == "1"
        assert retrieved.name == "test"
        assert retrieved.value == 42
        
        # Test update
        entity.value = 100
        await adapter.save("1", entity)
        
        updated = await adapter.get("1")
        assert updated.value == 100
        
        # Test delete
        deleted = await adapter.delete("1")
        assert deleted is True
        
        assert await adapter.get("1") is None
    
    @pytest.mark.asyncio
    async def test_batch_operations(self):
        """Test batch operations."""
        adapter = MemoryAdapter[TestEntity]()
        
        # Save many
        entities = {
            str(i): TestEntity(id=str(i), name=f"test{i}", value=i)
            for i in range(10)
        }
        await adapter.save_many(entities)
        
        # Get many
        keys = ["0", "5", "9"]
        results = await adapter.get_many(keys)
        assert len(results) == 3
        assert results["0"].value == 0
        assert results["5"].value == 5
        assert results["9"].value == 9
        
        # Delete many
        deleted = await adapter.delete_many(["1", "2", "3"])
        assert deleted == 3
        
        remaining = await adapter.list_keys()
        assert len(remaining) == 7
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction when capacity is reached."""
        config = PersistenceConfig(
            backend=PersistenceBackend.MEMORY,
            options={'max_items': 3}
        )
        adapter = MemoryAdapter[TestEntity](config)
        
        # Fill to capacity
        for i in range(3):
            await adapter.save(str(i), TestEntity(id=str(i), name=f"test{i}", value=i))
        
        # Access middle item to make it most recent
        await adapter.get("1")
        
        # Add new item - should evict "0" (least recently used)
        await adapter.save("3", TestEntity(id="3", name="test3", value=3))
        
        # Check eviction
        assert await adapter.get("0") is None  # Evicted
        assert await adapter.get("1") is not None  # Still there
        assert await adapter.get("2") is not None  # Still there
        assert await adapter.get("3") is not None  # New item
    
    @pytest.mark.asyncio
    async def test_query_operations(self):
        """Test query functionality."""
        adapter = MemoryAdapter[TestEntity]()
        
        # Add test data
        for i in range(10):
            entity = TestEntity(
                id=str(i),
                name=f"test{i % 3}",  # Groups: test0, test1, test2
                value=i * 10
            )
            await adapter.save(str(i), entity)
        
        # Query by filter
        results = await adapter.query({"name": "test1"})
        assert len(results) == 4  # Items 1, 4, 7
        assert all(e.name == "test1" for e in results)
        
        # Query with sorting
        sorted_results = await adapter.query_sorted(
            {},  # No filter
            "value",
            ascending=False,
            limit=3
        )
        assert len(sorted_results) == 3
        assert sorted_results[0].value == 90
        assert sorted_results[1].value == 80
        assert sorted_results[2].value == 70
        
        # Count
        count = await adapter.count({"name": "test0"})
        assert count == 4  # Items 0, 3, 6, 9


# Tests for HybridRepository

class TestHybridRepository:
    """Test the hybrid repository implementation."""
    
    @pytest.mark.asyncio
    async def test_memory_first_access(self):
        """Test that memory is checked first for performance."""
        memory_adapter = MemoryAdapter[TestEntity]()
        persistent_adapter = MockPersistentAdapter(
            PersistenceConfig(backend=PersistenceBackend.MEMORY)
        )
        
        repo = HybridRepository(
            memory_adapter=memory_adapter,
            persistent_adapter=persistent_adapter
        )
        
        # Save to repository
        entity = TestEntity(id="1", name="test", value=42)
        await repo.save("1", entity)
        
        # Get should hit memory (fast path)
        retrieved = await repo.get("1")
        assert retrieved is not None
        assert retrieved.id == "1"
        
        # Check that persistent adapter wasn't accessed
        metrics = await persistent_adapter.get_metrics()
        assert metrics['get_count'] == 0
    
    @pytest.mark.asyncio
    async def test_fallback_to_persistent(self):
        """Test fallback to persistent storage when not in memory."""
        memory_adapter = MemoryAdapter[TestEntity]()
        persistent_adapter = MockPersistentAdapter(
            PersistenceConfig(backend=PersistenceBackend.MEMORY)
        )
        
        # Pre-populate persistent storage
        entity = TestEntity(id="1", name="test", value=42)
        await persistent_adapter.save("1", entity)
        
        repo = HybridRepository(
            memory_adapter=memory_adapter,
            persistent_adapter=persistent_adapter
        )
        
        # Get should fall back to persistent
        retrieved = await repo.get("1")
        assert retrieved is not None
        assert retrieved.id == "1"
        
        # Check that persistent adapter was accessed
        metrics = await persistent_adapter.get_metrics()
        assert metrics['get_count'] == 1
        
        # Second get should hit memory (cached)
        await repo.get("1")
        metrics = await persistent_adapter.get_metrics()
        assert metrics['get_count'] == 1  # No additional persistent access
    
    @pytest.mark.asyncio
    async def test_completion_based_archival(self):
        """Test archival based on completion status."""
        memory_adapter = MemoryAdapter[GameEntity]()
        persistent_adapter = MockPersistentAdapter(
            PersistenceConfig(backend=PersistenceBackend.MEMORY)
        )
        
        policy = CompletionBasedArchivalPolicy('is_completed')
        repo = HybridRepository(
            memory_adapter=memory_adapter,
            persistent_adapter=persistent_adapter,
            archival_policy=policy,
            archive_interval=0.1  # Fast for testing
        )
        
        # Start background archival
        await repo.start()
        
        try:
            # Create and save active game
            game = GameEntity(id="game1", room_id="room1", players=["p1", "p2"])
            await repo.save("game1", game)
            
            # Complete the game
            game.complete()
            await repo.save("game1", game)
            
            # Wait for archival
            await asyncio.sleep(0.2)
            
            # Check that game was archived
            metrics = await persistent_adapter.get_metrics()
            assert metrics['save_count'] > 0
            
            # Game should still be accessible
            retrieved = await repo.get("game1")
            assert retrieved is not None
            assert retrieved.is_completed is True
            
        finally:
            await repo.stop()
    
    @pytest.mark.asyncio
    async def test_time_based_archival(self):
        """Test archival based on idle time."""
        memory_adapter = MemoryAdapter[TestEntity]()
        persistent_adapter = MockPersistentAdapter(
            PersistenceConfig(backend=PersistenceBackend.MEMORY)
        )
        
        # Very short idle time for testing
        policy = TimeBasedArchivalPolicy(max_idle_time=timedelta(seconds=0.1))
        repo = HybridRepository(
            memory_adapter=memory_adapter,
            persistent_adapter=persistent_adapter,
            archival_policy=policy,
            archive_interval=0.1
        )
        
        await repo.start()
        
        try:
            # Save entity
            entity = TestEntity(id="1", name="test", value=42)
            await repo.save("1", entity)
            
            # Access immediately - should not archive
            await repo.get("1")
            await asyncio.sleep(0.2)
            
            metrics = await persistent_adapter.get_metrics()
            assert metrics['save_count'] == 0  # Not archived yet
            
            # Wait for idle time to pass
            await asyncio.sleep(0.3)
            
            # Should be archived now
            metrics = await persistent_adapter.get_metrics()
            assert metrics['save_count'] > 0
            
        finally:
            await repo.stop()


# Tests for RepositoryFactory

class TestRepositoryFactory:
    """Test the repository factory."""
    
    def test_default_configurations(self):
        """Test that default configurations are set up correctly."""
        factory = get_repository_factory()
        
        # Room repository should be memory-only
        room_repo = factory.create_repository('room', TestEntity)
        assert isinstance(room_repo._adapter, MemoryAdapter)
        
        # Game repository should be hybrid
        game_repo = factory.create_repository('game', GameEntity)
        assert isinstance(game_repo, HybridRepository)
    
    def test_custom_configuration(self):
        """Test creating repository with custom configuration."""
        factory = RepositoryFactory()
        
        config = RepositoryConfig(
            strategy=RepositoryStrategy.MEMORY_ONLY,
            memory_config=PersistenceConfig(
                backend=PersistenceBackend.MEMORY,
                options={'max_items': 50}
            )
        )
        
        repo = factory.create_repository('custom', TestEntity, config)
        assert isinstance(repo._adapter, MemoryAdapter)
    
    def test_adapter_registration(self):
        """Test registering custom adapters."""
        factory = RepositoryFactory()
        
        # Register mock adapter
        factory.register_adapter(
            PersistenceBackend.POSTGRESQL,
            MockPersistentAdapter
        )
        
        # Create repository with custom backend
        config = RepositoryConfig(
            strategy=RepositoryStrategy.PERSISTENT_ONLY,
            persistent_config=PersistenceConfig(
                backend=PersistenceBackend.POSTGRESQL
            )
        )
        
        repo = factory.create_repository('test', TestEntity, config)
        assert isinstance(repo._adapter, MockPersistentAdapter)
    
    @pytest.mark.asyncio
    async def test_repository_metrics(self):
        """Test repository metrics collection."""
        factory = get_repository_factory()
        
        repo = factory.create_repository('test', TestEntity)
        
        # Perform some operations
        for i in range(5):
            await repo.save(str(i), TestEntity(id=str(i), name=f"test{i}", value=i))
        
        # Get metrics
        metrics = await repo.get_metrics()
        assert 'adapter_type' in metrics
        assert 'adapter_metrics' in metrics
        assert metrics['adapter_metrics']['total_items'] == 5