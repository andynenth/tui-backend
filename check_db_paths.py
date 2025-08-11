#!/usr/bin/env python3
"""Check database paths used by different services"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def check_paths():
    """Check where database files are being created/accessed"""
    
    print("🔍 Checking database paths...\n")
    
    # Current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # Check EventStore path
    from backend.api.services.event_store import EventStore
    event_store = EventStore()
    abs_path = os.path.abspath(event_store.db_path)
    print(f"\nEventStore database path:")
    print(f"  Relative: {event_store.db_path}")
    print(f"  Absolute: {abs_path}")
    print(f"  Exists: {os.path.exists(abs_path)}")
    
    # Check PlayHistoryService path
    from backend.services.event_store_play_history_service import EventStorePlayHistoryService
    play_history = EventStorePlayHistoryService()
    abs_path2 = os.path.abspath(play_history.db_path)
    print(f"\nPlayHistoryService database path:")
    print(f"  Relative: {play_history.db_path}")
    print(f"  Absolute: {abs_path2}")
    print(f"  Exists: {os.path.exists(abs_path2)}")
    
    # Check if they're the same
    print(f"\n✅ Same database? {abs_path == abs_path2}")
    
    # List all game_events.db files
    print("\n📁 All game_events.db files found:")
    for root, dirs, files in os.walk('.'):
        if 'game_events.db' in files:
            full_path = os.path.join(root, 'game_events.db')
            size = os.path.getsize(full_path)
            print(f"  {full_path} ({size:,} bytes)")

if __name__ == "__main__":
    check_paths()