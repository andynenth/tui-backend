#!/usr/bin/env python3
"""
Test the integrated adapter system
"""

import asyncio
from typing import Dict, Any
import json

from api.adapters.integrated_adapter_system import IntegratedAdapterSystem


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.room_id = "test_room"


async def mock_legacy_handler(websocket, message: Dict[str, Any]) -> Dict[str, Any]:
    """Mock legacy handler"""
    action = message.get("action")
    return {
        "event": "legacy_response",
        "data": {
            "action": action,
            "handled_by": "legacy"
        }
    }


async def test_integrated_system():
    """Test the integrated adapter system"""
    print("\n🚀 Integrated Adapter System Test\n")
    
    ws = MockWebSocket()
    room_state = {"room_id": "test_room"}
    
    # Create integrated system
    system = IntegratedAdapterSystem(mock_legacy_handler)
    
    # Test initial status
    print("1️⃣ Testing initial status...")
    status = system.get_status()
    print(f"   Total adapters: {status['total_adapters']}")
    print(f"   Enabled: {status['enabled_count']}")
    print(f"   Coverage: {status['coverage_percent']}%")
    assert status['global_enabled'] is True
    assert status['coverage_percent'] == 100.0
    print("   ✅ All adapters enabled by default")
    
    # Test connection adapter
    print("\n2️⃣ Testing connection adapter...")
    message = {"action": "ping", "data": {"timestamp": 123456}}
    response = await system.handle_message(ws, message, room_state)
    assert response["event"] == "pong"
    assert response["data"]["room_id"] == "test_room"
    print("   ✅ Ping handled by adapter")
    
    # Test room adapter
    print("\n3️⃣ Testing room adapter...")
    message = {"action": "create_room", "data": {"player_name": "Alice"}}
    response = await system.handle_message(ws, message, room_state)
    assert response["event"] == "room_created"
    assert response["data"]["host_name"] == "Alice"
    print("   ✅ Create room handled by adapter")
    
    # Test non-adapter action
    print("\n4️⃣ Testing legacy passthrough...")
    message = {"action": "unknown_action", "data": {}}
    response = await system.handle_message(ws, message, room_state)
    assert response["event"] == "legacy_response"
    assert response["data"]["handled_by"] == "legacy"
    print("   ✅ Unknown action passed to legacy")
    
    # Test disabling specific adapter
    print("\n5️⃣ Testing adapter disable...")
    system.disable_adapter("ping")
    message = {"action": "ping", "data": {"timestamp": 123456}}
    response = await system.handle_message(ws, message, room_state)
    assert response["event"] == "legacy_response"
    print("   ✅ Disabled adapter falls back to legacy")
    
    # Test re-enabling
    print("\n6️⃣ Testing adapter re-enable...")
    system.enable_adapter("ping")
    response = await system.handle_message(ws, message, room_state)
    assert response["event"] == "pong"
    print("   ✅ Re-enabled adapter works")
    
    # Test global disable
    print("\n7️⃣ Testing global disable...")
    system.disable_all()
    message = {"action": "create_room", "data": {"player_name": "Bob"}}
    response = await system.handle_message(ws, message, room_state)
    assert response["event"] == "legacy_response"
    print("   ✅ Global disable forces all to legacy")
    
    # Test phase enable
    print("\n8️⃣ Testing phase enable...")
    system.enable_all()
    system.enabled_adapters.clear()  # Start fresh
    system.enable_phase("connection")
    status = system.get_status()
    assert status["phases"]["connection"] is True
    assert status["phases"]["room"] is False
    print("   ✅ Phase enable works correctly")
    
    # Performance test
    print("\n9️⃣ Running performance test...")
    system.enable_all()
    
    test_messages = [
        {"action": "ping", "data": {"timestamp": 123456}},
        {"action": "create_room", "data": {"player_name": "Test"}},
        {"action": "play", "data": {"pieces": [1, 2, 3]}},  # Legacy
        {"action": "declare", "data": {"value": 3}},  # Legacy
    ]
    
    import time
    iterations = 10000
    
    start = time.time()
    for _ in range(iterations):
        for msg in test_messages:
            await system.handle_message(ws, msg, room_state)
    
    elapsed = time.time() - start
    total_messages = iterations * len(test_messages)
    per_message = elapsed / total_messages * 1000000  # microseconds
    
    print(f"   Processed {total_messages} messages in {elapsed:.3f}s")
    print(f"   Average: {per_message:.1f} μs per message")
    print("   ✅ Performance test complete")
    
    # Final status
    print("\n📊 Final Status")
    print("=" * 50)
    system.enable_all()
    status = system.get_status()
    print(json.dumps(status, indent=2))
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_integrated_system())