# State Machine Persistence Infrastructure

## Overview

The State Machine Persistence infrastructure provides comprehensive persistence capabilities for game state machines in the Liap Tui system. It implements multiple persistence strategies including snapshots, event sourcing, and hybrid approaches, with support for versioning, migration, and recovery.

## Key Features

### 1. **Multiple Persistence Strategies**
- **Snapshot-Only**: Periodic state snapshots for simple persistence
- **Event-Sourced**: Complete event history with state reconstruction
- **Hybrid**: Combines snapshots with event sourcing for optimal performance
- **Versioned**: Adds version management and migration capabilities

### 2. **Comprehensive State Management**
- State snapshots with compression
- Transaction logging with query support
- Event sourcing with custom projections
- State versioning and migrations
- Multi-level caching

### 3. **Recovery Mechanisms**
- Point-in-time recovery
- Snapshot-based recovery
- Event replay recovery
- Hybrid recovery strategies
- Automatic error recovery

### 4. **Performance Optimizations**
- In-memory caching with LRU eviction
- Batch operations support
- Compressed storage
- Efficient indexing
- Parallel processing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  StatePersistenceManager                      │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────────┐   │
│  │  Snapshot   │ │   Event      │ │    Version         │   │
│  │  Manager    │ │   Store      │ │    Manager         │   │
│  └──────┬──────┘ └──────┬───────┘ └────────┬───────────┘   │
│         │                │                   │               │
│  ┌──────┴──────┐ ┌──────┴───────┐ ┌────────┴───────────┐   │
│  │  Snapshot   │ │  Transition  │ │    Migration       │   │
│  │  Stores     │ │    Logs      │ │    Runner          │   │
│  └─────────────┘ └──────────────┘ └────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Recovery Manager                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │   │
│  │  │ Snapshot │ │  Event   │ │     Hybrid       │    │   │
│  │  │ Recovery │ │ Recovery │ │    Recovery      │    │   │
│  │  └──────────┘ └──────────┘ └──────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. State Persistence Manager
The main entry point for all persistence operations:

```python
from backend.infrastructure.state_persistence import (
    StatePersistenceManager,
    PersistenceConfig,
    PersistenceStrategy
)

# Configure persistence
config = PersistenceConfig(
    strategy=PersistenceStrategy.HYBRID,
    snapshot_interval=timedelta(minutes=5),
    cache_enabled=True,
    recovery_enabled=True
)

# Create manager
manager = StatePersistenceManager(
    config=config,
    snapshot_stores=[snapshot_store],
    transition_logs=[transition_log],
    event_store=event_store
)

# Save state
await manager.save_state('game_123', game_state)

# Load state
persisted = await manager.load_state('game_123')
```

### 2. Snapshot Management
Efficient state snapshots with compression:

```python
from backend.infrastructure.state_persistence import (
    StateSnapshotManager,
    InMemorySnapshotStore,
    FileSystemSnapshotStore
)

# Create snapshot stores
stores = [
    InMemorySnapshotStore(),
    FileSystemSnapshotStore(Path('/data/snapshots'))
]

# Create manager
snapshot_manager = StateSnapshotManager(stores)

# Create snapshot
snapshot_ids = await snapshot_manager.create_snapshot(
    'game_123',
    game_state,
    metadata={'reason': 'checkpoint'}
)

# Restore from snapshot
restored = await snapshot_manager.restore_latest('game_123')
```

### 3. Event Sourcing
Complete event history with projections:

```python
from backend.infrastructure.state_persistence import (
    StateMachineEventStore,
    InMemoryEventStore,
    EventSourcedStateMachine
)

# Create event store
event_store = StateMachineEventStore(
    InMemoryEventStore(),
    snapshot_frequency=100
)

# Record events
await event_store.create_state_machine('game_123', initial_state)
await event_store.transition_state('game_123', transition)

# Get current state by replaying events
current_state = await event_store.get_current_state('game_123')
```

### 4. State Versioning
Version management with migrations:

```python
from backend.infrastructure.state_persistence import (
    StateVersionManager,
    MigrationRunner,
    StateMigration
)

# Define migration
class V1ToV2Migration(StateMigration):
    from_version = StateVersion(1, 0, 0)
    to_version = StateVersion(2, 0, 0)
    
    async def migrate(self, state):
        # Add new fields
        state['new_feature'] = 'default_value'
        return state

# Register and run migrations
runner = MigrationRunner()
runner.register_migration(V1ToV2Migration())

version_manager = StateVersionManager(
    storage=base_storage,
    migration_runner=runner,
    conflict_resolver=resolver
)
```

### 5. Recovery Strategies
Multiple recovery options:

```python
from backend.infrastructure.state_persistence import (
    StateRecoveryManager,
    RecoveryOptions,
    RecoveryMode
)

# Configure recovery
recovery_manager = StateRecoveryManager(
    strategies=[snapshot_recovery, event_recovery],
    validator=state_validator
)

# Recover to latest state
options = RecoveryOptions(
    mode=RecoveryMode.LATEST,
    validate_state=True
)
result = await recovery_manager.recover_with_options('game_123', options)

# Point-in-time recovery
options = RecoveryOptions(
    mode=RecoveryMode.POINT_IN_TIME,
    target_timestamp=datetime.utcnow() - timedelta(hours=1)
)
result = await recovery_manager.recover_with_options('game_123', options)
```

## Usage Examples

### Basic Game State Persistence

```python
# Initialize persistence for a game
async def setup_game_persistence(game_id: str):
    # Create persistence manager with hybrid strategy
    manager = create_persistence_manager()
    
    # Save initial state
    initial_state = {
        'phase': 'waiting',
        'players': [],
        'created_at': datetime.utcnow().isoformat()
    }
    
    await manager.save_state(f'game_{game_id}', initial_state)
    
    return manager

# Handle state transitions
async def handle_game_transition(
    manager: StatePersistenceManager,
    game_id: str,
    transition: StateTransition
):
    # Log transition
    await manager.handle_transition(f'game_{game_id}', transition)
    
    # Load current state
    current = await manager.load_state(f'game_{game_id}')
    
    # Apply transition (game logic)
    new_state = apply_transition(current.state_data, transition)
    
    # Save new state
    await manager.save_state(f'game_{game_id}', new_state)
```

### Advanced Recovery Scenario

```python
async def recover_game_after_crash(game_id: str):
    manager = create_persistence_manager()
    
    # Try multiple recovery strategies
    recovery_options = [
        RecoveryOptions(mode=RecoveryMode.LATEST),
        RecoveryOptions(mode=RecoveryMode.SNAPSHOT),
        RecoveryOptions(mode=RecoveryMode.BEFORE_ERROR)
    ]
    
    for options in recovery_options:
        result = await manager.recover_state(f'game_{game_id}', options)
        
        if result and await validate_game_state(result.state_data):
            logger.info(f"Recovered game {game_id} using {options.mode}")
            return result
    
    logger.error(f"Failed to recover game {game_id}")
    return None
```

### Migration Example

```python
# Migrate all games to new version
async def migrate_all_games():
    registry = get_migration_registry()
    manager = create_persistence_manager()
    
    # Discover and register migrations
    registry.discover_migrations()
    
    # Get all game IDs
    game_ids = await get_all_game_ids()
    
    for game_id in game_ids:
        try:
            # Load current state
            current = await manager.load_state(game_id)
            if not current:
                continue
            
            # Determine version
            version_info = current.state_data.get('_version', {})
            from_version = parse_version(version_info.get('version', '1.0.0'))
            to_version = registry.get_latest_version()
            
            # Migrate if needed
            if from_version < to_version:
                migrated = await registry.migrate(
                    current.state_data,
                    from_version,
                    to_version
                )
                
                # Save migrated state
                await manager.save_state(game_id, migrated)
                logger.info(f"Migrated {game_id} from {from_version} to {to_version}")
                
        except Exception as e:
            logger.error(f"Failed to migrate {game_id}: {e}")
```

## Performance Considerations

### 1. **Caching Strategy**
- LRU cache for frequently accessed states
- Cache warming on startup
- Smart invalidation based on transitions

### 2. **Storage Optimization**
- Compression for snapshots (60-80% reduction)
- Efficient binary formats for events
- Indexed queries for fast retrieval

### 3. **Batch Operations**
- Group multiple saves/loads
- Parallel processing where possible
- Background persistence tasks

### 4. **Memory Management**
- Configurable limits for in-memory stores
- Automatic cleanup of old data
- Stream processing for large datasets

## Configuration

### Environment Variables
```bash
# Persistence strategy
PERSISTENCE_STRATEGY=hybrid  # snapshot_only, event_sourced, hybrid, versioned

# Snapshot settings
SNAPSHOT_INTERVAL_SECONDS=300
MAX_SNAPSHOTS_PER_STATE=10
SNAPSHOT_COMPRESSION=true

# Event sourcing
MAX_EVENTS_PER_STATE=10000
EVENT_COMPACT_THRESHOLD=1000

# Cache settings
CACHE_ENABLED=true
CACHE_SIZE=1000
CACHE_TTL_SECONDS=3600

# Recovery
RECOVERY_ENABLED=true
AUTO_RECOVERY=true
```

### Configuration File
```python
# config/persistence.py
PERSISTENCE_CONFIG = {
    'strategy': PersistenceStrategy.HYBRID,
    'snapshot': {
        'interval': timedelta(minutes=5),
        'max_per_state': 10,
        'compression': True,
        'stores': [
            {'type': 'memory', 'max_size': 1000},
            {'type': 'filesystem', 'path': '/data/snapshots'}
        ]
    },
    'event_sourcing': {
        'enabled': True,
        'max_events': 10000,
        'compact_after': 1000,
        'stores': [
            {'type': 'memory'},
            {'type': 'filesystem', 'path': '/data/events'}
        ]
    },
    'recovery': {
        'enabled': True,
        'strategies': ['snapshot', 'event_sourced', 'hybrid'],
        'auto_recover': True
    },
    'cache': {
        'enabled': True,
        'size': 1000,
        'ttl': 3600
    }
}
```

## Monitoring and Metrics

The persistence system provides comprehensive metrics:

```python
# Get metrics
metrics = manager.metrics.get_metrics()

print(f"Total saves: {metrics.total_saves}")
print(f"Total loads: {metrics.total_loads}")
print(f"Cache hit rate: {metrics.cache_hits / metrics.total_loads * 100:.2f}%")
print(f"Average save time: {metrics.average_save_time_ms:.2f}ms")
print(f"Average load time: {metrics.average_load_time_ms:.2f}ms")

# Per-game metrics
game_metrics = manager.metrics.get_metrics('game_123')
print(f"Game saves: {game_metrics.total_saves}")
print(f"Game recoveries: {game_metrics.total_recoveries}")
```

## Testing

The persistence system includes comprehensive tests:

```bash
# Run unit tests
pytest backend/tests/infrastructure/test_state_persistence.py

# Run integration tests
pytest backend/tests/infrastructure/test_state_persistence_integration.py

# Run with coverage
pytest --cov=backend.infrastructure.state_persistence
```

## Future Enhancements

1. **Distributed Persistence**
   - Multi-node support
   - Consensus-based replication
   - Geo-distributed storage

2. **Advanced Recovery**
   - Machine learning-based state validation
   - Automatic corruption detection
   - Partial state recovery

3. **Performance Improvements**
   - Zero-copy operations
   - Memory-mapped files
   - Native compression

4. **Enhanced Monitoring**
   - Real-time dashboards
   - Anomaly detection
   - Predictive maintenance

## Conclusion

The State Machine Persistence infrastructure provides a robust, scalable foundation for persisting game state in the Liap Tui system. With support for multiple strategies, comprehensive recovery options, and production-ready features, it ensures game state is never lost while maintaining high performance for real-time gameplay.