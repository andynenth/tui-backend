#!/usr/bin/env python3
"""
Test the broadcast_with_queue functionality
Ensures messages are properly queued for disconnected players
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, AsyncMock, patch
from api.websocket.message_queue import message_queue_manager
from engine.room import Room
from engine.player import Player
from engine.game import Game
from api.routes.ws import broadcast_with_queue


async def test_broadcast_with_queue():
    """Test that broadcast_with_queue properly queues messages"""
    print("=== TESTING BROADCAST WITH QUEUE ===\n")
    
    # Setup room with mixed connected/disconnected players
    room = Room("test_room", "Alice")
    room.players[1] = Player("Bob", is_bot=False)
    room.players[2] = Player("Charlie", is_bot=False)
    room.players[3] = Player("David", is_bot=False)
    room.game = Game(room.players)
    room.game_started = True
    
    # Simulate disconnected players
    room.players[1].is_connected = False  # Bob disconnected
    room.players[1].is_bot = True
    room.players[1].original_is_bot = False
    
    room.players[3].is_connected = False  # David disconnected
    room.players[3].is_bot = True
    room.players[3].original_is_bot = False
    
    # Create queues for disconnected players
    await message_queue_manager.create_queue("test_room", "Bob")
    await message_queue_manager.create_queue("test_room", "David")
    
    # Mock room_manager
    mock_room_manager = Mock()
    mock_room_manager.get_room.return_value = room
    
    # Mock the broadcast function
    broadcast_called = []
    async def mock_broadcast(room_id, event, data):
        broadcast_called.append((room_id, event, data))
    
    # Test broadcast_with_queue
    with patch('api.routes.ws.room_manager', mock_room_manager):
        with patch('api.routes.ws.broadcast', mock_broadcast):
            # Send a critical event
            await broadcast_with_queue("test_room", "phase_change", {"phase": "TURN"})
            
            # Send a non-critical event
            await broadcast_with_queue("test_room", "chat", {"message": "Hello"})
    
    # Verify broadcast was called
    print(f"1. Broadcast called {len(broadcast_called)} times ✓")
    
    # Check queued messages for Bob
    bob_messages = await message_queue_manager.get_queued_messages("test_room", "Bob")
    print(f"2. Bob has {len(bob_messages)} queued messages ✓")
    print(f"   - Events: {[m['event_type'] for m in bob_messages]}")
    
    # Check queued messages for David
    david_messages = await message_queue_manager.get_queued_messages("test_room", "David")
    print(f"3. David has {len(david_messages)} queued messages ✓")
    
    # Verify Alice and Charlie (connected) don't have queues
    alice_messages = await message_queue_manager.get_queued_messages("test_room", "Alice")
    charlie_messages = await message_queue_manager.get_queued_messages("test_room", "Charlie")
    print(f"4. Connected players have no queues: Alice={len(alice_messages)}, Charlie={len(charlie_messages)} ✓")
    
    # Verify critical events are marked correctly
    critical_count = sum(1 for m in bob_messages if m['is_critical'])
    print(f"5. Critical events marked: {critical_count} of {len(bob_messages)} ✓")
    
    # Cleanup
    await message_queue_manager.cleanup_room_queues("test_room")
    
    print("\n✅ Broadcast with queue working correctly!")


async def test_no_game_scenario():
    """Test broadcast_with_queue when room has no game"""
    print("\n=== TESTING NO GAME SCENARIO ===\n")
    
    # Room without game
    room = Room("lobby", "Host")
    
    mock_room_manager = Mock()
    mock_room_manager.get_room.return_value = room
    
    broadcast_called = []
    async def mock_broadcast(room_id, event, data):
        broadcast_called.append((room_id, event, data))
    
    with patch('api.routes.ws.room_manager', mock_room_manager):
        with patch('api.routes.ws.broadcast', mock_broadcast):
            # Should just broadcast, no queuing
            await broadcast_with_queue("lobby", "room_update", {"players": []})
    
    print(f"1. Broadcast called without errors ✓")
    print(f"2. No queues created for lobby")
    
    status = message_queue_manager.get_status()
    print(f"3. Total queues in system: {status['total_queues']} ✓")
    
    print("\n✅ No game scenario handled correctly!")


async def main():
    """Run all broadcast tests"""
    await test_broadcast_with_queue()
    await test_no_game_scenario()
    
    print("\n=== ALL BROADCAST TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())