#!/usr/bin/env python3
"""
Test ultra-optimized adapter performance
Compares multiple optimization strategies
"""

import asyncio
import time
from typing import Dict, Any, Optional
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import different implementations
from api.adapters.websocket_adapter_integration import handle_websocket_message_with_adapters as original_handler

# Import and configure optimized version
from api.adapters import adapter_registry_optimized
from api.adapters import websocket_adapter_integration_optimized

# Set up optimized registry
adapter_registry_optimized.adapter_registry = adapter_registry_optimized.AdapterRegistry()
websocket_adapter_integration_optimized._registry = adapter_registry_optimized.adapter_registry
optimized_handler = websocket_adapter_integration_optimized.handle_websocket_message_with_adapters

# Import ultra-optimized versions
from api.adapters.websocket_adapter_integration_ultra_optimized import (
    handle_websocket_message_ultra_optimized as ultra_handler,
    handle_websocket_message_direct_dispatch as direct_handler
)


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


async def test_single_implementation(name: str, handler_func, ws, messages, iterations, room_state):
    """Test a single implementation and return timing"""
    start_time = time.time()
    
    for _ in range(iterations):
        for msg in messages:
            await handler_func(ws, msg, mock_legacy_handler, room_state)
    
    elapsed = time.time() - start_time
    return elapsed


async def run_performance_comparison():
    """Run comprehensive performance comparison"""
    print("\n🚀 Ultra-Optimized Adapter Performance Test\n")
    
    # Test messages
    test_messages = [
        {"action": "ping", "data": {"timestamp": 123456}},
        {"action": "client_ready", "data": {"player_name": "test"}},
        {"action": "ack", "data": {"sequence": 1}},
        {"action": "sync_request", "data": {"client_id": "test123"}},
    ]
    
    # Number of iterations
    iterations = 10000
    
    # Create mock websocket and room state
    ws = MockWebSocket()
    room_state = {"room_id": "test_room", "players": [], "host_name": ""}
    
    # Test implementations
    implementations = [
        ("Legacy (baseline)", mock_legacy_handler),
        ("Original adapters", lambda ws, msg, _, rs: original_handler(ws, msg, mock_legacy_handler, rs)),
        ("Optimized adapters", lambda ws, msg, _, rs: optimized_handler(ws, msg, mock_legacy_handler, rs)),
        ("Ultra-optimized", lambda ws, msg, _, rs: ultra_handler(ws, msg, mock_legacy_handler, rs)),
        ("Direct dispatch", lambda ws, msg, _, rs: direct_handler(ws, msg, mock_legacy_handler, rs)),
    ]
    
    results = {}
    
    # Run tests
    for name, handler in implementations:
        print(f"Testing {name}...")
        if name == "Legacy (baseline)":
            # Special case for legacy - it doesn't take room_state
            start = time.time()
            for _ in range(iterations):
                for msg in test_messages:
                    await mock_legacy_handler(ws, msg)
            elapsed = time.time() - start
        else:
            elapsed = await test_single_implementation(
                name, handler, ws, test_messages, iterations, room_state
            )
        
        results[name] = elapsed
        total_messages = iterations * len(test_messages)
        print(f"  Time: {elapsed:.3f}s for {total_messages} messages")
        print(f"  Per message: {elapsed / total_messages * 1000:.3f}ms")
    
    # Calculate overheads
    legacy_time = results["Legacy (baseline)"]
    print("\n📊 Performance Summary")
    print("=" * 60)
    
    for name, elapsed in results.items():
        overhead = ((elapsed - legacy_time) / legacy_time) * 100
        if name == "Legacy (baseline)":
            print(f"{name:<20} {elapsed:.3f}s (baseline)")
        else:
            print(f"{name:<20} {elapsed:.3f}s (+{overhead:.1f}% overhead)")
    
    # Check against target
    print("\n🎯 Target Analysis (20% overhead goal)")
    print("=" * 60)
    
    target_overhead = 20.0
    for name, elapsed in results.items():
        if name == "Legacy (baseline)":
            continue
        
        overhead = ((elapsed - legacy_time) / legacy_time) * 100
        if overhead <= target_overhead:
            print(f"✅ {name:<20} MEETS target ({overhead:.1f}%)")
        else:
            print(f"❌ {name:<20} EXCEEDS target ({overhead:.1f}% vs {target_overhead}%)")
    
    # Test individual message types for best performer
    print("\n🔬 Detailed Analysis - Direct Dispatch")
    print("=" * 60)
    
    for msg in test_messages:
        action = msg["action"]
        
        # Legacy baseline
        start = time.time()
        for _ in range(5000):
            await mock_legacy_handler(ws, msg)
        legacy_single = time.time() - start
        
        # Direct dispatch
        start = time.time()
        for _ in range(5000):
            await direct_handler(ws, msg, mock_legacy_handler, room_state)
        direct_single = time.time() - start
        
        overhead = ((direct_single - legacy_single) / legacy_single) * 100
        print(f"{action:<15} Legacy: {legacy_single*200:.2f}ms/1000  "
              f"Direct: {direct_single*200:.2f}ms/1000  "
              f"Overhead: +{overhead:.1f}%")


if __name__ == "__main__":
    asyncio.run(run_performance_comparison())