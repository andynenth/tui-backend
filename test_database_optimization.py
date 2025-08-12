#!/usr/bin/env python3
"""
Test Database Optimization Implementation

This script tests that the complete database optimization pipeline works as designed:
1. Event compression (reducing granular events to semantic events)
2. Event buffering (batching writes every 2 seconds)
3. V2 schema writing (optimized tables)
4. Proper integration of all components
"""

import asyncio
import os
import sqlite3
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.api.services.event_store import event_store
from backend.services.migration_adapter import MigrationAdapter


async def test_optimization_pipeline():
    """Test the complete optimization pipeline"""
    print("🧪 Testing Database Optimization Pipeline")
    print("=" * 60)
    
    # Check environment configuration
    print("\n📋 Environment Configuration:")
    print(f"  EVENT_COMPRESSION_ENABLED: {os.getenv('EVENT_COMPRESSION_ENABLED', 'false')}")
    print(f"  EVENT_BUFFER_ENABLED: {os.getenv('EVENT_BUFFER_ENABLED', 'false')}")
    print(f"  MIGRATION_MODE: {os.getenv('MIGRATION_MODE', 'v2_only')}")
    
    # Check that event_store is now a MigrationAdapter
    print(f"\n🔍 Event Store Type: {type(event_store).__name__}")
    
    if isinstance(event_store, MigrationAdapter):
        print("✅ Event store is correctly using MigrationAdapter")
        
        # Check which stores are active
        print(f"  V1 Store Active: {event_store.v1_store is not None}")
        print(f"  V2 Store Active: {event_store.v2_store is not None}")
        
        if event_store.v2_store:
            # Check V2 store components
            v2 = event_store.v2_store
            print(f"\n📊 V2 Store Components:")
            print(f"  Compressor Enabled: {v2.compressor is not None}")
            print(f"  Buffer Enabled: {v2.buffer is not None}")
            
            if v2.compressor:
                print(f"  Compression Threshold: {v2.compressor.importance_threshold}")
            
            if v2.buffer:
                print(f"  Buffer Size: {v2.buffer.max_size}")
                print(f"  Flush Interval: {v2.buffer.flush_interval}s")
    else:
        print("❌ Event store is NOT using MigrationAdapter!")
        print(f"  Actual type: {type(event_store)}")
    
    # Test storing events
    print("\n🚀 Testing Event Storage:")
    
    test_room_id = "test_optimization"
    
    # Test 1: Store a semantic event (should go through compression + buffer + v2)
    print("\n1️⃣ Storing semantic event (game_started)...")
    await event_store.store_event(
        test_room_id,
        "game_started",
        {
            "players": ["Player1", "Player2", "Player3", "Player4"],
            "timestamp": 1234567890
        }
    )
    print("✅ Stored game_started event")
    
    # Test 2: Store multiple turn events (should be compressed)
    print("\n2️⃣ Storing turn events (should be compressed)...")
    # Store multiple play events that should be accumulated
    for i in range(4):
        await event_store.store_event(
            test_room_id,
            "pieces_played",
            {
                "player_name": f"Player{i + 1}",
                "pieces": [{"kind": "SOLDIER_BLACK", "point": 10}],
                "turn_number": 1
            }
        )
    
    # Store turn complete to trigger compression
    await event_store.store_event(
        test_room_id,
        "turn_complete",
        {
            "turn_number": 1,
            "winner": "Player1",
            "piles_won": 1
        }
    )
    print("✅ Stored 4 play events + 1 turn complete event")
    
    # Test 3: Store a round_complete event (should create round snapshot)
    print("\n3️⃣ Storing round_complete event...")
    await event_store.store_event(
        test_room_id,
        "round_complete",
        {
            "round_number": 1,
            "starter_player": "Player1",
            "starter_reason": "has_general_red",
            "initial_hands": {
                "Player1": [{"kind": "GENERAL_RED", "point": 20}],
                "Player2": [{"kind": "SOLDIER_BLACK", "point": 10}],
                "Player3": [{"kind": "SOLDIER_BLACK", "point": 10}],
                "Player4": [{"kind": "SOLDIER_BLACK", "point": 10}]
            },
            "declarations": {"Player1": 2, "Player2": 2, "Player3": 2, "Player4": 2},
            "turn_sequence": [
                {"turn": 1, "winner": "Player1", "piles": 1}
            ],
            "scores": {"Player1": 10, "Player2": -5, "Player3": -5, "Player4": -5},
            "total_scores": {"Player1": 10, "Player2": -5, "Player3": -5, "Player4": -5}
        }
    )
    print("✅ Stored round_complete event")
    
    # Test 4: Force buffer flush
    print("\n4️⃣ Forcing buffer flush...")
    if hasattr(event_store, 'v2_store') and event_store.v2_store and event_store.v2_store.buffer:
        await event_store.v2_store.buffer.flush()
        print("✅ Buffer flushed")
    else:
        print("⚠️ No buffer to flush")
    
    # Check what was written to the database
    print("\n📊 Database Contents:")
    
    db_path = str(Path(__file__).parent / "game_events.db")
    conn = sqlite3.connect(db_path)
    
    # Check v2 events table
    cursor = conn.execute("""
        SELECT COUNT(*) FROM game_events_v2 
        WHERE room_id = ?
    """, (test_room_id,))
    v2_count = cursor.fetchone()[0]
    print(f"  V2 Events: {v2_count}")
    
    # Check game summaries
    cursor = conn.execute("""
        SELECT COUNT(*) FROM game_summaries 
        WHERE room_id = ?
    """, (test_room_id,))
    summary_count = cursor.fetchone()[0]
    print(f"  Game Summaries: {summary_count}")
    
    # Check round snapshots
    cursor = conn.execute("""
        SELECT COUNT(*) FROM round_snapshots 
        WHERE room_id = ?
    """, (test_room_id,))
    snapshot_count = cursor.fetchone()[0]
    print(f"  Round Snapshots: {snapshot_count}")
    
    # List all v2 events
    cursor = conn.execute("""
        SELECT event_type, timestamp 
        FROM game_events_v2 
        WHERE room_id = ?
        ORDER BY timestamp
    """, (test_room_id,))
    
    print("\n📋 V2 Events Detail:")
    for row in cursor.fetchall():
        print(f"  - {row[0]} at {row[1]}")
    
    conn.close()
    
    # Get metrics
    if hasattr(event_store, 'get_metrics'):
        print("\n📈 Performance Metrics:")
        metrics = event_store.get_metrics()
        
        if 'v2_metrics' in metrics:
            v2_metrics = metrics['v2_metrics']
            if 'compression' in v2_metrics:
                comp = v2_metrics['compression']
                print(f"  Events Processed: {comp.get('events_processed', 0)}")
                print(f"  Events Compressed: {comp.get('events_compressed', 0)}")
                print(f"  Compression Ratio: {comp.get('compression_ratio', 0):.1%}")
            
            if 'buffer' in v2_metrics:
                buf = v2_metrics['buffer']
                print(f"  Buffer Events: {buf.get('current_size', 0)}")
                print(f"  Total Flushed: {buf.get('total_events_flushed', 0)}")
    
    print("\n✅ Database Optimization Test Complete!")


async def cleanup_test_data():
    """Clean up test data"""
    db_path = str(Path(__file__).parent / "game_events.db")
    conn = sqlite3.connect(db_path)
    
    # Clean up test data
    conn.execute("DELETE FROM game_events_v2 WHERE room_id = 'test_optimization'")
    conn.execute("DELETE FROM game_summaries WHERE room_id = 'test_optimization'")
    conn.execute("DELETE FROM round_snapshots WHERE room_id = 'test_optimization'")
    conn.commit()
    conn.close()
    
    print("🧹 Test data cleaned up")


async def main():
    """Main test runner"""
    try:
        await test_optimization_pipeline()
    finally:
        await cleanup_test_data()
        
        # Shutdown event store
        if hasattr(event_store, 'shutdown'):
            await event_store.shutdown()


if __name__ == "__main__":
    asyncio.run(main())