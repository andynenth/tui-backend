"""
Simple tests to catch phase transition errors

These tests would have caught the "Invalid transition: PREPARATION -> DECLARATION" error
"""

import pytest
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase
from engine.game import Game
from engine.player import Player


class TestPhaseTransitionErrors:
    """Tests specifically designed to catch transition errors"""

    def test_preparation_cannot_go_to_declaration(self):
        """This test would catch the exact error we saw"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)  # Add empty players list
        sm = GameStateMachine(game)

        # Check the validation map
        valid_from_prep = sm._valid_transitions.get(GamePhase.PREPARATION, set())

        # This assertion would FAIL before our fix
        assert (
            GamePhase.DECLARATION not in valid_from_prep
        ), "PREPARATION should NOT be able to transition directly to DECLARATION"

        # This assertion should PASS after our fix
        assert (
            GamePhase.ROUND_START in valid_from_prep
        ), "PREPARATION should be able to transition to ROUND_START"

    def test_round_start_can_go_to_declaration(self):
        """Ensure ROUND_START can transition to DECLARATION"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        sm = GameStateMachine(game)

        valid_from_round_start = sm._valid_transitions.get(GamePhase.ROUND_START, set())

        assert (
            GamePhase.DECLARATION in valid_from_round_start
        ), "ROUND_START should be able to transition to DECLARATION"

    def test_complete_phase_flow_validation(self):
        """Test the complete phase flow is valid"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        sm = GameStateMachine(game)

        # Define expected flow
        phase_flow = [
            (None, GamePhase.PREPARATION),  # Initial state
            (GamePhase.PREPARATION, GamePhase.ROUND_START),
            (GamePhase.ROUND_START, GamePhase.DECLARATION),
            (GamePhase.DECLARATION, GamePhase.TURN),
            (GamePhase.TURN, GamePhase.TURN_RESULTS),
            (GamePhase.TURN_RESULTS, GamePhase.TURN),  # Can loop
            (GamePhase.TURN_RESULTS, GamePhase.SCORING),
            (GamePhase.SCORING, GamePhase.PREPARATION),  # Next round
            (GamePhase.SCORING, GamePhase.GAME_OVER),
        ]

        for from_phase, to_phase in phase_flow:
            if from_phase is None:
                continue  # Skip initial state

            valid_transitions = sm._valid_transitions.get(from_phase, set())
            assert (
                to_phase in valid_transitions
            ), f"Invalid flow: {from_phase} should be able to transition to {to_phase}"

    @pytest.mark.asyncio
    async def test_actual_transition_attempt(self):
        """Test actual transition attempts to catch runtime errors"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        sm = GameStateMachine(game)

        # Start in PREPARATION phase
        await sm.start(GamePhase.PREPARATION)

        # Should be in PREPARATION
        assert sm.current_phase == GamePhase.PREPARATION

        # Try invalid transition (should be blocked)
        await sm._transition_to(GamePhase.DECLARATION)
        assert (
            sm.current_phase == GamePhase.PREPARATION
        ), "Invalid transition should be blocked"

        # Try valid transition
        await sm._transition_to(GamePhase.ROUND_START)
        assert (
            sm.current_phase == GamePhase.ROUND_START
        ), "Valid transition should succeed"

        # Clean up
        await sm.stop()


class TestQuickValidation:
    """Quick validation tests that can run frequently"""

    def test_no_direct_prep_to_declaration(self):
        """Single assertion test - would catch our bug immediately"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        sm = GameStateMachine(game)

        # This single line would have caught the bug
        assert GamePhase.DECLARATION not in sm._valid_transitions[GamePhase.PREPARATION]

    def test_round_start_exists_in_flow(self):
        """Ensure ROUND_START is properly connected in the flow"""
        players = [Player(f"Player{i}") for i in range(1, 5)]
        game = Game(players)
        sm = GameStateMachine(game)

        # ROUND_START should be reachable from PREPARATION
        assert GamePhase.ROUND_START in sm._valid_transitions[GamePhase.PREPARATION]

        # ROUND_START should lead to DECLARATION
        assert GamePhase.DECLARATION in sm._valid_transitions[GamePhase.ROUND_START]


# Run this specific test to quickly validate phase transitions
def test_phase_transitions_are_valid():
    """
    Run this test after any phase-related changes:
    pytest backend/tests/test_phase_transition_errors.py::test_phase_transitions_are_valid -v
    """
    players = [Player(f"Player{i}") for i in range(1, 5)]
    game = Game(players)
    sm = GameStateMachine(game)

    # Key assertions that would catch transition bugs
    errors = []

    # Check PREPARATION transitions
    if GamePhase.DECLARATION in sm._valid_transitions.get(GamePhase.PREPARATION, set()):
        errors.append(
            "ERROR: PREPARATION can transition directly to DECLARATION (should go through ROUND_START)"
        )

    if GamePhase.ROUND_START not in sm._valid_transitions.get(
        GamePhase.PREPARATION, set()
    ):
        errors.append("ERROR: PREPARATION cannot transition to ROUND_START")

    # Check ROUND_START transitions
    if GamePhase.DECLARATION not in sm._valid_transitions.get(
        GamePhase.ROUND_START, set()
    ):
        errors.append("ERROR: ROUND_START cannot transition to DECLARATION")

    # Print all errors
    if errors:
        for error in errors:
            print(f"❌ {error}")
        assert False, "Phase transition validation failed"
    else:
        print("✅ All phase transitions are valid")


if __name__ == "__main__":
    # Run the quick validation
    test_phase_transitions_are_valid()
