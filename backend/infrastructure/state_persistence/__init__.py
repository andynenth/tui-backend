"""
State machine persistence infrastructure.

This module provides persistence capabilities for game state machines,
including snapshots, event sourcing, and recovery mechanisms.
"""

from .abstractions import (
    IStatePersistence,
    IStateSnapshot,
    IStateTransitionLog,
    IStateRecovery,
    StateVersion,
    StateTransition,
    PersistedState,
    RecoveryPoint
)

from .snapshot import (
    StateSnapshotManager,
    InMemorySnapshotStore,
    FileSystemSnapshotStore,
    SnapshotConfig,
    SnapshotMetadata,
    CompressedSnapshot
)

from .transition_log import (
    StateTransitionLogger,
    TransitionEvent,
    TransitionLogStore,
    InMemoryTransitionLog,
    FileSystemTransitionLog,
    TransitionQuery
)

from .recovery import (
    StateRecoveryManager,
    RecoveryStrategy,
    SnapshotRecovery,
    EventSourcedRecovery,
    HybridRecovery,
    RecoveryResult,
    RecoveryOptions,
    RecoveryMode
)

from .event_sourcing import (
    StateMachineEventStore,
    StateEvent,
    StateEventType,
    StateProjection,
    EventSourcedStateMachine,
    StateRehydrator,
    InMemoryEventStore,
    DefaultStateProjection
)

from .versioning import (
    StateVersionManager,
    VersionedState,
    StateSchemaVersion,
    StateMigration,
    MigrationRunner,
    VersionConflictResolver,
    VersionStrategy,
    VersionConflict
)

from .persistence_manager import (
    StatePersistenceManager,
    PersistenceConfig,
    PersistenceStrategy,
    AutoPersistencePolicy,
    StatePersistenceMetrics,
    PersistenceMetrics
)

__all__ = [
    # Abstractions
    'IStatePersistence',
    'IStateSnapshot',
    'IStateTransitionLog',
    'IStateRecovery',
    'StateVersion',
    'StateTransition',
    'PersistedState',
    'RecoveryPoint',
    
    # Snapshots
    'StateSnapshotManager',
    'InMemorySnapshotStore',
    'FileSystemSnapshotStore',
    'SnapshotConfig',
    'SnapshotMetadata',
    'CompressedSnapshot',
    
    # Transition Logging
    'StateTransitionLogger',
    'TransitionEvent',
    'TransitionLogStore',
    'InMemoryTransitionLog',
    'FileSystemTransitionLog',
    'TransitionQuery',
    
    # Recovery
    'StateRecoveryManager',
    'RecoveryStrategy',
    'SnapshotRecovery',
    'EventSourcedRecovery',
    'HybridRecovery',
    'RecoveryResult',
    'RecoveryOptions',
    'RecoveryMode',
    
    # Event Sourcing
    'StateMachineEventStore',
    'StateEvent',
    'StateEventType',
    'StateProjection',
    'EventSourcedStateMachine',
    'StateRehydrator',
    'InMemoryEventStore',
    'DefaultStateProjection',
    
    # Versioning
    'StateVersionManager',
    'VersionedState',
    'StateSchemaVersion',
    'StateMigration',
    'MigrationRunner',
    'VersionConflictResolver',
    'VersionStrategy',
    'VersionConflict',
    
    # Manager
    'StatePersistenceManager',
    'PersistenceConfig',
    'PersistenceStrategy',
    'AutoPersistencePolicy',
    'StatePersistenceMetrics',
    'PersistenceMetrics'
]