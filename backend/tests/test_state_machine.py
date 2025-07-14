# File: backend/tests/test_state_machine.py
# Clean version with proper indentation

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from engine.state_machine.core import GamePhase, ActionType, GameAction
from engine.state_machine.action_queue import ActionQueue
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.states.declaration_state import DeclarationState


class MockGame:
    def __init__(self):
        self.round_starter = "Player1"
        self.player_declarations = {}
        self.players = ["Player1", "Player2", "Player3", "Player4"]

    def get_player_order_from(self, starter):
        start_idx = self.players.index(starter)
        return self.players[start_idx:] + self.players[:start_idx]


@pytest.fixture
def mock_game():
    return MockGame()


@pytest.fixture
def action_queue():
    return ActionQueue()


@pytest_asyncio.fixture
async def state_machine(mock_game):
    sm = GameStateMachine(mock_game)
    await sm.start(GamePhase.DECLARATION)
    yield sm
    await sm.stop()


class TestActionQueue:

    @pytest.mark.asyncio
    async def test_add_and_process_action(self, action_queue):
        """Test basic action queueing and processing"""
        # Create test action
        action = GameAction(
            player_name="TestPlayer",
            action_type=ActionType.DECLARE,
            payload={"value": 3},
            timestamp=datetime.now(),
            sequence_id=0,
        )

        # Add action to queue
        await action_queue.add_action(action)

        # Process actions
        processed_actions = await action_queue.process_actions()

        # Verify
        assert len(processed_actions) == 1
        assert processed_actions[0].player_name == "TestPlayer"
        assert processed_actions[0].action_type == ActionType.DECLARE
        assert processed_actions[0].sequence_id == 0  # Should be auto-assigned

    @pytest.mark.asyncio
    async def test_sequence_numbering(self, action_queue):
        """Test that actions get proper sequence numbers"""
        actions = []
        for i in range(3):
            action = GameAction(
                player_name=f"Player{i}",
                action_type=ActionType.DECLARE,
                payload={"value": i},
                timestamp=datetime.now(),
                sequence_id=0,  # Will be overwritten
            )
            actions.append(action)
            await action_queue.add_action(action)

        processed = await action_queue.process_actions()

        # Verify sequence numbers are assigned correctly
        for i, action in enumerate(processed):
            assert action.sequence_id == i


class TestDeclarationState:

    @pytest_asyncio.fixture
    async def declaration_state(self, mock_game):
        # Create mock state machine instead of importing
        class MockStateMachine:
            def __init__(self, game):
                self.game = game

        sm = MockStateMachine(mock_game)
        state = DeclarationState(sm)
        await state.on_enter()
        return state

    @pytest.mark.asyncio
    async def test_enter_phase_setup(self, declaration_state):
        """Test that entering declaration phase sets up correctly"""
        assert declaration_state.phase_data["current_declarer_index"] == 0
        assert declaration_state.phase_data["declarations"] == {}
        assert declaration_state.phase_data["declaration_total"] == 0
        assert len(declaration_state.phase_data["declaration_order"]) == 4

    @pytest.mark.asyncio
    async def test_valid_declaration(self, declaration_state):
        """Test processing a valid declaration"""
        action = GameAction(
            player_name="Player1",
            action_type=ActionType.DECLARE,
            payload={"value": 3},
            timestamp=datetime.now(),
            sequence_id=1,
        )

        result = await declaration_state.handle_action(action)

        assert result is not None
        assert result["status"] == "declaration_recorded"
        assert result["player"] == "Player1"
        assert result["value"] == 3
        assert declaration_state.phase_data["declarations"]["Player1"] == 3

    @pytest.mark.asyncio
    async def test_invalid_player_turn(self, declaration_state):
        """Test that wrong player can't declare out of turn"""
        action = GameAction(
            player_name="Player2",  # Player1 should go first
            action_type=ActionType.DECLARE,
            payload={"value": 3},
            timestamp=datetime.now(),
            sequence_id=1,
        )

        result = await declaration_state.handle_action(action)

        assert result is None  # Should be rejected

    @pytest.mark.asyncio
    async def test_invalid_action_type(self, declaration_state):
        """Test that wrong action types are rejected"""
        action = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,  # Wrong action for declaration phase
            payload={"pieces": ["card1"]},
            timestamp=datetime.now(),
            sequence_id=1,
        )

        result = await declaration_state.handle_action(action)

        assert result is None  # Should be rejected

    @pytest.mark.asyncio
    async def test_transition_conditions(self, declaration_state):
        """Test that transition happens when all players declare"""
        players = ["Player1", "Player2", "Player3", "Player4"]

        # Make all players declare
        for i, player in enumerate(players):
            action = GameAction(
                player_name=player,
                action_type=ActionType.DECLARE,
                payload={"value": i + 1},
                timestamp=datetime.now(),
                sequence_id=i,
            )
            await declaration_state.handle_action(action)

        # Check transition condition
        next_phase = await declaration_state.check_transition_conditions()
        assert next_phase == GamePhase.TURN


class TestStateMachine:

    @pytest.mark.asyncio
    async def test_start_and_current_phase(self, mock_game):
        """Test state machine startup"""
        sm = GameStateMachine(mock_game)
        await sm.start(GamePhase.DECLARATION)

        try:
            assert sm.get_current_phase() == GamePhase.DECLARATION
            assert ActionType.DECLARE in sm.get_allowed_actions()
        finally:
            await sm.stop()

    @pytest.mark.asyncio
    async def test_action_processing(self, state_machine):
        """Test that actions are properly processed"""
        action = GameAction(
            player_name="Player1",
            action_type=ActionType.DECLARE,
            payload={"value": 3},
            timestamp=datetime.now(),
            sequence_id=1,
        )

        await state_machine.handle_action(action)

        # Process all pending actions
        await state_machine.process_pending_actions()

        # Check that declaration was recorded
        assert state_machine.game.player_declarations.get("Player1") == 3

    @pytest.mark.asyncio
    async def test_full_declaration_round(self, state_machine):
        """Test complete declaration round with all players"""
        players = ["Player1", "Player2", "Player3", "Player4"]
        expected_declarations = {}

        # Each player declares
        for i, player in enumerate(players):
            value = i + 1
            expected_declarations[player] = value

            action = GameAction(
                player_name=player,
                action_type=ActionType.DECLARE,
                payload={"value": value},
                timestamp=datetime.now(),
                sequence_id=i,
            )

            await state_machine.handle_action(action)

        # Process all actions
        await state_machine.process_pending_actions()

        # Verify all declarations were recorded
        assert state_machine.game.player_declarations == expected_declarations

    @pytest.mark.asyncio
    async def test_invalid_actions_ignored(self, state_machine):
        """Test that invalid actions are ignored without breaking the state machine"""
        # Try to play pieces during declaration phase
        invalid_action = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": ["card1"]},
            timestamp=datetime.now(),
            sequence_id=1,
        )

        await state_machine.handle_action(invalid_action)
        await state_machine.process_pending_actions()

        # State machine should still be working
        assert state_machine.get_current_phase() == GamePhase.DECLARATION

        # Valid action should still work
        valid_action = GameAction(
            player_name="Player1",
            action_type=ActionType.DECLARE,
            payload={"value": 3},
            timestamp=datetime.now(),
            sequence_id=2,
        )

        await state_machine.handle_action(valid_action)
        await state_machine.process_pending_actions()

        assert state_machine.game.player_declarations.get("Player1") == 3
