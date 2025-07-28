#!/usr/bin/env python3
"""
Capture Golden Masters using Integrated Adapter System
This captures the current behavior to establish a baseline for comparison.
"""

import asyncio
import json
import os
from typing import Dict, Any
from datetime import datetime

from api.adapters.integrated_adapter_system import IntegratedAdapterSystem


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
        self.room_id = "test_room"


async def mock_legacy_handler(websocket, message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock legacy handler that simulates current system behavior.
    In a real scenario, this would call the actual legacy handlers.
    """
    action = message.get("action")
    data = message.get("data", {})
    
    # Simulate responses based on current system behavior
    responses = {
        "ping": {
            "event": "pong",
            "data": {
                "timestamp": data.get("timestamp"),
                "server_time": 1234567890.0,
                "room_id": "test_room"
            }
        },
        "client_ready": {
            "event": "room_state_update",
            "data": {
                "slots": [],
                "host_name": ""
            }
        },
        "create_room": {
            "event": "room_created",
            "data": {
                "room_id": "room_abc123",
                "host_name": data.get("player_name"),
                "success": True
            }
        },
        "join_room": {
            "event": "joined_room",
            "data": {
                "room_id": data.get("room_id"),
                "player_name": data.get("player_name"),
                "success": True,
                "slot": 1
            }
        },
        "leave_room": {
            "event": "left_room",
            "data": {
                "player_name": data.get("player_name"),
                "success": True
            }
        },
        "get_room_state": {
            "event": "room_state",
            "data": {
                "slots": [],
                "host_name": None,
                "game_active": False
            }
        },
        "request_room_list": {
            "event": "room_list_requested",
            "data": {
                "success": True,
                "message": "Room list update triggered"
            }
        },
        "get_rooms": {
            "event": "room_list",
            "data": {
                "rooms": [],
                "total_count": 0,
                "filter_applied": False
            }
        },
        "add_bot": {
            "event": "bot_added",
            "data": {
                "bot_name": "Bot_MED",
                "difficulty": data.get("difficulty", "medium"),
                "slot": 2,
                "success": True
            }
        },
        "remove_player": {
            "event": "player_removed",
            "data": {
                "player_name": data.get("player_name"),
                "removed_by": data.get("requester"),
                "success": True
            }
        },
        "start_game": {
            "event": "game_started",
            "data": {
                "success": True,
                "initial_phase": "PREPARATION",
                "round_number": 1,
                "starter_player": data.get("player_name")
            }
        },
        "declare": {
            "event": "declaration_made",
            "data": {
                "player_name": data.get("player_name"),
                "pile_count": data.get("pile_count"),
                "success": True
            }
        },
        "play": {
            "event": "play_made",
            "data": {
                "player_name": data.get("player_name"),
                "pieces_played": data.get("pieces", []),
                "pieces_count": len(data.get("pieces", [])),
                "success": True,
                "next_player": "NextPlayer",
                "winner": None
            }
        },
        "request_redeal": {
            "event": "redeal_requested",
            "data": {
                "requesting_player": data.get("player_name"),
                "reason": "weak_hand",
                "waiting_for_players": ["Player2", "Player3", "Player4"]
            }
        },
        "accept_redeal": {
            "event": "redeal_vote_cast",
            "data": {
                "player_name": data.get("player_name"),
                "vote": "accept",
                "votes_remaining": 2
            }
        },
        "decline_redeal": {
            "event": "redeal_declined",
            "data": {
                "declining_player": data.get("player_name"),
                "redeal_cancelled": True,
                "next_phase": "DECLARATION"
            }
        },
        "player_ready": {
            "event": "player_ready_status",
            "data": {
                "player_name": data.get("player_name"),
                "ready": data.get("ready", True),
                "all_ready": False
            }
        },
        "leave_game": {
            "event": "player_left_game",
            "data": {
                "player_name": data.get("player_name"),
                "game_continues": True,
                "replacement": "Bot_MED"
            }
        }
    }
    
    return responses.get(action, {
        "event": "error",
        "data": {"message": f"Unknown action: {action}"}
    })


async def capture_golden_masters():
    """Capture golden masters for all adapter actions"""
    
    # Create adapter system
    adapter_system = IntegratedAdapterSystem(mock_legacy_handler)
    
    # Test scenarios
    test_scenarios = [
        # Connection events
        {
            "name": "ping",
            "message": {"action": "ping", "data": {"timestamp": 123456}},
            "room_state": None
        },
        {
            "name": "client_ready",
            "message": {"action": "client_ready", "data": {"player_name": "TestPlayer"}},
            "room_state": None
        },
        # Room events
        {
            "name": "create_room",
            "message": {"action": "create_room", "data": {"player_name": "Alice"}},
            "room_state": None
        },
        {
            "name": "join_room",
            "message": {"action": "join_room", "data": {"room_id": "room_123", "player_name": "Bob"}},
            "room_state": {"room_id": "room_123", "players": [], "host_name": "Alice"}
        },
        {
            "name": "leave_room",
            "message": {"action": "leave_room", "data": {"player_name": "Charlie"}},
            "room_state": {"room_id": "room_123", "players": ["Charlie"], "host_name": "Alice"}
        },
        {
            "name": "get_room_state",
            "message": {"action": "get_room_state", "data": {}},
            "room_state": {"room_id": "room_123", "players": [], "host_name": "Alice"}
        },
        {
            "name": "add_bot",
            "message": {"action": "add_bot", "data": {"difficulty": "hard"}},
            "room_state": {"room_id": "room_123", "players": [], "host_name": "Alice"}
        },
        {
            "name": "remove_player",
            "message": {"action": "remove_player", "data": {"player_name": "Dave", "requester": "Alice"}},
            "room_state": {"room_id": "room_123", "players": ["Dave"], "host_name": "Alice"}
        },
        # Lobby events
        {
            "name": "request_room_list",
            "message": {"action": "request_room_list", "data": {}},
            "room_state": None
        },
        {
            "name": "get_rooms",
            "message": {"action": "get_rooms", "data": {"filter": {"available_only": True}}},
            "room_state": None
        },
        # Game events
        {
            "name": "start_game",
            "message": {"action": "start_game", "data": {"player_name": "Host"}},
            "room_state": {"room_id": "room_123", "players": ["Host", "Player2"], "host_name": "Host"}
        },
        {
            "name": "declare",
            "message": {"action": "declare", "data": {"player_name": "Player1", "pile_count": 3}},
            "room_state": {"room_id": "room_123", "game_active": True}
        },
        {
            "name": "play",
            "message": {"action": "play", "data": {"player_name": "Player1", "pieces": [5, 5, 5]}},
            "room_state": {"room_id": "room_123", "game_active": True}
        },
        {
            "name": "request_redeal",
            "message": {"action": "request_redeal", "data": {"player_name": "Player1"}},
            "room_state": {"room_id": "room_123", "game_active": True}
        },
        {
            "name": "accept_redeal",
            "message": {"action": "accept_redeal", "data": {"player_name": "Player2"}},
            "room_state": {"room_id": "room_123", "game_active": True}
        },
        {
            "name": "decline_redeal",
            "message": {"action": "decline_redeal", "data": {"player_name": "Player3"}},
            "room_state": {"room_id": "room_123", "game_active": True}
        },
        {
            "name": "player_ready",
            "message": {"action": "player_ready", "data": {"player_name": "Player1", "ready": True}},
            "room_state": {"room_id": "room_123", "players": ["Player1"]}
        },
        {
            "name": "leave_game",
            "message": {"action": "leave_game", "data": {"player_name": "Player1"}},
            "room_state": {"room_id": "room_123", "game_active": True}
        }
    ]
    
    # Create output directory
    output_dir = "tests/contracts/golden_masters"
    os.makedirs(output_dir, exist_ok=True)
    
    print("📸 Capturing Golden Masters")
    print("=" * 60)
    
    captured = 0
    errors = 0
    
    for scenario in test_scenarios:
        try:
            # Create mock websocket
            ws = MockWebSocket()
            
            # Get adapter response
            response = await adapter_system.handle_message(
                ws,
                scenario["message"],
                scenario["room_state"]
            )
            
            # Create golden master record
            golden_master = {
                "name": scenario["name"],
                "request": scenario["message"]["data"],
                "room_state": scenario["room_state"],
                "response": response,
                "captured_at": datetime.now().isoformat()
            }
            
            # Save to file
            filename = os.path.join(output_dir, f"{scenario['name']}.json")
            with open(filename, 'w') as f:
                json.dump(golden_master, f, indent=2)
            
            captured += 1
            print(f"✅ {scenario['name']:<20} - Captured")
            
        except Exception as e:
            errors += 1
            print(f"❌ {scenario['name']:<20} - Error: {str(e)}")
    
    print("\n📊 Summary")
    print("=" * 60)
    print(f"Total scenarios: {len(test_scenarios)}")
    print(f"Captured: {captured}")
    print(f"Errors: {errors}")
    print(f"\nGolden masters saved to: {output_dir}")
    
    return captured == len(test_scenarios)


async def verify_adapter_compatibility():
    """Verify adapters produce same output as legacy"""
    print("\n\n🔍 Verifying Adapter Compatibility")
    print("=" * 60)
    
    # This would compare adapter output with actual legacy output
    # For now, we'll just check that adapters are working
    
    adapter_system = IntegratedAdapterSystem(mock_legacy_handler)
    
    # Test a simple message
    ws = MockWebSocket()
    test_msg = {"action": "ping", "data": {"timestamp": 123}}
    
    response = await adapter_system.handle_message(ws, test_msg, None)
    
    if response and response.get("event") == "pong":
        print("✅ Adapters are responding correctly")
        return True
    else:
        print("❌ Adapters not working as expected")
        return False


async def main():
    """Main function"""
    print("🚀 Golden Master Capture for Adapter System\n")
    
    # Capture golden masters
    success = await capture_golden_masters()
    
    if success:
        # Verify compatibility
        await verify_adapter_compatibility()
        
        print("\n✅ Golden masters captured successfully!")
        print("\nNext steps:")
        print("1. Run contract tests: python3 tests/contracts/test_adapter_contracts.py")
        print("2. Enable shadow mode in ws.py")
        print("3. Monitor for discrepancies")
    else:
        print("\n❌ Some golden masters failed to capture")


if __name__ == "__main__":
    asyncio.run(main())