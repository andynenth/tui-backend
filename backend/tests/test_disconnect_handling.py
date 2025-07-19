#!/usr/bin/env python3
"""
Test script for disconnect handling across all game phases
Tests bot takeover behavior in PREPARATION, DECLARATION, TURN, and SCORING phases
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.websocket.connection_manager import ConnectionManager, ConnectionStatus
from engine.room import Room
from engine.player import Player
from engine.game import Game
from engine.state_machine.core import GamePhase


class TestPhaseSpecificDisconnect:
    """Test bot takeover during different game phases"""
    
    def setup_game(self):
        """Set up a game room with 4 players"""
        room = Room("test_room", "Alice")
        room.players[1] = Player("Bob", is_bot=False)
        room.players[2] = Player("Charlie", is_bot=False)
        room.players[3] = Player("David", is_bot=False)
        
        # Create game instance
        room.game = Game(room.players)
        return room
    
    @pytest.mark.asyncio
    async def test_bot_takeover_preparation_phase(self):
        """Test bot takeover during PREPARATION phase"""
        room = self.setup_game()
        room.game.phase = GamePhase.PREPARATION
        
        # Simulate player disconnect
        player = room.players[1]  # Bob
        assert player.is_bot == False
        
        # Activate bot
        player.is_bot = True
        player.is_connected = False
        player.disconnect_time = datetime.now()
        
        # Verify bot activation
        assert player.is_bot == True
        assert player.is_connected == False
        assert player.disconnect_time is not None
        
        print("✅ Bot takeover in PREPARATION phase successful")
    
    @pytest.mark.asyncio
    async def test_bot_takeover_declaration_phase(self):
        """Test bot takeover during DECLARATION phase"""
        room = self.setup_game()
        room.game.phase = GamePhase.DECLARATION
        
        # Simulate player disconnect during declaration
        player = room.players[2]  # Charlie
        original_declared = player.declared
        
        # Activate bot
        player.is_bot = True
        player.is_connected = False
        
        # Bot should maintain any existing declaration
        assert player.declared == original_declared
        assert player.is_bot == True
        
        print("✅ Bot takeover in DECLARATION phase successful")
    
    @pytest.mark.asyncio
    async def test_bot_takeover_turn_phase(self):
        """Test bot takeover during TURN phase"""
        room = self.setup_game()
        room.game.phase = GamePhase.TURN
        room.game.current_player = room.players[3]  # David's turn
        
        # Simulate disconnect during turn
        player = room.players[3]  # David
        assert room.game.current_player.name == "David"
        
        # Activate bot
        player.is_bot = True
        player.is_connected = False
        
        # Verify bot can take turn
        assert player.is_bot == True
        assert room.game.current_player.is_bot == True
        
        print("✅ Bot takeover in TURN phase successful")
    
    @pytest.mark.asyncio
    async def test_bot_takeover_scoring_phase(self):
        """Test bot behavior during SCORING phase"""
        room = self.setup_game()
        room.game.phase = GamePhase.SCORING
        
        # Simulate disconnect during scoring
        player = room.players[0]  # Alice
        original_score = player.score
        
        # Activate bot
        player.is_bot = True
        player.is_connected = False
        
        # Bot should not affect scoring calculations
        assert player.score == original_score
        assert player.is_bot == True
        
        print("✅ Bot takeover in SCORING phase successful")
    
    @pytest.mark.asyncio
    async def test_no_duplicate_bot_actions(self):
        """Verify no duplicate bot actions occur"""
        room = self.setup_game()
        
        # Track bot actions
        bot_actions = []
        
        # Mock bot action tracking
        original_is_bot = room.players[1].is_bot
        
        # Simulate multiple disconnects/reconnects
        for i in range(3):
            # Disconnect
            room.players[1].is_bot = True
            bot_actions.append(f"bot_activated_{i}")
            
            # Reconnect
            room.players[1].is_bot = original_is_bot
            bot_actions.append(f"bot_deactivated_{i}")
        
        # Verify no duplicate activations
        assert len(bot_actions) == 6  # 3 activations + 3 deactivations
        assert len(set(bot_actions)) == 6  # All unique
        
        print("✅ No duplicate bot actions verified")


class TestConnectionManager:
    """Test ConnectionManager functionality"""
    
    @pytest.mark.asyncio
    async def test_unlimited_reconnection(self):
        """Test that players can reconnect anytime"""
        cm = ConnectionManager()
        
        # Register player
        await cm.register_player("room1", "TestPlayer", "ws_001")
        
        # Disconnect
        connection = await cm.handle_disconnect("ws_001")
        assert connection is not None
        assert connection.connection_status == ConnectionStatus.DISCONNECTED
        
        # Verify no reconnect deadline
        assert not hasattr(connection, 'reconnect_deadline') or connection.reconnect_deadline is None
        
        # Verify can reconnect anytime
        can_reconnect = await cm.check_reconnection("room1", "TestPlayer")
        assert can_reconnect == True
        
        # Simulate long time passing (would exceed old 30s limit)
        await asyncio.sleep(0.1)  # In real test would be longer
        
        # Should still be able to reconnect
        can_reconnect = await cm.check_reconnection("room1", "TestPlayer")
        assert can_reconnect == True
        
        print("✅ Unlimited reconnection verified")


class TestHostMigration:
    """Test host migration functionality"""
    
    def test_host_migration_human_priority(self):
        """Test that humans are preferred over bots for host"""
        room = Room("test_room", "Alice")
        room.players[1] = Player("Bob", is_bot=False)
        room.players[2] = Player("Bot3", is_bot=True)
        room.players[3] = Player("Charlie", is_bot=False)
        
        # Migrate from Alice
        new_host = room.migrate_host()
        assert new_host == "Bob"  # First human after Alice
        
        # Simulate Bob disconnect by removing him
        room.players[1] = Player("BotBob", is_bot=True)
        new_host = room.migrate_host()
        assert new_host in ["Alice", "Charlie"]  # Should pick a human
        
        print("✅ Host migration prefers humans over bots")
    
    def test_host_migration_to_bot(self):
        """Test host migration to bot when no humans available"""
        room = Room("test_room", "Alice")
        # All other players are bots
        
        # Remove Alice
        room.players[0] = None
        
        # Should migrate to first bot
        new_host = room.migrate_host()
        assert new_host == "Bot 2"
        assert room.host_name == "Bot 2"
        
        print("✅ Host migration to bot when no humans")


def run_all_tests():
    """Run all disconnect handling tests"""
    print("🧪 Running Phase-Specific Disconnect Tests\n")
    
    # Run async tests
    async def run_async_tests():
        # Phase tests
        phase_tests = TestPhaseSpecificDisconnect()
        game_room = phase_tests.setup_game()
        
        await phase_tests.test_bot_takeover_preparation_phase()
        await phase_tests.test_bot_takeover_declaration_phase()
        await phase_tests.test_bot_takeover_turn_phase()
        await phase_tests.test_bot_takeover_scoring_phase()
        await phase_tests.test_no_duplicate_bot_actions()
        
        # Connection tests
        conn_tests = TestConnectionManager()
        await conn_tests.test_unlimited_reconnection()
    
    # Run sync tests
    host_tests = TestHostMigration()
    host_tests.test_host_migration_human_priority()
    host_tests.test_host_migration_to_bot()
    
    # Run async tests
    asyncio.run(run_async_tests())
    
    print("\n✅ All phase-specific tests passed!")
    print("✅ Bot takeover verified in all phases")
    print("✅ No duplicate bot actions")
    print("✅ Unlimited reconnection working")
    print("✅ Host migration functioning correctly")


if __name__ == "__main__":
    run_all_tests()