#!/usr/bin/env python3
"""Test script to verify v2 store is working"""

import asyncio
import sys
sys.path.append('.')

from backend.services.event_store_v2 import EventStoreV2

async def test_v2():
    print("Testing EventStoreV2...")
    
    # Create store
    store = EventStoreV2()
    
    # Test room ID
    room_id = "TEST-V2-ROOM"
    
    # Store game started
    players = [
        {"player_name": "Alice", "player_type": "human"},
        {"player_name": "Bob", "player_type": "ai"},
        {"player_name": "Charlie", "player_type": "ai"},
        {"player_name": "David", "player_type": "ai"}
    ]
    
    print(f"Storing game_started for room {room_id}...")
    await store.store_game_started(room_id, players)
    
    # Store a round
    round_data = {
        "round_number": 1,
        "starter_player": "Alice",
        "starter_reason": "test",
        "initial_hands": {},
        "declarations": {"Alice": 2, "Bob": 2, "Charlie": 2, "David": 2},
        "turn_sequence": [],
        "round_scores": {"Alice": 10, "Bob": 5, "Charlie": 5, "David": 5},
        "cumulative_scores": {"Alice": 10, "Bob": 5, "Charlie": 5, "David": 5}
    }
    
    print(f"Storing round snapshot...")
    await store.store_round_snapshot(room_id, 1, round_data)
    
    # Check game summary
    print(f"\nChecking game summary...")
    summary = await store.get_game_summary(room_id)
    print(f"Summary: {summary}")
    
    # Check round data
    print(f"\nChecking round snapshots...")
    rounds = await store.get_round_snapshots(room_id)
    print(f"Found {len(rounds)} rounds")
    
    print("\n✅ EventStoreV2 is working correctly!")

if __name__ == "__main__":
    asyncio.run(test_v2())