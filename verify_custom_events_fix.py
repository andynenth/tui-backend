#!/usr/bin/env python3
"""Verify that custom events are now being stored for new games"""

import sqlite3
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def check_room_custom_events(room_id):
    """Check if a room has custom events stored"""
    
    db_path = "game_events.db"  # Use root directory database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for custom events in this room
    cursor.execute("""
        SELECT event_type, COUNT(*) as count, MIN(timestamp) as first_event
        FROM game_events 
        WHERE room_id = ? 
        AND event_type IN ('hands_dealt', 'play_with_context')
        GROUP BY event_type
        ORDER BY first_event
    """, (room_id,))
    
    results = cursor.fetchall()
    
    if results:
        print(f"\n✅ Room {room_id} has custom events stored:")
        for event_type, count, timestamp in results:
            print(f"  - {event_type}: {count} events")
    else:
        # Check if room exists at all
        cursor.execute("""
            SELECT COUNT(*) FROM game_events WHERE room_id = ?
        """, (room_id,))
        total_events = cursor.fetchone()[0]
        
        if total_events > 0:
            print(f"\n❌ Room {room_id} exists but has no custom events (created before fix)")
            print(f"   Total events in room: {total_events}")
        else:
            print(f"\n❓ Room {room_id} not found in database")
    
    conn.close()
    return len(results) > 0

def list_recent_rooms_with_custom_events():
    """List recent rooms and check which have custom events"""
    
    db_path = "game_events.db"  # Use root directory database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Checking recent rooms for custom events...")
    
    # Get rooms created in the last hour
    cursor.execute("""
        SELECT DISTINCT room_id, MIN(timestamp) as created_at
        FROM game_events
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY room_id
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    recent_rooms = cursor.fetchall()
    
    if not recent_rooms:
        print("\nNo rooms created in the last hour.")
    else:
        print(f"\n📋 Rooms created in the last hour:")
        for room_id, created_at in recent_rooms:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM game_events
                WHERE room_id = ? 
                AND event_type IN ('hands_dealt', 'play_with_context')
            """, (room_id,))
            
            custom_count = cursor.fetchone()[0]
            status = "✅ Has custom events" if custom_count > 0 else "❌ No custom events"
            print(f"  - {room_id}: {status} ({custom_count} events)")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        room_id = sys.argv[1]
        check_room_custom_events(room_id)
    else:
        list_recent_rooms_with_custom_events()
        print("\n💡 Usage: python verify_custom_events_fix.py [ROOM_ID]")
        print("💡 Start a NEW game to test the fix!")