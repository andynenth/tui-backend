#!/usr/bin/env python3
"""
Test to reproduce JSON serialization error with Player objects
"""
import asyncio
import json

from engine.game import Game
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine


async def test_json_serialization_error():
    """Test that reproduces JSON serialization error during phase transitions"""
    print("🧪 Testing JSON serialization of phase_change events...")

    # Create test players
    players = [Player(f"Player {i+1}", is_bot=(i > 0)) for i in range(4)]

    # Create test game
    game = Game(players)

    # Track broadcast events and try to JSON serialize them
    broadcast_events = []

    async def capture_and_serialize_broadcast(event_type, event_data):
        broadcast_events.append({"event_type": event_type, "event_data": event_data})
        print(f"📡 Broadcast captured: {event_type}")

        # Try to JSON serialize the event data (this is where the error should occur)
        try:
            json_str = json.dumps(event_data)
            print(f"✅ JSON serialization successful for {event_type}")
        except TypeError as e:
            print(f"❌ JSON serialization failed for {event_type}: {e}")
            print(f"   Problematic data keys: {list(event_data.keys())}")
            # Look for Player objects in the data
            for key, value in event_data.items():
                if hasattr(value, "__dict__") and not isinstance(
                    value, (str, int, float, bool, list, dict)
                ):
                    print(
                        f"   Found non-serializable object in key '{key}': {type(value)} - {value}"
                    )
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if hasattr(sub_value, "__dict__") and not isinstance(
                            sub_value, (str, int, float, bool, list, dict)
                        ):
                            print(
                                f"   Found non-serializable object in '{key}.{sub_key}': {type(sub_value)} - {sub_value}"
                            )
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if hasattr(item, "__dict__") and not isinstance(
                            item, (str, int, float, bool, list, dict)
                        ):
                            print(
                                f"   Found non-serializable object in '{key}[{i}]': {type(item)} - {item}"
                            )
            raise  # Re-raise to show the full error

    # Create state machine with broadcast callback
    state_machine = GameStateMachine(game, capture_and_serialize_broadcast)

    # Start the state machine
    await state_machine.start(GamePhase.PREPARATION)

    # Wait for initial transitions to complete
    await asyncio.sleep(0.5)

    # Force transition to DECLARATION to see where Player objects appear
    print(f"\n🔄 Current phase: {state_machine.current_phase}")

    # Add some declarations to trigger TURN phase transition
    if state_machine.current_phase == GamePhase.DECLARATION:
        print("📢 Adding declarations to trigger TURN phase transition...")
        for i, player in enumerate(players):
            action = GameAction(
                player_name=player.name,
                action_type=ActionType.DECLARE,
                payload={"value": 2},  # Each player declares 2 piles
            )
            await state_machine.handle_action(action)
            await asyncio.sleep(0.1)  # Small delay between declarations

    # Wait for transition to TURN phase
    await asyncio.sleep(0.5)

    print(f"\n🔄 Final phase: {state_machine.current_phase}")
    print(f"Total broadcast events: {len(broadcast_events)}")

    # Stop the state machine
    await state_machine.stop()

    return len(broadcast_events) > 0


if __name__ == "__main__":
    try:
        result = asyncio.run(test_json_serialization_error())
        if result:
            print("\n🎉 Test completed - check output for JSON serialization errors")
        else:
            print("\n💥 Test failed - no broadcast events captured")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        exit(1)
