#!/usr/bin/env python3
"""
Test script to verify automatic transition from preparation to declaration
"""
import asyncio

from engine.game import Game
from engine.player import Player
from engine.state_machine.core import GamePhase
from engine.state_machine.game_state_machine import GameStateMachine


async def test_auto_transition():
    """Test that preparation phase automatically transitions to declaration"""
    print("🧪 Testing automatic phase transition...")

    # Create test players
    players = [Player(f"Player {i+1}", is_bot=(i > 0)) for i in range(4)]

    # Create test game
    game = Game(players)

    # Track broadcast events
    broadcast_events = []

    async def capture_broadcast(event_type, event_data):
        broadcast_events.append({"event_type": event_type, "event_data": event_data})
        print(f"📡 Broadcast: {event_type} - phase: {event_data.get('phase', 'N/A')}")

    # Create state machine with broadcast callback
    state_machine = GameStateMachine(game, capture_broadcast)

    # Start the state machine
    await state_machine.start(GamePhase.PREPARATION)

    # Wait for preparation phase to complete automatically
    print("⏳ Waiting for automatic transition...")
    for i in range(20):  # Wait up to 2 seconds
        await asyncio.sleep(0.1)
        if state_machine.current_phase == GamePhase.DECLARATION:
            break

    print(f"Final phase: {state_machine.current_phase}")

    # Check phase transitions
    phase_events = [e for e in broadcast_events if e["event_type"] == "phase_change"]
    phases = [e["event_data"]["phase"] for e in phase_events]

    print(f"Phase transitions: {' -> '.join(phases)}")

    success = (
        state_machine.current_phase == GamePhase.DECLARATION
        and "preparation" in phases
        and "declaration" in phases
    )

    await state_machine.stop()

    return success


if __name__ == "__main__":
    result = asyncio.run(test_auto_transition())
    if result:
        print("\n🎉 Test PASSED - Auto transition to declaration works!")
    else:
        print("\n💥 Test FAILED - Auto transition not working")
        exit(1)
