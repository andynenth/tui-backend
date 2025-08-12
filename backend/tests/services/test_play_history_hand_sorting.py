# backend/tests/services/test_play_history_hand_sorting.py
"""
TDD: Start with hand sorting tests as they're fundamental to the feature.
"""

import pytest
from backend.services.play_history_service import PlayHistoryService
from backend.engine.piece import Piece


class TestHandSorting:
    """Test hand sorting logic - RED before BLACK, then high to low value."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PlayHistoryService()

    def test_sort_red_before_black(self):
        """Test that RED pieces come before BLACK pieces."""
        hand = [
            Piece("SOLDIER_BLACK"),  # 1 point
            Piece("GENERAL_RED"),  # 14 points
            Piece("ADVISOR_BLACK"),  # 11 points
            Piece("HORSE_RED"),  # 6 points
        ]

        sorted_hand = self.service.sort_hand(hand)

        # All RED pieces should come before BLACK pieces
        assert sorted_hand[0].color == "RED"
        assert sorted_hand[1].color == "RED"
        assert sorted_hand[2].color == "BLACK"
        assert sorted_hand[3].color == "BLACK"

    def test_sort_by_value_within_color(self):
        """Test that pieces are sorted by value (high to low) within same color."""
        hand = [
            Piece("HORSE_RED"),  # 6 points
            Piece("CANNON_RED"),  # 4 points
            Piece("ADVISOR_RED"),  # 12 points
            Piece("SOLDIER_BLACK"),  # 1 point
            Piece("ELEPHANT_BLACK"),  # 9 points
            Piece("ADVISOR_BLACK"),  # 11 points
        ]

        sorted_hand = self.service.sort_hand(hand)

        # RED pieces: ADVISOR_RED(12), HORSE_RED(6), CANNON_RED(4)
        assert sorted_hand[0].kind == "ADVISOR_RED"
        assert sorted_hand[1].kind == "HORSE_RED"
        assert sorted_hand[2].kind == "CANNON_RED"

        # BLACK pieces: ADVISOR_BLACK(11), ELEPHANT_BLACK(9), SOLDIER_BLACK(1)
        assert sorted_hand[3].kind == "ADVISOR_BLACK"
        assert sorted_hand[4].kind == "ELEPHANT_BLACK"
        assert sorted_hand[5].kind == "SOLDIER_BLACK"

    def test_complete_hand_sorting(self):
        """Test sorting a complete 8-piece hand."""
        hand = [
            Piece("CANNON_BLACK"),  # 3
            Piece("GENERAL_RED"),  # 14
            Piece("SOLDIER_BLACK"),  # 1
            Piece("ELEPHANT_RED"),  # 10
            Piece("ADVISOR_BLACK"),  # 11
            Piece("HORSE_RED"),  # 6
            Piece("CHARIOT_BLACK"),  # 7
            Piece("SOLDIER_RED"),  # 2
        ]

        sorted_hand = self.service.sort_hand(hand)

        # Expected order:
        # RED: GENERAL_RED(14), ELEPHANT_RED(10), HORSE_RED(6), SOLDIER_RED(2)
        # BLACK: ADVISOR_BLACK(11), CHARIOT_BLACK(7), CANNON_BLACK(3), SOLDIER_BLACK(1)

        expected_order = [
            "GENERAL_RED",
            "ELEPHANT_RED",
            "HORSE_RED",
            "SOLDIER_RED",
            "ADVISOR_BLACK",
            "CHARIOT_BLACK",
            "CANNON_BLACK",
            "SOLDIER_BLACK",
        ]

        actual_order = [piece.kind for piece in sorted_hand]
        assert actual_order == expected_order

    def test_empty_hand(self):
        """Test handling of empty hand."""
        sorted_hand = self.service.sort_hand([])
        assert sorted_hand == []

    def test_single_piece_hand(self):
        """Test handling of single piece."""
        hand = [Piece("GENERAL_RED")]
        sorted_hand = self.service.sort_hand(hand)
        assert len(sorted_hand) == 1
        assert sorted_hand[0].kind == "GENERAL_RED"

    def test_all_same_color(self):
        """Test sorting when all pieces are same color."""
        hand = [
            Piece("CANNON_RED"),  # 4
            Piece("ADVISOR_RED"),  # 12
            Piece("HORSE_RED"),  # 6
            Piece("ELEPHANT_RED"),  # 10
        ]

        sorted_hand = self.service.sort_hand(hand)

        # Should be sorted by value: 12, 10, 6, 4
        assert sorted_hand[0].kind == "ADVISOR_RED"
        assert sorted_hand[1].kind == "ELEPHANT_RED"
        assert sorted_hand[2].kind == "HORSE_RED"
        assert sorted_hand[3].kind == "CANNON_RED"

    def test_duplicate_pieces(self):
        """Test sorting with duplicate pieces (e.g., multiple SOLDIERs)."""
        hand = [
            Piece("SOLDIER_BLACK"),  # 1
            Piece("SOLDIER_RED"),  # 2
            Piece("SOLDIER_BLACK"),  # 1
            Piece("SOLDIER_RED"),  # 2
            Piece("SOLDIER_RED"),  # 2
        ]

        sorted_hand = self.service.sort_hand(hand)

        # All RED soldiers should come first
        assert sorted_hand[0].kind == "SOLDIER_RED"
        assert sorted_hand[1].kind == "SOLDIER_RED"
        assert sorted_hand[2].kind == "SOLDIER_RED"
        assert sorted_hand[3].kind == "SOLDIER_BLACK"
        assert sorted_hand[4].kind == "SOLDIER_BLACK"
