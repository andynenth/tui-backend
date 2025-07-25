"""
Tests for the Piece value object.
"""

import pytest
from domain.value_objects.piece import Piece


class TestPiece:
    """Test the Piece value object."""
    
    def test_create_valid_piece(self):
        """Test creating a valid piece."""
        piece = Piece.create("GENERAL_RED")
        assert piece.kind == "GENERAL_RED"
        assert piece.point == 14
        assert piece.name == "GENERAL"
        assert piece.color == "RED"
        assert piece.is_red is True
        assert piece.is_black is False
    
    def test_create_all_pieces(self):
        """Test creating all valid pieces."""
        for kind in Piece.all_kinds():
            piece = Piece.create(kind)
            assert piece.kind == kind
            assert piece.point == Piece.PIECE_POINTS[kind]
    
    def test_invalid_piece_kind(self):
        """Test creating piece with invalid kind."""
        with pytest.raises(ValueError, match="Invalid piece kind"):
            Piece.create("INVALID_PIECE")
    
    def test_invalid_point_value(self):
        """Test creating piece with wrong point value."""
        with pytest.raises(ValueError, match="Invalid point value"):
            Piece(kind="GENERAL_RED", point=999)
    
    def test_piece_immutability(self):
        """Test that pieces are immutable."""
        piece = Piece.create("SOLDIER_BLACK")
        with pytest.raises(AttributeError):
            piece.kind = "GENERAL_RED"
        with pytest.raises(AttributeError):
            piece.point = 100
    
    def test_piece_comparison(self):
        """Test piece comparison methods."""
        general_red = Piece.create("GENERAL_RED")
        general_black = Piece.create("GENERAL_BLACK")
        soldier_red = Piece.create("SOLDIER_RED")
        
        # Test beats method
        assert general_red.beats(general_black) is True
        assert general_black.beats(general_red) is False
        assert general_red.beats(soldier_red) is True
        
        # Test comparison operators
        assert general_red > general_black
        assert general_black < general_red
        assert general_red >= general_black
        assert soldier_red <= general_red
    
    def test_piece_equality(self):
        """Test piece equality (value object semantics)."""
        piece1 = Piece.create("HORSE_RED")
        piece2 = Piece.create("HORSE_RED")
        piece3 = Piece.create("HORSE_BLACK")
        
        # Same attributes = equal (value object)
        assert piece1 == piece2
        assert piece1 != piece3
    
    def test_piece_representation(self):
        """Test string representation."""
        piece = Piece.create("CANNON_BLACK")
        assert repr(piece) == "CANNON_BLACK(3)"
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        piece = Piece.create("ADVISOR_RED")
        data = piece.to_dict()
        
        assert data == {
            "kind": "ADVISOR_RED",
            "point": 12,
            "name": "ADVISOR",
            "color": "RED"
        }
    
    def test_from_dict(self):
        """Test creating piece from dictionary."""
        data = {"kind": "ELEPHANT_BLACK", "point": 9}
        piece = Piece.from_dict(data)
        
        assert piece.kind == "ELEPHANT_BLACK"
        assert piece.point == 9
        assert piece.name == "ELEPHANT"
        assert piece.color == "BLACK"
    
    def test_build_deck(self):
        """Test building a complete deck."""
        deck = Piece.build_deck()
        
        # Should have 32 pieces total
        assert len(deck) == 32
        
        # Count pieces by type
        counts = {}
        for piece in deck:
            counts[piece.name] = counts.get(piece.name, 0) + 1
        
        # Verify counts
        assert counts["GENERAL"] == 2  # 1 red + 1 black
        assert counts["SOLDIER"] == 10  # 5 red + 5 black
        assert counts["ADVISOR"] == 4   # 2 red + 2 black
        assert counts["ELEPHANT"] == 4  # 2 red + 2 black
        assert counts["CHARIOT"] == 4   # 2 red + 2 black
        assert counts["HORSE"] == 4     # 2 red + 2 black
        assert counts["CANNON"] == 4    # 2 red + 2 black
    
    def test_get_point_value(self):
        """Test getting point value for a kind."""
        assert Piece.get_point_value("GENERAL_RED") == 14
        assert Piece.get_point_value("SOLDIER_BLACK") == 1
        
        with pytest.raises(ValueError):
            Piece.get_point_value("INVALID_KIND")