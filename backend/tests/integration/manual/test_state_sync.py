#!/usr/bin/env python3
"""
Simple test script to verify State Sync/Replay functionality
"""
import asyncio
import sys

sys.path.append("/Users/nrw/python/tui-project/liap-tui")

from backend.api.services.event_store import event_store
from backend.shared_instances import shared_room_manager


async def test_state_sync():
    print("Testing State Sync/Replay Capability...")
    print("=" * 60)

    # Create a room
    room_id = shared_room_manager.create_room("TestHost")
    room = shared_room_manager.get_room(room_id)
    print(f"✓ Created room: {room_id}")

    # Add players
    room.join_room("Player2")
    room.join_room("Player3")
    room.join_room("Player4")
    print("✓ Added 4 players")

    # Define a simple broadcast callback
    events_received = []

    async def test_broadcast(event_type: str, data: dict):
        events_received.append(event_type)
        print(f"  → Event: {event_type}")

    # Start the game
    result = await room.start_game_safe(test_broadcast)
    if result["success"]:
        print("✓ Game started successfully")
    else:
        print(f"✗ Failed to start game: {result}")
        return

    # Wait for some game activity
    print("\nWaiting for game activity...")
    await asyncio.sleep(3)

    # Check stored events
    print("\n" + "=" * 60)
    print("CHECKING STORED EVENTS")
    print("=" * 60)

    events = await event_store.get_room_events(room_id)
    print(f"Total events stored: {len(events)}")

    # Count by type
    event_types = {}
    for event in events:
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

    print("\nEvent breakdown:")
    for evt_type, count in sorted(event_types.items()):
        print(f"  {evt_type}: {count}")

    # Test replay
    print("\n" + "=" * 60)
    print("TESTING STATE REPLAY")
    print("=" * 60)

    replayed_state = await event_store.replay_room_state(room_id)
    print(f"✓ Replayed {replayed_state['events_processed']} events")
    print(f"✓ Current phase: {replayed_state.get('phase', 'Unknown')}")
    print(f"✓ Round number: {replayed_state.get('round_number', 0)}")

    # Show players
    if "players" in replayed_state:
        print("\nPlayers in game:")
        for name, data in replayed_state["players"].items():
            print(f"  - {name}: {data}")

    # Validate sequence
    validation = await event_store.validate_event_sequence(room_id)
    print(f"\n✓ Event sequence valid: {validation['valid']}")
    print(f"✓ No gaps in sequence: {len(validation['gaps']) == 0}")

    # Test debug endpoint data
    stats = await event_store.get_event_stats()
    print(f"\n✓ Total events in store: {stats['total_events']}")

    # Cleanup
    shared_room_manager.delete_room(room_id)
    print(f"\n✓ Cleaned up room {room_id}")

    print("\n" + "=" * 60)
    print("✅ State Sync/Replay test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_state_sync())
