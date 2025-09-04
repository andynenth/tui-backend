#!/usr/bin/env python3
"""Test the new event tracking system"""

import asyncio
import json
from backend.shared_event_store import event_store

async def test_event_storage():
    """Test storing various event types"""
    room_id = "TEST_ROOM"
    player_name = "TestPlayer"
    
    print("Testing event storage...")
    
    # Test 1: Store player_disconnected event
    await event_store.store_event(
        room_id,
        "player_disconnected",
        {
            "player_name": player_name,
            "timestamp": 1234567890,
            "was_bot": False,
            "grace_period_seconds": 5,
            "bot_takeover_scheduled_at": "2024-01-01T12:00:00",
            "disconnect_reason": "websocket_close",
            "game_context": {
                "current_phase": "turn",
                "current_player": player_name,
                "round_number": 1,
                "turn_number": 1,
                "is_players_turn": True
            },
            "connection_duration_seconds": 300
        },
        player_id=player_name
    )
    print("✓ Stored player_disconnected event")
    
    # Test 2: Store bot_takeover_scheduled event
    await event_store.store_event(
        room_id,
        "bot_takeover_scheduled",
        {
            "player_name": player_name,
            "scheduled_for": "2024-01-01T12:00:05",
            "current_time": "2024-01-01T12:00:00",
            "delay_seconds": 5,
            "game_context": {
                "current_phase": "turn",
                "current_player": player_name
            }
        },
        player_id=player_name
    )
    print("✓ Stored bot_takeover_scheduled event")
    
    # Test 3: Store human_action event
    await event_store.store_event(
        room_id,
        "human_action",
        {
            "player_name": player_name,
            "action_type": "play",
            "is_bot": False,
            "phase": "turn",
            "turn_number": 1,
            "round_number": 1,
            "timestamp": 1234567891,
            "action_details": {"indices": [0, 1]}
        },
        player_id=player_name
    )
    print("✓ Stored human_action event")
    
    # Test 4: Store bot_action event
    await event_store.store_event(
        room_id,
        "bot_action",
        {
            "player_name": "Bot1",
            "action_type": "declare",
            "is_bot": True,
            "phase": "declaration",
            "turn_number": None,
            "round_number": 1,
            "timestamp": 1234567892,
            "action_details": {"value": 2}
        },
        player_id="Bot1"
    )
    print("✓ Stored bot_action event")
    
    # Test 5: Store action_blocked event
    await event_store.store_event(
        room_id,
        "action_blocked",
        {
            "player_name": player_name,
            "action_attempted": "play",
            "reason": "bot_has_control",
            "is_bot": True,
            "timestamp": 1234567893,
            "payload": {"indices": [2, 3]}
        },
        player_id=player_name
    )
    print("✓ Stored action_blocked event")
    
    print("\nAll events stored successfully!")
    
    # Verify they're in the database by checking with debug endpoint
    import requests
    
    # Test the new endpoints
    print("\nTesting new debug endpoints...")
    
    # Test connection timeline
    resp = requests.get(f"http://localhost:5050/api/debug/connection-timeline/{room_id}")
    if resp.status_code == 200:
        timeline = resp.json()
        print(f"✓ Connection timeline: {timeline['timeline_events']} events")
    else:
        print(f"✗ Connection timeline failed: {resp.status_code}")
    
    # Test bot control analysis
    resp = requests.get(f"http://localhost:5050/api/debug/bot-control-analysis/{room_id}")
    if resp.status_code == 200:
        analysis = resp.json()
        print(f"✓ Bot control analysis: {analysis['summary']['total_players']} players analyzed")
    else:
        print(f"✗ Bot control analysis failed: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test_event_storage())