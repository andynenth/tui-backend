# tests/unit/domain/test_player_entity.py
"""
Unit tests for Player entity.
"""

import pytest

from domain.entities.player import Player
from domain.entities.piece import Piece


class TestPlayerEntity:
    """Test Player entity behavior."""
    
    def test_player_initialization(self):
        """Test player initializes with correct defaults."""
        player = Player(name="TestPlayer")
        
        assert player.name == "TestPlayer"
        assert not player.is_bot
        assert player.is_ready
        assert player.pieces == []
        assert player.won_pieces == []
        assert player.declared_piles is None
    
    def test_player_initialization_with_params(self):
        """Test player initialization with custom parameters."""
        player = Player(name="BotPlayer", is_bot=True, is_ready=False)
        
        assert player.name == "BotPlayer"
        assert player.is_bot
        assert not player.is_ready
    
    def test_receive_pieces(self):
        """Test player can receive pieces."""
        player = Player(name="TestPlayer")
        pieces = [Piece(3, 3), Piece(5, 5), Piece(7, 7)]
        
        player.receive_pieces(pieces)
        
        assert len(player.pieces) == 3
        assert all(p in player.pieces for p in pieces)
    
    def test_play_pieces(self):
        """Test player can play pieces."""
        player = Player(name="TestPlayer")
        initial_pieces = [Piece(3, 3), Piece(5, 5), Piece(7, 7)]
        player.receive_pieces(initial_pieces)
        
        # Play valid pieces
        played = player.play_pieces([1])  # Play piece at index 1
        
        assert len(played) == 1
        assert played[0].face == 5
        assert len(player.pieces) == 2
        assert not any(p.face == 5 for p in player.pieces)
    
    def test_play_pieces_invalid_indices(self):
        """Test playing pieces with invalid indices."""
        player = Player(name="TestPlayer")
        player.receive_pieces([Piece(3, 3), Piece(5, 5)])
        
        # Invalid index
        with pytest.raises(ValueError, match="Invalid piece indices"):
            player.play_pieces([5])
        
        # Duplicate indices
        with pytest.raises(ValueError, match="Invalid piece indices"):
            player.play_pieces([0, 0])
    
    def test_add_won_pieces(self):
        """Test player can win pieces."""
        player = Player(name="TestPlayer")
        won = [Piece(10, 10), Piece(11, 11)]
        
        player.add_won_pieces(won)
        
        assert len(player.won_pieces) == 2
        assert all(p in player.won_pieces for p in won)
    
    def test_declare_piles(self):
        """Test player can make declaration."""
        player = Player(name="TestPlayer")
        
        player.declare_piles(5)
        
        assert player.declared_piles == 5
    
    def test_reset_for_round(self):
        """Test player state reset for new round."""
        player = Player(name="TestPlayer")
        
        # Set up some state
        player.receive_pieces([Piece(3, 3), Piece(5, 5)])
        player.add_won_pieces([Piece(10, 10)])
        player.declare_piles(3)
        
        # Reset
        player.reset_for_round()
        
        assert player.pieces == []
        assert player.won_pieces == []
        assert player.declared_piles is None
    
    def test_count_piles(self):
        """Test pile counting."""
        player = Player(name="TestPlayer")
        
        # No pieces
        assert player.count_piles() == 0
        
        # Single pieces
        player.receive_pieces([Piece(3, 3), Piece(5, 5), Piece(7, 7)])
        assert player.count_piles() == 3
        
        # With pairs
        player.receive_pieces([Piece(3, 3)])  # Now has two 3s
        assert player.count_piles() == 3  # 3-3, 5, 7
        
        # With won pieces
        player.add_won_pieces([Piece(10, 10), Piece(10, 10)])
        assert player.count_piles() == 4  # 3-3, 5, 7, 10-10
    
    def test_get_all_pieces(self):
        """Test getting all pieces (hand + won)."""
        player = Player(name="TestPlayer")
        
        hand_pieces = [Piece(3, 3), Piece(5, 5)]
        won_pieces = [Piece(10, 10), Piece(11, 11)]
        
        player.receive_pieces(hand_pieces)
        player.add_won_pieces(won_pieces)
        
        all_pieces = player.get_all_pieces()
        
        assert len(all_pieces) == 4
        assert all(p in all_pieces for p in hand_pieces)
        assert all(p in all_pieces for p in won_pieces)
    
    def test_has_pieces(self):
        """Test checking if player has pieces."""
        player = Player(name="TestPlayer")
        
        assert not player.has_pieces()
        
        player.receive_pieces([Piece(3, 3)])
        assert player.has_pieces()
        
        player.play_pieces([0])
        assert not player.has_pieces()
    
    def test_player_equality(self):
        """Test player equality based on name."""
        player1 = Player(name="Player1")
        player2 = Player(name="Player1", is_bot=True)
        player3 = Player(name="Player2")
        
        assert player1 == player2  # Same name
        assert player1 != player3  # Different name
        assert player1 != "Player1"  # Different type
    
    def test_player_serialization(self):
        """Test player can be serialized to dict."""
        player = Player(name="TestPlayer", is_bot=True)
        player.receive_pieces([Piece(3, 3), Piece(5, 5)])
        player.declare_piles(2)
        
        data = player.to_dict()
        
        assert data["name"] == "TestPlayer"
        assert data["is_bot"] is True
        assert data["is_ready"] is True
        assert data["piece_count"] == 2
        assert data["declared_piles"] == 2
        assert "pieces" not in data  # Should not expose actual pieces