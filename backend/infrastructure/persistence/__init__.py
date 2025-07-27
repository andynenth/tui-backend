"""
Persistence abstraction layer for infrastructure.

This module provides:
- Adapter pattern for different storage backends
- Hybrid repositories with memory and persistence
- Repository factory with strategy pattern
- Built-in adapters for memory and filesystem
"""

from .base import (
    IPersistenceAdapter,
    ITransactionalAdapter,
    IQueryableAdapter,
    IArchivableAdapter,
    BaseRepository,
    PersistenceBackend,
    PersistenceConfig
)

from .memory_adapter import MemoryAdapter
from .filesystem_adapter import FilesystemAdapter

from .hybrid_repository import (
    HybridRepository,
    EntityState,
    ArchivalPolicy,
    TimeBasedArchivalPolicy,
    CompletionBasedArchivalPolicy
)

from .repository_factory import (
    RepositoryFactory,
    RepositoryStrategy,
    RepositoryConfig,
    AdapterRegistry,
    get_repository_factory,
    # Convenience functions
    create_room_repository,
    create_game_repository,
    create_player_stats_repository,
    create_connection_repository
)

__all__ = [
    # Base interfaces
    'IPersistenceAdapter',
    'ITransactionalAdapter',
    'IQueryableAdapter',
    'IArchivableAdapter',
    'BaseRepository',
    'PersistenceBackend',
    'PersistenceConfig',
    
    # Adapters
    'MemoryAdapter',
    'FilesystemAdapter',
    
    # Hybrid repository
    'HybridRepository',
    'EntityState',
    'ArchivalPolicy',
    'TimeBasedArchivalPolicy',
    'CompletionBasedArchivalPolicy',
    
    # Factory
    'RepositoryFactory',
    'RepositoryStrategy',
    'RepositoryConfig',
    'AdapterRegistry',
    'get_repository_factory',
    'create_room_repository',
    'create_game_repository',
    'create_player_stats_repository',
    'create_connection_repository'
]