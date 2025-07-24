#!/usr/bin/env python3
"""
Test room management adapters
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.adapters.room_adapters import (
    handle_room_messages,
    RoomAdapterIntegration,
    ROOM_ADAPTER_ACTIONS
)


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
        self.room_id = None


async def mock_legacy_handler(websocket, message: Dict[str, Any]) -> Dict[str, Any]:
    """Mock legacy handler"""
    return {"event": "legacy_response", "data": {"handled_by": "legacy"}}


async def test_create_room():
    """Test create_room adapter"""
    print("\n1️⃣ Testing create_room adapter...")
    
    ws = MockWebSocket()
    
    # Test valid create_room
    message = {
        "action": "create_room",
        "data": {"player_name": "Alice"}
    }
    
    response = await handle_room_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "room_created"
    assert response["data"]["host_name"] == "Alice"
    assert response["data"]["success"] is True
    assert "room_id" in response["data"]
    print("   ✅ Valid create_room works")
    
    # Test missing player name
    message = {
        "action": "create_room",
        "data": {}
    }
    
    response = await handle_room_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "error"
    assert "validation_error" in response["data"]["type"]
    print("   ✅ Validation error for missing player name")


async def test_join_room():
    """Test join_room adapter"""
    print("\n2️⃣ Testing join_room adapter...")
    
    ws = MockWebSocket()
    
    # Test valid join_room
    message = {
        "action": "join_room",
        "data": {
            "room_id": "room_123",
            "player_name": "Bob"
        }
    }
    
    response = await handle_room_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "joined_room"
    assert response["data"]["room_id"] == "room_123"
    assert response["data"]["player_name"] == "Bob"
    assert response["data"]["success"] is True
    print("   ✅ Valid join_room works")
    
    # Test missing parameters
    message = {
        "action": "join_room",
        "data": {"room_id": "room_123"}
    }
    
    response = await handle_room_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "error"
    print("   ✅ Validation error for missing player name")


async def test_leave_room():
    """Test leave_room adapter"""
    print("\n3️⃣ Testing leave_room adapter...")
    
    ws = MockWebSocket()
    
    message = {
        "action": "leave_room",
        "data": {"player_name": "Charlie"}
    }
    
    response = await handle_room_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "left_room"
    assert response["data"]["player_name"] == "Charlie"
    assert response["data"]["success"] is True
    print("   ✅ leave_room works")


async def test_get_room_state():
    """Test get_room_state adapter"""
    print("\n4️⃣ Testing get_room_state adapter...")
    
    ws = MockWebSocket()
    
    # Test with room state
    room_state = {
        "room_id": "room_123",
        "slots": [{"name": "Alice", "ready": True}],
        "host_name": "Alice",
        "game_active": False
    }
    
    message = {"action": "get_room_state", "data": {}}
    
    response = await handle_room_messages(ws, message, mock_legacy_handler, room_state)
    
    assert response["event"] == "room_state"
    assert response["data"] == room_state
    print("   ✅ get_room_state with existing state works")
    
    # Test without room state
    response = await handle_room_messages(ws, message, mock_legacy_handler, None)
    
    assert response["event"] == "room_state"
    assert response["data"]["slots"] == []
    assert response["data"]["host_name"] is None
    print("   ✅ get_room_state without state returns empty")


async def test_add_bot():
    """Test add_bot adapter"""
    print("\n5️⃣ Testing add_bot adapter...")
    
    ws = MockWebSocket()
    
    message = {
        "action": "add_bot",
        "data": {"difficulty": "hard"}
    }
    
    response = await handle_room_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "bot_added"
    assert response["data"]["difficulty"] == "hard"
    assert "Bot_" in response["data"]["bot_name"]
    assert response["data"]["success"] is True
    print("   ✅ add_bot works")


async def test_remove_player():
    """Test remove_player adapter"""
    print("\n6️⃣ Testing remove_player adapter...")
    
    ws = MockWebSocket()
    
    message = {
        "action": "remove_player",
        "data": {
            "player_name": "Dave",
            "requester": "Alice"
        }
    }
    
    response = await handle_room_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "player_removed"
    assert response["data"]["player_name"] == "Dave"
    assert response["data"]["removed_by"] == "Alice"
    assert response["data"]["success"] is True
    print("   ✅ remove_player works")


async def test_passthrough():
    """Test that non-room messages pass through to legacy"""
    print("\n7️⃣ Testing passthrough for non-room messages...")
    
    ws = MockWebSocket()
    
    # Test non-room action
    message = {
        "action": "ping",
        "data": {"timestamp": 123456}
    }
    
    response = await handle_room_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "legacy_response"
    assert response["data"]["handled_by"] == "legacy"
    print("   ✅ Non-room messages pass through to legacy")


async def test_room_adapter_integration():
    """Test RoomAdapterIntegration class"""
    print("\n8️⃣ Testing RoomAdapterIntegration...")
    
    ws = MockWebSocket()
    integration = RoomAdapterIntegration(mock_legacy_handler)
    
    # Test enabled state
    message = {
        "action": "create_room",
        "data": {"player_name": "Eve"}
    }
    
    response = await integration.handle_message(ws, message)
    assert response["event"] == "room_created"
    print("   ✅ Integration handles room messages when enabled")
    
    # Test disabled state
    integration.disable()
    response = await integration.handle_message(ws, message)
    assert response["event"] == "legacy_response"
    print("   ✅ Integration passes to legacy when disabled")
    
    # Re-enable
    integration.enable()
    response = await integration.handle_message(ws, message)
    assert response["event"] == "room_created"
    print("   ✅ Integration can be re-enabled")


async def run_all_tests():
    """Run all room adapter tests"""
    print("\n🧪 Room Adapter Tests")
    print("=" * 50)
    
    tests = [
        test_create_room,
        test_join_room,
        test_leave_room,
        test_get_room_state,
        test_add_bot,
        test_remove_player,
        test_passthrough,
        test_room_adapter_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            failed += 1
    
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} tests failed")


if __name__ == "__main__":
    asyncio.run(run_all_tests())