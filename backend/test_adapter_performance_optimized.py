#!/usr/bin/env python3
"""
Test adapter performance with optimizations
Compares optimized adapters vs original adapters vs legacy handlers
"""

import asyncio
import time
from typing import Dict, Any, Optional
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import original modules
from api.adapters.adapter_registry import get_adapter_registry as get_original_registry
from api.adapters.websocket_adapter_integration import handle_websocket_message_with_adapters as original_handler

# Import optimized modules
from api.adapters import adapter_registry_optimized
from api.adapters import websocket_adapter_integration_optimized

# Replace the registry in the optimized modules
adapter_registry_optimized.adapter_registry = adapter_registry_optimized.AdapterRegistry()
websocket_adapter_integration_optimized._registry = adapter_registry_optimized.adapter_registry

# Now import the functions
get_optimized_registry = adapter_registry_optimized.get_adapter_registry
optimized_handler = websocket_adapter_integration_optimized.handle_websocket_message_with_adapters


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
        self.room_id = "test_room"
    
    async def send(self, message: str):
        self.messages_sent.append(message)


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
    
    return {"event": "error", "data": {"message": "Unknown action"}}


async def run_performance_test():
    """Run performance comparison test"""
    print("\n🔬 Adapter Performance Test - Optimized vs Original vs Legacy\n")
    
    # Test messages
    test_messages = [
        {"action": "ping", "data": {"timestamp": 123456}},
        {"action": "client_ready", "data": {"player_name": "test"}},
        {"action": "ack", "data": {"sequence": 1}},
        {"action": "sync_request", "data": {"client_id": "test123"}},
    ]
    
    # Number of iterations
    iterations = 10000
    
    # Create mock websocket
    ws = MockWebSocket()
    room_state = {"room_id": "test_room", "players": [], "host_name": ""}
    
    # Test 1: Legacy handler baseline
    print("1️⃣ Testing legacy handler (baseline)...")
    start_time = time.time()
    
    for _ in range(iterations):
        for msg in test_messages:
            await mock_legacy_handler(ws, msg)
    
    legacy_time = time.time() - start_time
    print(f"   Legacy time: {legacy_time:.3f}s for {iterations * len(test_messages)} messages")
    print(f"   Per message: {legacy_time / (iterations * len(test_messages)) * 1000:.3f}ms")
    
    # Test 2: Original adapter implementation
    print("\n2️⃣ Testing original adapter implementation...")
    original_registry = get_original_registry()
    
    start_time = time.time()
    
    for _ in range(iterations):
        for msg in test_messages:
            await original_handler(ws, msg, mock_legacy_handler, room_state)
    
    original_time = time.time() - start_time
    original_overhead = ((original_time - legacy_time) / legacy_time) * 100
    
    print(f"   Original adapter time: {original_time:.3f}s")
    print(f"   Per message: {original_time / (iterations * len(test_messages)) * 1000:.3f}ms")
    print(f"   Overhead: {original_overhead:.1f}%")
    
    # Test 3: Optimized adapter implementation
    print("\n3️⃣ Testing optimized adapter implementation...")
    optimized_registry = get_optimized_registry()
    
    start_time = time.time()
    
    for _ in range(iterations):
        for msg in test_messages:
            await optimized_handler(ws, msg, mock_legacy_handler, room_state)
    
    optimized_time = time.time() - start_time
    optimized_overhead = ((optimized_time - legacy_time) / legacy_time) * 100
    
    print(f"   Optimized adapter time: {optimized_time:.3f}s")
    print(f"   Per message: {optimized_time / (iterations * len(test_messages)) * 1000:.3f}ms")
    print(f"   Overhead: {optimized_overhead:.1f}%")
    
    # Summary
    print("\n📊 Performance Summary")
    print("=" * 50)
    print(f"Legacy baseline:        {legacy_time:.3f}s (100%)")
    print(f"Original adapters:      {original_time:.3f}s ({100 + original_overhead:.1f}%)")
    print(f"Optimized adapters:     {optimized_time:.3f}s ({100 + optimized_overhead:.1f}%)")
    print(f"\nOptimization improvement: {original_overhead - optimized_overhead:.1f}% reduction")
    
    # Check if we meet the target
    target_overhead = 20.0
    if optimized_overhead <= target_overhead:
        print(f"\n✅ SUCCESS: Optimized overhead ({optimized_overhead:.1f}%) is within target ({target_overhead}%)")
    else:
        print(f"\n⚠️  WARNING: Optimized overhead ({optimized_overhead:.1f}%) exceeds target ({target_overhead}%)")
        print(f"   Additional {optimized_overhead - target_overhead:.1f}% reduction needed")
    
    # Detailed breakdown
    print("\n📈 Detailed Performance Metrics")
    print("=" * 50)
    
    # Test individual message types
    for msg_type in test_messages:
        action = msg_type["action"]
        print(f"\n{action}:")
        
        # Legacy
        start = time.time()
        for _ in range(1000):
            await mock_legacy_handler(ws, msg_type)
        legacy_single = time.time() - start
        
        # Original
        start = time.time()
        for _ in range(1000):
            await original_handler(ws, msg_type, mock_legacy_handler, room_state)
        original_single = time.time() - start
        
        # Optimized
        start = time.time()
        for _ in range(1000):
            await optimized_handler(ws, msg_type, mock_legacy_handler, room_state)
        optimized_single = time.time() - start
        
        print(f"  Legacy:    {legacy_single*1000:.2f}ms/1000 calls")
        print(f"  Original:  {original_single*1000:.2f}ms/1000 calls (+{((original_single-legacy_single)/legacy_single)*100:.1f}%)")
        print(f"  Optimized: {optimized_single*1000:.2f}ms/1000 calls (+{((optimized_single-legacy_single)/legacy_single)*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(run_performance_test())