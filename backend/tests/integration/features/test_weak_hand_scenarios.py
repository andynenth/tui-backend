# backend/tests/test_weak_hand_scenarios.py

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
import pytest_asyncio

from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.states.preparation_state import PreparationState


class MockGame:
    """Mock game class for testing complex scenarios"""

    def __init__(self):
        self.round = 1
        self.redeal_multiplier = 1
        self.current_player = None
        self.round_starter = None
        self.last_turn_winner = None
        self.players = ["PlayerA", "PlayerB", "PlayerC", "PlayerD"]

        # Track deal history for testing
        self.deal_history = []
        self.weak_hand_history = []

        # Mock methods
        self.deal_pieces = Mock(side_effect=self._mock_deal_pieces)
        self.get_weak_hand_players = Mock(side_effect=self._mock_get_weak_hands)
        self.get_player_order_from = Mock(return_value=self.players)

        # Control weak hands for testing
        self._weak_hand_scenarios = []
        self._scenario_index = 0

    def _mock_deal_pieces(self):
        """Track deals"""
        self.deal_history.append(f"Deal #{len(self.deal_history) + 1}")

    def _mock_get_weak_hands(self):
        """Return predetermined weak hand scenarios"""
        if self._scenario_index < len(self._weak_hand_scenarios):
            weak_players = self._weak_hand_scenarios[self._scenario_index]
            self._scenario_index += 1
            self.weak_hand_history.append(weak_players)
            return weak_players
        return []

    def set_weak_hand_scenarios(self, scenarios):
        """Set up a sequence of weak hand results"""
        self._weak_hand_scenarios = scenarios
        self._scenario_index = 0


@pytest.fixture
def mock_game_scenarios():
    """Create a mock game with scenario control"""
    return MockGame()


class TestComplexWeakHandScenarios:
    """Test complex weak hand and redeal scenarios"""

    @pytest_asyncio.fixture
    async def preparation_state(self, mock_game_scenarios):
        """Create preparation state with scenario-aware mock game"""

        class MockStateMachine:
            def __init__(self, game):
                self.game = game

        state_machine = MockStateMachine(mock_game_scenarios)
        state = PreparationState(state_machine)
        return state

    @pytest.mark.asyncio
    async def test_repeated_weak_hands_single_player(self, preparation_state):
        """Test when a player gets weak hands multiple times in a row"""
        state = preparation_state
        game = state.state_machine.game

        # Scenario: PlayerA gets weak hand 3 times in a row
        game.set_weak_hand_scenarios(
            [
                ["PlayerA"],  # First deal - PlayerA weak
                ["PlayerA"],  # After first redeal - PlayerA still weak
                ["PlayerA"],  # After second redeal - PlayerA STILL weak
                [],  # After third redeal - finally no weak hands
            ]
        )

        # Initial deal
        await state.on_enter()
        assert state.current_weak_player == "PlayerA"
        assert game.redeal_multiplier == 1

        # PlayerA accepts first redeal
        action1 = GameAction(
            player_name="PlayerA",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=0,
        )
        result1 = await state.handle_action(action1)
        assert result1["redeal"]
        assert game.redeal_multiplier == 2
        assert state.current_weak_player == "PlayerA"  # Still weak!

        # PlayerA accepts second redeal
        action2 = GameAction(
            player_name="PlayerA",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=1,
        )
        result2 = await state.handle_action(action2)
        assert result2["redeal"]
        assert game.redeal_multiplier == 3
        assert state.current_weak_player == "PlayerA"  # STILL weak!

        # PlayerA accepts third redeal
        action3 = GameAction(
            player_name="PlayerA",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=2,
        )
        result3 = await state.handle_action(action3)
        assert result3["redeal"]
        assert game.redeal_multiplier == 4

        # Finally no weak hands
        assert len(state.weak_players) == 0
        assert game.current_player == "PlayerA"  # PlayerA starts (was redeal requester)
        assert len(game.deal_history) == 4  # 4 total deals

    @pytest.mark.asyncio
    async def test_complex_multi_player_scenario(self, preparation_state):
        """Test the exact scenario described: A and B weak, A declines, B accepts, both weak again"""
        state = preparation_state
        game = state.state_machine.game

        # Setup the scenario
        game.set_weak_hand_scenarios(
            [
                ["PlayerA", "PlayerB"],  # First deal - A and B weak
                ["PlayerA", "PlayerB"],  # After first redeal - A and B still weak
                [],  # After second redeal - no weak hands
            ]
        )

        # Mock get_player_order_from to reflect play order changes
        def mock_get_player_order(starter):
            players = ["PlayerA", "PlayerB", "PlayerC", "PlayerD"]
            start_idx = players.index(starter)
            return players[start_idx:] + players[:start_idx]

        game.get_player_order_from = Mock(side_effect=mock_get_player_order)

        # Initial deal
        await state.on_enter()
        assert state.weak_players == {"PlayerA", "PlayerB"}

        # With original order A,B,C,D - PlayerA should be asked first
        assert state.current_weak_player == "PlayerA"

        # PlayerA declines
        decline_action = GameAction(
            player_name="PlayerA",
            action_type=ActionType.REDEAL_RESPONSE,
            payload={"accept": False},
            timestamp=datetime.now(),
            sequence_id=0,
        )
        result1 = await state.handle_action(decline_action)
        assert result1["next_weak_player"] == "PlayerB"
        assert game.redeal_multiplier == 1  # No redeal yet

        # PlayerB accepts
        accept_action = GameAction(
            player_name="PlayerB",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=1,
        )
        result2 = await state.handle_action(accept_action)
        assert result2["redeal"]
        assert result2["requester"] == "PlayerB"
        assert game.redeal_multiplier == 2
        assert game.current_player == "PlayerB"  # B is now starter

        # Both still have weak hands after redeal
        assert state.weak_players == {"PlayerA", "PlayerB"}

        # CRITICAL: With new order B,C,D,A - PlayerB should be asked first!
        assert state.current_weak_player == "PlayerB"

        # PlayerB declines this time
        decline_action2 = GameAction(
            player_name="PlayerB",
            action_type=ActionType.REDEAL_RESPONSE,
            payload={"accept": False},
            timestamp=datetime.now(),
            sequence_id=2,
        )
        result3 = await state.handle_action(decline_action2)
        assert result3["next_weak_player"] == "PlayerA"  # A is next in B,C,D,A order

        # PlayerA accepts this time
        accept_action2 = GameAction(
            player_name="PlayerA",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=3,
        )
        result4 = await state.handle_action(accept_action2)
        assert result4["redeal"]
        assert game.redeal_multiplier == 3

        # No more weak hands
        assert len(state.weak_players) == 0

        # PlayerA requested the LAST redeal, so PlayerA starts
        assert game.current_player == "PlayerA"
        assert state.redeal_requester == "PlayerA"

    @pytest.mark.asyncio
    async def test_unlimited_redeals_possible(self, preparation_state):
        """Test that redeals can continue indefinitely (no limit)"""
        state = preparation_state
        game = state.state_machine.game

        # PlayerC always has weak hands (simulating extremely bad luck)
        # Set up 10 rounds of weak hands to prove no limit
        scenarios = [["PlayerC"] for _ in range(10)] + [[]]  # Finally no weak
        game.set_weak_hand_scenarios(scenarios)

        # Start
        await state.on_enter()

        # Accept redeals 10 times
        for i in range(10):
            assert state.current_weak_player == "PlayerC"
            action = GameAction(
                player_name="PlayerC",
                action_type=ActionType.REDEAL_REQUEST,
                payload={"accept": True},
                timestamp=datetime.now(),
                sequence_id=i,
            )
            result = await state.handle_action(action)
            assert result["redeal"]
            assert game.redeal_multiplier == i + 2

        # After 10 redeals, multiplier is 11
        assert game.redeal_multiplier == 11
        # No forced no-weak deal - just got lucky finally
        assert len(state.weak_players) == 0
        assert game.current_player == "PlayerC"

    @pytest.mark.asyncio
    async def test_mixed_accept_decline_patterns(self, preparation_state):
        """Test various patterns of accepts and declines with realistic weak hand distribution"""
        state = preparation_state
        game = state.state_machine.game

        # Realistic scenario: Only 2 players have weak hands initially
        # (Having all 4 players with weak hands simultaneously is statistically very unlikely)
        game.set_weak_hand_scenarios(
            [
                ["PlayerA", "PlayerC"],  # Only A and C weak initially
                ["PlayerB"],  # After redeal, only B weak
                [],  # Finally none weak
            ]
        )

        await state.on_enter()
        assert len(state.weak_players) == 2  # Only A and C have weak hands

        # Simulate asking order: A, C (only these 2 have weak hands)
        # A declines
        action_a = GameAction(
            player_name="PlayerA",
            action_type=ActionType.REDEAL_RESPONSE,
            payload={"accept": False},
            timestamp=datetime.now(),
            sequence_id=0,
        )
        await state.handle_action(action_a)

        # C accepts - triggers redeal
        action_c = GameAction(
            player_name="PlayerC",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=1,
        )
        result_c = await state.handle_action(action_c)
        assert result_c["redeal"]
        assert state.redeal_requester == "PlayerC"

        # After redeal, only B has weak hand
        assert state.weak_players == {"PlayerB"}

        # B is the only one with weak hand now and accepts
        action_b2 = GameAction(
            player_name="PlayerB",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=2,
        )
        result_b2 = await state.handle_action(action_b2)
        assert result_b2["redeal"]

        # Final result: PlayerB requested the last redeal, so PlayerB starts
        assert game.current_player == "PlayerB"
        assert game.redeal_multiplier == 3  # Two redeals total

    @pytest.mark.asyncio
    async def test_disconnection_during_complex_scenario(self, preparation_state):
        """Test disconnections during multi-player weak hand scenarios"""
        state = preparation_state
        game = state.state_machine.game

        game.set_weak_hand_scenarios(
            [
                ["PlayerA", "PlayerB", "PlayerC"],  # Three weak players
            ]
        )

        await state.on_enter()

        # PlayerA disconnects while being asked
        if state.current_weak_player == "PlayerA":
            disconnect_action = GameAction(
                player_name="PlayerA",
                action_type=ActionType.PLAYER_DISCONNECT,
                payload={},
                timestamp=datetime.now(),
                sequence_id=0,
            )
            result = await state.handle_action(disconnect_action)
            assert result["success"]
            assert state.redeal_decisions["PlayerA"] is False  # Auto-declined
            assert state.current_weak_player in ["PlayerB", "PlayerC"]

    @pytest.mark.asyncio
    async def test_redeal_requester_priority_across_rounds(self, preparation_state):
        """Test that redeal requester priority works correctly"""
        state = preparation_state
        game = state.state_machine.game

        # Setup: PlayerD has GENERAL_RED
        player_a = Mock(name="PlayerA")
        player_a.name = "PlayerA"
        player_b = Mock(name="PlayerB")
        player_b.name = "PlayerB"
        player_c = Mock(name="PlayerC")
        player_c.name = "PlayerC"
        player_d = Mock(name="PlayerD")
        player_d.name = "PlayerD"
        player_d.hand = [Mock(name="GENERAL_RED")]

        game.players = [player_a, player_b, player_c, player_d]

        game.set_weak_hand_scenarios(
            [["PlayerB"], []]  # Only PlayerB weak  # No weak after redeal
        )

        await state.on_enter()

        # PlayerB accepts redeal
        action = GameAction(
            player_name="PlayerB",
            action_type=ActionType.REDEAL_REQUEST,
            payload={"accept": True},
            timestamp=datetime.now(),
            sequence_id=0,
        )
        await state.handle_action(action)

        # Even though PlayerD has GENERAL_RED, PlayerB should start (redeal requester)
        assert game.current_player == "PlayerB"
        assert hasattr(game, "round_starter")
        assert game.round_starter == "PlayerB"
