#!/usr/bin/env python3
"""
Test script for Task 1.2: Enhanced WebSocket Disconnect Detection

This script tests the enhanced disconnect handling with phase awareness.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from api.websocket.handlers import DisconnectHandler, ReconnectionHandler
from api.websocket.connection_manager import ConnectionManager, ConnectionStatus
from engine.player import Player
from engine.state_machine.core import GamePhase


class MockRoom:
    """Mock room for testing"""
    def __init__(self, phase=GamePhase.PREPARATION):
        self.game_started = True
        self.game = MockGame()
        self.game_state_machine = MockStateMachine(phase)


class MockGame:
    """Mock game for testing"""
    def __init__(self):
        self.players = [
            Player("Alice", is_bot=False),
            Player("Bob", is_bot=False),
            Player("Bot1", is_bot=True),
            Player("Bot2", is_bot=True)
        ]
        self.round_number = 1


class MockStateMachine:
    """Mock state machine for testing"""
    def __init__(self, phase):
        self.phase = phase
        self.phase_data = {
            "weak_hand_votes": {"Alice": None, "Bob": True},
            "declarations": {"Bob": 2},
            "current_player": "Alice"
        }
    
    def get_current_phase(self):
        return self.phase
    
    def get_phase_data(self):
        return self.phase_data
    
    def get_allowed_actions(self):
        return []


async def test_phase_aware_disconnect():
    """Test the enhanced phase-aware disconnect handling"""
    print("=" * 60)
    print("Testing Enhanced Phase-Aware Disconnect Handling")
    print("=" * 60)
    
    # Test 1: Disconnect during PREPARATION phase
    print("\n1. Testing disconnect during PREPARATION phase:")
    room = MockRoom(GamePhase.PREPARATION)
    
    result = await DisconnectHandler.handle_phase_aware_disconnect(
        "room1", "ws_001", room, "Alice"
    )
    
    assert result["success"], "Disconnect handling should succeed"
    print(f"  - Result phase: {result['phase']}")
    assert result["phase"] == "preparation", "Phase should be preparation"
    assert "pending_weak_hand_vote" in result["actions_taken"], "Should detect pending vote"
    assert result["bot_activated"], "Bot should be activated"
    
    print("✓ PREPARATION phase disconnect handled correctly")
    print(f"  - Phase: {result['phase']}")
    print(f"  - Actions: {result['actions_taken']}")
    print(f"  - Bot activated: {result['bot_activated']}")
    
    # Verify player state was updated
    alice = room.game.players[0]
    assert alice.is_bot == True, "Player should be marked as bot"
    assert alice.is_connected == False, "Player should be disconnected"
    assert alice.disconnect_time is not None, "Disconnect time should be set"
    
    # Test 2: Disconnect during DECLARATION phase
    print("\n2. Testing disconnect during DECLARATION phase:")
    room = MockRoom(GamePhase.DECLARATION)
    
    result = await DisconnectHandler.handle_phase_aware_disconnect(
        "room1", "ws_002", room, "Alice"
    )
    
    assert result["success"], "Disconnect handling should succeed"
    assert result["phase"] == "declaration", "Phase should be declaration"
    assert "pending_declaration" in result["actions_taken"], "Should detect pending declaration"
    
    print("✓ DECLARATION phase disconnect handled correctly")
    print(f"  - Phase: {result['phase']}")
    print(f"  - Actions: {result['actions_taken']}")
    
    # Test 3: Disconnect during TURN phase (active turn)
    print("\n3. Testing disconnect during TURN phase (active turn):")
    room = MockRoom(GamePhase.TURN)
    
    result = await DisconnectHandler.handle_phase_aware_disconnect(
        "room1", "ws_003", room, "Alice"
    )
    
    assert result["success"], "Disconnect handling should succeed"
    assert result["phase"] == "turn", "Phase should be turn"
    assert "active_turn_handoff" in result["actions_taken"], "Should detect active turn"
    
    print("✓ TURN phase disconnect (active) handled correctly")
    print(f"  - Phase: {result['phase']}")
    print(f"  - Actions: {result['actions_taken']}")
    
    # Test 4: Disconnect during TURN phase (not active turn)
    print("\n4. Testing disconnect during TURN phase (waiting):")
    
    result = await DisconnectHandler.handle_phase_aware_disconnect(
        "room1", "ws_004", room, "Bob"
    )
    
    assert result["success"], "Disconnect handling should succeed"
    assert "waiting_for_turn" in result["actions_taken"], "Should be waiting for turn"
    
    print("✓ TURN phase disconnect (waiting) handled correctly")
    print(f"  - Actions: {result['actions_taken']}")
    
    # Test 5: Disconnect during SCORING phase
    print("\n5. Testing disconnect during SCORING phase:")
    room = MockRoom(GamePhase.SCORING)
    
    result = await DisconnectHandler.handle_phase_aware_disconnect(
        "room1", "ws_005", room, "Alice"
    )
    
    assert result["success"], "Disconnect handling should succeed"
    assert result["phase"] == "scoring", "Phase should be scoring"
    assert "scoring_phase_passive" in result["actions_taken"], "Should be passive during scoring"
    
    print("✓ SCORING phase disconnect handled correctly")
    print(f"  - Phase: {result['phase']}")
    print(f"  - Actions: {result['actions_taken']}")
    
    # Test 6: Bot player disconnect (should not activate bot)
    print("\n6. Testing bot player disconnect:")
    
    result = await DisconnectHandler.handle_phase_aware_disconnect(
        "room1", "ws_006", room, "Bot1"
    )
    
    assert result["success"], "Disconnect handling should succeed"
    assert not result["bot_activated"], "Bot should not be activated for bot player"
    
    print("✓ Bot player disconnect handled correctly")
    print(f"  - Bot activated: {result['bot_activated']}")
    
    print("\n" + "=" * 60)
    print("All phase-aware disconnect tests passed! ✅")
    print("=" * 60)


async def test_reconnection_handling():
    """Test the enhanced reconnection handling"""
    print("\n" + "=" * 60)
    print("Testing Enhanced Reconnection Handling")
    print("=" * 60)
    
    # Create a mock websocket
    class MockWebSocket:
        async def send_json(self, data):
            print(f"  → Sending to client: {data['event']}")
            if data['event'] == 'full_state_sync':
                print(f"    - Phase: {data['data']['phase']}")
                print(f"    - Round: {data['data']['round']}")
                print(f"    - Players: {len(data['data']['players'])}")
    
    # Setup
    room = MockRoom(GamePhase.TURN)
    alice = room.game.players[0]
    alice.is_bot = True  # Simulating disconnected state
    alice.original_is_bot = False
    alice.is_connected = False
    alice.disconnect_time = datetime.now()
    
    websocket = MockWebSocket()
    
    print("\n1. Testing player reconnection:")
    
    result = await ReconnectionHandler.handle_player_reconnection(
        "room1", "Alice", "ws_new_001", room, websocket
    )
    
    assert result["success"], "Reconnection should succeed"
    assert result["bot_deactivated"], "Bot should be deactivated"
    assert result["state_synced"], "State should be synced"
    assert result["phase"] == "turn", "Phase should be turn"
    
    print("✓ Reconnection handled successfully")
    print(f"  - Bot deactivated: {result['bot_deactivated']}")
    print(f"  - State synced: {result['state_synced']}")
    print(f"  - Phase: {result['phase']}")
    
    # Verify player state restored
    assert alice.is_bot == False, "Player should no longer be bot"
    assert alice.is_connected == True, "Player should be connected"
    assert alice.disconnect_time is None, "Disconnect time should be cleared"
    
    print("\n" + "=" * 60)
    print("All reconnection tests passed! ✅")
    print("=" * 60)


async def test_error_handling():
    """Test error handling in disconnect scenarios"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    # Test 1: Invalid player name
    print("\n1. Testing disconnect with invalid player:")
    room = MockRoom()
    
    result = await DisconnectHandler.handle_phase_aware_disconnect(
        "room1", "ws_err_001", room, "InvalidPlayer"
    )
    
    assert result["success"] == False, "Should fail for invalid player"
    print("✓ Invalid player handled correctly")
    
    # Test 2: No game in room
    print("\n2. Testing disconnect with no game:")
    
    class EmptyRoom:
        game_started = True
        game = None
        game_state_machine = None
    
    empty_room = EmptyRoom()
    
    result = await DisconnectHandler.handle_phase_aware_disconnect(
        "room1", "ws_err_002", empty_room, "Alice"
    )
    
    assert result["phase"] is None, "Should detect no game"
    print("✓ No game scenario handled correctly")
    
    print("\n" + "=" * 60)
    print("All error handling tests passed! ✅")
    print("=" * 60)


if __name__ == "__main__":
    print("Starting Enhanced Disconnect Detection Tests...\n")
    
    # Run all tests
    asyncio.run(test_phase_aware_disconnect())
    asyncio.run(test_reconnection_handling())
    asyncio.run(test_error_handling())
    
    print("\n✅ All enhanced disconnect detection tests completed successfully!")
    print("\n📝 Summary:")
    print("- Phase-aware disconnect handling working correctly")
    print("- Different actions taken based on game phase")
    print("- Bot activation only for human players")
    print("- Full state synchronization on reconnection")
    print("- Proper error handling for edge cases")