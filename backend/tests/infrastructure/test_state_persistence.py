"""
Comprehensive tests for state persistence infrastructure.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from backend.infrastructure.state_persistence import (
    # Abstractions
    StateVersion,
    StateTransition,
    PersistedState,
    RecoveryPoint,
    
    # Snapshots
    StateSnapshotManager,
    InMemorySnapshotStore,
    FileSystemSnapshotStore,
    SnapshotConfig,
    
    # Transition Logging
    StateTransitionLogger,
    InMemoryTransitionLog,
    FileSystemTransitionLog,
    
    # Recovery
    StateRecoveryManager,
    SnapshotRecovery,
    EventSourcedRecovery,
    HybridRecovery,
    RecoveryOptions,
    RecoveryMode,
    
    # Event Sourcing
    StateMachineEventStore,
    InMemoryEventStore,
    EventSourcedStateMachine,
    StateEventType,
    DefaultStateProjection,
    
    # Versioning
    StateVersionManager,
    MigrationRunner,
    VersionConflictResolver,
    
    # Manager
    StatePersistenceManager,
    PersistenceConfig,
    PersistenceStrategy,
    AutoPersistencePolicy
)


class TestStateVersion:
    """Test state version functionality."""
    
    def test_version_creation(self):
        """Test version creation and string representation."""
        version = StateVersion(1, 2, 3)
        assert str(version) == "1.2.3"
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
    
    def test_version_comparison(self):
        """Test version comparison."""
        v1 = StateVersion(1, 0, 0)
        v2 = StateVersion(1, 0, 1)
        v3 = StateVersion(1, 1, 0)
        v4 = StateVersion(2, 0, 0)
        
        assert v1 < v2 < v3 < v4
        assert v4 > v3 > v2 > v1


class TestSnapshots:
    """Test snapshot functionality."""
    
    @pytest.mark.asyncio
    async def test_in_memory_snapshot(self):
        """Test in-memory snapshot store."""
        store = InMemorySnapshotStore(SnapshotConfig(max_snapshots=3))
        
        # Create snapshots
        state1 = {'current_state': 'playing', 'score': 10}
        state2 = {'current_state': 'playing', 'score': 20}
        state3 = {'current_state': 'playing', 'score': 30}
        state4 = {'current_state': 'finished', 'score': 40}
        
        snap1 = await store.create_snapshot('game1', state1)
        snap2 = await store.create_snapshot('game1', state2)
        snap3 = await store.create_snapshot('game1', state3)
        snap4 = await store.create_snapshot('game1', state4)
        
        # List snapshots (should be limited to 3)
        snapshots = await store.list_snapshots('game1')
        assert len(snapshots) == 3
        
        # Restore latest
        restored = await store.restore_snapshot(snap4)
        assert restored is not None
        assert restored.state_data['score'] == 40
        
        # Delete snapshot
        deleted = await store.delete_snapshot(snap4)
        assert deleted is True
        
        # Try to restore deleted
        restored = await store.restore_snapshot(snap4)
        assert restored is None
    
    @pytest.mark.asyncio
    async def test_filesystem_snapshot(self):
        """Test filesystem snapshot store."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store = FileSystemSnapshotStore(
                Path(temp_dir),
                SnapshotConfig(compression_enabled=True)
            )
            
            # Create snapshot
            state = {
                'current_state': 'playing',
                'players': ['alice', 'bob'],
                'data': {'round': 1, 'scores': [0, 0]}
            }
            
            snap_id = await store.create_snapshot('game1', state)
            assert snap_id is not None
            
            # Verify files created
            metadata_file = Path(temp_dir) / 'metadata' / f"{snap_id}.json"
            assert metadata_file.exists()
            
            # Restore snapshot
            restored = await store.restore_snapshot(snap_id)
            assert restored is not None
            assert restored.state_data == state
            
            # List snapshots
            snapshots = await store.list_snapshots('game1')
            assert len(snapshots) == 1
            assert snapshots[0].recovery_id == snap_id
    
    @pytest.mark.asyncio
    async def test_snapshot_manager(self):
        """Test high-level snapshot manager."""
        stores = [
            InMemorySnapshotStore(),
            InMemorySnapshotStore()
        ]
        
        manager = StateSnapshotManager(stores)
        
        # Create snapshot in all stores
        state = {'current_state': 'active', 'value': 42}
        snapshot_ids = await manager.create_snapshot('sm1', state)
        assert len(snapshot_ids) == 2
        
        # Restore from any store
        restored = await manager.restore_latest('sm1')
        assert restored is not None
        assert restored.state_data == state


class TestTransitionLogging:
    """Test transition logging functionality."""
    
    @pytest.mark.asyncio
    async def test_in_memory_transition_log(self):
        """Test in-memory transition logging."""
        log = InMemoryTransitionLog(max_transitions=100)
        
        # Log transitions
        t1 = StateTransition(
            from_state='idle',
            to_state='playing',
            action='start_game',
            payload={'players': 4},
            actor_id='player1'
        )
        
        t2 = StateTransition(
            from_state='playing',
            to_state='scoring',
            action='end_round',
            payload={'round': 1},
            actor_id='system'
        )
        
        await log.log_transition('game1', t1)
        await log.log_transition('game1', t2)
        
        # Get transitions
        transitions = await log.get_transitions('game1')
        assert len(transitions) == 2
        assert transitions[0].action == 'end_round'  # Most recent first
        assert transitions[1].action == 'start_game'
        
        # Replay transitions
        base_state = {'current_state': 'idle', 'round': 0}
        final_state = await log.replay_transitions('game1', base_state, [t1, t2])
        assert final_state['current_state'] == 'scoring'
        
        # Compact log
        removed = await log.compact_log('game1', datetime.utcnow() + timedelta(hours=1))
        assert removed == 2
    
    @pytest.mark.asyncio
    async def test_filesystem_transition_log(self):
        """Test filesystem transition logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log = FileSystemTransitionLog(
                Path(temp_dir),
                max_file_size_mb=1,
                max_files_per_state_machine=5
            )
            
            # Log many transitions to test rotation
            for i in range(20):
                transition = StateTransition(
                    from_state=f'state{i}',
                    to_state=f'state{i+1}',
                    action=f'action{i}',
                    payload={'index': i}
                )
                await log.log_transition('game1', transition)
            
            # Verify files created
            game_dir = Path(temp_dir) / 'game1'
            assert game_dir.exists()
            log_files = list(game_dir.glob('*.log'))
            assert len(log_files) > 0
            
            # Get transitions
            transitions = await log.get_transitions('game1', limit=5)
            assert len(transitions) == 5
    
    @pytest.mark.asyncio
    async def test_transition_logger_with_stats(self):
        """Test transition logger with statistics."""
        stores = [InMemoryTransitionLog()]
        logger = StateTransitionLogger(stores, analyze_patterns=True)
        
        # Log transitions
        for i in range(10):
            transition = StateTransition(
                from_state='playing',
                to_state='scoring' if i % 2 == 0 else 'playing',
                action='play_turn',
                payload={'turn': i}
            )
            await logger.log_transition('game1', transition, duration_ms=50.0)
        
        # Get statistics
        stats = await logger.get_transition_stats('game1')
        assert stats['total_transitions'] == 10
        assert stats['unique_states'] >= 2
        assert 'transition_distribution' in stats


class TestRecovery:
    """Test state recovery functionality."""
    
    @pytest.mark.asyncio
    async def test_snapshot_recovery(self):
        """Test recovery from snapshots."""
        # Create snapshot store with some snapshots
        snapshot_store = InMemorySnapshotStore()
        
        states = [
            {'current_state': 'idle', 'version': 1},
            {'current_state': 'playing', 'version': 2},
            {'current_state': 'finished', 'version': 3}
        ]
        
        snapshot_ids = []
        for state in states:
            snap_id = await snapshot_store.create_snapshot('game1', state)
            snapshot_ids.append(snap_id)
            await asyncio.sleep(0.01)  # Ensure different timestamps
        
        # Create recovery strategy
        recovery = SnapshotRecovery([snapshot_store])
        
        # Test latest recovery
        result = await recovery.recover(
            'game1',
            RecoveryOptions(mode=RecoveryMode.LATEST)
        )
        assert result.is_successful
        assert result.recovered_state.state_data['version'] == 3
        
        # Test specific snapshot recovery
        result = await recovery.recover(
            'game1',
            RecoveryOptions(
                mode=RecoveryMode.SNAPSHOT,
                snapshot_id=snapshot_ids[0]
            )
        )
        assert result.is_successful
        assert result.recovered_state.state_data['version'] == 1
    
    @pytest.mark.asyncio
    async def test_event_sourced_recovery(self):
        """Test recovery from event log."""
        # Create transition log with events
        log = InMemoryTransitionLog()
        
        transitions = [
            StateTransition('idle', 'starting', 'start', {'players': 4}),
            StateTransition('starting', 'playing', 'begin', {'round': 1}),
            StateTransition('playing', 'scoring', 'score', {'scores': [10, 20, 15, 25]})
        ]
        
        for t in transitions:
            await log.log_transition('game1', t)
        
        # Create recovery strategy
        initial_state_provider = lambda x: {'current_state': 'idle', 'data': {}}
        recovery = EventSourcedRecovery([log], initial_state_provider)
        
        # Recover latest state
        result = await recovery.recover(
            'game1',
            RecoveryOptions(mode=RecoveryMode.LATEST)
        )
        assert result.is_successful
        assert result.recovered_state.current_state == 'scoring'
        assert result.metadata['transitions_replayed'] == 3
    
    @pytest.mark.asyncio
    async def test_hybrid_recovery(self):
        """Test hybrid recovery strategy."""
        # Create stores
        snapshot_store = InMemorySnapshotStore()
        transition_log = InMemoryTransitionLog()
        
        # Create old snapshot
        old_state = {'current_state': 'playing', 'round': 5}
        await snapshot_store.create_snapshot('game1', old_state)
        
        # Add recent transitions
        recent_transitions = [
            StateTransition('playing', 'playing', 'play_turn', {'turn': 1}),
            StateTransition('playing', 'scoring', 'end_round', {'round': 5})
        ]
        
        for t in recent_transitions:
            await transition_log.log_transition('game1', t)
        
        # Create recovery strategies
        snapshot_recovery = SnapshotRecovery([snapshot_store])
        event_recovery = EventSourcedRecovery(
            [transition_log],
            lambda x: {'current_state': 'idle'}
        )
        
        hybrid = HybridRecovery(
            snapshot_recovery,
            event_recovery,
            snapshot_age_threshold=timedelta(seconds=0)  # Force event replay
        )
        
        # Recover with hybrid strategy
        result = await hybrid.recover(
            'game1',
            RecoveryOptions(mode=RecoveryMode.LATEST)
        )
        assert result.is_successful
        assert result.recovered_state.current_state == 'scoring'
        assert result.metadata.get('hybrid_recovery') is True


class TestEventSourcing:
    """Test event sourcing functionality."""
    
    @pytest.mark.asyncio
    async def test_event_store(self):
        """Test basic event store operations."""
        store = InMemoryEventStore()
        event_store = StateMachineEventStore(store)
        
        # Create state machine
        initial_state = {
            'current_state': 'idle',
            'players': [],
            'config': {'max_players': 4}
        }
        
        create_event = await event_store.create_state_machine(
            'game1',
            initial_state,
            actor_id='system'
        )
        assert create_event.event_type == StateEventType.CREATED
        
        # Add transition
        transition = StateTransition(
            from_state='idle',
            to_state='waiting',
            action='create_room',
            payload={'room_code': 'ABC123'}
        )
        
        trans_event = await event_store.transition_state('game1', transition)
        assert trans_event.event_type == StateEventType.TRANSITIONED
        
        # Update state
        update_event = await event_store.update_state(
            'game1',
            {'players': ['alice', 'bob']},
            actor_id='system'
        )
        assert update_event.event_type == StateEventType.UPDATED
        
        # Get current state
        current = await event_store.get_current_state('game1')
        assert current['current_state'] == 'waiting'
        assert len(current['state_data']['players']) == 2
        
        # Get version
        version = await event_store.get_state_version('game1')
        assert version == 3  # 3 events
    
    @pytest.mark.asyncio
    async def test_event_sourced_state_machine(self):
        """Test event-sourced state machine persistence."""
        store = InMemoryEventStore()
        event_store = StateMachineEventStore(store)
        state_machine = EventSourcedStateMachine(event_store)
        
        # Save new state
        state = {
            'current_state': 'playing',
            'round': 1,
            'scores': [0, 0, 0, 0]
        }
        
        save_id = await state_machine.save_state('game1', state)
        assert save_id.startswith('event_')
        
        # Load state
        loaded = await state_machine.load_state('game1')
        assert loaded is not None
        assert loaded.current_state == 'playing'
        assert loaded.state_data['round'] == 1
        
        # Update and save again
        state['round'] = 2
        state['scores'] = [10, 15, 20, 25]
        await state_machine.save_state('game1', state)
        
        # Load updated state
        loaded = await state_machine.load_state('game1')
        assert loaded.state_data['round'] == 2
        assert loaded.state_data['scores'] == [10, 15, 20, 25]
    
    @pytest.mark.asyncio
    async def test_custom_projection(self):
        """Test custom state projection."""
        
        class GameStateProjection(DefaultStateProjection):
            """Custom projection for game state."""
            
            def apply_event(self, event, state):
                # Use default projection first
                state = super().apply_event(event, state)
                
                # Add custom logic
                if event.event_type == StateEventType.TRANSITIONED:
                    if event.event_data.get('to_state') == 'game_over':
                        # Calculate final statistics
                        state['final_stats'] = {
                            'duration': 0,
                            'winner': None,
                            'final_scores': state.get('state_data', {}).get('scores', [])
                        }
                
                return state
        
        # Create event store with custom projection
        store = InMemoryEventStore()
        event_store = StateMachineEventStore(
            store,
            projections=[GameStateProjection()]
        )
        
        # Create and transition state
        await event_store.create_state_machine('game1', {'current_state': 'playing'})
        
        transition = StateTransition(
            'playing',
            'game_over',
            'end_game',
            {'scores': [100, 90, 80, 70]}
        )
        await event_store.transition_state('game1', transition)
        
        # Check custom projection applied
        state = await event_store.get_current_state('game1')
        assert 'final_stats' in state
        assert state['final_stats']['final_scores'] == [100, 90, 80, 70]


class TestVersioning:
    """Test state versioning functionality."""
    
    @pytest.mark.asyncio
    async def test_version_manager(self):
        """Test version management."""
        # Create base storage
        base_storage = InMemoryStorage()
        
        # Create version manager
        migration_runner = MigrationRunner()
        conflict_resolver = VersionConflictResolver()
        
        version_manager = StateVersionManager(
            base_storage,
            migration_runner,
            conflict_resolver
        )
        
        # Save versioned state
        state = {
            'current_state': 'active',
            'data': {'value': 42}
        }
        
        save_id = await version_manager.save_state('sm1', state)
        assert save_id is not None
        
        # Load state
        loaded = await version_manager.load_state('sm1')
        assert loaded is not None
        assert '_version' in loaded.state_data
        
        # List versions
        versions = await version_manager.list_versions('sm1')
        assert len(versions) >= 1
    
    @pytest.mark.asyncio
    async def test_migration_runner(self):
        """Test migration execution."""
        runner = MigrationRunner()
        
        # Create test migration
        class TestMigration:
            from_version = StateVersion(1, 0, 0)
            to_version = StateVersion(2, 0, 0)
            
            async def migrate(self, state):
                state['migrated'] = True
                state['version'] = '2.0.0'
                return state
            
            async def rollback(self, state):
                state.pop('migrated', None)
                state['version'] = '1.0.0'
                return state
        
        # Register migration
        runner.register_migration(TestMigration())
        
        # Run migration
        state = {'version': '1.0.0', 'data': 'test'}
        migrated = await runner.migrate(
            state,
            StateVersion(1, 0, 0),
            StateVersion(2, 0, 0)
        )
        
        assert migrated['migrated'] is True
        assert migrated['version'] == '2.0.0'


class TestPersistenceManager:
    """Test high-level persistence management."""
    
    @pytest.mark.asyncio
    async def test_persistence_manager_hybrid(self):
        """Test persistence manager with hybrid strategy."""
        # Create components
        snapshot_stores = [InMemorySnapshotStore()]
        transition_logs = [InMemoryTransitionLog()]
        event_store = StateMachineEventStore(InMemoryEventStore())
        
        # Create config
        config = PersistenceConfig(
            strategy=PersistenceStrategy.HYBRID,
            cache_enabled=True,
            cache_size=10
        )
        
        # Create manager
        manager = StatePersistenceManager(
            config,
            snapshot_stores,
            transition_logs,
            event_store
        )
        
        # Save state
        state = {
            'current_state': 'playing',
            'round': 1,
            'players': ['alice', 'bob', 'charlie', 'dave']
        }
        
        save_id = await manager.save_state('game1', state)
        assert save_id is not None
        
        # Load state (should hit cache)
        loaded = await manager.load_state('game1')
        assert loaded is not None
        assert loaded.current_state == 'playing'
        assert manager.metrics.get_metrics().cache_hits == 1
        
        # Handle transition
        transition = StateTransition(
            'playing',
            'scoring',
            'end_round',
            {'round': 1}
        )
        
        await manager.handle_transition('game1', transition)
        
        # Create snapshot
        snapshot_ids = await manager.create_snapshot('game1')
        assert len(snapshot_ids) > 0
        assert manager.metrics.get_metrics().total_snapshots == 1
    
    @pytest.mark.asyncio
    async def test_auto_persistence_policy(self):
        """Test automatic persistence policies."""
        policy = AutoPersistencePolicy(
            persist_on_transition=True,
            persist_on_phase_change=True,
            persist_interval=timedelta(seconds=1)
        )
        
        assert policy.should_persist('transition') is True
        assert policy.should_persist('phase_change') is True
        assert policy.should_persist('unknown') is False
    
    @pytest.mark.asyncio
    async def test_persistence_metrics(self):
        """Test metrics collection."""
        metrics = StatePersistenceMetrics()
        
        # Record operations
        metrics.get_metrics().record_save(100.0)
        metrics.get_metrics().record_save(150.0)
        metrics.get_metrics().record_load(50.0, cache_hit=True)
        metrics.get_metrics().record_load(200.0, cache_hit=False)
        
        # Check metrics
        assert metrics.get_metrics().total_saves == 2
        assert metrics.get_metrics().total_loads == 2
        assert metrics.get_metrics().cache_hits == 1
        assert metrics.get_metrics().cache_misses == 1
        assert metrics.get_metrics().average_save_time_ms == 125.0
        
        # Check per-state-machine metrics
        game_metrics = metrics.get_metrics('game1')
        game_metrics.record_save(75.0)
        
        assert game_metrics.total_saves == 1
        assert metrics.get_metrics().total_saves == 2  # Global unchanged


# Helper class for testing
class InMemoryStorage(IStatePersistence):
    """Simple in-memory storage for testing."""
    
    def __init__(self):
        super().__init__()
        self._states = {}
    
    async def save_state(self, state_machine_id, state, version=None):
        self._states[state_machine_id] = PersistedState(
            state_machine_id=state_machine_id,
            state_type='test',
            current_state=state.get('current_state', 'unknown'),
            state_data=state,
            version=version or self._generate_version(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return f"test_{state_machine_id}"
    
    async def load_state(self, state_machine_id, version=None):
        return self._states.get(state_machine_id)
    
    async def delete_state(self, state_machine_id):
        return self._states.pop(state_machine_id, None) is not None
    
    async def list_versions(self, state_machine_id):
        state = self._states.get(state_machine_id)
        return [state.version] if state else []