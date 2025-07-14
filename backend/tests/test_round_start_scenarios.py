"""
Test Round Start Scenarios from ROUND_START_TEST_PLAN.md

Tests all scenarios outlined in the test plan to ensure ROUND_START phase
works correctly in all situations.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from engine.game import Game
from engine.piece import Piece
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine


class TestRoundStartScenarios:
    """Test all scenarios from ROUND_START_TEST_PLAN.md"""

    @pytest.fixture
    def mock_broadcast(self):
        """Mock broadcast callback to capture phase change events"""
        return AsyncMock()

    @pytest.fixture
    def create_game_with_hands(self):
        """Factory to create games with specific card distributions"""

        def _create(player_hands=None):
            players = [Player(f"Player{i}") for i in range(1, 5)]
            game = Game(players)

            if player_hands:
                for i, hand in enumerate(player_hands):
                    if i < len(players):
                        players[i].hand = hand

            return game, players

        return _create

    @pytest.mark.asyncio
    async def test_scenario_1_round1_red_general(
        self, create_game_with_hands, mock_broadcast
    ):
        """
        Scenario 1: Round 1 - Red General Test
        Player with GENERAL_RED becomes starter
        """
        # Create specific hands - Player2 has GENERAL_RED
        hands = [
            [Piece("ADVISOR_BLACK"), Piece("ELEPHANT_BLACK")],
            [Piece("GENERAL_RED"), Piece("HORSE_BLACK")],  # Player2 has GENERAL_RED
            [Piece("CANNON_BLACK"), Piece("CHARIOT_RED")],
            [Piece("HORSE_RED"), Piece("ADVISOR_RED")],
        ]

        game, players = create_game_with_hands(hands)
        game.round_number = 1

        # Debug: Check which player actually has GENERAL_RED
        for i, player in enumerate(game.players):
            print(f"Player{i+1} hand: {player.hand}")
            for piece in player.hand:
                if "GENERAL_RED" in str(piece):
                    print(f"  -> Player{i+1} has GENERAL_RED!")

        # Create state machine
        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = mock_broadcast

        # Start in PREPARATION
        await sm.start(GamePhase.PREPARATION)

        # Simulate preparation complete
        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()  # No weak hands

        # Manually call _determine_starter to set the starter without dealing new cards
        starter = prep_state._determine_starter()
        assert starter == "Player2", f"Expected Player2 to be starter, got {starter}"

        # Transition to ROUND_START
        await sm._transition_to(GamePhase.ROUND_START)
        assert sm.current_phase == GamePhase.ROUND_START

        # Verify phase data
        phase_data = sm.get_phase_data()
        assert phase_data["starter"] == "Player2"
        assert phase_data["starter_reason"] == "has_general_red"
        assert game.starter_reason == "has_general_red"

        # Verify broadcast was called with correct data
        broadcast_calls = [
            call
            for call in mock_broadcast.call_args_list
            if call[0][0] == "phase_change" and call[0][1].get("phase") == "round_start"
        ]
        assert len(broadcast_calls) > 0

        last_broadcast = broadcast_calls[-1][0][1]
        assert last_broadcast["round"] == 1
        assert last_broadcast["phase_data"]["starter"] == "Player2"
        assert last_broadcast["phase_data"]["starter_reason"] == "has_general_red"

        # Clean up
        await sm.stop()

    @pytest.mark.asyncio
    async def test_scenario_2_round2_previous_winner(
        self, create_game_with_hands, mock_broadcast
    ):
        """
        Scenario 2: Round 2+ - Previous Winner Test
        Last turn winner from previous round becomes starter
        """
        game, players = create_game_with_hands()
        game.round_number = 2
        game.last_turn_winner = "Player3"  # Player3 won last turn of round 1

        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = mock_broadcast

        # Start in PREPARATION
        await sm.start(GamePhase.PREPARATION)

        # Simulate preparation complete
        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()

        # Transition to ROUND_START
        await sm._transition_to(GamePhase.ROUND_START)
        assert sm.current_phase == GamePhase.ROUND_START

        # Verify phase data
        phase_data = sm.get_phase_data()
        assert phase_data["starter"] == "Player3"
        assert phase_data["starter_reason"] == "won_last_turn"
        assert game.starter_reason == "won_last_turn"

        # Verify correct round number
        broadcast_calls = [
            call
            for call in mock_broadcast.call_args_list
            if call[0][0] == "phase_change" and call[0][1].get("phase") == "round_start"
        ]
        last_broadcast = broadcast_calls[-1][0][1]
        assert last_broadcast["round"] == 2

        await sm.stop()

    @pytest.mark.asyncio
    async def test_scenario_3_redeal_acceptance(
        self, create_game_with_hands, mock_broadcast
    ):
        """
        Scenario 3: Redeal Acceptance Test
        Player who accepts redeal becomes starter
        """
        # Create hands where Player1 has weak hand
        hands = [
            [Piece("ADVISOR_BLACK"), Piece("ELEPHANT_BLACK")],  # Weak hand
            [Piece("GENERAL_RED"), Piece("HORSE_BLACK")],
            [Piece("CANNON_BLACK"), Piece("CHARIOT_RED")],
            [Piece("HORSE_RED"), Piece("ADVISOR_RED")],
        ]

        game, players = create_game_with_hands(hands)
        game.round_number = 1

        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = mock_broadcast

        await sm.start(GamePhase.PREPARATION)

        # Set up redeal scenario
        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = {"Player1"}
        prep_state.redeal_requester = "Player1"  # Player1 accepted redeal
        game.redeal_multiplier = 2

        # Clear weak players after redeal
        prep_state.weak_players = set()

        # Transition to ROUND_START
        await sm._transition_to(GamePhase.ROUND_START)
        assert sm.current_phase == GamePhase.ROUND_START

        # Verify phase data
        phase_data = sm.get_phase_data()
        assert phase_data["starter"] == "Player1"
        assert phase_data["starter_reason"] == "accepted_redeal"
        assert game.starter_reason == "accepted_redeal"

        # Verify redeal multiplier is included
        assert phase_data.get("redeal_multiplier", 1) == 2

        await sm.stop()

    @pytest.mark.asyncio
    async def test_scenario_4_timer_functionality(
        self, create_game_with_hands, mock_broadcast
    ):
        """
        Scenario 4: Timer Functionality Test
        Phase auto-advances after 5 seconds
        """
        game, players = create_game_with_hands()
        game.round_number = 1

        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = mock_broadcast

        await sm.start(GamePhase.PREPARATION)

        # Quick transition to ROUND_START
        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()

        await sm._transition_to(GamePhase.ROUND_START)
        assert sm.current_phase == GamePhase.ROUND_START

        round_start_state = sm.current_state
        start_time = round_start_state.start_time

        # Initially should not transition
        next_phase = await round_start_state.check_transition_conditions()
        assert next_phase is None

        # Test at different time intervals
        for elapsed, should_transition in [
            (0, False),
            (2, False),
            (4.9, False),
            (5.1, True),
        ]:
            # Mock the time
            round_start_state.start_time = time.time() - elapsed
            next_phase = await round_start_state.check_transition_conditions()

            if should_transition:
                assert (
                    next_phase == GamePhase.DECLARATION
                ), f"Should transition after {elapsed} seconds"
            else:
                assert (
                    next_phase is None
                ), f"Should not transition after {elapsed} seconds"

        await sm.stop()

    @pytest.mark.asyncio
    async def test_scenario_6_backend_state_sync(self, create_game_with_hands):
        """
        Scenario 6: Backend State Sync Test
        Verify all state data is properly synchronized
        """
        # Create multiple broadcast callbacks to simulate multiple clients
        client_broadcasts = [AsyncMock() for _ in range(3)]

        game, players = create_game_with_hands()
        game.round_number = 1

        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"

        # Test with each client
        received_data = []

        for client_broadcast in client_broadcasts:
            sm.broadcast_callback = client_broadcast

            await sm.start(GamePhase.PREPARATION)

            # Set up scenario
            prep_state = sm.current_state
            prep_state.initial_deal_complete = True
            prep_state.weak_players = set()
            game.current_player = "Player2"
            game.starter_reason = "has_general_red"

            await sm._transition_to(GamePhase.ROUND_START)

            # Collect broadcast data
            for call in client_broadcast.call_args_list:
                if (
                    call[0][0] == "phase_change"
                    and call[0][1].get("phase") == "round_start"
                ):
                    received_data.append(call[0][1])

            await sm.stop()

        # Verify all clients received identical data
        assert len(received_data) >= len(client_broadcasts)

        # Check consistency across all broadcasts
        first_data = received_data[0]
        for data in received_data[1:]:
            assert (
                data["phase_data"]["current_starter"]
                == first_data["phase_data"]["current_starter"]
            )
            assert (
                data["phase_data"]["starter_reason"]
                == first_data["phase_data"]["starter_reason"]
            )
            assert data["round"] == first_data["round"]

    @pytest.mark.asyncio
    async def test_edge_case_no_general_red_round1(
        self, create_game_with_hands, mock_broadcast
    ):
        """
        Edge case: Round 1 but no player has GENERAL_RED
        Should fall back to first player
        """
        # Create hands without GENERAL_RED
        hands = [
            [Piece("ADVISOR_BLACK"), Piece("ELEPHANT_BLACK")],
            [Piece("GENERAL_BLACK"), Piece("HORSE_BLACK")],  # BLACK general
            [Piece("CANNON_BLACK"), Piece("CHARIOT_RED")],
            [Piece("HORSE_RED"), Piece("ADVISOR_RED")],
        ]

        game, players = create_game_with_hands(hands)
        game.round_number = 1

        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = mock_broadcast

        await sm.start(GamePhase.PREPARATION)

        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()

        await sm._transition_to(GamePhase.ROUND_START)

        # Should use fallback starter
        phase_data = sm.get_phase_data()
        assert phase_data["starter"] == "Player1"  # First player
        assert phase_data["starter_reason"] == "default"

        await sm.stop()

    @pytest.mark.asyncio
    async def test_phase_data_persistence(self, create_game_with_hands, mock_broadcast):
        """
        Test that phase data persists correctly during ROUND_START phase
        """
        game, players = create_game_with_hands()
        game.round_number = 3
        game.last_turn_winner = "Player4"

        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = mock_broadcast

        await sm.start(GamePhase.PREPARATION)

        # Transition to ROUND_START
        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()

        await sm._transition_to(GamePhase.ROUND_START)

        # Get initial phase data
        initial_data = sm.get_phase_data()

        # Simulate some time passing
        await asyncio.sleep(0.1)

        # Get phase data again
        later_data = sm.get_phase_data()

        # Data should be identical
        assert initial_data["starter"] == later_data["starter"]
        assert initial_data["starter_reason"] == later_data["starter_reason"]
        assert initial_data == later_data

        await sm.stop()

    @pytest.mark.asyncio
    async def test_multiple_broadcasts_during_round_start(
        self, create_game_with_hands, mock_broadcast
    ):
        """
        Test that phase_change is only broadcast once when entering ROUND_START
        """
        game, players = create_game_with_hands()
        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = mock_broadcast

        await sm.start(GamePhase.PREPARATION)

        # Clear previous broadcasts
        mock_broadcast.reset_mock()

        # Transition to ROUND_START
        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()

        await sm._transition_to(GamePhase.ROUND_START)

        # Count phase_change broadcasts for round_start
        round_start_broadcasts = [
            call
            for call in mock_broadcast.call_args_list
            if call[0][0] == "phase_change" and call[0][1].get("phase") == "round_start"
        ]

        # Should broadcast exactly once
        assert len(round_start_broadcasts) == 1

        await sm.stop()


class TestRoundStartIntegration:
    """Integration tests for ROUND_START with full game flow"""

    @pytest.mark.asyncio
    async def test_full_flow_preparation_to_declaration(self):
        """Test complete flow: PREPARATION → ROUND_START → DECLARATION"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)

        # Give Player3 the GENERAL_RED
        players[2].hand = [Piece("GENERAL_RED")]

        sm = GameStateMachine(game)
        sm.room_id = "TEST_ROOM"
        sm.broadcast_callback = AsyncMock()

        # Start game
        await sm.start(GamePhase.PREPARATION)
        assert sm.current_phase == GamePhase.PREPARATION

        # Complete preparation
        prep_state = sm.current_state
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()

        # Let state machine handle transition automatically
        next_phase = await prep_state.check_transition_conditions()
        assert next_phase == GamePhase.ROUND_START

        await sm._transition_to(next_phase)
        assert sm.current_phase == GamePhase.ROUND_START

        # Verify starter was determined correctly
        assert game.current_player == "Player3"
        assert game.starter_reason == "has_general_red"

        # Simulate time passing
        round_start_state = sm.current_state
        round_start_state.start_time = time.time() - 6

        # Check for auto-transition
        next_phase = await round_start_state.check_transition_conditions()
        assert next_phase == GamePhase.DECLARATION

        await sm._transition_to(next_phase)
        assert sm.current_phase == GamePhase.DECLARATION

        await sm.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
