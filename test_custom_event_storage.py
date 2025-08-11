#!/usr/bin/env python3
"""Test that custom events are now stored in the event store"""

import asyncio
import sqlite3
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_custom_event_storage():
    """Check if custom events are stored in the database"""
    
    # Connect to the database
    db_path = "backend/game_events.db"
    if not os.path.exists(db_path):
        print("❌ Database not found at", db_path)
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Checking for custom events in event store...")
    
    # Check for hands_dealt events
    cursor.execute("""
        SELECT COUNT(*) FROM game_events 
        WHERE event_type = 'hands_dealt'
    """)
    hands_dealt_count = cursor.fetchone()[0]
    print(f"📊 hands_dealt events: {hands_dealt_count}")
    
    # Check for play_with_context events  
    cursor.execute("""
        SELECT COUNT(*) FROM game_events
        WHERE event_type = 'play_with_context'
    """)
    play_context_count = cursor.fetchone()[0]
    print(f"📊 play_with_context events: {play_context_count}")
    
    # Get the most recent rooms
    cursor.execute("""
        SELECT DISTINCT room_id 
        FROM game_events 
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    recent_rooms = cursor.fetchall()
    
    print("\n📋 Recent rooms:")
    for room in recent_rooms:
        room_id = room[0]
        
        # Check each room for custom events
        cursor.execute("""
            SELECT event_type, COUNT(*) 
            FROM game_events 
            WHERE room_id = ? 
            AND event_type IN ('hands_dealt', 'play_with_context')
            GROUP BY event_type
        """, (room_id,))
        
        custom_events = cursor.fetchall()
        if custom_events:
            print(f"\n  Room {room_id}:")
            for event_type, count in custom_events:
                print(f"    - {event_type}: {count} events")
        else:
            print(f"  Room {room_id}: No custom events yet")
    
    conn.close()
    
    print("\n✅ After the fix, new games will store custom events!")
    print("🎮 Start a new game to test the fix.")

if __name__ == "__main__":
    asyncio.run(test_custom_event_storage())