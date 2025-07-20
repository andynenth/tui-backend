# backend/tests/test_bot_replacement.py

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime
from api.websocket.connection_manager import connection_manager, ConnectionStatus
from api.websocket.message_queue import message_queue_manager


@pytest.mark.asyncio
async def test_connection_manager_basic():
    """Test basic connection manager functionality"""
    # Clear any existing state
    connection_manager._connections.clear()
    connection_manager._player_lookup.clear()
    
    # Register a player
    room_id = "test_room"
    player_name = "TestPlayer"
    ws_id = "ws_123"
    
    await connection_manager.register_player(room_id, player_name, ws_id)
    
    # Check player is registered
    assert await connection_manager.is_player_connected(room_id, player_name)
    
    # Handle disconnect
    connection = await connection_manager.handle_disconnect(ws_id)
    assert connection is not None
    assert connection.player_name == player_name
    assert connection.status == ConnectionStatus.DISCONNECTED
    
    # Check player is disconnected
    assert not await connection_manager.is_player_connected(room_id, player_name)
    
    # Check reconnection detection
    assert await connection_manager.check_reconnection(room_id, player_name)


@pytest.mark.asyncio
async def test_message_queue_basic():
    """Test basic message queue functionality"""
    # Clear any existing state
    message_queue_manager._queues.clear()
    
    room_id = "test_room"
    player_name = "TestPlayer"
    
    # Queue some messages
    queued1 = await message_queue_manager.queue_message(
        room_id, player_name, "phase_change", {"phase": "declaration"}
    )
    assert queued1 is True
    
    queued2 = await message_queue_manager.queue_message(
        room_id, player_name, "turn_resolved", {"winner": "Player2"}
    )
    assert queued2 is True
    
    # Non-critical event should not be queued
    queued3 = await message_queue_manager.queue_message(
        room_id, player_name, "ping", {}
    )
    assert queued3 is False
    
    # Get queued messages
    messages = await message_queue_manager.get_queued_messages(room_id, player_name)
    assert len(messages) == 2
    assert messages[0]["event"] == "phase_change"
    assert messages[1]["event"] == "turn_resolved"
    
    # Queue should be empty after retrieval
    messages2 = await message_queue_manager.get_queued_messages(room_id, player_name)
    assert len(messages2) == 0


@pytest.mark.asyncio
async def test_host_migration():
    """Test host migration functionality"""
    from engine.room import Room
    from engine.player import Player
    
    room = Room("test_room", "Host")
    
    # Set up players
    room.players[0] = Player("Host", is_bot=False)
    room.players[0].is_connected = False  # Host disconnected
    room.players[1] = Player("Player2", is_bot=False)
    room.players[1].is_connected = True
    room.players[2] = Player("Bot3", is_bot=True)
    room.players[3] = Player("Bot4", is_bot=True)
    
    # Migrate host
    new_host = room.migrate_host()
    assert new_host == "Player2"  # Should migrate to connected human
    assert room.host_name == "Player2"
    
    # Test migration when no humans are connected
    room.players[1].is_connected = False
    new_host2 = room.migrate_host()
    assert new_host2 in ["Host", "Player2"]  # Should still prefer a human even if disconnected
    
    # Test migration to bot when no humans
    room.players[0].is_bot = True
    room.players[1].is_bot = True
    new_host3 = room.migrate_host()
    assert new_host3 in ["Host", "Player2", "Bot3", "Bot4"]  # Any bot


@pytest.mark.asyncio
async def test_player_connection_tracking():
    """Test player connection tracking fields"""
    from engine.player import Player
    
    player = Player("TestPlayer", is_bot=False)
    
    # Check initial state
    assert player.is_connected is True
    assert player.disconnect_time is None
    assert player.original_is_bot is False
    
    # Simulate disconnect
    player.is_connected = False
    player.disconnect_time = datetime.now()
    player.is_bot = True  # Bot takes over
    
    assert player.is_bot is True
    assert player.is_connected is False
    assert player.disconnect_time is not None
    assert player.original_is_bot is False  # Original state preserved


if __name__ == "__main__":
    asyncio.run(test_connection_manager_basic())
    asyncio.run(test_message_queue_basic())
    asyncio.run(test_host_migration())
    asyncio.run(test_player_connection_tracking())
    print("All tests passed!")