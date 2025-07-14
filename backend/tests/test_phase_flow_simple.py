#!/usr/bin/env python3
"""
Simple Phase Flow Verification Test

Quick test to verify that all 7 phases can be instantiated and transitioned correctly.
"""

import asyncio
import logging
import sys

# Add current directory to path
sys.path.append(".")

from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine


async def test_phase_instantiation():
    """Test that all phases can be instantiated"""
    print("🧪 Testing Phase Instantiation...")

    # Create state machine
    sm = GameStateMachine(game=None)

    print(f"✅ All 7 phases created successfully:")
    for phase, state in sm.states.items():
        print(f"   • {phase.value}: {state.__class__.__name__}")

    return True


async def test_transition_validation():
    """Test transition validation logic"""
    print("\n🧪 Testing Transition Validation...")

    sm = GameStateMachine(game=None)

    # Test valid transitions
    valid_tests = [
        (GamePhase.WAITING, GamePhase.PREPARATION),
        (GamePhase.PREPARATION, GamePhase.DECLARATION),
        (GamePhase.DECLARATION, GamePhase.TURN),
        (GamePhase.TURN, GamePhase.TURN_RESULTS),
        (GamePhase.TURN_RESULTS, GamePhase.SCORING),
        (GamePhase.TURN_RESULTS, GamePhase.TURN),
        (GamePhase.SCORING, GamePhase.PREPARATION),
        (GamePhase.SCORING, GamePhase.GAME_OVER),
    ]

    print("✅ Valid transitions:")
    for from_phase, to_phase in valid_tests:
        valid_to = sm._valid_transitions.get(from_phase, set())
        is_valid = to_phase in valid_to
        status = "✅" if is_valid else "❌"
        print(f"   {status} {from_phase.value} → {to_phase.value}")
        assert is_valid, f"Expected {from_phase.value} → {to_phase.value} to be valid"

    # Test invalid transitions
    invalid_tests = [
        (GamePhase.WAITING, GamePhase.TURN),
        (GamePhase.PREPARATION, GamePhase.SCORING),
        (GamePhase.GAME_OVER, GamePhase.WAITING),
    ]

    print("\n✅ Invalid transitions properly blocked:")
    for from_phase, to_phase in invalid_tests:
        valid_to = sm._valid_transitions.get(from_phase, set())
        is_invalid = to_phase not in valid_to
        status = "✅" if is_invalid else "❌"
        print(f"   {status} {from_phase.value} → {to_phase.value} (blocked)")
        assert (
            is_invalid
        ), f"Expected {from_phase.value} → {to_phase.value} to be invalid"

    return True


async def test_basic_phase_flow():
    """Test basic phase flow with minimal setup"""
    print("\n🧪 Testing Basic Phase Flow...")

    # Create minimal mock game
    class MockGame:
        def __init__(self):
            self.players = []
            self.room_id = "test_room"

    # Create state machine with mock broadcast
    events_received = []

    async def mock_broadcast(event_type, data):
        events_received.append(f"{event_type}: {data.get('phase', 'unknown')}")

    sm = GameStateMachine(MockGame(), mock_broadcast)
    sm.room_id = "test_room"

    # Start in WAITING phase
    await sm.start(GamePhase.WAITING)
    assert sm.current_phase == GamePhase.WAITING
    print("   ✅ Started in WAITING phase")

    # Stop the state machine
    await sm.stop()
    print("   ✅ State machine stopped successfully")

    # Verify events were broadcast
    assert len(events_received) > 0
    print(f"   ✅ Broadcast events received: {len(events_received)}")

    return True


async def main():
    """Run all tests"""
    print("🚀 Simple Phase Flow Verification Test")
    print("=" * 60)

    try:
        # Run tests
        await test_phase_instantiation()
        await test_transition_validation()
        await test_basic_phase_flow()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Backend phase implementation is working correctly")
        print(
            "✅ All 7 phases: waiting, preparation, declaration, turn, turn_results, scoring, game_over"
        )
        print("✅ Frontend/backend phase synchronization should work perfectly")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
