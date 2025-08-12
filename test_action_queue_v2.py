#!/usr/bin/env python3
"""Test that ActionQueue is using v2 store"""

import asyncio
import sys
sys.path.append('.')

from backend.engine.state_machine.action_queue import ActionQueue

async def test_action_queue():
    print("Testing ActionQueue with v2 store...")
    
    # Create action queue
    room_id = "TEST-QUEUE-V2"
    queue = ActionQueue(room_id)
    
    # Test storing various events
    print("\n1. Testing game_started event...")
    await queue.store_state_event(
        "game_started",
        {
            "players": [
                {"player_name": "Alice", "player_type": "human"},
                {"player_name": "Bob", "player_type": "ai"},
                {"player_name": "Charlie", "player_type": "ai"},
                {"player_name": "David", "player_type": "ai"}
            ]
        }
    )
    
    print("2. Testing phase_change event...")
    await queue.store_state_event(
        "phase_change",
        {
            "old_phase": "WAITING",
            "new_phase": "PREPARATION",
            "phase_data": {"dealing": True}
        }
    )
    
    print("3. Testing round_completed event...")
    await queue.store_state_event(
        "round_completed",
        {
            "round_number": 1,
            "starter_player": "Alice",
            "declarations": {"Alice": 2, "Bob": 2, "Charlie": 2, "David": 2},
            "scores": {"Alice": 10, "Bob": 5, "Charlie": 5, "David": 5},
            "total_scores": {"Alice": 10, "Bob": 5, "Charlie": 5, "David": 5}
        }
    )
    
    # Check v2 database
    print("\n4. Checking v2 database...")
    import sqlite3
    conn = sqlite3.connect('game_events.db')
    
    # Check game_summaries
    cursor = conn.execute("SELECT * FROM game_summaries WHERE room_id = ?", (room_id,))
    summary = cursor.fetchone()
    print(f"Game summary found: {summary is not None}")
    
    # Check round_snapshots
    cursor = conn.execute("SELECT * FROM round_snapshots WHERE room_id = ?", (room_id,))
    rounds = cursor.fetchall()
    print(f"Round snapshots found: {len(rounds)}")
    
    # Check game_events_v2
    cursor = conn.execute("SELECT event_type, COUNT(*) FROM game_events_v2 WHERE room_id = ? GROUP BY event_type", (room_id,))
    events = cursor.fetchall()
    print(f"Events in v2: {events}")
    
    # Check v1 (should be empty)
    cursor = conn.execute("SELECT COUNT(*) FROM game_events WHERE room_id = ?", (room_id,))
    v1_count = cursor.fetchone()[0]
    print(f"Events in v1 (should be 0): {v1_count}")
    
    conn.close()
    
    if summary and len(rounds) > 0 and v1_count == 0:
        print("\n✅ ActionQueue is correctly using v2 store!")
    else:
        print("\n❌ ActionQueue is NOT using v2 store correctly")
        print(f"   Summary: {summary is not None}, Rounds: {len(rounds)}, V1 Events: {v1_count}")

if __name__ == "__main__":
    asyncio.run(test_action_queue())