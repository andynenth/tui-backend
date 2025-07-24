#!/usr/bin/env python3
"""
Test WebSocket Adapter Integration
Verifies the adapter wrapper works correctly before integrating into ws.py.
"""

import asyncio
import os
from typing import Dict, Any

# Set environment variables for testing
os.environ["ADAPTER_ENABLED"] = "true"
os.environ["ADAPTER_ROLLOUT_PERCENTAGE"] = "100"

from api.routes.ws_adapter_wrapper import adapter_wrapper


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
        self.room_id = None
    
    async def send_json(self, data: Dict[str, Any]):
        self.messages_sent.append(data)


async def test_adapter_wrapper():
    """Test the adapter wrapper functionality"""
    print("\n🧪 Testing WebSocket Adapter Wrapper\n")
    
    # Initialize wrapper
    adapter_wrapper.initialize()
    
    # Test 1: Status check
    print("1️⃣ Testing status endpoint...")
    status = adapter_wrapper.get_status()
    print(f"   Enabled: {status['enabled']}")
    print(f"   Rollout: {status['rollout_percentage']}%")
    print(f"   Initialized: {status['initialized']}")
    assert status['enabled'] is True
    assert status['rollout_percentage'] == 100
    print("   ✅ Status check passed")
    
    # Test 2: Message handling
    print("\n2️⃣ Testing message handling...")
    
    ws = MockWebSocket()
    
    # Test ping message
    message = {
        "event": "ping",
        "data": {"timestamp": 123456}
    }
    
    response = await adapter_wrapper.try_handle_with_adapter(ws, message, "lobby")
    
    assert response is not None, "Adapter should handle ping"
    assert response["event"] == "pong"
    assert response["data"]["timestamp"] == 123456
    print("   ✅ Ping message handled correctly")
    
    # Test 3: Legacy-only events
    print("\n3️⃣ Testing legacy-only events...")
    
    # ack should not be handled by adapter
    ack_message = {
        "event": "ack",
        "data": {"sequence": 1}
    }
    
    ack_response = await adapter_wrapper.try_handle_with_adapter(ws, ack_message, "lobby")
    assert ack_response is None, "ack should be handled by legacy"
    print("   ✅ Legacy-only events passed through correctly")
    
    # Test 4: Room events
    print("\n4️⃣ Testing room events...")
    
    create_room_message = {
        "event": "create_room",
        "data": {"player_name": "TestPlayer"}
    }
    
    room_response = await adapter_wrapper.try_handle_with_adapter(ws, create_room_message, "lobby")
    
    assert room_response is not None, "Adapter should handle create_room"
    assert room_response["event"] == "room_created"
    assert room_response["data"]["host_name"] == "TestPlayer"
    print("   ✅ Room events handled correctly")
    
    # Test 5: Rollout percentage
    print("\n5️⃣ Testing rollout percentage...")
    
    # Temporarily change rollout to 0%
    adapter_wrapper.rollout_percentage = 0
    
    response = await adapter_wrapper.try_handle_with_adapter(ws, message, "lobby")
    assert response is None, "Should not handle at 0% rollout"
    
    # Reset to 100%
    adapter_wrapper.rollout_percentage = 100
    print("   ✅ Rollout percentage works correctly")
    
    # Test 6: Error handling
    print("\n6️⃣ Testing error handling...")
    
    # Test with invalid message
    invalid_message = {
        "event": "unknown_event",
        "data": {}
    }
    
    error_response = await adapter_wrapper.try_handle_with_adapter(ws, invalid_message, "lobby")
    # Should fall back to None (legacy) for unknown events
    assert error_response is None or error_response["event"] == "legacy_response"
    print("   ✅ Error handling works correctly")
    
    # Test 7: Disabled state
    print("\n7️⃣ Testing disabled state...")
    
    adapter_wrapper.enabled = False
    response = await adapter_wrapper.try_handle_with_adapter(ws, message, "lobby")
    assert response is None, "Should not handle when disabled"
    
    adapter_wrapper.enabled = True
    print("   ✅ Disable functionality works correctly")
    
    print("\n✅ All tests passed!")
    print("\n📊 Summary:")
    print("- Adapter wrapper works correctly")
    print("- Messages are routed to adapters when enabled")
    print("- Legacy-only events are passed through")
    print("- Rollout percentage controls usage")
    print("- Error handling falls back to legacy")
    print("\n🎯 Ready for integration into ws.py!")


async def test_integration_example():
    """Example of how the integration would work in ws.py"""
    print("\n\n🔧 Integration Example")
    print("=" * 50)
    print("""
Example code for ws.py integration:

async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # ... existing code ...
    
    while True:
        message = await websocket.receive_json()
        
        # Validation...
        
        # ADAPTER INTEGRATION
        adapter_response = await adapter_wrapper.try_handle_with_adapter(
            registered_ws, message, room_id
        )
        
        if adapter_response is not None:
            if adapter_response:
                await registered_ws.send_json(adapter_response)
            continue
        
        # Continue with existing event handling...
        event_name = message.get("event")
        # ... rest of existing code ...
""")


if __name__ == "__main__":
    asyncio.run(test_adapter_wrapper())
    asyncio.run(test_integration_example())