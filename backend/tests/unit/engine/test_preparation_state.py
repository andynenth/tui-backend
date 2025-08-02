# backend/tests/test_preparation_state.py

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio

from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.states.preparation_state import PreparationState


class MockGame:
    """Mock game class for testing"""

    def __init__(self):
        self.round = 1
        self.redeal_multiplier = 1
        self.current_player = None
        self.round_starter = None
        self.last_turn_winner = None
        self.players = ["Player1", "Player2", "Player3", "Player4"]

        # Mock methods
        self.deal_pieces = Mock()
        self.get_weak_hand_players = Mock(return_value=[])

        # Mock get_player_order_from to return proper order
        def _get_player_order(starter):
            if starter in self.players:
                idx = self.players.index(starter)
                return self.players[idx:] + self.players[:idx]
            return self.players

        self.get_player_order_from = Mock(side_effect=_get_player_order)


@pytest.fixture
def mock_game():
    """Create a mock game instance"""
    return MockGame()


class TestPreparationState:
    """Test suite for Preparation phase state"""

    @pytest_asyncio.fixture
    async def preparation_state(self, mock_game):
        """Create preparation state with mock game"""

        # Create mock state machine
        class MockStateMachine:
            def __init__(self, game):
                self.game = game

        state_machine = MockStateMachine(mock_game)
        state = PreparationState(state_machine)

        return state

    @pytest.mark.asyncio
    async def test_enter_phase_deals_cards(self, preparation_state):
        """Test that entering phase deals cards"""
        state = preparation_state
        game = state.state_machine.game

        await state.on_enter()

        # Should have dealt cards
        game.deal_pieces.assert_called_once()
        assert state.initial_deal_complete

    @pytest.mark.asyncio
    async def test_no_weak_hands_sets_starter(self, preparation_state):
        """Test starter selection when no weak hands"""
        state = preparation_state
        game = state.state_machine.game

        # Mock player with GENERAL_RED for round 1
        mock_player = Mock()
        mock_player.name = "Player1"
        mock_piece = Mock()
        mock_piece.name = "GENERAL_RED"
        mock_player.hand = [mock_piece]
        game.players = [mock_player, Mock(name="Player2")]

        await state.on_enter()

        # Should set starter to player with GENERAL_RED
        assert game.current_player == "Player1"

    @pytest.mark.asyncio
    async def test_weak_hand_detection(self, preparation_state):
        """Test weak hand detection and setup"""
        state = preparation_state
        game = state.state_machine.game

        # Mock weak hand detection
        game.get_weak_hand_players.return_value = ["Player1", "Player3"]

        await state.on_enter()

        # Should identify weak players
        assert state.weak_players == {"Player1", "Player3"}
        # Order doesn't matter for pending players, just check they're both there
        assert set(state.pending_weak_players) == {"Player1", "Player3"}
        assert state.current_weak_player in ["Player1", "Player3"]

    @pytest.mark.asyncio
    async def test_redeal_accept_flow(self, preparation_state):
        """Test accepting redeal request"""
        state = preparation_state
        game = state.state_machine.game

        # Set up weak player state
        state.weak_players = {"Player1"}
        state.current_weak_player = "Player1"
        state.pending_weak_players = ["Player1"]
        state.initial_deal_complete = True

        # Create redeal accept action
        action = GameAction(
            player_name="Player1",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=0,
        )

        # Reset mock
        game.deal_pieces.reset_mock()

        # Process action
        result = await state.handle_action(action)

        # Should trigger redeal
        assert result["success"]
        assert result["redeal"]
        assert result["requester"] == "Player1"
        assert game.redeal_multiplier == 2
        game.deal_pieces.assert_called_once()

        # State should be reset
        assert len(state.weak_players) == 0
        assert len(state.redeal_decisions) == 0
        assert state.redeal_requester == "Player1"

    @pytest.mark.asyncio
    async def test_redeal_decline_flow(self, preparation_state):
        """Test declining redeal request"""
        state = preparation_state
        game = state.state_machine.game

        # Set up multiple weak players
        state.weak_players = {"Player1", "Player3"}
        state.current_weak_player = "Player1"
        state.pending_weak_players = ["Player1", "Player3"]
        state.initial_deal_complete = True

        # Player1 declines
        action = GameAction(
            player_name="Player1",
            action_type=ActionType.REDEAL_RESPONSE,
            payload={"accept": False},
            timestamp=datetime.now(),
            sequence_id=0,
        )

        result = await state.handle_action(action)

        # Should move to next weak player
        assert result["success"]
        assert result["next_weak_player"] == "Player3"
        assert state.current_weak_player == "Player3"
        assert state.redeal_decisions["Player1"] is False

    @pytest.mark.asyncio
    async def test_all_decline_sets_starter(self, preparation_state):
        """Test that all players declining sets starter"""
        state = preparation_state
        game = state.state_machine.game

        # Set up last weak player
        state.weak_players = {"Player3"}
        state.current_weak_player = "Player3"
        state.pending_weak_players = ["Player3"]
        state.initial_deal_complete = True
        state.redeal_decisions = {"Player1": False}  # Others already declined

        # Last player declines
        action = GameAction(
            player_name="Player3",
            action_type=ActionType.REDEAL_RESPONSE,
            payload={"accept": False},
            timestamp=datetime.now(),
            sequence_id=0,
        )

        result = await state.handle_action(action)

        # Should finalize and set starter
        assert result["success"]
        assert result["all_declined"]
        assert game.current_player is not None

    @pytest.mark.asyncio
    async def test_starter_priority_redeal_requester(self, preparation_state):
        """Test redeal requester has highest priority for starter"""
        state = preparation_state
        game = state.state_machine.game

        # Set up round 1 with GENERAL_RED player
        game.round = 1
        player_with_general = Mock(name="Player2")
        mock_piece = Mock()
        mock_piece.name = "GENERAL_RED"
        player_with_general.hand = [mock_piece]
        game.players = [Mock(name="Player1"), player_with_general]

        # But Player1 requested redeal
        state.redeal_requester = "Player1"

        starter = state._determine_starter()

        # Redeal requester should override GENERAL_RED
        assert starter == "Player1"

    @pytest.mark.asyncio
    async def test_multiple_redeals_no_limit(self, preparation_state):
        """Test that redeals can continue without limit"""
        state = preparation_state
        game = state.state_machine.game

        # Simulate multiple rounds of weak hands
        game.get_weak_hand_players.side_effect = [
            ["Player1"],  # Round 1: weak
            ["Player1"],  # Round 2: still weak
            ["Player1"],  # Round 3: still weak
            [],  # Round 4: finally no weak
        ]

        # Initial deal
        await state.on_enter()

        # Multiple redeals
        for i in range(3):
            action = GameAction(
                player_name="Player1",
                action_type=ActionType.REDEAL_REQUEST,
                payload={"accept": True},
                timestamp=datetime.now(),
                sequence_id=i,
            )
            result = await state.handle_action(action)
            assert result["redeal"]
            assert game.redeal_multiplier == i + 2

        # Can continue beyond 3 redeals - no limit
        assert game.redeal_multiplier == 4
        # Regular deal, not forced no-weak
        assert game.deal_pieces.call_count == 4

    @pytest.mark.asyncio
    async def test_transition_conditions(self, preparation_state):
        """Test transition to Declaration phase"""
        state = preparation_state

        # Not ready if initial deal not complete
        state.initial_deal_complete = False
        assert await state.check_transition_conditions() is None

        # Ready if no weak players
        state.initial_deal_complete = True
        state.weak_players = set()
        assert await state.check_transition_conditions() == GamePhase.DECLARATION

        # Not ready if weak players haven't decided
        state.weak_players = {"Player1", "Player2"}
        state.redeal_decisions = {"Player1": False}
        assert await state.check_transition_conditions() is None

        # Ready when all weak players decided
        state.redeal_decisions = {"Player1": False, "Player2": False}
        assert await state.check_transition_conditions() == GamePhase.DECLARATION

    @pytest.mark.asyncio
    async def test_player_disconnect_during_redeal(self, preparation_state):
        """Test handling disconnection during redeal decision"""
        state = preparation_state

        # Player being asked disconnects
        state.current_weak_player = "Player1"
        state.pending_weak_players = ["Player1", "Player2"]
        state.weak_players = {"Player1", "Player2"}

        action = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAYER_DISCONNECT,
            payload={},
            timestamp=datetime.now(),
            sequence_id=0,
        )

        result = await state.handle_action(action)

        # Should auto-decline and move to next
        assert result["success"]
        assert state.current_weak_player == "Player2"
        assert state.redeal_decisions["Player1"] is False

    @pytest.mark.asyncio
    async def test_invalid_redeal_request_wrong_player(self, preparation_state):
        """Test that wrong player cannot request redeal"""
        state = preparation_state

        # Set up Player1 as current weak player
        state.current_weak_player = "Player1"
        state.weak_players = {"Player1", "Player2"}

        # Player2 tries to request redeal
        action = GameAction(
            player_name="Player2",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=0,
        )

        # Should be invalid
        result = await state.handle_action(action)
        assert result is None  # Invalid actions return None

    @pytest.mark.asyncio
    async def test_fallback_starter_selection(self, preparation_state):
        """Test fallback starter selection when no special conditions"""
        state = preparation_state
        game = state.state_machine.game

        # Round > 1, no last winner, no redeal requester
        game.round = 2
        game.last_turn_winner = None
        state.redeal_requester = None
        game.players = ["Player1", "Player2", "Player3", "Player4"]

        starter = state._determine_starter()

        # Should fall back to first player
        assert starter == "Player1"

    @pytest.mark.asyncio
    async def test_round_starter_set_correctly(self, preparation_state):
        """Test that round_starter is set correctly in simple case"""
        state = preparation_state
        game = state.state_machine.game

        # No weak hands scenario
        game.get_weak_hand_players.return_value = []

        # Enter and exit phase
        await state.on_enter()
        await state.on_exit()

        # Both current_player and round_starter should be set
        assert game.current_player is not None
        assert game.round_starter is not None
        assert game.round_starter == game.current_player

    @pytest.mark.asyncio
    async def test_cleanup_phase_sets_starter(self, preparation_state):
        """Test that cleanup phase properly sets both current_player and round_starter"""
        state = preparation_state
        game = state.state_machine.game

        # Manually set some state
        game.current_player = "TestPlayer"

        # Call cleanup directly
        await state._cleanup_phase()

        # Should set round_starter to match current_player
        assert game.round_starter == "TestPlayer"
