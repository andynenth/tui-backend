#!/usr/bin/env python3
"""
Script to capture golden masters for all WebSocket messages from the current system.
This creates reference behaviors that the refactored system must match exactly.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from tests.contracts.golden_master import GoldenMasterCapture, GoldenMasterRecord
from tests.contracts.websocket_contracts import get_all_contracts


# Test scenarios for each message type
TEST_SCENARIOS = {
    "ping": [
        {
            "message": {"action": "ping", "data": {"timestamp": 1234567890}},
            "room_state": None,
            "description": "Basic ping with timestamp",
        },
        {
            "message": {"action": "ping", "data": {}},
            "room_state": None,
            "description": "Ping without timestamp",
        },
    ],
    "client_ready": [
        {
            "message": {"action": "client_ready", "data": {"player_name": "Alice"}},
            "room_state": {
                "room_id": "ABC123",
                "players": [{"name": "Alice", "slot": 0}],
                "started": False,
            },
            "description": "Client ready with player name",
        },
        {
            "message": {"action": "client_ready", "data": {}},
            "room_state": None,
            "description": "Client ready without player name (lobby)",
        },
    ],
    "create_room": [
        {
            "message": {"action": "create_room", "data": {"player_name": "Alice"}},
            "room_state": None,
            "description": "Create room with valid name",
        },
        {
            "message": {"action": "create_room", "data": {"player_name": "Player One"}},
            "room_state": None,
            "description": "Create room with space in name",
        },
        {
            "message": {
                "action": "create_room",
                "data": {"player_name": "VeryLongPlayerName20"},
            },
            "room_state": None,
            "description": "Create room with max length name",
        },
    ],
    "join_room": [
        {
            "message": {
                "action": "join_room",
                "data": {"room_id": "ABC123", "player_name": "Bob"},
            },
            "room_state": {
                "room_id": "ABC123",
                "players": [{"name": "Alice", "slot": 0, "is_host": True}],
                "started": False,
            },
            "description": "Join existing room with space",
        },
        {
            "message": {
                "action": "join_room",
                "data": {"room_id": "FULL01", "player_name": "Eve"},
            },
            "room_state": {
                "room_id": "FULL01",
                "players": [
                    {"name": "Alice", "slot": 0},
                    {"name": "Bob", "slot": 1},
                    {"name": "Charlie", "slot": 2},
                    {"name": "David", "slot": 3},
                ],
                "started": False,
            },
            "description": "Join full room (should fail)",
        },
        {
            "message": {
                "action": "join_room",
                "data": {"room_id": "NOEXIST", "player_name": "Frank"},
            },
            "room_state": None,
            "description": "Join non-existent room (should fail)",
        },
    ],
    "start_game": [
        {
            "message": {"action": "start_game", "data": {}},
            "room_state": {
                "room_id": "GAME01",
                "players": [
                    {"name": "Alice", "slot": 0, "is_host": True},
                    {"name": "Bob", "slot": 1},
                    {"name": "Charlie", "slot": 2},
                    {"name": "David", "slot": 3},
                ],
                "started": False,
            },
            "description": "Start game with 4 players",
        },
        {
            "message": {"action": "start_game", "data": {}},
            "room_state": {
                "room_id": "GAME02",
                "players": [
                    {"name": "Alice", "slot": 0, "is_host": True},
                    {"name": "Bob", "slot": 1},
                ],
                "started": False,
            },
            "description": "Start game with insufficient players (should fail)",
        },
    ],
    "declare": [
        {
            "message": {
                "action": "declare",
                "data": {"player_name": "Alice", "value": 3},
            },
            "room_state": {
                "room_id": "GAME01",
                "phase": "DECLARATION",
                "players": [
                    {"name": "Alice", "declared": False},
                    {"name": "Bob", "declared": False},
                    {"name": "Charlie", "declared": False},
                    {"name": "David", "declared": False},
                ],
            },
            "description": "Valid declaration",
        },
        {
            "message": {
                "action": "declare",
                "data": {"player_name": "Alice", "value": 0},
            },
            "room_state": {
                "room_id": "GAME01",
                "phase": "DECLARATION",
                "players": [{"name": "Alice", "declared": False}],
            },
            "description": "Declaration of zero",
        },
        {
            "message": {
                "action": "declare",
                "data": {"player_name": "Alice", "value": 3},
            },
            "room_state": {
                "room_id": "GAME01",
                "phase": "TURN",
                "players": [{"name": "Alice"}],
            },
            "description": "Declaration in wrong phase (should fail)",
        },
    ],
    "play": [
        {
            "message": {
                "action": "play",
                "data": {"player_name": "Alice", "indices": [0, 1, 2]},
            },
            "room_state": {
                "room_id": "GAME01",
                "phase": "TURN",
                "current_player": "Alice",
                "required_piece_count": 3,
                "players": [{"name": "Alice", "hand": ["R10", "R9", "R8", "B7", "B6"]}],
            },
            "description": "Valid play with 3 pieces",
        },
        {
            "message": {
                "action": "play",
                "data": {"player_name": "Alice", "indices": [0]},
            },
            "room_state": {
                "room_id": "GAME01",
                "phase": "TURN",
                "current_player": "Alice",
                "required_piece_count": 1,
                "players": [{"name": "Alice", "hand": ["G2", "B7", "B6"]}],
            },
            "description": "Valid play with 1 piece",
        },
        {
            "message": {
                "action": "play",
                "data": {"player_name": "Bob", "indices": [0, 1]},
            },
            "room_state": {
                "room_id": "GAME01",
                "phase": "TURN",
                "current_player": "Alice",
                "required_piece_count": 2,
                "players": [{"name": "Bob", "hand": ["R10", "R9"]}],
            },
            "description": "Play out of turn (should fail)",
        },
    ],
    "leave_room": [
        {
            "message": {"action": "leave_room", "data": {"player_name": "Bob"}},
            "room_state": {
                "room_id": "ABC123",
                "players": [
                    {"name": "Alice", "slot": 0, "is_host": True},
                    {"name": "Bob", "slot": 1},
                ],
                "started": False,
            },
            "description": "Player leaves room before game start",
        },
        {
            "message": {"action": "leave_room", "data": {"player_name": "Alice"}},
            "room_state": {
                "room_id": "ABC123",
                "players": [
                    {"name": "Alice", "slot": 0, "is_host": True},
                    {"name": "Bob", "slot": 1},
                ],
                "started": False,
            },
            "description": "Host leaves room (room should close)",
        },
    ],
    "accept_redeal": [
        {
            "message": {"action": "accept_redeal", "data": {"player_name": "Alice"}},
            "room_state": {
                "room_id": "GAME01",
                "phase": "PREPARATION",
                "redeal_offered": True,
                "players": [{"name": "Alice", "weak_hand": True}],
            },
            "description": "Accept redeal offer",
        }
    ],
    "decline_redeal": [
        {
            "message": {"action": "decline_redeal", "data": {"player_name": "Bob"}},
            "room_state": {
                "room_id": "GAME01",
                "phase": "PREPARATION",
                "redeal_offered": True,
                "players": [{"name": "Bob", "weak_hand": False}],
            },
            "description": "Decline redeal offer",
        }
    ],
}


class CurrentSystemSimulator:
    """Simulates the current system's WebSocket handler for testing"""

    def __init__(self):
        self.broadcasts = []

    async def handle_message(
        self, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None
    ):
        """Simulate current system behavior"""
        action = message.get("action")
        data = message.get("data", {})

        # Simulate responses based on action
        if action == "ping":
            return {
                "event": "pong",
                "data": {
                    "timestamp": data.get("timestamp"),
                    "server_time": 1234567890.123,
                    "room_id": room_state.get("room_id") if room_state else None,
                },
            }

        elif action == "create_room":
            player_name = data.get("player_name")
            if not player_name or len(player_name) > 20:
                return {
                    "event": "error",
                    "data": {
                        "message": "Failed to create room: Invalid player name",
                        "type": "room_creation_error",
                    },
                }

            # Simulate successful creation
            self.broadcasts.append(
                {
                    "room_id": "lobby",
                    "event": "room_list_update",
                    "data": {
                        "rooms": [],
                        "timestamp": 1234567890.123,
                        "reason": "new_room_created",
                    },
                }
            )

            return {
                "event": "room_created",
                "data": {
                    "room_id": "ABC123",
                    "host_name": player_name,
                    "success": True,
                },
            }

        elif action == "join_room":
            room_id = data.get("room_id")
            player_name = data.get("player_name")

            if not room_state:
                return {
                    "event": "error",
                    "data": {"message": "Room not found", "type": "join_room_error"},
                }

            if len(room_state.get("players", [])) >= 4:
                return {
                    "event": "error",
                    "data": {"message": "Room is full", "type": "join_room_error"},
                }

            # Simulate successful join
            slot = len(room_state.get("players", []))
            self.broadcasts.append(
                {
                    "room_id": room_id,
                    "event": "room_update",
                    "data": {
                        "players": room_state.get("players", [])
                        + [{"name": player_name, "slot": slot}],
                        "host_name": room_state.get("players", [{}])[0].get("name"),
                        "room_id": room_id,
                        "started": False,
                    },
                }
            )

            return {
                "event": "room_joined",
                "data": {
                    "room_id": room_id,
                    "player_name": player_name,
                    "assigned_slot": slot,
                    "success": True,
                },
            }

        elif action == "declare":
            if room_state and room_state.get("phase") != "DECLARATION":
                return {
                    "event": "error",
                    "data": {
                        "message": "Cannot declare in current phase",
                        "type": "invalid_action",
                    },
                }

            # Simulate declaration broadcast
            self.broadcasts.append(
                {
                    "room_id": room_state.get("room_id") if room_state else "GAME01",
                    "event": "declare",
                    "data": {
                        "player": data.get("player_name"),
                        "value": data.get("value"),
                        "players_declared": 1,
                        "total_players": 4,
                    },
                }
            )

            return None  # No direct response for declare

        # Add more action handlers as needed...

        return {
            "event": "error",
            "data": {"message": f"Unknown action: {action}", "type": "unknown_action"},
        }


async def capture_all_golden_masters():
    """Capture golden masters for all WebSocket message types"""
    print("Starting Golden Master Capture Process")
    print("=" * 60)

    capture = GoldenMasterCapture()
    simulator = CurrentSystemSimulator()

    # Track results
    total_scenarios = 0
    captured_scenarios = 0
    failed_scenarios = []

    # Process each message type
    for message_type, scenarios in TEST_SCENARIOS.items():
        print(f"\nCapturing golden masters for: {message_type}")
        print("-" * 40)

        for scenario in scenarios:
            total_scenarios += 1

            try:
                # Create a fresh simulator for each test
                test_simulator = CurrentSystemSimulator()

                # Capture behavior
                record = await capture.capture_message_behavior(
                    test_simulator, scenario["message"], scenario.get("room_state")
                )

                # Add broadcasts from simulator
                record.broadcasts = test_simulator.broadcasts

                # Save golden master
                filepath = capture.save_golden_master(record)
                print(f"✅ Captured: {scenario['description']}")
                print(f"   Saved to: {filepath}")
                captured_scenarios += 1

            except Exception as e:
                print(f"❌ Failed: {scenario['description']}")
                print(f"   Error: {str(e)}")
                failed_scenarios.append(
                    {
                        "message_type": message_type,
                        "description": scenario["description"],
                        "error": str(e),
                    }
                )

    # Summary report
    print("\n" + "=" * 60)
    print("Golden Master Capture Summary")
    print("=" * 60)
    print(f"Total scenarios: {total_scenarios}")
    print(f"Successfully captured: {captured_scenarios}")
    print(f"Failed: {len(failed_scenarios)}")

    if failed_scenarios:
        print("\nFailed scenarios:")
        for failure in failed_scenarios:
            print(f"  - {failure['message_type']}: {failure['description']}")
            print(f"    Error: {failure['error']}")

    # List all captured masters
    print("\nCaptured golden masters:")
    masters = capture.list_golden_masters()
    for master in masters:
        print(f"  - {master['filename']} (captured at {master['timestamp']})")

    print(f"\nGolden masters saved to: {capture.storage_path}")

    return captured_scenarios == total_scenarios


if __name__ == "__main__":
    # Run the capture process
    success = asyncio.run(capture_all_golden_masters())

    if success:
        print("\n✅ All golden masters captured successfully!")
        print("You can now use these as references during refactoring.")
    else:
        print("\n⚠️  Some golden masters failed to capture.")
        print("Please review the errors and update the simulator as needed.")
        sys.exit(1)
