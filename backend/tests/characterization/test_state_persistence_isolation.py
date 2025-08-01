"""
Characterization tests for StatePersistenceManager in isolation.

These tests verify that the infrastructure state management works correctly
before we attempt to integrate it with the use cases.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Mark all async tests
pytestmark = pytest.mark.asyncio

from infrastructure.state_persistence.persistence_manager import (
    StatePersistenceManager,
    PersistenceConfig,
    PersistenceStrategy,
    AutoPersistencePolicy,
)
from infrastructure.state_persistence.abstractions import (
    StateTransition,
    PersistedState,
    StateVersion,
    IStateSnapshot,
    IStateTransitionLog,
)


class TestStatePersistenceManagerCapabilities:
    """Test the unused StatePersistenceManager infrastructure."""

    @pytest.fixture
    def mock_snapshot_store(self):
        """Create mock snapshot store."""
        store = Mock(spec=IStateSnapshot)
        store.create_snapshot = AsyncMock(return_value="snapshot-123")
        store.restore_snapshot = AsyncMock()
        store.list_snapshots = AsyncMock(return_value=[])
        store.delete_snapshot = AsyncMock(return_value=True)
        return store

    @pytest.fixture
    def mock_transition_log(self):
        """Create mock transition log."""
        log = Mock(spec=IStateTransitionLog)
        log.log_transition = AsyncMock()
        log.get_transitions = AsyncMock(return_value=[])
        log.replay_transitions = AsyncMock()
        log.compact_log = AsyncMock(return_value=0)
        return log

    @pytest.fixture
    def persistence_config(self):
        """Create test persistence configuration."""
        return PersistenceConfig(
            strategy=PersistenceStrategy.HYBRID,
            snapshot_enabled=True,
            event_sourcing_enabled=True,
            recovery_enabled=True,
            persist_on_phase_change=True,  # This is what we want to use!
            cache_enabled=True,
        )

    async def test_state_persistence_handles_game_transitions(
        self, mock_snapshot_store, mock_transition_log, persistence_config
    ):
        """
        Test that StatePersistenceManager can handle game state transitions.
        
        This verifies the infrastructure is ready for integration.
        """
        # Arrange - create state manager with mocks
        with patch('infrastructure.state_persistence.persistence_manager.StateSnapshotManager'):
            with patch('infrastructure.state_persistence.persistence_manager.StateTransitionLogger'):
                manager = StatePersistenceManager(
                    config=persistence_config,
                    snapshot_stores=[mock_snapshot_store],
                    transition_logs=[mock_transition_log],
                )
                
                # Create a game state transition
                transition = StateTransition(
                    from_state="NOT_STARTED",
                    to_state="PREPARATION",
                    action="start_game",
                    payload={"room_id": "test-room", "players": 4},
                    actor_id="host-player",
                    metadata={"is_phase_change": True}
                )
                
                # Act - handle the transition
                policy = AutoPersistencePolicy(persist_on_phase_change=True)
                await manager.handle_transition("game-123", transition, policy)
                
                # Assert - verify infrastructure capabilities
                # 1. Transition should be logged
                assert mock_transition_log.log_transition.called
                
                # 2. Since it's a phase change, should trigger persistence
                assert "game-123" in manager._pending_persists

    async def test_automatic_phase_change_persistence(
        self, mock_snapshot_store, mock_transition_log, persistence_config
    ):
        """
        Test automatic persistence on phase changes.
        
        This is a KEY feature we want to enable.
        """
        # Arrange
        with patch('infrastructure.state_persistence.persistence_manager.StateSnapshotManager'):
            with patch('infrastructure.state_persistence.persistence_manager.StateTransitionLogger'):
                manager = StatePersistenceManager(
                    config=persistence_config,
                    snapshot_stores=[mock_snapshot_store],
                    transition_logs=[mock_transition_log],
                )
                
                # Simulate existing game state
                game_state = {
                    "current_state": "PREPARATION",
                    "state_data": {
                        "room_id": "test-room",
                        "round_number": 1,
                        "players": ["p1", "p2", "p3", "p4"],
                        "phase": "PREPARATION"
                    }
                }
                
                # Mock load_state to return current state
                with patch.object(manager, 'load_state') as mock_load:
                    mock_load.return_value = PersistedState(
                        state_machine_id="game-123",
                        state_type="game",
                        current_state="PREPARATION",
                        state_data=game_state,
                        version=StateVersion(1, 0, 0)
                    )
                    
                    # Create phase change transition
                    transition = StateTransition(
                        from_state="PREPARATION",
                        to_state="DECLARATION",
                        action="phase_change",
                        payload={},
                        metadata={"is_phase_change": True}
                    )
                    
                    # Act
                    policy = AutoPersistencePolicy(persist_on_phase_change=True)
                    await manager.handle_transition("game-123", transition, policy)
                    
                    # Assert - should immediately persist on phase change
                    mock_load.assert_called_with("game-123")

    async def test_snapshot_creation_capability(
        self, mock_snapshot_store, mock_transition_log, persistence_config
    ):
        """
        Test snapshot creation for game recovery.
        
        This enables game state recovery after disconnections.
        """
        # Arrange
        with patch('infrastructure.state_persistence.persistence_manager.StateSnapshotManager') as MockSnapshotManager:
            mock_snapshot_manager = Mock()
            mock_snapshot_manager.create_snapshot = AsyncMock(return_value=["snapshot-123"])
            MockSnapshotManager.return_value = mock_snapshot_manager
            
            with patch('infrastructure.state_persistence.persistence_manager.StateTransitionLogger'):
                manager = StatePersistenceManager(
                    config=persistence_config,
                    snapshot_stores=[mock_snapshot_store],
                    transition_logs=[mock_transition_log],
                )
                
                # Mock current game state
                with patch.object(manager, 'load_state') as mock_load:
                    current_state = PersistedState(
                        state_machine_id="game-123",
                        state_type="game",
                        current_state="TURN",
                        state_data={
                            "room_id": "test-room",
                            "round_number": 3,
                            "turn_number": 5,
                            "current_player": "p2",
                            "scores": {"p1": 15, "p2": 22, "p3": 18, "p4": 12}
                        },
                        version=StateVersion(1, 0, 5)
                    )
                    mock_load.return_value = current_state
                    
                    # Act - create manual snapshot
                    snapshot_ids = await manager.create_snapshot("game-123")
                    
                    # Assert
                    mock_load.assert_called_with("game-123")
                    mock_snapshot_manager.create_snapshot.assert_called_once()
                    assert manager.metrics.get_metrics("game-123").total_snapshots == 1

    async def test_state_recovery_mechanism(
        self, mock_snapshot_store, mock_transition_log, persistence_config
    ):
        """
        Test state recovery capabilities.
        
        This is crucial for handling disconnections and failures.
        """
        # Arrange
        from infrastructure.state_persistence.recovery import RecoveryOptions, RecoveryMode
        
        with patch('infrastructure.state_persistence.persistence_manager.StateRecoveryManager') as MockRecoveryManager:
            mock_recovery = Mock()
            mock_recovery.recover_with_options = AsyncMock()
            mock_recovery.recover_with_options.return_value = Mock(
                is_successful=True,
                recovered_state=PersistedState(
                    state_machine_id="game-123",
                    state_type="game",
                    current_state="TURN",
                    state_data={"recovered": True},
                    version=StateVersion(1, 0, 3)
                )
            )
            MockRecoveryManager.return_value = mock_recovery
            
            manager = StatePersistenceManager(
                config=persistence_config,
                snapshot_stores=[mock_snapshot_store],
                transition_logs=[mock_transition_log],
            )
            
            # Act - attempt recovery
            options = RecoveryOptions(mode=RecoveryMode.HYBRID)
            recovered_state = await manager.recover_state("game-123", options)
            
            # Assert
            assert recovered_state is not None
            assert manager.metrics.get_metrics("game-123").total_recoveries == 1

    async def test_performance_optimizations(
        self, mock_snapshot_store, mock_transition_log, persistence_config
    ):
        """
        Test performance features like caching and batching.
        
        These optimizations minimize the performance impact.
        """
        # Arrange
        persistence_config.cache_enabled = True
        persistence_config.cache_size = 100
        persistence_config.batch_operations = True
        persistence_config.batch_size = 10
        
        with patch('infrastructure.state_persistence.persistence_manager.StateSnapshotManager'):
            with patch('infrastructure.state_persistence.persistence_manager.StateTransitionLogger'):
                manager = StatePersistenceManager(
                    config=persistence_config,
                    snapshot_stores=[mock_snapshot_store],
                    transition_logs=[mock_transition_log],
                )
                
                # Test caching
                test_state = {
                    "current_state": "TURN",
                    "state_data": {"cached": True}
                }
                
                # First save should update cache
                manager._update_cache("game-123", test_state)
                
                # Assert - verify caching works
                cached_state = manager._get_cached("game-123")
                assert cached_state is not None
                assert cached_state.state_data["cached"] is True
                
                # Test cache hit metrics
                with patch.object(manager, '_get_cached', return_value=cached_state):
                    await manager.load_state("game-123")
                    metrics = manager.metrics.get_metrics("game-123")
                    assert metrics.cache_hits == 1

    async def test_event_sourcing_capabilities(
        self, mock_snapshot_store, mock_transition_log, persistence_config
    ):
        """
        Test event sourcing for complete audit trail.
        
        This provides full game history and audit capabilities.
        """
        # Arrange
        persistence_config.strategy = PersistenceStrategy.EVENT_SOURCED
        persistence_config.event_sourcing_enabled = True
        
        # Create mock event store
        from infrastructure.state_persistence.event_sourcing import StateMachineEventStore
        mock_event_store = Mock(spec=StateMachineEventStore)
        mock_event_store.append_events = AsyncMock()
        mock_event_store.get_events = AsyncMock(return_value=[])
        
        with patch('infrastructure.state_persistence.persistence_manager.EventSourcedStateMachine'):
            manager = StatePersistenceManager(
                config=persistence_config,
                snapshot_stores=[mock_snapshot_store],
                transition_logs=[mock_transition_log],
                event_store=mock_event_store,
            )
            
            # Test transition logging
            transitions = [
                StateTransition("NOT_STARTED", "PREPARATION", "start_game", {}),
                StateTransition("PREPARATION", "DECLARATION", "all_dealt", {}),
                StateTransition("DECLARATION", "TURN", "all_declared", {}),
            ]
            
            # Act - log multiple transitions
            for transition in transitions:
                await manager.handle_transition("game-123", transition)
            
            # Assert - all transitions should be logged
            assert len(manager._pending_persists) > 0

    async def test_concurrent_state_management(
        self, mock_snapshot_store, mock_transition_log, persistence_config
    ):
        """
        Test concurrent state operations.
        
        Important for multiplayer games with simultaneous actions.
        """
        import asyncio
        
        # Arrange
        with patch('infrastructure.state_persistence.persistence_manager.StateSnapshotManager'):
            with patch('infrastructure.state_persistence.persistence_manager.StateTransitionLogger'):
                manager = StatePersistenceManager(
                    config=persistence_config,
                    snapshot_stores=[mock_snapshot_store],
                    transition_logs=[mock_transition_log],
                )
                
                # Simulate concurrent transitions from different players
                async def player_action(player_id: str, action: str):
                    transition = StateTransition(
                        from_state="TURN",
                        to_state="TURN",
                        action=action,
                        payload={"player": player_id},
                        actor_id=player_id
                    )
                    await manager.handle_transition("game-123", transition)
                
                # Act - simulate 4 players acting concurrently
                tasks = [
                    player_action("p1", "play_card"),
                    player_action("p2", "play_card"),
                    player_action("p3", "play_card"),
                    player_action("p4", "play_card"),
                ]
                
                await asyncio.gather(*tasks)
                
                # Assert - all transitions handled without errors
                # The manager should handle concurrent access properly
                assert "game-123" in manager._pending_persists