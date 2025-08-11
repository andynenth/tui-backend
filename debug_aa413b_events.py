#!/usr/bin/env python3
"""Debug event retrieval for room AA413B"""

import sqlite3
import json

def debug_room_events():
    """Check what events exist for room AA413B"""
    
    conn = sqlite3.connect("game_events.db")
    cursor = conn.cursor()
    
    print("🔍 Debugging room AA413B events...\n")
    
    # Check hands_dealt events
    cursor.execute("""
        SELECT payload 
        FROM game_events 
        WHERE room_id = 'AA413B' 
        AND event_type = 'hands_dealt'
        ORDER BY timestamp
        LIMIT 5
    """)
    
    hands_dealt = cursor.fetchall()
    print(f"📊 Found {len(hands_dealt)} hands_dealt events")
    
    for i, (payload_str,) in enumerate(hands_dealt):
        payload = json.loads(payload_str)
        print(f"\nHands dealt event {i+1}:")
        print(f"  Round: {payload.get('round_number')}")
        print(f"  Starter: {payload.get('starter')}")
        print(f"  Starter reason: {payload.get('starter_reason')}")
        print(f"  Reason field: {payload.get('reason')}")  # Check if 'reason' exists
        print(f"  Has hands data: {'hands' in payload}")
    
    # Check phase_change events for round 1
    cursor.execute("""
        SELECT payload 
        FROM game_events 
        WHERE room_id = 'AA413B' 
        AND event_type = 'phase_change'
        AND payload LIKE '%"round": 1%'
        ORDER BY timestamp
        LIMIT 3
    """)
    
    phase_changes = cursor.fetchall()
    print(f"\n📊 Found {len(phase_changes)} phase_change events for round 1")
    
    conn.close()

if __name__ == "__main__":
    debug_room_events()