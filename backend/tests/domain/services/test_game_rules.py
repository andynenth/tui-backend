"""
Tests for the GameRules domain service.
"""

import pytest
from domain.services.game_rules import GameRules, PlayType
from domain.value_objects.piece import Piece
from domain.entities.player import Player


class TestGameRules:
    """Test the GameRules domain service."""

    def test_identify_single(self):
        """Test identifying a single piece play."""
        pieces = [Piece.create("GENERAL_RED")]
        assert GameRules.identify_play_type(pieces) == PlayType.SINGLE

    def test_identify_pair(self):
        """Test identifying a pair."""
        # Valid pair - same name and color
        pieces = [Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_RED")]
        assert GameRules.identify_play_type(pieces) == PlayType.PAIR

        # Invalid pair - different colors
        pieces = [Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_BLACK")]
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

        # Invalid pair - different names
        pieces = [Piece.create("SOLDIER_RED"), Piece.create("GENERAL_RED")]
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

    def test_identify_three_of_a_kind(self):
        """Test identifying three of a kind."""
        # Valid - 3 soldiers same color
        pieces = [
            Piece.create("SOLDIER_RED"),
            Piece.create("SOLDIER_RED"),
            Piece.create("SOLDIER_RED"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.THREE_OF_A_KIND

        # Invalid - mixed colors
        pieces = [
            Piece.create("SOLDIER_RED"),
            Piece.create("SOLDIER_RED"),
            Piece.create("SOLDIER_BLACK"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

        # Invalid - not soldiers
        pieces = [
            Piece.create("GENERAL_RED"),
            Piece.create("GENERAL_RED"),
            Piece.create("GENERAL_RED"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

    def test_identify_straight(self):
        """Test identifying a straight."""
        # Valid straight - GENERAL group
        pieces = [
            Piece.create("GENERAL_RED"),
            Piece.create("ADVISOR_RED"),
            Piece.create("ELEPHANT_RED"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.STRAIGHT

        # Valid straight - CHARIOT group
        pieces = [
            Piece.create("CHARIOT_BLACK"),
            Piece.create("HORSE_BLACK"),
            Piece.create("CANNON_BLACK"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.STRAIGHT

        # Invalid - mixed colors
        pieces = [
            Piece.create("GENERAL_RED"),
            Piece.create("ADVISOR_RED"),
            Piece.create("ELEPHANT_BLACK"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

        # Invalid - mixed groups
        pieces = [
            Piece.create("GENERAL_RED"),
            Piece.create("HORSE_RED"),
            Piece.create("CANNON_RED"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

    def test_identify_four_of_a_kind(self):
        """Test identifying four of a kind."""
        # Valid
        pieces = [Piece.create("SOLDIER_BLACK")] * 4
        assert GameRules.identify_play_type(pieces) == PlayType.FOUR_OF_A_KIND

        # Invalid - not soldiers
        pieces = [Piece.create("CANNON_BLACK")] * 4
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

    def test_identify_extended_straight(self):
        """Test identifying extended straight."""
        # Valid - 2 horses, 1 chariot, 1 cannon
        pieces = [
            Piece.create("HORSE_RED"),
            Piece.create("HORSE_RED"),
            Piece.create("CHARIOT_RED"),
            Piece.create("CANNON_RED"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.EXTENDED_STRAIGHT

        # Valid - 2 generals, 1 advisor, 1 elephant
        pieces = [
            Piece.create("GENERAL_BLACK"),
            Piece.create("GENERAL_BLACK"),
            Piece.create("ADVISOR_BLACK"),
            Piece.create("ELEPHANT_BLACK"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.EXTENDED_STRAIGHT

        # Invalid - wrong distribution
        pieces = [
            Piece.create("HORSE_RED"),
            Piece.create("CHARIOT_RED"),
            Piece.create("CHARIOT_RED"),
            Piece.create("CHARIOT_RED"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

    def test_identify_extended_straight_5(self):
        """Test identifying 5-piece extended straight."""
        # Valid - 2 horses, 2 cannons, 1 chariot
        pieces = [
            Piece.create("HORSE_RED"),
            Piece.create("HORSE_RED"),
            Piece.create("CANNON_RED"),
            Piece.create("CANNON_RED"),
            Piece.create("CHARIOT_RED"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.EXTENDED_STRAIGHT_5

        # Invalid - wrong distribution (3-1-1)
        pieces = [
            Piece.create("HORSE_RED"),
            Piece.create("HORSE_RED"),
            Piece.create("HORSE_RED"),
            Piece.create("CANNON_RED"),
            Piece.create("CHARIOT_RED"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

    def test_identify_five_of_a_kind(self):
        """Test identifying five of a kind."""
        # Valid
        pieces = [Piece.create("SOLDIER_RED")] * 5
        assert GameRules.identify_play_type(pieces) == PlayType.FIVE_OF_A_KIND

        # Invalid - not soldiers
        pieces = [Piece.create("HORSE_RED")] * 5
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

    def test_identify_double_straight(self):
        """Test identifying double straight."""
        # Valid
        pieces = [
            Piece.create("CHARIOT_BLACK"),
            Piece.create("CHARIOT_BLACK"),
            Piece.create("HORSE_BLACK"),
            Piece.create("HORSE_BLACK"),
            Piece.create("CANNON_BLACK"),
            Piece.create("CANNON_BLACK"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.DOUBLE_STRAIGHT

        # Invalid - wrong counts
        pieces = [
            Piece.create("CHARIOT_BLACK"),
            Piece.create("CHARIOT_BLACK"),
            Piece.create("CHARIOT_BLACK"),
            Piece.create("HORSE_BLACK"),
            Piece.create("CANNON_BLACK"),
            Piece.create("CANNON_BLACK"),
        ]
        assert GameRules.identify_play_type(pieces) == PlayType.INVALID

    def test_is_valid_play(self):
        """Test play validation."""
        # Valid single
        assert GameRules.is_valid_play([Piece.create("GENERAL_RED")]) is True

        # Valid pair
        assert (
            GameRules.is_valid_play(
                [Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_RED")]
            )
            is True
        )

        # Invalid
        assert (
            GameRules.is_valid_play(
                [Piece.create("SOLDIER_RED"), Piece.create("GENERAL_RED")]
            )
            is False
        )

    def test_compare_plays_same_type(self):
        """Test comparing plays of the same type."""
        # Compare singles - GENERAL (14) vs SOLDIER (2)
        play1 = [Piece.create("GENERAL_RED")]
        play2 = [Piece.create("SOLDIER_RED")]
        assert GameRules.compare_plays(play1, play2) == 1  # play1 wins

        # Compare pairs - higher total wins
        play1 = [Piece.create("ELEPHANT_RED")] * 2  # 10 * 2 = 20
        play2 = [Piece.create("SOLDIER_RED")] * 2  # 2 * 2 = 4
        assert GameRules.compare_plays(play1, play2) == 1  # play1 wins

        # Tie - same point values
        play1 = [Piece.create("SOLDIER_RED")]  # 2 points
        play2 = [Piece.create("SOLDIER_RED")]  # 2 points
        assert GameRules.compare_plays(play1, play2) == 0  # tie

    def test_compare_plays_different_types(self):
        """Test that different play types cannot be compared."""
        play1 = [Piece.create("SOLDIER_RED")]  # Single
        play2 = [Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_RED")]  # Pair
        assert GameRules.compare_plays(play1, play2) == -1  # Invalid comparison

    def test_compare_extended_straights(self):
        """Test special comparison for extended straights."""
        # Extended straight comparison uses top 3 unique piece values
        # Play1: 2 GENERALs (14), 1 ADVISOR (11), 1 ELEPHANT (10) = 14+11+10 = 35
        play1 = [
            Piece.create("GENERAL_RED"),
            Piece.create("GENERAL_RED"),
            Piece.create("ADVISOR_RED"),
            Piece.create("ELEPHANT_RED"),
        ]

        # Play2: 2 CHARIOTs (7), 1 HORSE (6), 1 CANNON (4) = 7+6+4 = 17
        play2 = [
            Piece.create("CHARIOT_RED"),
            Piece.create("CHARIOT_RED"),
            Piece.create("HORSE_RED"),
            Piece.create("CANNON_RED"),
        ]

        assert GameRules.compare_plays(play1, play2) == 1  # play1 wins

    def test_get_valid_declarations(self):
        """Test declaration validation."""
        player = Player(name="Alice", is_bot=False)

        # Normal case - all options available
        options = GameRules.get_valid_declarations(player, 0, False)
        assert options == [0, 1, 2, 3, 4, 5, 6, 7, 8]

        # Last player cannot make total 8
        options = GameRules.get_valid_declarations(player, 5, True)
        assert 3 not in options  # 5 + 3 = 8

        # Player with 2 consecutive zero declares must declare at least 1
        player.stats.zero_declares_in_a_row = 2
        options = GameRules.get_valid_declarations(player, 0, False)
        assert 0 not in options
        assert all(opt > 0 for opt in options)

    def test_has_weak_hand(self):
        """Test weak hand detection."""
        # Weak hand - all pieces <= 9 points
        weak_hand = [
            Piece.create("SOLDIER_RED"),  # 2 points
            Piece.create("CANNON_BLACK"),  # 3 points
            Piece.create("HORSE_RED"),  # 6 points
            Piece.create("CHARIOT_BLACK"),  # 7 points
        ]
        assert GameRules.has_weak_hand(weak_hand) is True

        # Strong hand - has piece > 9 points
        strong_hand = [
            Piece.create("SOLDIER_RED"),  # 2 points
            Piece.create("GENERAL_RED"),  # 14 points
            Piece.create("HORSE_RED"),  # 6 points
        ]
        assert GameRules.has_weak_hand(strong_hand) is False

    def test_calculate_hand_strength(self):
        """Test hand strength calculation."""
        hand = [
            Piece.create("GENERAL_RED"),  # 14 points
            Piece.create("ADVISOR_BLACK"),  # 11 points
            Piece.create("SOLDIER_RED"),  # 2 points
        ]
        assert GameRules.calculate_hand_strength(hand) == 27

    def test_is_play_type_stronger(self):
        """Test play type strength comparison."""
        # Pair is stronger than single
        assert GameRules.is_play_type_stronger(PlayType.PAIR, PlayType.SINGLE) is True

        # Double straight is strongest
        assert (
            GameRules.is_play_type_stronger(
                PlayType.DOUBLE_STRAIGHT, PlayType.FIVE_OF_A_KIND
            )
            is True
        )

        # Single is weakest
        assert GameRules.is_play_type_stronger(PlayType.SINGLE, PlayType.PAIR) is False

        # Invalid type
        assert GameRules.is_play_type_stronger("INVALID_TYPE", PlayType.SINGLE) is False
