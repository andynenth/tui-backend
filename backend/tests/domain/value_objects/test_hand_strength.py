"""
Tests for the HandStrength value object.
"""

import pytest
from domain.value_objects.hand_strength import HandStrength, HandComparison
from domain.value_objects.piece import Piece


class TestHandStrength:
    """Test the HandStrength value object."""

    def test_calculate_normal_hand(self):
        """Test calculating strength for a normal hand."""
        pieces = [
            Piece.create("GENERAL_RED"),  # 14 points
            Piece.create("ADVISOR_BLACK"),  # 11 points
            Piece.create("SOLDIER_RED"),  # 2 points
            Piece.create("CANNON_BLACK"),  # 3 points
        ]

        strength = HandStrength.calculate(pieces)

        assert strength.total_points == 30  # 14 + 11 + 2 + 3
        assert strength.highest_piece_value == 14
        assert strength.is_weak is False
        assert strength.piece_count == 4
        assert strength.average_value == 7.5

        # Check pieces are sorted by value
        assert strength.pieces[0].kind == "GENERAL_RED"
        assert strength.pieces[-1].kind == "SOLDIER_RED"

    def test_calculate_weak_hand(self):
        """Test calculating strength for a weak hand."""
        pieces = [
            Piece.create("SOLDIER_RED"),  # 2 points
            Piece.create("CANNON_BLACK"),  # 3 points
            Piece.create("HORSE_RED"),  # 6 points
            Piece.create("CHARIOT_BLACK"),  # 7 points
        ]

        strength = HandStrength.calculate(pieces)

        assert strength.total_points == 18
        assert strength.highest_piece_value == 7
        assert strength.is_weak is True  # No piece > 9 points

    def test_calculate_empty_hand(self):
        """Test calculating strength for empty hand."""
        strength = HandStrength.calculate([])

        assert strength.total_points == 0
        assert strength.highest_piece_value == 0
        assert strength.is_weak is True
        assert strength.piece_count == 0
        assert strength.average_value == 0.0

    def test_piece_distribution(self):
        """Test piece distribution calculation."""
        pieces = [
            Piece.create("SOLDIER_RED"),
            Piece.create("SOLDIER_RED"),
            Piece.create("SOLDIER_BLACK"),
            Piece.create("GENERAL_RED"),
            Piece.create("CANNON_BLACK"),
        ]

        strength = HandStrength.calculate(pieces)

        # Distribution should be sorted by count then name
        distribution = dict(strength.piece_distribution)
        assert distribution["SOLDIER_RED"] == 2
        assert distribution["SOLDIER_BLACK"] == 1
        assert distribution["GENERAL_RED"] == 1
        assert distribution["CANNON_BLACK"] == 1

        # First item should be most common
        assert strength.piece_distribution[0] == ("SOLDIER_RED", 2)

    def test_has_piece(self):
        """Test checking for specific piece."""
        pieces = [Piece.create("GENERAL_RED"), Piece.create("SOLDIER_BLACK")]

        strength = HandStrength.calculate(pieces)

        assert strength.has_piece("GENERAL_RED") is True
        assert strength.has_piece("SOLDIER_BLACK") is True
        assert strength.has_piece("ELEPHANT_RED") is False

    def test_count_piece_type(self):
        """Test counting pieces by type."""
        pieces = [
            Piece.create("SOLDIER_RED"),
            Piece.create("SOLDIER_BLACK"),
            Piece.create("SOLDIER_RED"),
            Piece.create("GENERAL_RED"),
        ]

        strength = HandStrength.calculate(pieces)

        assert strength.count_piece_type("SOLDIER") == 3
        assert strength.count_piece_type("GENERAL") == 1
        assert strength.count_piece_type("ELEPHANT") == 0

    def test_get_strongest_pieces(self):
        """Test getting strongest pieces."""
        pieces = [
            Piece.create("SOLDIER_RED"),  # 2
            Piece.create("HORSE_BLACK"),  # 5
            Piece.create("GENERAL_RED"),  # 14
            Piece.create("ADVISOR_BLACK"),  # 11
        ]

        strength = HandStrength.calculate(pieces)
        strongest = strength.get_strongest_pieces(2)

        assert len(strongest) == 2
        assert strongest[0].kind == "GENERAL_RED"
        assert strongest[1].kind == "ADVISOR_BLACK"

    def test_get_weakest_pieces(self):
        """Test getting weakest pieces."""
        pieces = [
            Piece.create("SOLDIER_RED"),  # 2
            Piece.create("HORSE_BLACK"),  # 5
            Piece.create("GENERAL_RED"),  # 14
            Piece.create("ADVISOR_BLACK"),  # 11
        ]

        strength = HandStrength.calculate(pieces)
        weakest = strength.get_weakest_pieces(2)

        assert len(weakest) == 2
        assert weakest[0].kind == "HORSE_BLACK"
        assert weakest[1].kind == "SOLDIER_RED"

    def test_compare_to(self):
        """Test comparing hand strengths."""
        # Stronger hand
        strong = HandStrength.calculate(
            [Piece.create("GENERAL_RED"), Piece.create("ADVISOR_BLACK")]
        )

        # Weaker hand
        weak = HandStrength.calculate(
            [Piece.create("SOLDIER_RED"), Piece.create("CANNON_BLACK")]
        )

        # Equal strength but different highest piece
        equal_total = HandStrength.calculate(
            [Piece.create("ELEPHANT_RED"), Piece.create("CHARIOT_BLACK")]  # 10  # 7
        )  # Total: 17

        another_equal = HandStrength.calculate(
            [Piece.create("ELEPHANT_BLACK"), Piece.create("CHARIOT_RED")]  # 9  # 8
        )  # Total: 17

        assert strong.compare_to(weak) == 1  # Strong wins
        assert weak.compare_to(strong) == -1  # Weak loses
        assert equal_total.compare_to(another_equal) == 1  # Higher max piece wins
        assert strong.compare_to(strong) == 0  # Equal to self

    def test_immutability(self):
        """Test that HandStrength is immutable."""
        pieces = [Piece.create("GENERAL_RED")]
        strength = HandStrength.calculate(pieces)

        with pytest.raises(AttributeError):
            strength.total_points = 100

    def test_to_dict(self):
        """Test converting to dictionary."""
        pieces = [Piece.create("GENERAL_RED"), Piece.create("SOLDIER_BLACK")]

        strength = HandStrength.calculate(pieces)
        data = strength.to_dict()

        assert data["total_points"] == 15  # 14 + 1
        assert data["highest_piece_value"] == 14
        assert data["is_weak"] is False
        assert data["piece_count"] == 2
        assert "GENERAL_RED" in data["pieces"]

    def test_get_summary(self):
        """Test getting summary string."""
        pieces = [Piece.create("SOLDIER_RED"), Piece.create("CANNON_BLACK")]

        strength = HandStrength.calculate(pieces)
        summary = strength.get_summary()

        assert "5 points" in summary  # 2 + 3
        assert "2 pieces" in summary
        assert "highest: 3" in summary
        assert "(WEAK)" in summary


class TestHandComparison:
    """Test the HandComparison value object."""

    def test_compare_multiple_hands(self):
        """Test comparing multiple player hands."""
        player_hands = {
            "Alice": [
                Piece.create("GENERAL_RED"),
                Piece.create("ADVISOR_BLACK"),
            ],  # 25 points
            "Bob": [
                Piece.create("SOLDIER_RED"),
                Piece.create("CANNON_BLACK"),
            ],  # 5 points
            "Carol": [
                Piece.create("ELEPHANT_RED"),
                Piece.create("HORSE_BLACK"),
            ],  # 15 points
        }

        comparison = HandComparison.compare_hands(player_hands)

        assert comparison.strongest_player == "Alice"
        assert comparison.weakest_player == "Bob"
        assert len(comparison.weak_hand_players) == 1
        assert "Bob" in comparison.weak_hand_players

    def test_empty_hands_raises_error(self):
        """Test that comparing empty hands raises error."""
        with pytest.raises(ValueError, match="Cannot compare empty hands"):
            HandComparison.compare_hands({})

    def test_get_player_strength(self):
        """Test getting strength for specific player."""
        player_hands = {
            "Alice": [Piece.create("GENERAL_RED")],
            "Bob": [Piece.create("SOLDIER_RED")],
        }

        comparison = HandComparison.compare_hands(player_hands)

        alice_strength = comparison.get_player_strength("Alice")
        assert alice_strength.total_points == 14

        # Non-existent player
        with pytest.raises(ValueError, match="Player Eve not found"):
            comparison.get_player_strength("Eve")

    def test_get_rank(self):
        """Test getting player rank."""
        player_hands = {
            "Alice": [Piece.create("SOLDIER_RED")],  # 2 points (rank 3)
            "Bob": [Piece.create("GENERAL_RED")],  # 14 points (rank 1)
            "Carol": [Piece.create("ELEPHANT_BLACK")],  # 9 points (rank 2)
        }

        comparison = HandComparison.compare_hands(player_hands)

        assert comparison.get_rank("Bob") == 1
        assert comparison.get_rank("Carol") == 2
        assert comparison.get_rank("Alice") == 3

    def test_all_weak_hands(self):
        """Test comparison when all hands are weak."""
        player_hands = {
            "Alice": [Piece.create("SOLDIER_RED"), Piece.create("CANNON_BLACK")],
            "Bob": [Piece.create("HORSE_RED"), Piece.create("CHARIOT_BLACK")],
        }

        comparison = HandComparison.compare_hands(player_hands)

        assert len(comparison.weak_hand_players) == 2
        assert "Alice" in comparison.weak_hand_players
        assert "Bob" in comparison.weak_hand_players

    def test_to_dict(self):
        """Test converting to dictionary."""
        player_hands = {
            "Alice": [Piece.create("GENERAL_RED")],
            "Bob": [Piece.create("SOLDIER_RED")],
        }

        comparison = HandComparison.compare_hands(player_hands)
        data = comparison.to_dict()

        assert data["strongest_player"] == "Alice"
        assert data["weakest_player"] == "Bob"
        assert len(data["rankings"]) == 2
        assert data["rankings"][0]["player"] == "Alice"
        assert data["rankings"][0]["rank"] == 1
