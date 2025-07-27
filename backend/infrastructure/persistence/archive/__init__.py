"""
Archive subsystem for hybrid persistence.

Provides archival strategies, workers, and backends for game data.
"""

from .archive_strategy import (
    ArchivalTrigger,
    ArchivalPriority,
    ArchivalPolicy,
    ArchivalRequest,
    ArchivalResult,
    IArchivalBackend,
    ArchivalStrategy,
    GameArchivalStrategy,
    DEFAULT_GAME_POLICY,
    DEFAULT_ROOM_POLICY
)

from .archive_worker import (
    WorkerState,
    WorkerMetrics,
    ArchivalWorker
)

from .archive_backends import (
    FileSystemArchiveBackend,
    S3ArchiveBackend,
    PostgreSQLArchiveBackend,
    CompositeArchiveBackend
)

from .archive_manager import (
    ArchiveManager,
    ArchiveQuery,
    ArchiveStats
)

__all__ = [
    # Strategy components
    'ArchivalTrigger',
    'ArchivalPriority',
    'ArchivalPolicy',
    'ArchivalRequest',
    'ArchivalResult',
    'IArchivalBackend',
    'ArchivalStrategy',
    'GameArchivalStrategy',
    'DEFAULT_GAME_POLICY',
    'DEFAULT_ROOM_POLICY',
    
    # Worker components
    'WorkerState',
    'WorkerMetrics',
    'ArchivalWorker',
    
    # Backend implementations
    'FileSystemArchiveBackend',
    'S3ArchiveBackend',
    'PostgreSQLArchiveBackend',
    'CompositeArchiveBackend',
    
    # Manager
    'ArchiveManager',
    'ArchiveQuery',
    'ArchiveStats'
]