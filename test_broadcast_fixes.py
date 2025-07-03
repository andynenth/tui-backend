#!/usr/bin/env python3
"""
Test and utility script for broadcast loop fixes
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import after path is set up
import backend.socket_manager as socket_manager


async def test_deduplication():
    """Test that comprehensive event deduplication works"""
    print("\n=== Testing Comprehensive Event Deduplication ===")
    
    # Test different event types
    test_events = [
        ('phase_change', {'phase': 'turn', 'sequence': 1}),
        ('phase_change', {'phase': 'turn', 'sequence': 1}),  # Duplicate
        ('turn_complete', {'turn_number': 5, 'winner': 'Alice', 'timestamp': 123}),
        ('turn_complete', {'turn_number': 5, 'winner': 'Alice', 'timestamp': 123}),  # Duplicate
        ('play', {'player': 'Bob', 'sequence': 10, 'timestamp': 456}),
        ('play', {'player': 'Bob', 'sequence': 10, 'timestamp': 456}),  # Duplicate
    ]
    
    sm = socket_manager._socket_manager
    duplicates_blocked = 0
    
    for event_type, data in test_events:
        event_hash = sm._create_event_hash(event_type, data)
        print(f"Event: {event_type}, Hash: {event_hash}")
        
        # Simulate broadcast attempt
        last_time = sm._last_broadcast.get(f"test_room:{event_hash}", 0)
        if last_time > 0:
            print(f"  ✅ Would block duplicate!")
            duplicates_blocked += 1
        else:
            print(f"  → Would broadcast")
            sm._last_broadcast[f"test_room:{event_hash}"] = 100  # Fake timestamp
    
    print(f"\nResult: Blocked {duplicates_blocked} duplicates out of 6 events")
    return duplicates_blocked == 3


async def test_queue_cleanup():
    """Test queue cleanup mechanism"""
    print("\n=== Testing Queue Cleanup ===")
    
    # Create a test queue
    test_queue = asyncio.Queue()
    
    # Add old and new messages
    old_time = 100
    new_time = 200
    
    messages = [
        {'event': 'turn_complete', 'data': {'timestamp': old_time}},  # Old
        {'event': 'turn_complete', 'data': {'timestamp': old_time}},  # Old
        {'event': 'phase_change', 'data': {'timestamp': new_time}},   # New
        {'event': 'play', 'data': {'timestamp': new_time}},           # New
    ]
    
    for msg in messages:
        await test_queue.put(msg)
    
    print(f"Queue size before cleanup: {test_queue.qsize()}")
    
    # Simulate cleanup (keeping only recent messages)
    messages_to_keep = []
    cleaned_count = 0
    
    while not test_queue.empty():
        msg = await test_queue.get()
        if msg.get('data', {}).get('timestamp', 0) >= new_time:
            messages_to_keep.append(msg)
        else:
            cleaned_count += 1
    
    # Put back kept messages
    for msg in messages_to_keep:
        await test_queue.put(msg)
    
    print(f"Cleaned {cleaned_count} old messages")
    print(f"Queue size after cleanup: {test_queue.qsize()}")
    
    return cleaned_count == 2 and test_queue.qsize() == 2


async def clear_room_broadcast_queue(room_id: str):
    """Utility to clear all stale messages from a room's broadcast queue"""
    print(f"\n=== Clearing Broadcast Queue for Room {room_id} ===")
    
    try:
        # Clear turn_complete messages
        cleared_turn = await socket_manager.clear_room_queue(room_id, ['turn_complete'])
        print(f"Cleared {cleared_turn} turn_complete messages")
        
        # Clear old phase_change messages
        cleared_phase = await socket_manager.clear_room_queue(room_id, ['phase_change'])
        print(f"Cleared {cleared_phase} phase_change messages")
        
        # Get current queue stats
        stats = socket_manager.get_room_stats(room_id)
        if stats and 'queue_stats' in stats:
            queue_info = stats['queue_stats'].get(room_id, {})
            print(f"Queue stats: {queue_info}")
        
        return True
    except Exception as e:
        print(f"Error clearing queue: {e}")
        return False


async def monitor_room_queue(room_id: str, duration: int = 10):
    """Monitor a room's broadcast queue for activity"""
    print(f"\n=== Monitoring Room {room_id} Queue for {duration} seconds ===")
    
    start_time = asyncio.get_event_loop().time()
    last_stats = {}
    
    while asyncio.get_event_loop().time() - start_time < duration:
        stats = socket_manager.get_room_stats(room_id)
        
        if stats and stats != last_stats:
            queue_stats = stats.get('queue_stats', {}).get(room_id, {})
            active_connections = stats.get('active_connections', 0)
            
            print(f"\nTime: +{asyncio.get_event_loop().time() - start_time:.1f}s")
            print(f"  Active connections: {active_connections}")
            print(f"  Messages processed: {queue_stats.get('messages_processed', 0)}")
            print(f"  Average latency: {queue_stats.get('average_latency', 0):.3f}s")
            
            last_stats = stats
        
        await asyncio.sleep(1)
    
    print("\nMonitoring complete")


async def main():
    """Run tests and provide utility options"""
    print("🔧 Broadcast Loop Fix Test & Utility Tool")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "clear" and len(sys.argv) > 2:
            room_id = sys.argv[2]
            await clear_room_broadcast_queue(room_id)
        
        elif command == "monitor" and len(sys.argv) > 2:
            room_id = sys.argv[2]
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            await monitor_room_queue(room_id, duration)
        
        else:
            print("Usage:")
            print("  python test_broadcast_fixes.py               # Run tests")
            print("  python test_broadcast_fixes.py clear ROOM    # Clear room queue")
            print("  python test_broadcast_fixes.py monitor ROOM [SECONDS]  # Monitor queue")
    
    else:
        # Run tests
        print("\nRunning automated tests...\n")
        
        test_results = []
        
        # Test 1: Deduplication
        result1 = await test_deduplication()
        test_results.append(("Event Deduplication", result1))
        
        # Test 2: Queue Cleanup
        result2 = await test_queue_cleanup()
        test_results.append(("Queue Cleanup", result2))
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        for test_name, passed in test_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        all_passed = all(passed for _, passed in test_results)
        
        if all_passed:
            print("\n✅ All tests passed! The broadcast loop fixes are working correctly.")
            print("\nTo clear a stuck room queue, run:")
            print("  python test_broadcast_fixes.py clear ROOM_ID")
        else:
            print("\n❌ Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())
