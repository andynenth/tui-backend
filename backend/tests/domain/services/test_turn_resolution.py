"""
Tests for the TurnResolutionService domain service.
"""

import pytest
from domain.services.turn_resolution import TurnResolutionService, TurnPlay, TurnResult
from domain.value_objects.piece import Piece


class TestTurnResolution:
    """Test the TurnResolutionService domain service."""

    def test_turn_play_creation(self):
        """Test creating a TurnPlay."""
        pieces = [Piece.create("GENERAL_RED"), Piece.create("SOLDIER_RED")]
        play = TurnPlay.create("Alice", pieces)

        assert play.player_name == "Alice"
        assert len(play.pieces) == 2
        assert play.play_type == "INVALID"  # Not a valid combination
        assert play.total_points == 16  # 14 + 2
        assert play.is_valid() is False

    def test_valid_turn_play(self):
        """Test creating a valid TurnPlay."""
        pieces = [Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_RED")]
        play = TurnPlay.create("Bob", pieces)

        assert play.play_type == "PAIR"
        assert play.is_valid() is True
        assert play.total_points == 4  # 2 + 2

    def test_turn_play_beats(self):
        """Test comparing turn plays."""
        # Higher value pair beats lower value pair
        play1 = TurnPlay.create(
            "Alice", [Piece.create("ELEPHANT_RED"), Piece.create("ELEPHANT_RED")]
        )
        play2 = TurnPlay.create(
            "Bob", [Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_RED")]
        )

        assert play1.beats(play2) is True
        assert play2.beats(play1) is False

        # Different play types cannot be compared
        play3 = TurnPlay.create("Carol", [Piece.create("GENERAL_RED")])
        assert play1.beats(play3) is False
        assert play3.beats(play1) is False

    def test_turn_play_immutability(self):
        """Test that TurnPlay is immutable."""
        play = TurnPlay.create("Alice", [Piece.create("SOLDIER_RED")])

        with pytest.raises(AttributeError):
            play.player_name = "Bob"

    def test_resolve_turn_single_winner(self):
        """Test resolving a turn with a clear winner."""
        plays = [
            TurnPlay.create("Alice", [Piece.create("GENERAL_RED")]),  # 14 points
            TurnPlay.create("Bob", [Piece.create("SOLDIER_RED")]),  # 2 points
            TurnPlay.create("Carol", [Piece.create("ELEPHANT_BLACK")]),  # 9 points
            TurnPlay.create("Dave", [Piece.create("HORSE_RED")]),  # 6 points
        ]

        result = TurnResolutionService.resolve_turn(plays, turn_number=1)

        assert isinstance(result, TurnResult)
        assert result.turn_number == 1
        assert result.winner_name == "Alice"
        assert result.winning_play.player_name == "Alice"
        assert result.pile_awarded is True
        assert len(result.plays) == 4

    def test_resolve_turn_no_valid_plays(self):
        """Test resolving a turn with no valid plays."""
        plays = [
            TurnPlay.create(
                "Alice",
                [
                    Piece.create("GENERAL_RED"),
                    Piece.create("SOLDIER_BLACK"),  # Invalid combination
                ],
            ),
            TurnPlay.create(
                "Bob",
                [
                    Piece.create("ELEPHANT_RED"),
                    Piece.create("CANNON_BLACK"),  # Invalid combination
                ],
            ),
        ]

        result = TurnResolutionService.resolve_turn(plays, turn_number=2)

        assert result.winner_name is None
        assert result.winning_play is None
        assert result.pile_awarded is False

    def test_resolve_turn_with_required_piece_count(self):
        """Test turn resolution with required piece count."""
        plays = [
            TurnPlay.create("Alice", [Piece.create("GENERAL_RED")]),  # 1 piece
            TurnPlay.create(
                "Bob",
                [Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_RED")],  # 2 pieces
            ),
            TurnPlay.create(
                "Carol",
                [  # 2 pieces
                    Piece.create("ELEPHANT_BLACK"),
                    Piece.create("ELEPHANT_BLACK"),
                ],
            ),
        ]

        # Require 2 pieces - Alice's play should be excluded
        result = TurnResolutionService.resolve_turn(
            plays, turn_number=3, required_piece_count=2
        )

        # Carol wins (ELEPHANT pair beats SOLDIER pair)
        assert result.winner_name == "Carol"
        assert len(result.winning_play.pieces) == 2

    def test_validate_turn_plays(self):
        """Test validating turn plays."""
        plays = [
            TurnPlay.create("Alice", [Piece.create("GENERAL_RED")]),
            TurnPlay.create(
                "Bob",
                [Piece.create("GENERAL_RED"), Piece.create("SOLDIER_BLACK")],  # Invalid
            ),
            TurnPlay.create(
                "Carol", [Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_RED")]
            ),
        ]

        # Validate without required count
        results = TurnResolutionService.validate_turn_plays(plays)
        assert results["Alice"] == ""  # Valid
        assert "Invalid play type" in results["Bob"]
        assert results["Carol"] == ""  # Valid

        # Validate with required count of 2
        results = TurnResolutionService.validate_turn_plays(
            plays, required_piece_count=2
        )
        assert "Must play 2 pieces" in results["Alice"]
        assert "Invalid play type" in results["Bob"]
        assert results["Carol"] == ""  # Valid

    def test_get_turn_summary(self):
        """Test getting turn summary."""
        # Create a winning result
        winning_play = TurnPlay.create(
            "Alice",
            [
                Piece.create("GENERAL_RED"),
                Piece.create("ADVISOR_RED"),
                Piece.create("ELEPHANT_RED"),
            ],
        )

        result = TurnResult(
            turn_number=5,
            plays=[winning_play],
            winner_name="Alice",
            winning_play=winning_play,
            pile_awarded=True,
        )

        summary = TurnResolutionService.get_turn_summary(result)
        assert "Turn 5: Alice wins" in summary
        assert "STRAIGHT" in summary
        assert "36 points" in summary  # 14 + 12 + 10

        # No winner result
        no_winner_result = TurnResult(
            turn_number=6,
            plays=[],
            winner_name=None,
            winning_play=None,
            pile_awarded=False,
        )

        summary = TurnResolutionService.get_turn_summary(no_winner_result)
        assert "Turn 6: No winner" in summary

    def test_turn_result_to_dict(self):
        """Test converting turn result to dictionary."""
        plays = [
            TurnPlay.create("Alice", [Piece.create("GENERAL_RED")]),
            TurnPlay.create("Bob", [Piece.create("SOLDIER_RED")]),
        ]

        result = TurnResult(
            turn_number=1,
            plays=plays,
            winner_name="Alice",
            winning_play=plays[0],
            pile_awarded=True,
        )

        data = result.to_dict()
        assert data["turn_number"] == 1
        assert data["winner_name"] == "Alice"
        assert data["pile_awarded"] is True
        assert len(data["plays"]) == 2
        assert data["winning_play"]["player_name"] == "Alice"

    def test_get_play_summary(self):
        """Test getting play summary from turn result."""
        plays = [
            TurnPlay.create(
                "Alice", [Piece.create("GENERAL_RED"), Piece.create("ADVISOR_RED")]
            ),
            TurnPlay.create(
                "Bob", [Piece.create("SOLDIER_BLACK"), Piece.create("SOLDIER_BLACK")]
            ),
        ]

        result = TurnResult(
            turn_number=1,
            plays=plays,
            winner_name="Alice",
            winning_play=plays[0],
            pile_awarded=True,
        )

        summary = result.get_play_summary()
        assert summary == {
            "Alice": ["GENERAL_RED", "ADVISOR_RED"],
            "Bob": ["SOLDIER_BLACK", "SOLDIER_BLACK"],
        }

    def test_calculate_turn_statistics(self):
        """Test calculating statistics from multiple turns."""
        # Create some turn results
        results = []

        # Turn 1: Alice wins with a pair
        plays1 = [
            TurnPlay.create(
                "Alice", [Piece.create("ELEPHANT_RED"), Piece.create("ELEPHANT_RED")]
            ),
            TurnPlay.create(
                "Bob", [Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_RED")]
            ),
        ]
        results.append(TurnResolutionService.resolve_turn(plays1, 1))

        # Turn 2: Bob wins with a single
        plays2 = [
            TurnPlay.create("Alice", [Piece.create("SOLDIER_RED")]),
            TurnPlay.create("Bob", [Piece.create("GENERAL_BLACK")]),
        ]
        results.append(TurnResolutionService.resolve_turn(plays2, 2))

        # Turn 3: No winner (invalid plays)
        plays3 = [
            TurnPlay.create(
                "Alice", [Piece.create("GENERAL_RED"), Piece.create("SOLDIER_BLACK")]
            )
        ]
        results.append(TurnResolutionService.resolve_turn(plays3, 3))

        # Calculate statistics
        stats = TurnResolutionService.calculate_turn_statistics(results)

        assert stats["total_turns"] == 3
        assert stats["turns_with_winner"] == 2
        assert stats["turns_without_winner"] == 1
        assert stats["wins_by_player"]["Alice"] == 1
        assert stats["wins_by_player"]["Bob"] == 1
        assert stats["play_type_frequency"]["PAIR"] == 1
        assert stats["play_type_frequency"]["SINGLE"] == 1
        assert stats["average_winning_points"] == (20 + 13) / 2  # 16.5
