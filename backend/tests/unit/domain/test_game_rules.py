# tests/unit/domain/test_game_rules.py
"""
Unit tests for game rules service.
"""

import pytest

from domain.services.game_rules import GameRules
from domain.entities.piece import Piece
from domain.value_objects.play_result import PlayResult


class TestGameRules:
    """Test GameRules service."""
    
    def test_is_valid_play_single_piece(self):
        """Test valid single piece play."""
        pieces = [Piece(5, 5)]
        
        # First play is always valid
        assert GameRules.is_valid_play(pieces, None, None)
        
        # Must match count
        assert GameRules.is_valid_play(pieces, 1, None)
        assert not GameRules.is_valid_play(pieces, 2, None)
    
    def test_is_valid_play_multiple_pieces(self):
        """Test valid multiple piece play."""
        # Valid set (same face value)
        pieces = [Piece(3, 3), Piece(3, 3)]
        assert GameRules.is_valid_play(pieces, 2, None)
        
        # Invalid set (different face values)
        pieces = [Piece(3, 3), Piece(4, 4)]
        assert not GameRules.is_valid_play(pieces, 2, None)
    
    def test_is_valid_play_must_beat_last(self):
        """Test play must beat last play."""
        current = [Piece(5, 5)]
        last_play = PlayResult(
            player="Player1",
            pieces=[Piece(4, 4)],
            success=True
        )
        
        # Higher value beats
        assert GameRules.is_valid_play(current, 1, last_play)
        
        # Lower value doesn't beat
        current = [Piece(3, 3)]
        assert not GameRules.is_valid_play(current, 1, last_play)
        
        # Same value doesn't beat
        current = [Piece(4, 4)]
        assert not GameRules.is_valid_play(current, 1, last_play)
    
    def test_beats_comparison(self):
        """Test piece comparison logic."""
        # Single pieces
        assert GameRules.beats([Piece(5, 5)], [Piece(4, 4)])
        assert not GameRules.beats([Piece(4, 4)], [Piece(5, 5)])
        assert not GameRules.beats([Piece(4, 4)], [Piece(4, 4)])
        
        # Sets of pieces
        assert GameRules.beats(
            [Piece(5, 5), Piece(5, 5)],
            [Piece(4, 4), Piece(4, 4)]
        )
        
        # Different counts
        assert not GameRules.beats([Piece(10, 10)], [Piece(3, 3), Piece(3, 3)])
    
    def test_get_piece_value(self):
        """Test piece value calculation."""
        # Single piece
        assert GameRules.get_piece_value([Piece(5, 5)]) == 5
        
        # Multiple pieces (same face)
        pieces = [Piece(3, 3), Piece(3, 3)]
        assert GameRules.get_piece_value(pieces) == 3
        
        # Empty list
        assert GameRules.get_piece_value([]) == 0
    
    def test_is_valid_declaration(self):
        """Test declaration validation."""
        # Valid: doesn't sum to 8
        assert GameRules.is_valid_declaration(5)
        assert GameRules.is_valid_declaration(3)
        assert GameRules.is_valid_declaration(0)
        assert GameRules.is_valid_declaration(10)
        
        # Invalid: sums to 8
        assert not GameRules.is_valid_declaration(8)
        
        # Invalid: negative or too high
        assert not GameRules.is_valid_declaration(-1)
        assert not GameRules.is_valid_declaration(16)
    
    def test_calculate_declaration_score(self):
        """Test declaration scoring."""
        # Exact match: 0 points
        assert GameRules.calculate_declaration_score(5, 5) == 0
        
        # Off by 1: -5 points
        assert GameRules.calculate_declaration_score(5, 4) == -5
        assert GameRules.calculate_declaration_score(5, 6) == -5
        
        # Off by 2: -10 points
        assert GameRules.calculate_declaration_score(5, 3) == -10
        assert GameRules.calculate_declaration_score(5, 7) == -10
        
        # Off by 3: -15 points
        assert GameRules.calculate_declaration_score(5, 2) == -15
        
        # Multiplier for 0 or 10
        assert GameRules.calculate_declaration_score(0, 0) == 0  # 0 * 2
        assert GameRules.calculate_declaration_score(10, 10) == 0  # 0 * 2
        assert GameRules.calculate_declaration_score(0, 1) == -10  # -5 * 2
        assert GameRules.calculate_declaration_score(10, 9) == -10  # -5 * 2
    
    def test_is_weak_hand(self):
        """Test weak hand detection."""
        # Weak hand: no piece > 9
        weak_pieces = [
            Piece(3, 3), Piece(5, 5), Piece(7, 7), Piece(9, 9),
            Piece(2, 2), Piece(4, 4), Piece(6, 6), Piece(8, 8)
        ]
        assert GameRules.is_weak_hand(weak_pieces)
        
        # Not weak: has piece > 9
        strong_pieces = [
            Piece(3, 3), Piece(5, 5), Piece(10, 10), Piece(9, 9),
            Piece(2, 2), Piece(4, 4), Piece(6, 6), Piece(8, 8)
        ]
        assert not GameRules.is_weak_hand(strong_pieces)
        
        # Edge case: exactly one 10
        edge_pieces = [
            Piece(1, 1), Piece(2, 2), Piece(3, 3), Piece(4, 4),
            Piece(5, 5), Piece(6, 6), Piece(7, 7), Piece(10, 10)
        ]
        assert not GameRules.is_weak_hand(edge_pieces)
    
    def test_count_piles(self):
        """Test pile counting."""
        pieces = [
            Piece(3, 3), Piece(3, 3), Piece(5, 5), Piece(5, 5),
            Piece(7, 7), Piece(10, 10), Piece(10, 10), Piece(10, 10)
        ]
        
        piles = GameRules.count_piles(pieces)
        
        assert piles == 4  # 3-3, 5-5, 7, 10-10-10
    
    def test_group_pieces_by_face(self):
        """Test piece grouping."""
        pieces = [
            Piece(3, 3), Piece(5, 5), Piece(3, 3), Piece(10, 10),
            Piece(5, 5), Piece(5, 5), Piece(10, 10), Piece(7, 7)
        ]
        
        groups = GameRules.group_pieces_by_face(pieces)
        
        assert len(groups[3]) == 2
        assert len(groups[5]) == 3
        assert len(groups[7]) == 1
        assert len(groups[10]) == 2
        assert 4 not in groups