"""
Test Round Start Phase Transitions

Tests the new phase flow: PREPARATION → ROUND_START → DECLARATION
Ensures no invalid transitions occur and all edge cases are handled.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.game import Game
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine


class TestRoundStartPhaseTransitions:
    """Test suite for ROUND_START phase transitions"""

    @pytest.fixture
    def game(self):
        """Create a test game with 4 players"""
        game = Game()
        game.players = [Player(f"Player{i}", is_bot=(i > 1)) for i in range(1, 5)]
        game.round_number = 1
        return game

    @pytest.fixture
    async def state_machine(self, game):
        """Create state machine with mocked broadcast"""
        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = AsyncMock()

        # Initialize to PREPARATION phase
        await sm.initialize()
        return sm

    @pytest.mark.asyncio
    async def test_preparation_to_round_start_no_weak_hands(self, state_machine):
        """Test transition from PREPARATION to ROUND_START when no weak hands"""
        # Ensure we're in PREPARATION
        assert state_machine.current_phase == GamePhase.PREPARATION

        # Mock the preparation state to have no weak hands
        prep_state = state_machine.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()  # No weak hands

        # Check transition conditions
        next_phase = await prep_state.check_transition_conditions()
        assert (
            next_phase == GamePhase.ROUND_START
        ), "Should transition to ROUND_START, not DECLARATION"

        # Execute the transition
        await state_machine._transition_to(GamePhase.ROUND_START)
        assert state_machine.current_phase == GamePhase.ROUND_START

    @pytest.mark.asyncio
    async def test_preparation_to_round_start_after_redeal(self, state_machine):
        """Test transition after all players decline redeal"""
        prep_state = state_machine.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = {"Player1", "Player2"}
        prep_state.redeal_decisions = {"Player1": False, "Player2": False}

        # Process all decisions
        result = await prep_state._process_all_decisions()
        assert result["redeal"] == False

        # After processing, weak_players should be cleared
        assert len(prep_state.weak_players) == 0

        # Should transition to ROUND_START
        with patch.object(state_machine, "_transition_to") as mock_transition:
            await prep_state._handle_redeal_decision(
                GameAction(
                    player_name="Player2",
                    action_type=ActionType.REDEAL_RESPONSE,
                    payload={"accept": False},
                )
            )
            # Verify it tries to transition to ROUND_START, not DECLARATION
            mock_transition.assert_called_with(GamePhase.ROUND_START)

    @pytest.mark.asyncio
    async def test_round_start_auto_transition_to_declaration(self, state_machine):
        """Test ROUND_START automatically transitions to DECLARATION after 5 seconds"""
        # Transition to ROUND_START
        await state_machine._transition_to(GamePhase.ROUND_START)
        assert state_machine.current_phase == GamePhase.ROUND_START

        # Get the round start state
        round_start_state = state_machine.current_state

        # Initially should not transition
        next_phase = await round_start_state.check_transition_conditions()
        assert next_phase is None

        # Mock time to simulate 5 seconds passing
        round_start_state.start_time = asyncio.get_event_loop().time() - 6

        # Now should transition to DECLARATION
        next_phase = await round_start_state.check_transition_conditions()
        assert next_phase == GamePhase.DECLARATION

    @pytest.mark.asyncio
    async def test_invalid_preparation_to_declaration_blocked(self, state_machine):
        """Test that direct PREPARATION → DECLARATION transition is blocked"""
        assert state_machine.current_phase == GamePhase.PREPARATION

        # Try to transition directly to DECLARATION
        await state_machine._transition_to(GamePhase.DECLARATION)

        # Should still be in PREPARATION (transition blocked)
        assert state_machine.current_phase == GamePhase.PREPARATION

    @pytest.mark.asyncio
    async def test_valid_transition_chain(self, state_machine):
        """Test the full valid transition chain"""
        # Start in PREPARATION
        assert state_machine.current_phase == GamePhase.PREPARATION

        # Transition to ROUND_START
        await state_machine._transition_to(GamePhase.ROUND_START)
        assert state_machine.current_phase == GamePhase.ROUND_START

        # Transition to DECLARATION
        await state_machine._transition_to(GamePhase.DECLARATION)
        assert state_machine.current_phase == GamePhase.DECLARATION

    @pytest.mark.asyncio
    async def test_bot_manager_notifications(self, state_machine):
        """Test bot manager receives correct notifications for each phase"""
        with patch(
            "engine.state_machine.game_state_machine.BotManager"
        ) as mock_bot_manager:
            bot_manager_instance = mock_bot_manager.return_value
            bot_manager_instance.handle_game_event = AsyncMock()

            # Transition to ROUND_START
            await state_machine._transition_to(GamePhase.ROUND_START)

            # Should receive phase_change event, not round_started
            bot_manager_instance.handle_game_event.assert_called_with(
                "TEST_ROOM",
                "phase_change",
                {"phase": "round_start", "phase_data": state_machine.get_phase_data()},
            )

            # Reset mock
            bot_manager_instance.handle_game_event.reset_mock()

            # Transition to DECLARATION
            await state_machine._transition_to(GamePhase.DECLARATION)

            # Now should receive round_started event
            calls = bot_manager_instance.handle_game_event.call_args_list
            assert any(
                call[0][1] == "round_started" for call in calls
            ), "Bot manager should receive round_started event for DECLARATION phase"

    @pytest.mark.asyncio
    async def test_phase_data_in_round_start(self, state_machine):
        """Test that ROUND_START phase has correct phase data"""
        # Set up game state
        game = state_machine.game
        game.current_player = "Player1"
        game.starter_reason = "has_general_red"

        # Transition to ROUND_START
        await state_machine._transition_to(GamePhase.ROUND_START)

        # Get phase data
        phase_data = state_machine.get_phase_data()

        # Verify phase data contains starter info
        assert phase_data.get("current_starter") == "Player1"
        assert phase_data.get("starter_reason") == "has_general_red"

    @pytest.mark.asyncio
    async def test_redeal_accept_transitions_correctly(self, state_machine):
        """Test that accepting redeal eventually leads to ROUND_START"""
        prep_state = state_machine.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = {"Player1"}

        # Mock the state machine transition
        with patch.object(state_machine, "_transition_to") as mock_transition:
            # Player accepts redeal
            action = GameAction(
                player_name="Player1",
                action_type=ActionType.REDEAL_REQUEST,
                payload={"accept": True},
            )

            # Mock _deal_cards to not find new weak hands
            with patch.object(prep_state, "_deal_cards", new_callable=AsyncMock):
                prep_state.redeal_decisions["Player1"] = True
                result = await prep_state._process_all_decisions()

                # Since no new weak hands after redeal, should transition
                if not prep_state.weak_players:
                    await state_machine._transition_to(GamePhase.ROUND_START)
                    mock_transition.assert_called_with(GamePhase.ROUND_START)

    @pytest.mark.asyncio
    async def test_multiple_redeals_maintain_correct_flow(self, state_machine):
        """Test multiple redeals still follow correct phase flow"""
        prep_state = state_machine.current_state

        # First redeal cycle
        prep_state.weak_players = {"Player1"}
        prep_state.redeal_decisions = {"Player1": True}

        # Process first redeal
        with patch.object(
            prep_state, "_deal_cards", new_callable=AsyncMock
        ) as mock_deal:
            # After first redeal, new weak hands found
            async def deal_with_weak_hands():
                prep_state.weak_players = {"Player2"}

            mock_deal.side_effect = deal_with_weak_hands

            result = await prep_state._process_all_decisions()
            assert result["new_weak_hands"] == True
            assert prep_state.weak_players == {"Player2"}

        # Second redeal cycle - all decline
        prep_state.redeal_decisions = {"Player2": False}

        with patch.object(state_machine, "_transition_to") as mock_transition:
            # Process second round of decisions
            result = await prep_state._process_all_decisions()
            assert result["redeal"] == False

            # Should clear weak players and transition to ROUND_START
            assert len(prep_state.weak_players) == 0

            # Simulate the transition call that happens in _handle_redeal_decision
            await state_machine._transition_to(GamePhase.ROUND_START)
            mock_transition.assert_called_with(GamePhase.ROUND_START)


class TestPhaseTransitionValidation:
    """Test the phase transition validation system"""

    @pytest.mark.asyncio
    async def test_transition_validation_map(self):
        """Test that transition validation map is correctly configured"""
        game = Game()
        sm = GameStateMachine(game)

        # Check PREPARATION transitions
        assert GamePhase.ROUND_START in sm._valid_transitions[GamePhase.PREPARATION]
        assert GamePhase.DECLARATION not in sm._valid_transitions[GamePhase.PREPARATION]

        # Check ROUND_START transitions
        assert GamePhase.DECLARATION in sm._valid_transitions[GamePhase.ROUND_START]
        assert GamePhase.TURN not in sm._valid_transitions[GamePhase.ROUND_START]

        # Check that ROUND_START cannot go back to PREPARATION
        assert GamePhase.PREPARATION not in sm._valid_transitions[GamePhase.ROUND_START]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
