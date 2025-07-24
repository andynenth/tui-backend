#!/usr/bin/env python3
"""
Test game action adapters
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.adapters.game_adapters import (
    handle_game_messages,
    GameAdapterIntegration,
    GAME_ADAPTER_ACTIONS
)


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
        self.room_id = "test_room"
        self.player_name = "TestPlayer"


async def mock_legacy_handler(websocket, message: Dict[str, Any]) -> Dict[str, Any]:
    """Mock legacy handler"""
    return {"event": "legacy_response", "data": {"handled_by": "legacy"}}


async def test_start_game():
    """Test start_game adapter"""
    print("\n1️⃣ Testing start_game adapter...")
    
    ws = MockWebSocket()
    
    # Test valid start_game
    message = {
        "action": "start_game",
        "data": {"player_name": "Alice"}
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "game_started"
    assert response["data"]["success"] is True
    assert response["data"]["initial_phase"] == "PREPARATION"
    assert response["data"]["round_number"] == 1
    print("   ✅ Valid start_game works")
    
    # Test missing player name
    message = {
        "action": "start_game",
        "data": {}
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "error"
    assert "validation_error" in response["data"]["type"]
    print("   ✅ Validation error for missing player name")


async def test_declare():
    """Test declare adapter"""
    print("\n2️⃣ Testing declare adapter...")
    
    ws = MockWebSocket()
    
    # Test valid declaration
    message = {
        "action": "declare",
        "data": {
            "player_name": "Bob",
            "pile_count": 3
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "declaration_made"
    assert response["data"]["player_name"] == "Bob"
    assert response["data"]["pile_count"] == 3
    assert response["data"]["success"] is True
    print("   ✅ Valid declaration works")
    
    # Test invalid pile count
    message = {
        "action": "declare",
        "data": {
            "player_name": "Bob",
            "pile_count": 9
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "error"
    assert "between 0 and 8" in response["data"]["message"]
    print("   ✅ Validation error for invalid pile count")
    
    # Test missing parameters
    message = {
        "action": "declare",
        "data": {"player_name": "Bob"}
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "error"
    print("   ✅ Validation error for missing pile count")


async def test_play():
    """Test play/play_pieces adapter"""
    print("\n3️⃣ Testing play adapter...")
    
    ws = MockWebSocket()
    
    # Test valid play action
    message = {
        "action": "play",
        "data": {
            "player_name": "Charlie",
            "pieces": [5, 5, 5]
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "play_made"
    assert response["data"]["player_name"] == "Charlie"
    assert response["data"]["pieces_played"] == [5, 5, 5]
    assert response["data"]["pieces_count"] == 3
    assert response["data"]["success"] is True
    print("   ✅ Valid play action works")
    
    # Test legacy play_pieces action
    message = {
        "action": "play_pieces",
        "data": {
            "player_name": "Charlie",
            "pieces": [10]
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "play_made"
    assert response["data"]["pieces_count"] == 1
    print("   ✅ Legacy play_pieces action works")
    
    # Test invalid piece count
    message = {
        "action": "play",
        "data": {
            "player_name": "Charlie",
            "pieces": [1, 2, 3, 4, 5, 6, 7]  # Too many
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "error"
    assert "between 1 and 6" in response["data"]["message"]
    print("   ✅ Validation error for too many pieces")
    
    # Test empty pieces
    message = {
        "action": "play",
        "data": {
            "player_name": "Charlie",
            "pieces": []
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "error"
    print("   ✅ Validation error for empty pieces")


async def test_redeal_flow():
    """Test redeal request/accept/decline flow"""
    print("\n4️⃣ Testing redeal flow...")
    
    ws = MockWebSocket()
    
    # Test request_redeal
    message = {
        "action": "request_redeal",
        "data": {"player_name": "Dave"}
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "redeal_requested"
    assert response["data"]["requesting_player"] == "Dave"
    assert response["data"]["reason"] == "weak_hand"
    print("   ✅ Redeal request works")
    
    # Test accept_redeal
    message = {
        "action": "accept_redeal",
        "data": {"player_name": "Eve"}
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "redeal_vote_cast"
    assert response["data"]["player_name"] == "Eve"
    assert response["data"]["vote"] == "accept"
    print("   ✅ Accept redeal works")
    
    # Test decline_redeal
    message = {
        "action": "decline_redeal",
        "data": {"player_name": "Frank"}
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "redeal_declined"
    assert response["data"]["declining_player"] == "Frank"
    assert response["data"]["redeal_cancelled"] is True
    print("   ✅ Decline redeal works")
    
    # Test redeal_decision with accept
    message = {
        "action": "redeal_decision",
        "data": {
            "player_name": "Grace",
            "decision": "accept"
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "redeal_vote_cast"
    assert response["data"]["vote"] == "accept"
    print("   ✅ Redeal decision (accept) works")
    
    # Test redeal_decision with decline
    message = {
        "action": "redeal_decision",
        "data": {
            "player_name": "Henry",
            "decision": "decline"
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "redeal_declined"
    print("   ✅ Redeal decision (decline) works")


async def test_player_ready():
    """Test player_ready adapter"""
    print("\n5️⃣ Testing player_ready adapter...")
    
    ws = MockWebSocket()
    
    # Test setting ready
    message = {
        "action": "player_ready",
        "data": {
            "player_name": "Ivy",
            "ready": True
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "player_ready_status"
    assert response["data"]["player_name"] == "Ivy"
    assert response["data"]["ready"] is True
    print("   ✅ Player ready (true) works")
    
    # Test setting not ready
    message = {
        "action": "player_ready",
        "data": {
            "player_name": "Ivy",
            "ready": False
        }
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["data"]["ready"] is False
    print("   ✅ Player ready (false) works")
    
    # Test default ready status
    message = {
        "action": "player_ready",
        "data": {"player_name": "Jack"}
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["data"]["ready"] is True  # Default
    print("   ✅ Player ready default (true) works")


async def test_leave_game():
    """Test leave_game adapter"""
    print("\n6️⃣ Testing leave_game adapter...")
    
    ws = MockWebSocket()
    
    message = {
        "action": "leave_game",
        "data": {"player_name": "Kate"}
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "player_left_game"
    assert response["data"]["player_name"] == "Kate"
    assert "game_continues" in response["data"]
    assert "replacement" in response["data"]
    print("   ✅ Leave game works")


async def test_passthrough():
    """Test that non-game messages pass through to legacy"""
    print("\n7️⃣ Testing passthrough for non-game messages...")
    
    ws = MockWebSocket()
    
    # Test non-game action
    message = {
        "action": "ping",
        "data": {"timestamp": 123456}
    }
    
    response = await handle_game_messages(ws, message, mock_legacy_handler)
    
    assert response["event"] == "legacy_response"
    assert response["data"]["handled_by"] == "legacy"
    print("   ✅ Non-game messages pass through to legacy")


async def test_game_adapter_integration():
    """Test GameAdapterIntegration class"""
    print("\n8️⃣ Testing GameAdapterIntegration...")
    
    ws = MockWebSocket()
    integration = GameAdapterIntegration(mock_legacy_handler)
    
    # Test enabled state
    message = {
        "action": "start_game",
        "data": {"player_name": "Leo"}
    }
    
    response = await integration.handle_message(ws, message)
    assert response["event"] == "game_started"
    print("   ✅ Integration handles game messages when enabled")
    
    # Test disabled state
    integration.disable()
    response = await integration.handle_message(ws, message)
    assert response["event"] == "legacy_response"
    print("   ✅ Integration passes to legacy when disabled")
    
    # Re-enable
    integration.enable()
    response = await integration.handle_message(ws, message)
    assert response["event"] == "game_started"
    print("   ✅ Integration can be re-enabled")


async def run_all_tests():
    """Run all game adapter tests"""
    print("\n🧪 Game Adapter Tests")
    print("=" * 50)
    
    tests = [
        test_start_game,
        test_declare,
        test_play,
        test_redeal_flow,
        test_player_ready,
        test_leave_game,
        test_passthrough,
        test_game_adapter_integration
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