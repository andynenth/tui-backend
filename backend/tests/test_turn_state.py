# backend/tests/test_turn_state.py

from datetime import datetime
from unittest.mock import Mock

import pytest
import pytest_asyncio

from engine.piece import Piece
from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.states.turn_state import TurnState
from tests.test_helpers import create_test_hand_realistic, create_test_play_data


class MockGame:
    def __init__(self):
        self.players = ["Player1", "Player2", "Player3", "Player4"]
        self.round_starter = "Player1"
        self.current_player = "Player1"
        # Use realistic piece data instead of integers
        self.player_hands = create_test_hand_realistic()
        self.player_piles = {"Player1": 0, "Player2": 0, "Player3": 0, "Player4": 0}

    def get_player_order_from(self, starter):
        start_idx = self.players.index(starter)
        return self.players[start_idx:] + self.players[:start_idx]


class MockStateMachine:
    def __init__(self, game):
        self.game = game


@pytest_asyncio.fixture
async def turn_state(mock_game):
    """Create a TurnState instance for testing"""
    state_machine = MockStateMachine(mock_game)
    state = TurnState(state_machine)
    await state.on_enter()
    return state


@pytest.fixture
def mock_game():
    return MockGame()


class TestTurnState:

    @pytest.mark.asyncio
    async def test_enter_phase_setup(self, turn_state):
        """Test turn phase initialization"""
        # Check phase properties
        assert turn_state.phase_name == GamePhase.TURN
        assert GamePhase.SCORING in turn_state.next_phases

        # Check allowed actions
        expected_actions = {
            ActionType.PLAY_PIECES,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT,
        }
        assert turn_state.allowed_actions == expected_actions

        # Check initial state
        assert turn_state.current_turn_starter == "Player1"
        assert turn_state.turn_order == ["Player1", "Player2", "Player3", "Player4"]
        assert turn_state.required_piece_count is None
        assert turn_state.turn_plays == {}
        assert not turn_state.turn_complete
        assert turn_state.winner is None

    @pytest.mark.asyncio
    async def test_starter_sets_piece_count(self, turn_state):
        """Test that starter's play sets the required piece count"""
        # Get realistic pieces from Player1's hand
        player1_pieces = turn_state.state_machine.game.player_hands["Player1"]
        play_pieces = player1_pieces[:3]  # Take first 3 pieces

        # Calculate realistic play value (sum of piece points)
        play_value = sum(piece.point for piece in play_pieces)

        # Starter plays 3 pieces
        action = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": play_pieces,
                "play_type": "sequence",
                "play_value": play_value,
                "is_valid": True,
            },
        )

        # Validate and process action
        is_valid = await turn_state._validate_action(action)
        assert is_valid

        result = await turn_state._process_action(action)

        # Check results
        assert result["status"] == "play_accepted"
        assert result["required_count"] == 3
        assert turn_state.required_piece_count == 3
        assert "Player1" in turn_state.turn_plays
        assert turn_state.turn_plays["Player1"]["piece_count"] == 3

    @pytest.mark.asyncio
    async def test_other_players_must_match_count(self, turn_state):
        """Test that other players must play same number of pieces as starter"""
        # Get realistic pieces for starter
        player1_pieces = turn_state.state_machine.game.player_hands["Player1"]
        starter_play = player1_pieces[:2]  # Take first 2 pieces
        starter_value = sum(piece.point for piece in starter_play)

        # Starter plays 2 pieces
        starter_action = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": starter_play,
                "play_type": "pair",
                "play_value": starter_value,
            },
        )
        await turn_state._process_action(starter_action)

        # Get realistic pieces for Player2
        player2_pieces = turn_state.state_machine.game.player_hands["Player2"]

        # Player2 tries to play 3 pieces (invalid)
        invalid_play = player2_pieces[:3]
        invalid_value = sum(piece.point for piece in invalid_play)
        invalid_action = GameAction(
            player_name="Player2",
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": invalid_play,
                "play_type": "sequence",
                "play_value": invalid_value,
            },
        )

        is_valid = await turn_state._validate_action(invalid_action)
        assert not is_valid

        # Player2 plays correct number (valid)
        valid_play = player2_pieces[:2]  # Take first 2 pieces
        valid_value = sum(piece.point for piece in valid_play)
        valid_action = GameAction(
            player_name="Player2",
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": valid_play,
                "play_type": "pair",
                "play_value": valid_value,
            },
        )

        is_valid = await turn_state._validate_action(valid_action)
        assert is_valid

    @pytest.mark.asyncio
    async def test_wrong_player_turn_rejected(self, turn_state):
        """Test that plays from wrong player are rejected"""
        # Player2 tries to play when it's Player1's turn
        action = GameAction(
            player_name="Player2",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [9, 10], "play_type": "pair", "play_value": 19},
        )

        is_valid = await turn_state._validate_action(action)
        assert not is_valid

    @pytest.mark.asyncio
    async def test_starter_piece_count_limits(self, turn_state):
        """Test that starter must play 1-6 pieces"""
        # Too few pieces (0)
        action_zero = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [], "play_type": "none", "play_value": 0},
        )
        is_valid = await turn_state._validate_action(action_zero)
        assert not is_valid

        # Too many pieces (7)
        action_seven = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": [1, 2, 3, 4, 5, 6, 7],
                "play_type": "sequence",
                "play_value": 28,
            },
        )
        is_valid = await turn_state._validate_action(action_seven)
        assert not is_valid

        # Valid counts (1-6)
        for count in range(1, 7):
            pieces = list(range(1, count + 1))
            action = GameAction(
                player_name="Player1",
                action_type=ActionType.PLAY_PIECES,
                payload={
                    "pieces": pieces,
                    "play_type": "valid",
                    "play_value": sum(pieces),
                },
            )
            is_valid = await turn_state._validate_action(action)
            assert is_valid

    @pytest.mark.asyncio
    async def test_player_cannot_play_twice(self, turn_state):
        """Test that a player cannot play twice in the same turn"""
        # Player1 plays first
        action1 = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [1, 2], "play_type": "pair", "play_value": 3},
        )
        await turn_state._process_action(action1)

        # Player1 tries to play again
        action2 = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [3, 4], "play_type": "pair", "play_value": 7},
        )

        is_valid = await turn_state._validate_action(action2)
        assert not is_valid

    @pytest.mark.asyncio
    async def test_complete_turn_sequence(self, turn_state):
        """Test a complete turn with all players"""
        # Player1 (starter) plays 2 pieces
        action1 = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [1, 2], "play_type": "pair", "play_value": 10},
        )
        result1 = await turn_state._process_action(action1)
        assert result1["next_player"] == "Player2"
        assert not result1["turn_complete"]

        # Player2 plays 2 pieces
        action2 = GameAction(
            player_name="Player2",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [9, 10], "play_type": "pair", "play_value": 15},
        )
        result2 = await turn_state._process_action(action2)
        assert result2["next_player"] == "Player3"
        assert not result2["turn_complete"]

        # Player3 plays 2 pieces
        action3 = GameAction(
            player_name="Player3",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [17, 18], "play_type": "pair", "play_value": 20},
        )
        result3 = await turn_state._process_action(action3)
        assert result3["next_player"] == "Player4"
        assert not result3["turn_complete"]

        # Player4 plays 2 pieces (completes turn)
        action4 = GameAction(
            player_name="Player4",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [25, 26], "play_type": "pair", "play_value": 8},
        )
        result4 = await turn_state._process_action(action4)
        assert result4["turn_complete"]

        # Check turn completion
        assert turn_state.turn_complete
        assert len(turn_state.turn_plays) == 4

    @pytest.mark.asyncio
    async def test_winner_determination_by_value(self, turn_state):
        """Test winner determination based on play value"""
        # Set up plays with different values
        plays = [
            ("Player1", {"pieces": [1, 2], "play_type": "pair", "play_value": 10}),
            ("Player2", {"pieces": [9, 10], "play_type": "pair", "play_value": 15}),
            (
                "Player3",
                {"pieces": [17, 18], "play_type": "pair", "play_value": 20},
            ),  # Highest
            ("Player4", {"pieces": [25, 26], "play_type": "pair", "play_value": 8}),
        ]

        # Process all plays
        for player, payload in plays:
            action = GameAction(
                player_name=player, action_type=ActionType.PLAY_PIECES, payload=payload
            )
            await turn_state._process_action(action)

        # Player3 should win with highest value (20)
        assert turn_state.winner == "Player3"
        assert (
            turn_state.state_machine.game.player_piles["Player3"] == 2
        )  # Required piece count

    @pytest.mark.asyncio
    async def test_winner_determination_by_play_order(self, turn_state):
        """Test winner determination by play order when values are tied"""
        # Set up plays with same values
        plays = [
            ("Player1", {"pieces": [1, 2], "play_type": "pair", "play_value": 15}),
            (
                "Player2",
                {"pieces": [9, 10], "play_type": "pair", "play_value": 15},
            ),  # Same value, but later
            ("Player3", {"pieces": [17, 18], "play_type": "pair", "play_value": 10}),
            ("Player4", {"pieces": [25, 26], "play_type": "pair", "play_value": 8}),
        ]

        # Process all plays
        for player, payload in plays:
            action = GameAction(
                player_name=player, action_type=ActionType.PLAY_PIECES, payload=payload
            )
            await turn_state._process_action(action)

        # Player1 should win (earlier play order with tied highest value)
        assert turn_state.winner == "Player1"

    @pytest.mark.asyncio
    async def test_different_play_types_ignored(self, turn_state):
        """Test that only plays matching starter's type are considered"""
        # Set up plays with different types
        plays = [
            (
                "Player1",
                {"pieces": [1, 2], "play_type": "pair", "play_value": 10},
            ),  # Starter type
            (
                "Player2",
                {"pieces": [9, 10], "play_type": "sequence", "play_value": 50},
            ),  # Different type, high value
            (
                "Player3",
                {"pieces": [17, 18], "play_type": "pair", "play_value": 15},
            ),  # Same type as starter
            (
                "Player4",
                {"pieces": [25, 26], "play_type": "single", "play_value": 100},
            ),  # Different type
        ]

        # Process all plays
        for player, payload in plays:
            action = GameAction(
                player_name=player, action_type=ActionType.PLAY_PIECES, payload=payload
            )
            await turn_state._process_action(action)

        # Player3 should win (highest value among 'pair' type plays)
        assert turn_state.winner == "Player3"

    @pytest.mark.asyncio
    async def test_invalid_plays_ignored(self, turn_state):
        """Test that invalid plays cannot win"""
        # Set up plays with invalid flag
        plays = [
            (
                "Player1",
                {
                    "pieces": [1, 2],
                    "play_type": "pair",
                    "play_value": 10,
                    "is_valid": True,
                },
            ),
            (
                "Player2",
                {
                    "pieces": [9, 10],
                    "play_type": "pair",
                    "play_value": 50,
                    "is_valid": False,
                },
            ),  # Invalid
            (
                "Player3",
                {
                    "pieces": [17, 18],
                    "play_type": "pair",
                    "play_value": 8,
                    "is_valid": True,
                },
            ),
            (
                "Player4",
                {
                    "pieces": [25, 26],
                    "play_type": "pair",
                    "play_value": 100,
                    "is_valid": False,
                },
            ),  # Invalid
        ]

        # Process all plays
        for player, payload in plays:
            action = GameAction(
                player_name=player, action_type=ActionType.PLAY_PIECES, payload=payload
            )
            await turn_state._process_action(action)

        # Player1 should win (highest value among valid plays)
        assert turn_state.winner == "Player1"

    @pytest.mark.asyncio
    async def test_no_valid_plays_no_winner(self, turn_state):
        """Test that no winner is determined when no valid plays exist"""
        # Set up all invalid plays
        plays = [
            (
                "Player1",
                {
                    "pieces": [1, 2],
                    "play_type": "pair",
                    "play_value": 10,
                    "is_valid": False,
                },
            ),
            (
                "Player2",
                {
                    "pieces": [9, 10],
                    "play_type": "pair",
                    "play_value": 15,
                    "is_valid": False,
                },
            ),
            (
                "Player3",
                {
                    "pieces": [17, 18],
                    "play_type": "pair",
                    "play_value": 20,
                    "is_valid": False,
                },
            ),
            (
                "Player4",
                {
                    "pieces": [25, 26],
                    "play_type": "pair",
                    "play_value": 8,
                    "is_valid": False,
                },
            ),
        ]

        # Process all plays
        for player, payload in plays:
            action = GameAction(
                player_name=player, action_type=ActionType.PLAY_PIECES, payload=payload
            )
            await turn_state._process_action(action)

        # No winner should be determined
        assert turn_state.winner is None

    @pytest.mark.asyncio
    async def test_player_disconnect_during_turn(self, turn_state):
        """Test handling player disconnection during their turn"""
        # Player1 starts, then Player2's turn
        action1 = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [1, 2], "play_type": "pair", "play_value": 10},
        )
        await turn_state._process_action(action1)

        # Player2 disconnects during their turn
        disconnect_action = GameAction(
            player_name="Player2", action_type=ActionType.PLAYER_DISCONNECT, payload={}
        )

        result = await turn_state._process_action(disconnect_action)
        assert result["status"] == "player_disconnected"
        assert result["player"] == "Player2"

        # Should have auto-played for Player2
        assert "Player2" in turn_state.turn_plays
        assert (
            turn_state.turn_plays["Player2"]["is_valid"] == False
        )  # Auto-plays are invalid

    @pytest.mark.asyncio
    async def test_timeout_handling(self, turn_state):
        """Test handling action timeout"""
        # Player1 starts
        action1 = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [1, 2], "play_type": "pair", "play_value": 10},
        )
        await turn_state._process_action(action1)

        # Timeout occurs for Player2
        timeout_action = GameAction(
            player_name="System", action_type=ActionType.TIMEOUT, payload={}
        )

        result = await turn_state._process_action(timeout_action)
        assert result["status"] == "timeout_handled"
        assert result["player"] == "Player2"

        # Should have auto-played for Player2
        assert "Player2" in turn_state.turn_plays

    @pytest.mark.asyncio
    async def test_pieces_removed_from_hands(self, turn_state):
        """Test that played pieces are removed from player hands"""
        game = turn_state.state_machine.game
        initial_hand_size = len(game.player_hands["Player1"])

        # Get realistic pieces for each player
        player1_pieces = game.player_hands["Player1"][:2]
        player2_pieces = game.player_hands["Player2"][:2]
        player3_pieces = game.player_hands["Player3"][:2]
        player4_pieces = game.player_hands["Player4"][:2]

        # Complete a turn with realistic pieces
        plays = [
            (
                "Player1",
                {
                    "pieces": player1_pieces,
                    "play_type": "pair",
                    "play_value": sum(p.point for p in player1_pieces),
                },
            ),
            (
                "Player2",
                {
                    "pieces": player2_pieces,
                    "play_type": "pair",
                    "play_value": sum(p.point for p in player2_pieces),
                },
            ),
            (
                "Player3",
                {
                    "pieces": player3_pieces,
                    "play_type": "pair",
                    "play_value": sum(p.point for p in player3_pieces),
                },
            ),
            (
                "Player4",
                {
                    "pieces": player4_pieces,
                    "play_type": "pair",
                    "play_value": sum(p.point for p in player4_pieces),
                },
            ),
        ]

        for player, payload in plays:
            action = GameAction(
                player_name=player, action_type=ActionType.PLAY_PIECES, payload=payload
            )
            await turn_state._process_action(action)

        # Check that pieces were removed
        assert len(game.player_hands["Player1"]) == initial_hand_size - 2
        # Check that the specific pieces are no longer in the hand
        for piece in player1_pieces:
            assert piece not in game.player_hands["Player1"]

    @pytest.mark.asyncio
    async def test_transition_to_scoring_when_hands_empty(self, turn_state):
        """Test transition to scoring phase when all hands are empty"""
        game = turn_state.state_machine.game

        # Empty all hands
        for player in game.player_hands:
            game.player_hands[player] = []

        # Check transition condition
        next_phase = await turn_state.check_transition_conditions()
        assert next_phase == GamePhase.SCORING

    @pytest.mark.asyncio
    async def test_next_turn_starter_is_winner(self, turn_state):
        """Test that turn winner becomes next turn starter"""
        # Complete a turn where Player3 wins
        plays = [
            ("Player1", {"pieces": [1, 2], "play_type": "pair", "play_value": 10}),
            ("Player2", {"pieces": [9, 10], "play_type": "pair", "play_value": 15}),
            (
                "Player3",
                {"pieces": [17, 18], "play_type": "pair", "play_value": 20},
            ),  # Winner
            ("Player4", {"pieces": [25, 26], "play_type": "pair", "play_value": 8}),
        ]

        for player, payload in plays:
            action = GameAction(
                player_name=player, action_type=ActionType.PLAY_PIECES, payload=payload
            )
            await turn_state._process_action(action)

        # Winner should become next turn starter
        assert turn_state.current_turn_starter == "Player3"
        assert turn_state.turn_order[0] == "Player3"  # First in new turn order

    @pytest.mark.asyncio
    async def test_phase_data_updates(self, turn_state):
        """Test that phase data is properly updated throughout the turn"""
        # Check initial phase data
        phase_data = turn_state.phase_data
        assert phase_data["current_turn_starter"] == "Player1"
        assert phase_data["current_player"] == "Player1"
        assert phase_data["required_piece_count"] is None
        assert not phase_data["turn_complete"]

        # Player1 plays
        action = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [1, 2], "play_type": "pair", "play_value": 10},
        )
        await turn_state._process_action(action)

        # Check updated phase data
        assert turn_state.phase_data["current_player"] == "Player2"
        assert turn_state.phase_data["required_piece_count"] == 2
        assert "Player1" in turn_state.phase_data["turn_plays"]
