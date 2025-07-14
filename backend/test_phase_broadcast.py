#!/usr/bin/env python3
"""
Test script to verify that phase transitions are properly broadcast
"""
import asyncio
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase
from engine.game import Game
from engine.player import Player


async def test_phase_broadcast():
    """Test that phase transitions broadcast phase_change events"""
    print("🧪 Testing phase transition broadcasting...")

    # Create test players
    players = [Player(f"Player {i+1}", is_bot=(i > 0)) for i in range(4)]

    # Create test game
    game = Game(players)

    # Track broadcast events
    broadcast_events = []

    async def capture_broadcast(event_type, event_data):
        broadcast_events.append({"event_type": event_type, "event_data": event_data})
        print(f"📡 Broadcast captured: {event_type} - {event_data}")

    # Create state machine with broadcast callback
    state_machine = GameStateMachine(game, capture_broadcast)

    print(f"Initial phase: {state_machine.current_phase}")

    # Start the state machine
    await state_machine.start(GamePhase.PREPARATION)

    # Wait a moment for processing
    await asyncio.sleep(0.1)

    print(f"After start - Current phase: {state_machine.current_phase}")
    print(f"Broadcasts captured: {len(broadcast_events)}")

    # Check if phase_change was broadcast
    phase_change_events = [
        e for e in broadcast_events if e["event_type"] == "phase_change"
    ]

    if phase_change_events:
        print("✅ Phase change event was broadcast successfully!")
        for event in phase_change_events:
            print(f"   Phase: {event['event_data']['phase']}")
            print(f"   Actions: {event['event_data']['allowed_actions']}")
    else:
        print("❌ No phase_change events were broadcast")

    # Stop the state machine
    await state_machine.stop()

    return len(phase_change_events) > 0


if __name__ == "__main__":
    result = asyncio.run(test_phase_broadcast())
    if result:
        print("\n🎉 Test PASSED - Phase broadcasts are working!")
    else:
        print("\n💥 Test FAILED - Phase broadcasts are not working")
        exit(1)
