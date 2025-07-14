#!/usr/bin/env python3
"""
Quick test to verify that the transition fixes resolve the infinite loop bug.
"""

import asyncio
import sys

# Add current directory to path
sys.path.append(".")

from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase


async def test_transition_fixes():
    """Test that transition validation now works correctly"""
    print("🧪 Testing Transition Fixes...")

    # Create state machine
    sm = GameStateMachine(game=None)

    # Check that transitions are now valid
    print("\n✅ Checking Updated Transition Validation:")

    # TurnState should now allow TURN_RESULTS
    turn_state = sm.states[GamePhase.TURN]
    assert GamePhase.TURN_RESULTS in turn_state.next_phases
    print(f"   ✅ TurnState.next_phases = {[p.value for p in turn_state.next_phases]}")

    # ScoringState should now allow GAME_OVER
    scoring_state = sm.states[GamePhase.SCORING]
    assert GamePhase.GAME_OVER in scoring_state.next_phases
    assert GamePhase.PREPARATION in scoring_state.next_phases
    print(
        f"   ✅ ScoringState.next_phases = {[p.value for p in scoring_state.next_phases]}"
    )

    # Verify transition validation map
    turn_valid = sm._valid_transitions[GamePhase.TURN]
    assert GamePhase.TURN_RESULTS in turn_valid
    print(f"   ✅ Valid transitions from TURN: {[p.value for p in turn_valid]}")

    scoring_valid = sm._valid_transitions[GamePhase.SCORING]
    assert GamePhase.GAME_OVER in scoring_valid
    assert GamePhase.PREPARATION in scoring_valid
    print(f"   ✅ Valid transitions from SCORING: {[p.value for p in scoring_valid]}")

    print("\n🎉 All transition fixes verified!")
    print("✅ TURN → TURN_RESULTS transition is now valid")
    print("✅ SCORING → GAME_OVER transition is now valid")
    print("✅ Infinite loop bug should be resolved")

    return True


async def test_basic_state_instantiation():
    """Test that all states can still be instantiated after fixes"""
    print("\n🧪 Testing State Instantiation After Fixes...")

    try:
        sm = GameStateMachine(game=None)

        # Test all states can be created
        for phase, state in sm.states.items():
            # Try to access basic properties
            assert state.phase_name == phase
            assert isinstance(state.next_phases, list)
            print(f"   ✅ {phase.value}: {state.__class__.__name__}")

        print("✅ All states instantiate correctly after fixes")
        return True

    except Exception as e:
        print(f"❌ State instantiation failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Transition Fix Verification Test")
    print("=" * 50)

    try:
        success1 = await test_transition_fixes()
        success2 = await test_basic_state_instantiation()

        if success1 and success2:
            print("\n" + "=" * 50)
            print("🎉 ALL TRANSITION FIXES VERIFIED!")
            print("🚫 The infinite loop bug should now be resolved")
            print("✅ Complete game flow should work correctly")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
