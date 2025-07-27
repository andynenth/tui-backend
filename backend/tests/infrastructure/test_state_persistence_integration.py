"""
Integration tests for state persistence with game state machine.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from backend.engine.state_machine.game_state_machine import GameStateMachine
from backend.engine.state_machine.game_action import GameAction, ActionType
from backend.engine.state_machine.game_state import GamePhase
from backend.engine.game import Game
from backend.engine.room import Room
from backend.engine.player import Player

from infrastructure.state_persistence import (
    StatePersistenceManager,
    PersistenceConfig,
    PersistenceStrategy,
    StateSnapshotManager,
    InMemorySnapshotStore,
    FileSystemSnapshotStore,
    StateTransitionLogger,
    InMemoryTransitionLog,
    StateMachineEventStore,
    InMemoryEventStore,
    StateRecoveryManager,
    RecoveryOptions,
    RecoveryMode
)


class TestGameStatePersistence:
    """Test persistence with actual game state machine."""
    
    @pytest.fixture
    async def game_setup(self):
        """Set up a game with state machine."""
        # Create room and players
        room = Room("TEST123")
        players = [
            Player(f"player{i}", f"Player {i}")
            for i in range(4)
        ]
        
        for player in players:
            room.add_player(player)
        
        # Create game
        game = Game(room)
        
        # Create state machine
        state_machine = GameStateMachine(game)
        await state_machine.initialize()
        
        return {
            'room': room,
            'game': game,
            'state_machine': state_machine,
            'players': players
        }
    
    @pytest.fixture
    async def persistence_manager(self):
        """Create persistence manager for testing."""
        # Create stores
        snapshot_stores = [InMemorySnapshotStore()]
        transition_logs = [InMemoryTransitionLog()]
        event_store = StateMachineEventStore(InMemoryEventStore())
        
        # Create config
        config = PersistenceConfig(
            strategy=PersistenceStrategy.HYBRID,
            snapshot_interval=timedelta(seconds=1),
            cache_enabled=True
        )
        
        # Create manager
        manager = StatePersistenceManager(
            config,
            snapshot_stores,
            transition_logs,
            event_store
        )
        
        return manager
    
    @pytest.mark.asyncio
    async def test_persist_game_state_transitions(self, game_setup, persistence_manager):
        """Test persisting game state transitions."""
        state_machine = game_setup['state_machine']
        game = game_setup['game']
        players = game_setup['players']
        
        # Get initial state
        initial_state = await state_machine.get_state_data()
        
        # Save initial state
        await persistence_manager.save_state(
            f"game_{game.id}",
            initial_state
        )
        
        # Start game (transition to PREPARATION)
        action = GameAction(
            type=ActionType.START_GAME,
            actor_id=players[0].id,
            payload={}
        )
        
        result = await state_machine.handle_action(action)
        assert result.success
        assert state_machine.current_phase == GamePhase.PREPARATION
        
        # Save after transition
        prep_state = await state_machine.get_state_data()
        await persistence_manager.save_state(
            f"game_{game.id}",
            prep_state
        )
        
        # Load state and verify
        loaded = await persistence_manager.load_state(f"game_{game.id}")
        assert loaded is not None
        assert loaded.state_data['phase'] == GamePhase.PREPARATION.value
        assert loaded.state_data['game_started'] is True
    
    @pytest.mark.asyncio
    async def test_recover_game_state(self, game_setup, persistence_manager):
        """Test recovering game state from persistence."""
        state_machine = game_setup['state_machine']
        game = game_setup['game']
        players = game_setup['players']
        
        # Play through several transitions
        transitions = [
            GameAction(ActionType.START_GAME, players[0].id, {}),
            GameAction(ActionType.DEAL_COMPLETE, 'system', {}),
            GameAction(ActionType.DECLARE, players[0].id, {'declaration': 2}),
            GameAction(ActionType.DECLARE, players[1].id, {'declaration': 2}),
            GameAction(ActionType.DECLARE, players[2].id, {'declaration': 2}),
            GameAction(ActionType.DECLARE, players[3].id, {'declaration': 2})
        ]
        
        # Execute transitions and save states
        for i, action in enumerate(transitions):
            result = await state_machine.handle_action(action)
            if result.success:
                state = await state_machine.get_state_data()
                await persistence_manager.save_state(
                    f"game_{game.id}",
                    state,
                    force=(i == len(transitions) - 1)  # Force save last state
                )
                
                # Log transition
                if persistence_manager.transition_logger and result.transition:
                    await persistence_manager.handle_transition(
                        f"game_{game.id}",
                        result.transition
                    )
        
        # Simulate crash - create new state machine
        new_state_machine = GameStateMachine(game)
        
        # Recover state
        recovered = await persistence_manager.recover_state(
            f"game_{game.id}",
            RecoveryOptions(mode=RecoveryMode.LATEST)
        )
        
        assert recovered is not None
        
        # Restore to new state machine
        # In real implementation, state machine would have restore method
        assert recovered.state_data['phase'] == GamePhase.TURN.value
        assert len(recovered.state_data.get('declarations', {})) == 4
    
    @pytest.mark.asyncio
    async def test_event_sourced_game_replay(self, game_setup, persistence_manager):
        """Test replaying game from events."""
        state_machine = game_setup['state_machine']
        game = game_setup['game']
        players = game_setup['players']
        
        # Enable event sourcing
        if persistence_manager.event_store:
            # Create initial state
            initial_state = await state_machine.get_state_data()
            await persistence_manager.event_store.create_state_machine(
                f"game_{game.id}",
                initial_state
            )
            
            # Play game and record events
            actions = [
                GameAction(ActionType.START_GAME, players[0].id, {}),
                GameAction(ActionType.DEAL_COMPLETE, 'system', {}),
                GameAction(ActionType.DECLARE, players[0].id, {'declaration': 3}),
                GameAction(ActionType.DECLARE, players[1].id, {'declaration': 2}),
                GameAction(ActionType.DECLARE, players[2].id, {'declaration': 2}),
                GameAction(ActionType.DECLARE, players[3].id, {'declaration': 1})
            ]
            
            for action in actions:
                result = await state_machine.handle_action(action)
                if result.success and result.transition:
                    # Record transition as event
                    await persistence_manager.event_store.transition_state(
                        f"game_{game.id}",
                        result.transition
                    )
            
            # Get event history
            events = await persistence_manager.event_store.get_event_history(
                f"game_{game.id}"
            )
            assert len(events) > 0
            
            # Replay to get current state
            replayed_state = await persistence_manager.event_store.get_current_state(
                f"game_{game.id}"
            )
            assert replayed_state['current_state'] == GamePhase.TURN.value
    
    @pytest.mark.asyncio
    async def test_snapshot_and_event_hybrid(self, game_setup):
        """Test hybrid persistence with snapshots and events."""
        state_machine = game_setup['state_machine']
        game = game_setup['game']
        players = game_setup['players']
        
        # Create persistence with filesystem storage
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create stores
            snapshot_stores = [
                InMemorySnapshotStore(),
                FileSystemSnapshotStore(Path(temp_dir))
            ]
            transition_logs = [
                InMemoryTransitionLog(),
                FileSystemTransitionLog(Path(temp_dir) / 'logs')
            ]
            event_store = StateMachineEventStore(InMemoryEventStore())
            
            # Create manager with short snapshot interval
            config = PersistenceConfig(
                strategy=PersistenceStrategy.HYBRID,
                snapshot_interval=timedelta(milliseconds=100),
                max_snapshots_per_state=3
            )
            
            manager = StatePersistenceManager(
                config,
                snapshot_stores,
                transition_logs,
                event_store
            )
            
            # Play game with saves
            initial = await state_machine.get_state_data()
            await manager.save_state(f"game_{game.id}", initial)
            
            # Start game
            await state_machine.handle_action(
                GameAction(ActionType.START_GAME, players[0].id, {})
            )
            await asyncio.sleep(0.15)  # Ensure snapshot interval passed
            
            state1 = await state_machine.get_state_data()
            await manager.save_state(f"game_{game.id}", state1)
            
            # Deal complete
            await state_machine.handle_action(
                GameAction(ActionType.DEAL_COMPLETE, 'system', {})
            )
            await asyncio.sleep(0.15)
            
            state2 = await state_machine.get_state_data()
            await manager.save_state(f"game_{game.id}", state2)
            
            # Verify snapshots created
            assert manager.metrics.get_metrics().total_snapshots >= 2
            
            # Verify files created
            assert (Path(temp_dir) / 'data' / f"game_{game.id}").exists()
            assert (Path(temp_dir) / 'logs' / f"game_{game.id}").exists()
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, game_setup, persistence_manager):
        """Test performance metrics collection."""
        state_machine = game_setup['state_machine']
        game = game_setup['game']
        
        # Perform multiple save/load operations
        for i in range(10):
            state = await state_machine.get_state_data()
            state['iteration'] = i
            
            # Save
            await persistence_manager.save_state(
                f"game_{game.id}",
                state,
                force=True
            )
            
            # Load
            await persistence_manager.load_state(f"game_{game.id}")
        
        # Check metrics
        metrics = persistence_manager.metrics.get_metrics(f"game_{game.id}")
        assert metrics.total_saves == 10
        assert metrics.total_loads == 10
        assert metrics.average_save_time_ms > 0
        assert metrics.average_load_time_ms > 0
        
        # Cache should have helped with loads
        assert metrics.cache_hits > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_game_persistence(self, persistence_manager):
        """Test persisting multiple games concurrently."""
        games = []
        
        # Create multiple games
        for i in range(5):
            room = Room(f"ROOM{i}")
            for j in range(4):
                player = Player(f"p{i}_{j}", f"Player {j}")
                room.add_player(player)
            
            game = Game(room)
            state_machine = GameStateMachine(game)
            await state_machine.initialize()
            
            games.append({
                'game': game,
                'state_machine': state_machine,
                'room': room
            })
        
        # Save all games concurrently
        save_tasks = []
        for game_data in games:
            state = await game_data['state_machine'].get_state_data()
            task = persistence_manager.save_state(
                f"game_{game_data['game'].id}",
                state
            )
            save_tasks.append(task)
        
        save_results = await asyncio.gather(*save_tasks)
        assert all(result is not None for result in save_results)
        
        # Load all games concurrently
        load_tasks = []
        for game_data in games:
            task = persistence_manager.load_state(f"game_{game_data['game'].id}")
            load_tasks.append(task)
        
        load_results = await asyncio.gather(*load_tasks)
        assert all(result is not None for result in load_results)
        
        # Verify each game loaded correctly
        for i, (game_data, loaded) in enumerate(zip(games, load_results)):
            assert loaded.state_data['room_id'] == f"ROOM{i}"
            assert len(loaded.state_data['players']) == 4
    
    @pytest.mark.asyncio
    async def test_state_machine_recovery_after_error(self, game_setup, persistence_manager):
        """Test recovering from error states."""
        state_machine = game_setup['state_machine']
        game = game_setup['game']
        players = game_setup['players']
        
        # Start game and save checkpoint
        await state_machine.handle_action(
            GameAction(ActionType.START_GAME, players[0].id, {})
        )
        await state_machine.handle_action(
            GameAction(ActionType.DEAL_COMPLETE, 'system', {})
        )
        
        checkpoint_state = await state_machine.get_state_data()
        await persistence_manager.save_state(
            f"game_{game.id}",
            checkpoint_state,
            force=True
        )
        
        # Create snapshot for recovery
        await persistence_manager.create_snapshot(f"game_{game.id}")
        
        # Simulate error by putting game in invalid state
        # (In real scenario, this would be an actual error)
        state_machine.current_phase = None  # Invalid state
        
        # Attempt recovery
        recovery_options = RecoveryOptions(
            mode=RecoveryMode.LATEST,
            validate_state=True
        )
        
        recovered = await persistence_manager.recover_state(
            f"game_{game.id}",
            recovery_options
        )
        
        assert recovered is not None
        assert recovered.state_data['phase'] == GamePhase.DECLARATION.value
        
        # Verify we can continue from recovered state
        # In real implementation, would restore to state machine
        assert recovered.state_data['game_started'] is True
        assert 'players' in recovered.state_data