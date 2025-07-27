"""
Repository factory with strategy pattern for backend selection.

This factory creates repositories with the appropriate persistence
strategy based on configuration and entity type.
"""

from typing import Dict, Any, Optional, Type, TypeVar, Generic, Callable
from enum import Enum
from dataclasses import dataclass

from .base import (
    IPersistenceAdapter,
    BaseRepository,
    PersistenceBackend,
    PersistenceConfig
)
from .memory_adapter import MemoryAdapter
from .filesystem_adapter import FilesystemAdapter
from .hybrid_repository import (
    HybridRepository,
    ArchivalPolicy,
    TimeBasedArchivalPolicy,
    CompletionBasedArchivalPolicy
)


T = TypeVar('T')


class RepositoryStrategy(Enum):
    """Available repository strategies."""
    MEMORY_ONLY = "memory_only"          # Pure in-memory, no persistence
    HYBRID_ASYNC = "hybrid_async"        # Memory + async persistence
    PERSISTENT_ONLY = "persistent_only"  # Direct persistent storage
    CACHED = "cached"                    # Persistent with memory cache


@dataclass
class RepositoryConfig:
    """Configuration for repository creation."""
    strategy: RepositoryStrategy
    memory_config: Optional[PersistenceConfig] = None
    persistent_config: Optional[PersistenceConfig] = None
    archival_policy: Optional[ArchivalPolicy] = None
    cache_config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        # Set defaults based on strategy
        if self.strategy == RepositoryStrategy.MEMORY_ONLY:
            if not self.memory_config:
                self.memory_config = PersistenceConfig(
                    backend=PersistenceBackend.MEMORY,
                    options={'max_items': 100000}
                )
        
        elif self.strategy == RepositoryStrategy.HYBRID_ASYNC:
            if not self.memory_config:
                self.memory_config = PersistenceConfig(
                    backend=PersistenceBackend.MEMORY,
                    options={'max_items': 10000}
                )
            if not self.archival_policy:
                # Default to time-based archival
                from datetime import timedelta
                self.archival_policy = TimeBasedArchivalPolicy(
                    max_idle_time=timedelta(hours=1)
                )


class AdapterRegistry:
    """Registry for persistence adapter implementations."""
    
    def __init__(self):
        self._adapters: Dict[PersistenceBackend, Type[IPersistenceAdapter]] = {}
        self._factories: Dict[PersistenceBackend, Callable] = {}
        
        # Register built-in adapters
        self.register_adapter(PersistenceBackend.MEMORY, MemoryAdapter)
        self.register_adapter(PersistenceBackend.FILESYSTEM, FilesystemAdapter)
    
    def register_adapter(
        self,
        backend: PersistenceBackend,
        adapter_class: Type[IPersistenceAdapter],
        factory: Optional[Callable] = None
    ) -> None:
        """
        Register an adapter implementation.
        
        Args:
            backend: The backend type
            adapter_class: The adapter class
            factory: Optional factory function
        """
        self._adapters[backend] = adapter_class
        if factory:
            self._factories[backend] = factory
    
    def create_adapter(
        self,
        backend: PersistenceBackend,
        config: PersistenceConfig
    ) -> IPersistenceAdapter:
        """
        Create an adapter instance.
        
        Args:
            backend: The backend type
            config: Configuration for the adapter
            
        Returns:
            Configured adapter instance
        """
        if backend not in self._adapters:
            raise ValueError(f"No adapter registered for backend: {backend}")
        
        # Use custom factory if available
        if backend in self._factories:
            return self._factories[backend](config)
        
        # Default construction
        adapter_class = self._adapters[backend]
        return adapter_class(config)


class RepositoryFactory:
    """
    Factory for creating repositories with different persistence strategies.
    
    This factory:
    - Creates repositories based on configuration
    - Supports multiple strategies (memory, hybrid, persistent)
    - Allows custom adapter registration
    - Provides sensible defaults for common use cases
    """
    
    def __init__(self):
        self._adapter_registry = AdapterRegistry()
        self._default_configs: Dict[str, RepositoryConfig] = {}
        
        # Set up default configurations
        self._setup_defaults()
    
    def _setup_defaults(self) -> None:
        """Set up default configurations for common entity types."""
        # Room repository - memory only (always active)
        self._default_configs['room'] = RepositoryConfig(
            strategy=RepositoryStrategy.MEMORY_ONLY,
            memory_config=PersistenceConfig(
                backend=PersistenceBackend.MEMORY,
                options={
                    'max_items': 10000,
                    'enable_archives': False
                }
            )
        )
        
        # Game repository - hybrid with completion-based archival
        self._default_configs['game'] = RepositoryConfig(
            strategy=RepositoryStrategy.HYBRID_ASYNC,
            memory_config=PersistenceConfig(
                backend=PersistenceBackend.MEMORY,
                options={
                    'max_items': 1000,
                    'enable_archives': True
                }
            ),
            archival_policy=CompletionBasedArchivalPolicy('is_completed')
        )
        
        # Player stats - hybrid with time-based archival
        from datetime import timedelta
        self._default_configs['player_stats'] = RepositoryConfig(
            strategy=RepositoryStrategy.HYBRID_ASYNC,
            memory_config=PersistenceConfig(
                backend=PersistenceBackend.MEMORY,
                options={
                    'max_items': 50000,
                    'enable_archives': True
                }
            ),
            archival_policy=TimeBasedArchivalPolicy(
                max_idle_time=timedelta(days=7)
            )
        )
        
        # Connection repository - memory only (transient data)
        self._default_configs['connection'] = RepositoryConfig(
            strategy=RepositoryStrategy.MEMORY_ONLY,
            memory_config=PersistenceConfig(
                backend=PersistenceBackend.MEMORY,
                options={
                    'max_items': 100000,
                    'enable_archives': False
                }
            )
        )
    
    def register_adapter(
        self,
        backend: PersistenceBackend,
        adapter_class: Type[IPersistenceAdapter],
        factory: Optional[Callable] = None
    ) -> None:
        """
        Register a custom adapter implementation.
        
        Args:
            backend: The backend type
            adapter_class: The adapter class
            factory: Optional factory function
        """
        self._adapter_registry.register_adapter(backend, adapter_class, factory)
    
    def set_default_config(self, entity_type: str, config: RepositoryConfig) -> None:
        """
        Set default configuration for an entity type.
        
        Args:
            entity_type: Type of entity (e.g., 'room', 'game')
            config: Repository configuration
        """
        self._default_configs[entity_type] = config
    
    def create_repository(
        self,
        entity_type: str,
        entity_class: Type[T],
        config: Optional[RepositoryConfig] = None
    ) -> BaseRepository[T]:
        """
        Create a repository for the specified entity type.
        
        Args:
            entity_type: Type of entity (e.g., 'room', 'game')
            entity_class: The entity class
            config: Optional custom configuration
            
        Returns:
            Configured repository instance
        """
        # Use provided config or fall back to default
        if config is None:
            if entity_type not in self._default_configs:
                # Create a basic memory-only config
                config = RepositoryConfig(strategy=RepositoryStrategy.MEMORY_ONLY)
            else:
                config = self._default_configs[entity_type]
        
        # Create repository based on strategy
        if config.strategy == RepositoryStrategy.MEMORY_ONLY:
            return self._create_memory_repository(entity_class, config)
        
        elif config.strategy == RepositoryStrategy.HYBRID_ASYNC:
            return self._create_hybrid_repository(entity_class, config)
        
        elif config.strategy == RepositoryStrategy.PERSISTENT_ONLY:
            return self._create_persistent_repository(entity_class, config)
        
        elif config.strategy == RepositoryStrategy.CACHED:
            return self._create_cached_repository(entity_class, config)
        
        else:
            raise ValueError(f"Unknown repository strategy: {config.strategy}")
    
    def _create_memory_repository(
        self,
        entity_class: Type[T],
        config: RepositoryConfig
    ) -> BaseRepository[T]:
        """Create a memory-only repository."""
        memory_adapter = self._adapter_registry.create_adapter(
            PersistenceBackend.MEMORY,
            config.memory_config
        )
        return BaseRepository(memory_adapter)
    
    def _create_hybrid_repository(
        self,
        entity_class: Type[T],
        config: RepositoryConfig
    ) -> HybridRepository[T]:
        """Create a hybrid repository with async persistence."""
        # Create memory adapter
        memory_adapter = self._adapter_registry.create_adapter(
            PersistenceBackend.MEMORY,
            config.memory_config
        )
        
        # Create persistent adapter if configured
        persistent_adapter = None
        if config.persistent_config:
            persistent_adapter = self._adapter_registry.create_adapter(
                config.persistent_config.backend,
                config.persistent_config
            )
        
        # Create hybrid repository
        return HybridRepository(
            memory_adapter=memory_adapter,
            persistent_adapter=persistent_adapter,
            archival_policy=config.archival_policy
        )
    
    def _create_persistent_repository(
        self,
        entity_class: Type[T],
        config: RepositoryConfig
    ) -> BaseRepository[T]:
        """Create a persistent-only repository."""
        if not config.persistent_config:
            raise ValueError("Persistent repository requires persistent_config")
        
        persistent_adapter = self._adapter_registry.create_adapter(
            config.persistent_config.backend,
            config.persistent_config
        )
        return BaseRepository(persistent_adapter)
    
    def _create_cached_repository(
        self,
        entity_class: Type[T],
        config: RepositoryConfig
    ) -> BaseRepository[T]:
        """Create a repository with caching layer."""
        # This would be implemented when we have a caching adapter
        # For now, fall back to hybrid
        return self._create_hybrid_repository(entity_class, config)
    
    def create_unit_of_work(self, repositories: Dict[str, BaseRepository]) -> 'UnitOfWork':
        """
        Create a unit of work with the specified repositories.
        
        Args:
            repositories: Dictionary of repository name to instance
            
        Returns:
            Configured unit of work
        """
        from ..repositories.in_memory_unit_of_work import InMemoryUnitOfWork
        
        # For now, return in-memory unit of work
        # This would be extended to support different UoW types
        return InMemoryUnitOfWork()


# Global factory instance
_factory = RepositoryFactory()


def get_repository_factory() -> RepositoryFactory:
    """Get the global repository factory instance."""
    return _factory


# Convenience functions

def create_room_repository():
    """Create a room repository with default configuration."""
    from domain.entities.room import Room
    return _factory.create_repository('room', Room)


def create_game_repository():
    """Create a game repository with default configuration."""
    from backend.engine.game import Game
    return _factory.create_repository('game', Game)


def create_player_stats_repository():
    """Create a player stats repository with default configuration."""
    from domain.entities.player_stats import PlayerStats
    return _factory.create_repository('player_stats', PlayerStats)


def create_connection_repository():
    """Create a connection repository with default configuration."""
    from domain.entities.connection import PlayerConnection
    return _factory.create_repository('connection', PlayerConnection)