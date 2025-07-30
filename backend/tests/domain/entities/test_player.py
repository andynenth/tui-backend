"""
Tests for the Player entity.
"""

import pytest
from domain.entities.player import Player, PlayerStats
from domain.value_objects.piece import Piece
from domain.events.player_events import (
    PlayerDeclaredPiles,
    PlayerCapturedPiles,
    PlayerScoreUpdated,
    PlayerHandUpdated,
    PlayerStatUpdated,
)


class TestPlayer:
    """Test the Player entity."""

    def test_create_player(self):
        """Test creating a player."""
        player = Player(name="Alice", is_bot=False)

        assert player.name == "Alice"
        assert player.id == "Alice"
        assert player.is_bot is False
        assert player.hand == []
        assert player.score == 0
        assert player.declared_piles == 0
        assert player.captured_piles == 0
        assert player.stats.turns_won == 0
        assert player.stats.perfect_rounds == 0
        assert player.stats.zero_declares_in_a_row == 0

    def test_create_bot_player(self):
        """Test creating a bot player."""
        bot = Player(name="Bot1", is_bot=True)

        assert bot.name == "Bot1"
        assert bot.is_bot is True
        assert bot._original_is_bot is True

    def test_update_hand(self):
        """Test updating player's hand."""
        player = Player(name="Alice")
        pieces = [
            Piece.create("GENERAL_RED"),
            Piece.create("SOLDIER_BLACK"),
            Piece.create("HORSE_RED"),
        ]

        player.update_hand(pieces, room_id="room123")

        assert len(player.hand) == 3
        assert player.hand[0].kind == "GENERAL_RED"
        assert player.hand[1].kind == "SOLDIER_BLACK"
        assert player.hand[2].kind == "HORSE_RED"

        # Check event was emitted
        events = player.events
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, PlayerHandUpdated)
        assert event.player_name == "Alice"
        assert event.old_hand == []
        assert event.new_hand == ["GENERAL_RED", "SOLDIER_BLACK", "HORSE_RED"]

    def test_add_pieces_to_hand(self):
        """Test adding pieces to hand."""
        player = Player(name="Bob")
        initial_pieces = [Piece.create("ADVISOR_RED")]
        player.hand = initial_pieces.copy()

        new_pieces = [Piece.create("CANNON_BLACK"), Piece.create("ELEPHANT_RED")]

        player.add_pieces_to_hand(new_pieces, room_id="room123")

        assert len(player.hand) == 3
        assert player.hand[0].kind == "ADVISOR_RED"
        assert player.hand[1].kind == "CANNON_BLACK"
        assert player.hand[2].kind == "ELEPHANT_RED"

        # Check event
        events = player.events
        assert len(events) == 1
        event = events[0]
        assert event.old_hand == ["ADVISOR_RED"]
        assert event.new_hand == ["ADVISOR_RED", "CANNON_BLACK", "ELEPHANT_RED"]

    def test_remove_pieces_from_hand(self):
        """Test removing pieces from hand."""
        player = Player(name="Carol")
        pieces = [
            Piece.create("GENERAL_RED"),
            Piece.create("SOLDIER_BLACK"),
            Piece.create("HORSE_RED"),
            Piece.create("CHARIOT_BLACK"),
        ]
        player.hand = pieces.copy()

        # Remove pieces at indices 1 and 3
        removed = player.remove_pieces_from_hand([1, 3], room_id="room123")

        assert len(removed) == 2
        assert removed[0].kind == "SOLDIER_BLACK"
        assert removed[1].kind == "CHARIOT_BLACK"

        assert len(player.hand) == 2
        assert player.hand[0].kind == "GENERAL_RED"
        assert player.hand[1].kind == "HORSE_RED"

        # Check event
        events = player.events
        assert len(events) == 1
        event = events[0]
        assert event.old_hand == [
            "GENERAL_RED",
            "SOLDIER_BLACK",
            "HORSE_RED",
            "CHARIOT_BLACK",
        ]
        assert event.new_hand == ["GENERAL_RED", "HORSE_RED"]

    def test_remove_invalid_indices(self):
        """Test removing pieces with invalid indices."""
        player = Player(name="Dave")
        pieces = [Piece.create("ADVISOR_RED"), Piece.create("CANNON_BLACK")]
        player.hand = pieces.copy()

        # Try to remove invalid index
        with pytest.raises(ValueError, match="Invalid piece index: 5"):
            player.remove_pieces_from_hand([0, 5], room_id="room123")

        # Hand should be unchanged
        assert len(player.hand) == 2

    def test_has_piece(self):
        """Test checking if player has specific piece."""
        player = Player(name="Eve")
        player.hand = [Piece.create("GENERAL_RED"), Piece.create("ADVISOR_BLACK")]

        assert player.has_piece("GENERAL_RED") is True
        assert player.has_piece("ADVISOR_BLACK") is True
        assert player.has_piece("SOLDIER_RED") is False
        assert player.has_red_general() is True

    def test_declare_piles(self):
        """Test declaring pile count."""
        player = Player(name="Frank")

        # First declaration (non-zero)
        player.declare_piles(3, room_id="room123")
        assert player.declared_piles == 3
        assert player.stats.zero_declares_in_a_row == 0

        # Check event
        events = player.events
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, PlayerDeclaredPiles)
        assert event.declared_count == 3
        assert event.zero_streak == 0

        player.clear_events()

        # Zero declaration
        player.declare_piles(0, room_id="room123")
        assert player.declared_piles == 0
        assert player.stats.zero_declares_in_a_row == 1

        # Another zero declaration
        player.declare_piles(0, room_id="room123")
        assert player.stats.zero_declares_in_a_row == 2

        # Non-zero resets streak
        player.declare_piles(2, room_id="room123")
        assert player.stats.zero_declares_in_a_row == 0

    def test_invalid_declaration(self):
        """Test invalid pile declarations."""
        player = Player(name="Grace")

        with pytest.raises(ValueError, match="Invalid declaration count: -1"):
            player.declare_piles(-1, room_id="room123")

        with pytest.raises(ValueError, match="Invalid declaration count: 9"):
            player.declare_piles(9, room_id="room123")

    def test_capture_piles(self):
        """Test capturing piles."""
        player = Player(name="Henry")

        player.capture_piles(2, room_id="room123")
        assert player.captured_piles == 2

        player.capture_piles(3, room_id="room123")
        assert player.captured_piles == 5

        # Check events
        events = player.events
        assert len(events) == 2

        event1 = events[0]
        assert isinstance(event1, PlayerCapturedPiles)
        assert event1.piles_captured == 2
        assert event1.total_captured == 2

        event2 = events[1]
        assert event2.piles_captured == 3
        assert event2.total_captured == 5

    def test_update_score(self):
        """Test updating player score."""
        player = Player(name="Ivy", score=10)

        player.update_score(5, room_id="room123", reason="Perfect round")
        assert player.score == 15

        player.update_score(-3, room_id="room123", reason="Penalty")
        assert player.score == 12

        # Check events
        events = player.events
        assert len(events) == 2

        event1 = events[0]
        assert isinstance(event1, PlayerScoreUpdated)
        assert event1.old_score == 10
        assert event1.new_score == 15
        assert event1.points_change == 5
        assert event1.reason == "Perfect round"

        event2 = events[1]
        assert event2.old_score == 15
        assert event2.new_score == 12
        assert event2.points_change == -3
        assert event2.reason == "Penalty"

    def test_record_stats(self):
        """Test recording player statistics."""
        player = Player(name="Jack")

        player.record_turn_won(room_id="room123")
        assert player.stats.turns_won == 1

        player.record_perfect_round(room_id="room123")
        assert player.stats.perfect_rounds == 1

        # Check events
        events = player.events
        assert len(events) == 2

        assert all(isinstance(e, PlayerStatUpdated) for e in events)
        assert events[0].stat_name == "turns_won"
        assert events[1].stat_name == "perfect_rounds"

    def test_reset_for_next_round(self):
        """Test resetting for next round."""
        player = Player(name="Kate")
        player.hand = [Piece.create("GENERAL_RED")]
        player.declared_piles = 3
        player.captured_piles = 2
        player.score = 15
        player.stats.turns_won = 5

        player.reset_for_next_round()

        # These should be reset
        assert player.hand == []
        assert player.declared_piles == 0
        assert player.captured_piles == 0

        # These should NOT be reset
        assert player.score == 15
        assert player.stats.turns_won == 5

        # No events should be emitted for reset
        assert len(player.events) == 0

    def test_to_dict(self):
        """Test converting player to dictionary."""
        player = Player(
            name="Leo", is_bot=True, score=25, declared_piles=2, captured_piles=3
        )
        player.hand = [Piece.create("ADVISOR_RED"), Piece.create("CANNON_BLACK")]
        player.stats.turns_won = 4
        player.stats.perfect_rounds = 1
        player.stats.zero_declares_in_a_row = 2

        data = player.to_dict()

        assert data == {
            "name": "Leo",
            "is_bot": True,
            "hand": [
                {"kind": "ADVISOR_RED", "point": 12, "name": "ADVISOR", "color": "RED"},
                {
                    "kind": "CANNON_BLACK",
                    "point": 3,
                    "name": "CANNON",
                    "color": "BLACK",
                },
            ],
            "score": 25,
            "declared_piles": 2,
            "captured_piles": 3,
            "stats": {"turns_won": 4, "perfect_rounds": 1, "zero_declares_in_a_row": 2},
        }

    def test_from_dict(self):
        """Test creating player from dictionary."""
        data = {
            "name": "Mike",
            "is_bot": False,
            "hand": [
                {"kind": "ELEPHANT_RED", "point": 10},
                {"kind": "SOLDIER_BLACK", "point": 1},
            ],
            "score": 30,
            "declared_piles": 4,
            "captured_piles": 3,
            "stats": {"turns_won": 6, "perfect_rounds": 2, "zero_declares_in_a_row": 0},
        }

        player = Player.from_dict(data)

        assert player.name == "Mike"
        assert player.is_bot is False
        assert len(player.hand) == 2
        assert player.hand[0].kind == "ELEPHANT_RED"
        assert player.hand[1].kind == "SOLDIER_BLACK"
        assert player.score == 30
        assert player.declared_piles == 4
        assert player.captured_piles == 3
        assert player.stats.turns_won == 6
        assert player.stats.perfect_rounds == 2
        assert player.stats.zero_declares_in_a_row == 0

    def test_event_management(self):
        """Test event management methods."""
        player = Player(name="Nancy")

        # Should start with no events
        assert len(player.events) == 0

        # Do some actions
        player.declare_piles(2, room_id="room123")
        player.update_score(5, room_id="room123", reason="Test")

        # Should have 2 events
        events = player.events
        assert len(events) == 2

        # Events should be copies
        events.append("dummy")
        assert len(player.events) == 2  # Original unchanged

        # Clear events
        player.clear_events()
        assert len(player.events) == 0
