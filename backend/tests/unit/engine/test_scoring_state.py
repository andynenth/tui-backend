# backend/tests/test_scoring_state.py

from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.states.scoring_state import ScoringState


class TestScoringState:
    """Comprehensive tests for ScoringState"""

    @pytest_asyncio.fixture
    async def mock_game(self):
        """Create mock game object"""
        game = Mock()
        game.players = []
        game.redeal_multiplier = 1
        game.round_number = 1
        game.game_over = False
        game.winners = []
        game.round_scores = {}
        game.turn_results = []
        game.current_turn_starter = None
        return game

    @pytest_asyncio.fixture
    async def mock_state_machine(self, mock_game):
        """Create mock state machine"""
        state_machine = Mock()
        state_machine.game = mock_game
        return state_machine

    @pytest_asyncio.fixture
    async def scoring_state(self, mock_state_machine):
        """Create ScoringState instance"""
        return ScoringState(mock_state_machine)

    @pytest_asyncio.fixture
    async def mock_players(self):
        """Create mock players with different scores"""
        players = []
        for i, name in enumerate(["Alice", "Bob", "Charlie", "Diana"]):
            player = Mock()
            player.name = name
            player.score = 0
            player.declared_piles = 0
            player.captured_piles = 0
            player.connected = True
            player.hand = []
            players.append(player)
        return players

    # Basic State Properties Tests

    def test_phase_name(self, scoring_state):
        """Test that phase_name returns SCORING"""
        assert scoring_state.phase_name == GamePhase.SCORING

    def test_next_phases(self, scoring_state):
        """Test that next_phases returns PREPARATION"""
        assert scoring_state.next_phases == [GamePhase.PREPARATION]

    def test_allowed_actions(self, scoring_state):
        """Test that allowed actions are correctly set"""
        expected_actions = {
            ActionType.GAME_STATE_UPDATE,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT,
        }
        assert scoring_state.allowed_actions == expected_actions

    def test_initial_state(self, scoring_state):
        """Test initial state values"""
        assert scoring_state.round_scores == {}
        assert scoring_state.game_complete == False
        assert scoring_state.winners == []
        assert scoring_state.scores_calculated == False

    # Scoring Logic Tests

    def test_calculate_base_score_perfect_zero(self, scoring_state):
        """Test perfect zero declaration (declared 0, got 0) = +3"""
        score = scoring_state._calculate_base_score(0, 0)
        assert score == 3

    def test_calculate_base_score_broken_zero(self, scoring_state):
        """Test broken zero declaration (declared 0, got >0) = -actual"""
        assert scoring_state._calculate_base_score(0, 1) == -1
        assert scoring_state._calculate_base_score(0, 3) == -3
        assert scoring_state._calculate_base_score(0, 5) == -5

    def test_calculate_base_score_perfect_match(self, scoring_state):
        """Test perfect matches (declared X, got X) = X + 5"""
        assert scoring_state._calculate_base_score(1, 1) == 6  # 1 + 5
        assert scoring_state._calculate_base_score(3, 3) == 8  # 3 + 5
        assert scoring_state._calculate_base_score(5, 5) == 10  # 5 + 5
        assert scoring_state._calculate_base_score(8, 8) == 13  # 8 + 5

    def test_calculate_base_score_missed_target(self, scoring_state):
        """Test missed targets (declared X, got ≠X) = -|difference|"""
        assert scoring_state._calculate_base_score(3, 1) == -2  # |3-1| = 2
        assert scoring_state._calculate_base_score(1, 3) == -2  # |1-3| = 2
        assert scoring_state._calculate_base_score(5, 2) == -3  # |5-2| = 3
        assert scoring_state._calculate_base_score(2, 5) == -3  # |2-5| = 3
        assert scoring_state._calculate_base_score(4, 0) == -4  # |4-0| = 4

    # Round Scoring Tests

    @pytest.mark.asyncio
    async def test_calculate_round_scores_no_multiplier(
        self, scoring_state, mock_players
    ):
        """Test calculating round scores without redeal multiplier"""
        # Setup players with different scenarios
        mock_players[0].declared_piles = 0  # Alice: perfect zero
        mock_players[0].captured_piles = 0

        mock_players[1].declared_piles = 3  # Bob: perfect match
        mock_players[1].captured_piles = 3

        mock_players[2].declared_piles = 2  # Charlie: missed target
        mock_players[2].captured_piles = 4

        mock_players[3].declared_piles = 0  # Diana: broken zero
        mock_players[3].captured_piles = 1

        scoring_state.state_machine.game.players = mock_players
        scoring_state.state_machine.game.redeal_multiplier = 1

        await scoring_state._calculate_round_scores()

        # Check calculated scores
        assert scoring_state.round_scores["Alice"]["base_score"] == 3
        assert scoring_state.round_scores["Alice"]["final_score"] == 3
        assert mock_players[0].score == 3

        assert scoring_state.round_scores["Bob"]["base_score"] == 8  # 3 + 5
        assert scoring_state.round_scores["Bob"]["final_score"] == 8
        assert mock_players[1].score == 8

        assert scoring_state.round_scores["Charlie"]["base_score"] == -2  # |2-4|
        assert scoring_state.round_scores["Charlie"]["final_score"] == -2
        assert mock_players[2].score == -2

        assert scoring_state.round_scores["Diana"]["base_score"] == -1
        assert scoring_state.round_scores["Diana"]["final_score"] == -1
        assert mock_players[3].score == -1

    @pytest.mark.asyncio
    async def test_calculate_round_scores_with_multiplier(
        self, scoring_state, mock_players
    ):
        """Test calculating round scores with redeal multiplier"""
        # Setup players
        mock_players[0].declared_piles = 3
        mock_players[0].captured_piles = 3  # Perfect match: 3 + 5 = 8

        mock_players[1].declared_piles = 0
        mock_players[1].captured_piles = 2  # Broken zero: -2

        scoring_state.state_machine.game.players = mock_players[
            :2
        ]  # Only use first 2 players
        scoring_state.state_machine.game.redeal_multiplier = 3  # Triple multiplier

        await scoring_state._calculate_round_scores()

        # Check multiplied scores
        assert scoring_state.round_scores["Alice"]["base_score"] == 8
        assert scoring_state.round_scores["Alice"]["final_score"] == 24  # 8 * 3
        assert scoring_state.round_scores["Alice"]["multiplier"] == 3
        assert mock_players[0].score == 24

        assert scoring_state.round_scores["Bob"]["base_score"] == -2
        assert scoring_state.round_scores["Bob"]["final_score"] == -6  # -2 * 3
        assert scoring_state.round_scores["Bob"]["multiplier"] == 3
        assert mock_players[1].score == -6

    # Winner Detection Tests

    @pytest.mark.asyncio
    async def test_check_game_winner_single_winner(self, scoring_state, mock_players):
        """Test detecting single game winner"""
        mock_players[0].score = 52  # Alice wins
        mock_players[1].score = 48  # Bob close but not enough
        mock_players[2].score = 35  # Charlie behind
        mock_players[3].score = 20  # Diana far behind

        scoring_state.state_machine.game.players = mock_players

        await scoring_state._check_game_winner()

        assert scoring_state.game_complete == True
        assert scoring_state.winners == ["Alice"]

    @pytest.mark.asyncio
    async def test_check_game_winner_tie(self, scoring_state, mock_players):
        """Test detecting tied winners"""
        mock_players[0].score = 55  # Alice ties for win
        mock_players[1].score = 55  # Bob ties for win
        mock_players[2].score = 45  # Charlie behind
        mock_players[3].score = 30  # Diana behind

        scoring_state.state_machine.game.players = mock_players

        await scoring_state._check_game_winner()

        assert scoring_state.game_complete == True
        assert set(scoring_state.winners) == {"Alice", "Bob"}

    @pytest.mark.asyncio
    async def test_check_game_winner_no_winner(self, scoring_state, mock_players):
        """Test no winner yet (all below 50 points)"""
        mock_players[0].score = 48  # Alice close but not enough
        mock_players[1].score = 45  # Bob behind
        mock_players[2].score = 40  # Charlie behind
        mock_players[3].score = 35  # Diana behind

        scoring_state.state_machine.game.players = mock_players

        await scoring_state._check_game_winner()

        assert scoring_state.game_complete == False
        assert scoring_state.winners == []

    @pytest.mark.asyncio
    async def test_check_game_winner_exactly_50(self, scoring_state, mock_players):
        """Test winner with exactly 50 points"""
        mock_players[0].score = 50  # Alice exactly at threshold
        mock_players[1].score = 49  # Bob one short

        scoring_state.state_machine.game.players = mock_players[:2]

        await scoring_state._check_game_winner()

        assert scoring_state.game_complete == True
        assert scoring_state.winners == ["Alice"]

    # Setup and Cleanup Tests

    @pytest.mark.asyncio
    async def test_setup_phase(self, scoring_state, mock_players):
        """Test setup phase calculates scores and checks winner"""
        mock_players[0].declared_piles = 3
        mock_players[0].captured_piles = 3
        mock_players[0].score = 45  # Will reach 53 (45 + 8)

        scoring_state.state_machine.game.players = mock_players[:1]
        scoring_state.state_machine.game.redeal_multiplier = 1

        await scoring_state._setup_phase()

        assert scoring_state.scores_calculated == True
        assert scoring_state.game_complete == True
        assert scoring_state.winners == ["Alice"]

    @pytest.mark.asyncio
    async def test_cleanup_phase_game_over(self, scoring_state):
        """Test cleanup when game is over"""
        scoring_state.game_complete = True
        scoring_state.winners = ["Alice"]
        scoring_state.round_scores = {"Alice": {"final_score": 10}}

        await scoring_state._cleanup_phase()

        assert scoring_state.state_machine.game.game_over == True
        assert scoring_state.state_machine.game.winners == ["Alice"]
        assert scoring_state.state_machine.game.round_scores == {
            "Alice": {"final_score": 10}
        }

    @pytest.mark.asyncio
    async def test_cleanup_phase_next_round(self, scoring_state, mock_players):
        """Test cleanup when continuing to next round"""
        scoring_state.game_complete = False
        scoring_state.state_machine.game.players = mock_players
        scoring_state.state_machine.game.round_number = 2

        # Setup some round data to clear
        for player in mock_players:
            player.hand = ["piece1", "piece2"]
            player.captured_piles = 3
            player.declared_piles = 2

        scoring_state.state_machine.game.redeal_multiplier = 2
        scoring_state.state_machine.game.turn_results = ["result1", "result2"]
        scoring_state.state_machine.game.current_turn_starter = "Alice"

        await scoring_state._cleanup_phase()

        # Check round number incremented
        assert scoring_state.state_machine.game.round_number == 3

        # Check player data reset
        for player in mock_players:
            assert player.hand == []
            assert player.captured_piles == 0
            assert player.declared_piles == 0

        # Check game data reset
        assert scoring_state.state_machine.game.redeal_multiplier == 1
        assert scoring_state.state_machine.game.turn_results == []
        assert scoring_state.state_machine.game.current_turn_starter == None

    # Action Validation Tests (simplified to match existing ActionTypes)

    @pytest.mark.asyncio
    async def test_validate_action_game_state_update(self, scoring_state):
        """Test validating GAME_STATE_UPDATE action"""
        action = GameAction("Alice", ActionType.GAME_STATE_UPDATE, {})
        result = await scoring_state._validate_action(action)
        assert result == True

    @pytest.mark.asyncio
    async def test_validate_action_disconnect_reconnect(self, scoring_state):
        """Test validating disconnect/reconnect actions"""
        disconnect_action = GameAction(
            "Alice", ActionType.PLAYER_DISCONNECT, {"player_name": "Alice"}
        )
        reconnect_action = GameAction(
            "Alice", ActionType.PLAYER_RECONNECT, {"player_name": "Alice"}
        )

        assert await scoring_state._validate_action(disconnect_action) == True
        assert await scoring_state._validate_action(reconnect_action) == True

    @pytest.mark.asyncio
    async def test_validate_action_timeout(self, scoring_state):
        """Test validating timeout action"""
        action = GameAction("Alice", ActionType.TIMEOUT, {})
        assert await scoring_state._validate_action(action) == True

    # Action Processing Tests

    @pytest.mark.asyncio
    async def test_handle_view_scores(self, scoring_state, mock_players):
        """Test handling GAME_STATE_UPDATE action to view scores"""
        scoring_state.round_scores = {"Alice": {"final_score": 8}}
        scoring_state.game_complete = True
        scoring_state.winners = ["Alice"]
        scoring_state.state_machine.game.players = mock_players[:1]
        scoring_state.state_machine.game.redeal_multiplier = 2

        action = GameAction("Alice", ActionType.GAME_STATE_UPDATE, {})
        result = await scoring_state._handle_view_scores(action)

        assert result["success"] == True
        assert result["data"]["round_scores"] == {"Alice": {"final_score": 8}}
        assert result["data"]["game_complete"] == True
        assert result["data"]["winners"] == ["Alice"]
        assert result["data"]["redeal_multiplier"] == 2
        assert "Alice" in result["data"]["total_scores"]

    @pytest.mark.asyncio
    async def test_handle_player_disconnect(self, scoring_state, mock_players):
        """Test handling player disconnection"""
        scoring_state.state_machine.game.players = mock_players

        action = GameAction("Bob", ActionType.PLAYER_DISCONNECT, {"player_name": "Bob"})
        result = await scoring_state._handle_player_disconnect(action)

        assert result["success"] == True
        assert mock_players[1].connected == False  # Bob is index 1
        assert result["data"]["disconnected_player"] == "Bob"

    @pytest.mark.asyncio
    async def test_handle_player_reconnect(self, scoring_state, mock_players):
        """Test handling player reconnection"""
        scoring_state.state_machine.game.players = mock_players
        scoring_state.round_scores = {"Charlie": {"final_score": 5}}
        scoring_state.game_complete = False

        # First disconnect Charlie
        mock_players[2].connected = False

        action = GameAction(
            "Charlie", ActionType.PLAYER_RECONNECT, {"player_name": "Charlie"}
        )
        result = await scoring_state._handle_player_reconnect(action)

        assert result["success"] == True
        assert mock_players[2].connected == True  # Charlie is index 2
        assert result["data"]["reconnected_player"] == "Charlie"
        assert result["data"]["round_scores"] == {"Charlie": {"final_score": 5}}
        assert result["data"]["game_complete"] == False

    # Transition Condition Tests

    @pytest.mark.asyncio
    async def test_check_transition_conditions_not_calculated(self, scoring_state):
        """Test transition conditions when scores not calculated"""
        scoring_state.scores_calculated = False
        result = await scoring_state.check_transition_conditions()
        assert result is None

    @pytest.mark.asyncio
    async def test_check_transition_conditions_game_complete(self, scoring_state):
        """Test transition conditions when game is complete"""
        scoring_state.scores_calculated = True
        scoring_state.game_complete = True
        result = await scoring_state.check_transition_conditions()
        assert result is None

    @pytest.mark.asyncio
    async def test_check_transition_conditions_next_round(self, scoring_state):
        """Test transition conditions for next round"""
        scoring_state.scores_calculated = True
        scoring_state.game_complete = False
        result = await scoring_state.check_transition_conditions()
        assert result == GamePhase.PREPARATION

    # Action Processing Integration Tests

    @pytest.mark.asyncio
    async def test_process_action_game_state_update(self, scoring_state, mock_players):
        """Test processing GAME_STATE_UPDATE action"""
        scoring_state.round_scores = {"Alice": {"final_score": 8}}
        scoring_state.state_machine.game.players = mock_players[:1]

        action = GameAction("Alice", ActionType.GAME_STATE_UPDATE, {})
        result = await scoring_state._process_action(action)

        assert result["success"] == True
        assert "round_scores" in result["data"]
        assert "total_scores" in result["data"]

    @pytest.mark.asyncio
    async def test_process_action_timeout(self, scoring_state):
        """Test processing TIMEOUT action"""
        action = GameAction("Alice", ActionType.TIMEOUT, {})
        result = await scoring_state._process_action(action)

        assert result["success"] == True
        assert "Timeout handled" in result["message"]
