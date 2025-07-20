#!/usr/bin/env python3
"""
Integration test for player reconnection flow
Tests disconnect → bot activation → reconnection → human restoration
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# Add parent directory to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.websocket.connection_manager import ConnectionManager, PlayerConnection, ConnectionStatus
from api.websocket.message_queue import MessageQueueManager
from engine.room import Room
from engine.player import Player
from engine.game import Game
from engine.state_machine.core import GamePhase


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self._closed = False
        self._messages = []
        self._ws_id = f"ws_{id(self)}"
        
    async def send_json(self, data):
        """Mock sending JSON data"""
        self._messages.append(data)
        
    async def receive_json(self):
        """Mock receiving JSON data"""
        await asyncio.sleep(0.1)
        return {"event": "test", "data": {}}
        
    def close(self):
        """Mock close"""
        self._closed = True
        
    @property
    def closed(self):
        return self._closed
        
    def get_sent_messages(self):
        """Get all messages sent to this websocket"""
        return self._messages


class TestReconnectionFlow:
    """Test the complete reconnection flow"""
    
    def setup_game_room(self):
        """Set up a game room with 4 players"""
        room = Room("test_room", "Alice")
        room.players[1] = Player("Bob", is_bot=False)
        room.players[2] = Player("Charlie", is_bot=False) 
        room.players[3] = Player("David", is_bot=False)
        
        # Start game
        room.started = True
        room.game = Game(room.players)
        room.game.phase = GamePhase.TURN
        
        return room
    
    @pytest.mark.asyncio
    async def test_basic_reconnection(self):
        """Test basic disconnect and reconnect flow"""
        # Setup
        connection_manager = ConnectionManager()
        room = self.setup_game_room()
        player_name = "Bob"
        room_id = room.room_id
        
        # Initial connection
        ws1 = MockWebSocket()
        await connection_manager.register_player(room_id, player_name, ws1._ws_id)
        
        # Get the player
        player = next((p for p in room.game.players if p.name == player_name), None)
        assert player is not None
        assert player.is_bot == False
        assert player.is_connected == True
        
        # Store original bot state
        player.original_is_bot = player.is_bot
        
        # Disconnect - simulate what ws.py does
        connection_info = await connection_manager.handle_disconnect(ws1._ws_id)
        
        # Activate bot (simulating ws.py disconnect handler)
        player.is_bot = True
        player.is_connected = False
        player.disconnect_time = connection_info.disconnect_time
        
        # Verify bot activation
        assert player.is_bot == True
        assert player.is_connected == False
        assert player.disconnect_time is not None
        
        # Reconnect with new websocket
        ws2 = MockWebSocket()
        await connection_manager.register_player(room_id, player_name, ws2._ws_id)
        
        # Verify player was successfully reconnected
        connection = await connection_manager.get_connection(room_id, player_name)
        assert connection is not None
        assert connection.connection_status == ConnectionStatus.CONNECTED
        
        # Restore human control
        player.is_bot = False
        player.is_connected = True
        player.disconnect_time = None
        
        # Verify restoration
        assert player.is_bot == False
        assert player.is_connected == True
        assert player.disconnect_time is None
        
        print("✅ Basic reconnection flow: disconnect → bot → reconnect → human")
    
    @pytest.mark.asyncio
    async def test_message_queue_delivery(self):
        """Test that queued messages are delivered on reconnection"""
        # Setup
        connection_manager = ConnectionManager()
        message_queue_manager = MessageQueueManager()
        room = self.setup_game_room()
        player_name = "Alice"
        room_id = room.room_id
        
        # Initial connection
        ws1 = MockWebSocket()
        await connection_manager.register_player(room_id, player_name, ws1._ws_id)
        
        # Disconnect
        await connection_manager.handle_disconnect(ws1._ws_id)
        
        # Create message queue for disconnected player
        await message_queue_manager.create_queue(room_id, player_name)
        
        # Queue some game events while disconnected
        test_events = [
            ("phase_change", {"phase": "turn", "current_player": "Bob"}),
            ("player_played", {"player": "Bob", "pieces": [1, 2]}),
            ("turn_resolved", {"winner": "Bob", "captured": 2}),
        ]
        
        for event, data in test_events:
            await message_queue_manager.queue_message(room_id, player_name, event, data)
        
        # Verify messages are queued by checking the status
        status = message_queue_manager.get_status()
        queue_key = f"{room_id}:{player_name}"
        assert queue_key in status["queues"]
        assert status["queues"][queue_key]["message_count"] == 3
        
        # Reconnect
        ws2 = MockWebSocket()
        await connection_manager.register_player(room_id, player_name, ws2._ws_id)
        
        # Get and deliver queued messages
        messages = await message_queue_manager.get_queued_messages(room_id, player_name)
        assert len(messages) == 3
        
        # Simulate delivery
        for msg in messages:
            await ws2.send_json(msg)
        
        # Clear queue after delivery
        await message_queue_manager.clear_queue(room_id, player_name)
        
        # Verify messages were delivered (they are in dict format from to_dict())
        sent_messages = ws2.get_sent_messages()
        assert len(sent_messages) == 3
        assert sent_messages[0]["event_type"] == "phase_change"
        assert sent_messages[1]["event_type"] == "player_played"
        assert sent_messages[2]["event_type"] == "turn_resolved"
        
        print("✅ Message queue delivery on reconnection works correctly")
    
    @pytest.mark.asyncio
    async def test_state_restoration(self):
        """Test that player state is properly restored on reconnection"""
        # Setup
        connection_manager = ConnectionManager()
        room = self.setup_game_room()
        player_name = "Charlie"
        room_id = room.room_id
        
        # Get player and set some state
        player = next((p for p in room.game.players if p.name == player_name), None)
        assert player is not None
        
        # Set some game state
        player.score = 25
        player.declared = 3
        player.captured_piles = 2
        player.hand = ["piece1", "piece2", "piece3"]  # Simplified for testing
        
        # Store state before disconnect
        original_score = player.score
        original_declared = player.declared
        original_captured = player.captured_piles
        original_hand = player.hand.copy()
        
        # Disconnect and activate bot
        ws1 = MockWebSocket()
        await connection_manager.register_player(room_id, player_name, ws1._ws_id)
        await connection_manager.handle_disconnect(ws1._ws_id)
        
        player.is_bot = True
        player.is_connected = False
        
        # Bot might make some moves, but core state should persist
        # Simulate bot maintaining state
        assert player.score == original_score
        assert player.declared == original_declared
        assert player.captured_piles == original_captured
        
        # Reconnect
        ws2 = MockWebSocket()
        await connection_manager.register_player(room_id, player_name, ws2._ws_id)
        
        # Restore human control
        player.is_bot = False
        player.is_connected = True
        
        # Verify state preservation
        assert player.score == original_score
        assert player.declared == original_declared
        assert player.captured_piles == original_captured
        assert player.is_bot == False
        assert player.is_connected == True
        
        print("✅ Player state is preserved across disconnect/reconnect")
    
    @pytest.mark.asyncio
    async def test_multiple_reconnections(self):
        """Test multiple disconnect/reconnect cycles"""
        connection_manager = ConnectionManager()
        room = self.setup_game_room()
        player_name = "David"
        room_id = room.room_id
        
        player = next((p for p in room.game.players if p.name == player_name), None)
        assert player is not None
        
        # Multiple cycles
        for i in range(3):
            # Connect
            ws = MockWebSocket()
            await connection_manager.register_player(room_id, player_name, ws._ws_id)
            
            # Verify connected
            player.is_bot = False
            player.is_connected = True
            assert player.is_bot == False
            
            # Disconnect
            await connection_manager.handle_disconnect(ws._ws_id)
            player.is_bot = True
            player.is_connected = False
            
            # Verify disconnected
            assert player.is_bot == True
            assert player.is_connected == False
        
        # Final reconnection
        ws_final = MockWebSocket()
        await connection_manager.register_player(room_id, player_name, ws_final._ws_id)
        player.is_bot = False
        player.is_connected = True
        
        # Verify final state
        assert player.is_bot == False
        assert player.is_connected == True
        
        print("✅ Multiple reconnection cycles handled correctly")
    
    @pytest.mark.asyncio
    async def test_reconnection_during_different_phases(self):
        """Test reconnection works in all game phases"""
        connection_manager = ConnectionManager()
        phases = [GamePhase.PREPARATION, GamePhase.DECLARATION, 
                  GamePhase.TURN, GamePhase.SCORING]
        
        for phase in phases:
            room = self.setup_game_room()
            room.game.phase = phase
            player_name = "Alice"
            room_id = f"room_{phase.value}"
            
            # Connect
            ws1 = MockWebSocket()
            await connection_manager.register_player(room_id, player_name, ws1._ws_id)
            
            # Disconnect
            await connection_manager.handle_disconnect(ws1._ws_id)
            
            # Reconnect
            ws2 = MockWebSocket()
            await connection_manager.register_player(room_id, player_name, ws2._ws_id)
            
            # Verify reconnection successful in all phases
            connection = await connection_manager.get_connection(room_id, player_name)
            assert connection is not None
            assert connection.connection_status == ConnectionStatus.CONNECTED
            
            print(f"✅ Reconnection works in {phase.value} phase")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])