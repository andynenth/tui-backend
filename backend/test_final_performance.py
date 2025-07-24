#!/usr/bin/env python3
"""
Test final adapter performance - targeting <20% overhead
"""

import asyncio
import time
from typing import Dict, Any
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import implementations
from api.adapters.websocket_adapter_final import (
    handle_with_minimal_overhead,
    handle_with_surgical_precision
)


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.room_id = "test_room"


async def mock_legacy_handler(websocket, message: Dict[str, Any]) -> Dict[str, Any]:
    """Mock legacy handler that simulates original behavior"""
    action = message.get("action")
    
    if action == "ping":
        return {
            "event": "pong",
            "data": {
                "server_time": time.time(),
                "room_id": getattr(websocket, 'room_id', None)
            }
        }
    elif action == "client_ready":
        return {
            "event": "room_state_update",
            "data": {"slots": [], "host_name": ""}
        }
    elif action == "ack":
        return None
    elif action == "sync_request":
        return {
            "event": "sync_response",
            "data": {
                "room_state": None,
                "client_id": message.get("data", {}).get("client_id"),
                "timestamp": "2025-01-01T00:00:00"
            }
        }
    elif action == "play":
        # Simulate a more complex game action
        return {
            "event": "play_result",
            "data": {
                "success": True,
                "next_player": "player2",
                "game_state": "active"
            }
        }
    
    return {"event": "error", "data": {"message": "Unknown action"}}


async def run_final_performance_test():
    """Run final performance test with realistic message mix"""
    print("\n🎯 Final Adapter Performance Test - Targeting <20% Overhead\n")
    
    # Realistic message mix (based on actual game usage)
    test_messages = [
        # High frequency messages
        {"action": "ping", "data": {"timestamp": 123456}},  # 40%
        {"action": "ping", "data": {"timestamp": 123457}},
        {"action": "ping", "data": {"timestamp": 123458}},
        {"action": "ping", "data": {"timestamp": 123459}},
        
        # Game actions (most common)
        {"action": "play", "data": {"pieces": [1, 2, 3]}},  # 30%
        {"action": "play", "data": {"pieces": [4, 5]}},
        {"action": "play", "data": {"pieces": [6]}},
        
        # Less frequent
        {"action": "declare", "data": {"value": 3}},  # 20%
        {"action": "start_game", "data": {}},
        
        # Rare
        {"action": "client_ready", "data": {"player_name": "test"}},  # 10%
    ]
    
    iterations = 10000
    ws = MockWebSocket()
    room_state = {"room_id": "test_room", "players": [], "host_name": ""}
    
    # Test 1: Legacy baseline
    print("1️⃣ Testing legacy handler (baseline)...")
    start = time.time()
    
    for _ in range(iterations):
        for msg in test_messages:
            await mock_legacy_handler(ws, msg)
    
    legacy_time = time.time() - start
    total_messages = iterations * len(test_messages)
    print(f"   Time: {legacy_time:.3f}s for {total_messages} messages")
    print(f"   Per message: {legacy_time / total_messages * 1000000:.1f} μs")
    
    # Test 2: Minimal overhead approach
    print("\n2️⃣ Testing minimal overhead approach...")
    start = time.time()
    
    for _ in range(iterations):
        for msg in test_messages:
            await handle_with_minimal_overhead(ws, msg, mock_legacy_handler, room_state)
    
    minimal_time = time.time() - start
    minimal_overhead = ((minimal_time - legacy_time) / legacy_time) * 100
    print(f"   Time: {minimal_time:.3f}s")
    print(f"   Per message: {minimal_time / total_messages * 1000000:.1f} μs")
    print(f"   Overhead: {minimal_overhead:.1f}%")
    
    # Test 3: Surgical precision approach
    print("\n3️⃣ Testing surgical precision approach...")
    start = time.time()
    
    for _ in range(iterations):
        for msg in test_messages:
            await handle_with_surgical_precision(ws, msg, mock_legacy_handler, room_state)
    
    surgical_time = time.time() - start
    surgical_overhead = ((surgical_time - legacy_time) / legacy_time) * 100
    print(f"   Time: {surgical_time:.3f}s")
    print(f"   Per message: {surgical_time / total_messages * 1000000:.1f} μs")
    print(f"   Overhead: {surgical_overhead:.1f}%")
    
    # Summary
    print("\n📊 Performance Summary")
    print("=" * 50)
    print(f"Legacy baseline:      {legacy_time:.3f}s (100%)")
    print(f"Minimal overhead:     {minimal_time:.3f}s ({100 + minimal_overhead:.1f}%)")
    print(f"Surgical precision:   {surgical_time:.3f}s ({100 + surgical_overhead:.1f}%)")
    
    # Target analysis
    print("\n🎯 Target Analysis (20% overhead goal)")
    print("=" * 50)
    
    target = 20.0
    if minimal_overhead <= target:
        print(f"✅ Minimal overhead MEETS target: {minimal_overhead:.1f}% ≤ {target}%")
    else:
        print(f"❌ Minimal overhead EXCEEDS target: {minimal_overhead:.1f}% > {target}%")
    
    if surgical_overhead <= target:
        print(f"✅ Surgical precision MEETS target: {surgical_overhead:.1f}% ≤ {target}%")
    else:
        print(f"❌ Surgical precision EXCEEDS target: {surgical_overhead:.1f}% > {target}%")
    
    # Breakdown by message type
    print("\n📈 Per-Message Type Analysis (Minimal Overhead)")
    print("=" * 50)
    
    message_types = [
        ("ping", {"action": "ping", "data": {"timestamp": 123456}}),
        ("play", {"action": "play", "data": {"pieces": [1, 2, 3]}}),
        ("declare", {"action": "declare", "data": {"value": 3}}),
        ("client_ready", {"action": "client_ready", "data": {"player_name": "test"}}),
    ]
    
    for name, msg in message_types:
        # Legacy
        start = time.time()
        for _ in range(5000):
            await mock_legacy_handler(ws, msg)
        legacy_single = time.time() - start
        
        # Minimal
        start = time.time()
        for _ in range(5000):
            await handle_with_minimal_overhead(ws, msg, mock_legacy_handler, room_state)
        minimal_single = time.time() - start
        
        overhead = ((minimal_single - legacy_single) / legacy_single) * 100
        print(f"{name:<15} Legacy: {legacy_single*200:.2f}ms/1000  "
              f"Minimal: {minimal_single*200:.2f}ms/1000  "
              f"Overhead: +{overhead:.1f}%")
    
    print("\n💡 Recommendations:")
    if minimal_overhead <= target:
        print("✅ The minimal overhead approach achieves the performance target!")
        print("   - Use this approach for the adapter implementation")
        print("   - Only intercept messages that need adaptation")
        print("   - Pass through everything else to legacy")
    else:
        print("⚠️  Further optimization needed:")
        print("   - Consider caching compiled message handlers")
        print("   - Use C extensions for critical paths")
        print("   - Profile with cProfile to find hidden bottlenecks")


if __name__ == "__main__":
    asyncio.run(run_final_performance_test())