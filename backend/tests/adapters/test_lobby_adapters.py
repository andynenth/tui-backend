#!/usr/bin/env python3
"""
Test lobby operation adapters
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.adapters.lobby_adapters import (
    handle_lobby_messages,
    LobbyAdapterIntegration,
    LOBBY_ADAPTER_ACTIONS,
    format_room_for_lobby
)


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
        self.in_lobby = True


async def mock_legacy_handler(websocket, message: Dict[str, Any]) -> Dict[str, Any]:
    """Mock legacy handler"""
    return {"event": "legacy_response", "data": {"handled_by": "legacy"}}


async def test_request_room_list():
    """Test request_room_list adapter"""
    print("\n1️⃣ Testing request_room_list adapter...")
    
    ws = MockWebSocket()
    
    message = {
        "action": "request_room_list",
        "data": {}
    }
    
    response = await handle_lobby_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "room_list_requested"
    assert response["data"]["success"] is True
    assert "message" in response["data"]
    print("   ✅ request_room_list works")


async def test_get_rooms():
    """Test get_rooms adapter"""
    print("\n2️⃣ Testing get_rooms adapter...")
    
    ws = MockWebSocket()
    
    # Test without filters
    message = {
        "action": "get_rooms",
        "data": {}
    }
    
    response = await handle_lobby_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "room_list"
    assert "rooms" in response["data"]
    assert "total_count" in response["data"]
    assert response["data"]["filter_applied"] is False
    print("   ✅ get_rooms without filter works")
    
    # Test with available_only filter
    message = {
        "action": "get_rooms",
        "data": {
            "filter": {
                "available_only": True
            }
        }
    }
    
    response = await handle_lobby_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "room_list"
    assert response["data"]["filter_applied"] is True
    # Should filter out full rooms
    for room in response["data"]["rooms"]:
        assert room["player_count"] < room["max_players"]
    print("   ✅ get_rooms with available_only filter works")
    
    # Test with not_in_game filter
    message = {
        "action": "get_rooms",
        "data": {
            "filter": {
                "not_in_game": True
            }
        }
    }
    
    response = await handle_lobby_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "room_list"
    # Should filter out rooms with active games
    for room in response["data"]["rooms"]:
        assert room["game_active"] is False
    print("   ✅ get_rooms with not_in_game filter works")
    
    # Test with combined filters
    message = {
        "action": "get_rooms",
        "data": {
            "filter": {
                "available_only": True,
                "not_in_game": True
            }
        }
    }
    
    response = await handle_lobby_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "room_list"
    # Should apply both filters
    for room in response["data"]["rooms"]:
        assert room["player_count"] < room["max_players"]
        assert room["game_active"] is False
    print("   ✅ get_rooms with combined filters works")


async def test_format_room_for_lobby():
    """Test room formatting function"""
    print("\n3️⃣ Testing format_room_for_lobby...")
    
    # Test with full room data
    room_data = {
        "room_id": "test_123",
        "host_name": "Alice",
        "players": [
            {"name": "Alice", "ready": True},
            {"name": "Bob", "ready": False}
        ],
        "game_active": True,
        "is_public": False,
        "extra_field": "should_be_ignored"
    }
    
    formatted = format_room_for_lobby(room_data)
    
    assert formatted["room_id"] == "test_123"
    assert formatted["host_name"] == "Alice"
    assert formatted["player_count"] == 2
    assert formatted["max_players"] == 4
    assert formatted["game_active"] is True
    assert formatted["is_public"] is False
    assert "extra_field" not in formatted
    print("   ✅ Room formatting works correctly")
    
    # Test with minimal room data
    minimal_room = {
        "room_id": "test_456",
        "host_name": "Charlie"
    }
    
    formatted = format_room_for_lobby(minimal_room)
    
    assert formatted["room_id"] == "test_456"
    assert formatted["host_name"] == "Charlie"
    assert formatted["player_count"] == 0
    assert formatted["max_players"] == 4
    assert formatted["game_active"] is False
    assert formatted["is_public"] is True
    print("   ✅ Formatting handles missing fields with defaults")


async def test_passthrough():
    """Test that non-lobby messages pass through to legacy"""
    print("\n4️⃣ Testing passthrough for non-lobby messages...")
    
    ws = MockWebSocket()
    
    # Test non-lobby action
    message = {
        "action": "ping",
        "data": {"timestamp": 123456}
    }
    
    response = await handle_lobby_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "legacy_response"
    assert response["data"]["handled_by"] == "legacy"
    print("   ✅ Non-lobby messages pass through to legacy")


async def test_lobby_adapter_integration():
    """Test LobbyAdapterIntegration class"""
    print("\n5️⃣ Testing LobbyAdapterIntegration...")
    
    ws = MockWebSocket()
    integration = LobbyAdapterIntegration(mock_legacy_handler)
    
    # Test enabled state
    message = {
        "action": "get_rooms",
        "data": {}
    }
    
    response = await integration.handle_message(ws, message)
    assert response["event"] == "room_list"
    print("   ✅ Integration handles lobby messages when enabled")
    
    # Test disabled state
    integration.disable()
    response = await integration.handle_message(ws, message)
    assert response["event"] == "legacy_response"
    print("   ✅ Integration passes to legacy when disabled")
    
    # Re-enable
    integration.enable()
    response = await integration.handle_message(ws, message)
    assert response["event"] == "room_list"
    print("   ✅ Integration can be re-enabled")


async def run_all_tests():
    """Run all lobby adapter tests"""
    print("\n🧪 Lobby Adapter Tests")
    print("=" * 50)
    
    tests = [
        test_request_room_list,
        test_get_rooms,
        test_format_room_for_lobby,
        test_passthrough,
        test_lobby_adapter_integration
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