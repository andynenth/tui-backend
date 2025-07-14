"""
Simple focused tests for Round Start functionality
These tests are more isolated and don't rely on full state machine flow
"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from engine.state_machine.states.round_start_state import RoundStartState
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase
from engine.game import Game
from engine.player import Player
from engine.piece import Piece


class TestRoundStartSimple:
    """Simple isolated tests for round start functionality"""

    @pytest.mark.asyncio
    async def test_round_start_phase_data(self):
        """Test that RoundStartState sets correct phase data"""
        # Create game
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        game.round_number = 3
        game.current_player = "Player2"
        game.starter_reason = "won_last_turn"

        # Create state machine
        sm = GameStateMachine(game)
        sm.current_phase = GamePhase.ROUND_START

        # Create round start state
        round_start_state = RoundStartState(sm)

        # Setup phase
        await round_start_state._setup_phase()

        # Check phase data
        assert round_start_state.phase_data["round_number"] == 3
        assert round_start_state.phase_data["starter"] == "Player2"
        assert round_start_state.phase_data["starter_reason"] == "won_last_turn"
        assert round_start_state.phase_data["display_duration"] == 5.0

    @pytest.mark.asyncio
    async def test_round_start_timer(self):
        """Test that timer works correctly"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        sm = GameStateMachine(game)

        round_start_state = RoundStartState(sm)

        # Initially no transition
        assert await round_start_state.check_transition_conditions() is None

        # Set start time
        round_start_state.start_time = time.time()

        # Still no transition immediately
        assert await round_start_state.check_transition_conditions() is None

        # Mock time passed
        round_start_state.start_time = time.time() - 6  # 6 seconds ago

        # Should transition now
        assert (
            await round_start_state.check_transition_conditions()
            == GamePhase.DECLARATION
        )

    @pytest.mark.asyncio
    async def test_starter_determination_general_red(self):
        """Test starter determination when player has GENERAL_RED"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        game.round_number = 1

        # Give Player3 the GENERAL_RED
        players[2].hand = [Piece("GENERAL_RED"), Piece("HORSE_BLACK")]

        # Create state machine and preparation state
        sm = GameStateMachine(game)
        from engine.state_machine.states.preparation_state import PreparationState

        prep_state = PreparationState(sm)

        # Determine starter
        starter = prep_state._determine_starter()

        assert starter == "Player3"
        assert game.starter_reason == "has_general_red"

    @pytest.mark.asyncio
    async def test_starter_determination_previous_winner(self):
        """Test starter determination for round 2+"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        game.round_number = 2
        game.last_turn_winner = "Player4"

        sm = GameStateMachine(game)
        from engine.state_machine.states.preparation_state import PreparationState

        prep_state = PreparationState(sm)

        starter = prep_state._determine_starter()

        assert starter == "Player4"
        assert game.starter_reason == "won_last_turn"

    @pytest.mark.asyncio
    async def test_starter_determination_redeal(self):
        """Test starter determination after redeal"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)

        sm = GameStateMachine(game)
        from engine.state_machine.states.preparation_state import PreparationState

        prep_state = PreparationState(sm)
        prep_state.redeal_requester = "Player1"

        starter = prep_state._determine_starter()

        assert starter == "Player1"
        assert game.starter_reason == "accepted_redeal"

    @pytest.mark.asyncio
    async def test_phase_data_broadcasting(self):
        """Test that phase data is broadcast correctly"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        game.round_number = 2
        game.current_player = "Player3"
        game.starter_reason = "has_general_red"

        sm = GameStateMachine(game)
        sm.current_phase = GamePhase.ROUND_START

        # Mock the update_phase_data method
        round_start_state = RoundStartState(sm)
        round_start_state.update_phase_data = AsyncMock()

        await round_start_state._setup_phase()

        # Verify update_phase_data was called with correct data
        round_start_state.update_phase_data.assert_called_once()
        call_args = round_start_state.update_phase_data.call_args[0]

        assert call_args[0]["round_number"] == 2
        assert call_args[0]["starter"] == "Player3"
        assert call_args[0]["starter_reason"] == "has_general_red"
        assert call_args[0]["display_duration"] == 5.0

    def test_transition_validation_from_preparation(self):
        """Test that PREPARATION can transition to ROUND_START"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        sm = GameStateMachine(game)

        # Check transition map
        assert GamePhase.ROUND_START in sm._valid_transitions[GamePhase.PREPARATION]
        assert GamePhase.DECLARATION not in sm._valid_transitions[GamePhase.PREPARATION]

    def test_transition_validation_from_round_start(self):
        """Test that ROUND_START can only transition to DECLARATION"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        sm = GameStateMachine(game)

        # Check transition map
        assert GamePhase.DECLARATION in sm._valid_transitions[GamePhase.ROUND_START]
        assert GamePhase.TURN not in sm._valid_transitions[GamePhase.ROUND_START]
        assert GamePhase.PREPARATION not in sm._valid_transitions[GamePhase.ROUND_START]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
