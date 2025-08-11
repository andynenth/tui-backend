# backend/tests/services/test_play_history_player_detection.py
"""
TDD: Tests for player type detection (AI vs human).
"""

import pytest
from backend.services.play_history_service import PlayHistoryService
from backend.engine.game import Game
from backend.engine.player import Player


class TestPlayerDetection:
    """Test player type detection logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = PlayHistoryService()
    
    def test_detect_ai_players(self):
        """Test detection of AI players."""
        # Create game with AI players
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]
        game = Game(players)
        
        player_info = self.service.extract_player_info(game)
        
        assert len(player_info) == 4
        for player_name in ["Bot 1", "Bot 2", "Bot 3", "Bot 4"]:
            assert player_info[player_name].player_type == "ai"
            assert player_info[player_name].player_name == player_name
            assert player_info[player_name].ai_version == "v2"  # Assuming v2 is current
    
    def test_detect_human_players(self):
        """Test detection of human players."""
        # Create game with human players
        players = [
            Player("Alice", is_bot=False),
            Player("Bob", is_bot=False),
            Player("Charlie", is_bot=False),
            Player("David", is_bot=False),
        ]
        game = Game(players)
        
        player_info = self.service.extract_player_info(game)
        
        assert len(player_info) == 4
        for player_name in ["Alice", "Bob", "Charlie", "David"]:
            assert player_info[player_name].player_type == "human"
            assert player_info[player_name].player_name == player_name
            assert player_info[player_name].ai_version is None
    
    def test_mixed_ai_and_human_players(self):
        """Test detection with mixed AI and human players."""
        # Create game with mixed players
        players = [
            Player("Bot 1", is_bot=True),
            Player("Alice", is_bot=False),
            Player("Bot 2", is_bot=True),
            Player("Bob", is_bot=False),
        ]
        game = Game(players)
        
        player_info = self.service.extract_player_info(game)
        
        assert len(player_info) == 4
        
        # Check AI players
        assert player_info["Bot 1"].player_type == "ai"
        assert player_info["Bot 1"].ai_version == "v2"
        assert player_info["Bot 2"].player_type == "ai"
        assert player_info["Bot 2"].ai_version == "v2"
        
        # Check human players
        assert player_info["Alice"].player_type == "human"
        assert player_info["Alice"].ai_version is None
        assert player_info["Bob"].player_type == "human"
        assert player_info["Bob"].ai_version is None
    
    def test_player_id_generation(self):
        """Test that player IDs are generated correctly."""
        players = [
            Player("Bot 1", is_bot=True),
            Player("Alice", is_bot=False),
        ]
        game = Game(players)
        
        player_info = self.service.extract_player_info(game)
        
        # Player IDs should be based on player names (or index if no ID field)
        assert player_info["Bot 1"].player_id == "bot_1"  # Normalized ID
        assert player_info["Alice"].player_id == "alice"  # Normalized ID