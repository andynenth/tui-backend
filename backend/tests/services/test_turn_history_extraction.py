# backend/tests/services/test_turn_history_extraction.py
"""
Test turn-by-turn history extraction functionality.
"""

import pytest
from backend.services.play_history_service import PlayHistoryService
from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.turn_resolution import TurnPlay


class TestTurnHistoryExtraction:
    """Test extraction of turn-by-turn play history."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PlayHistoryService()

        # Create test players
        self.players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]

        # Create test game
        self.game = Game(self.players)
        self.game.round_number = 1
        self.game.starter_index = 0
        self.game.turn_number = 0

        # Set up initial hands for all players
        self.game.initial_hands = {
            "Bot 1": [
                Piece("GENERAL_RED"),  # 14 points
                Piece("ADVISOR_BLACK"),  # 13 points
                Piece("ELEPHANT_RED"),  # 12 points
                Piece("CHARIOT_BLACK"),  # 11 points
                Piece("HORSE_RED"),  # 10 points
                Piece("CANNON_BLACK"),  # 9 points
                Piece("SOLDIER_RED"),  # 1 point
                Piece("SOLDIER_BLACK"),  # 1 point
            ],
            "Bot 2": [
                Piece("ADVISOR_RED"),  # 13 points
                Piece("ELEPHANT_BLACK"),  # 12 points
                Piece("CHARIOT_RED"),  # 11 points
                Piece("HORSE_BLACK"),  # 10 points
                Piece("CANNON_RED"),  # 9 points
                Piece("SOLDIER_RED"),  # 1 point
                Piece("SOLDIER_BLACK"),  # 1 point
                Piece("SOLDIER_BLACK"),  # 1 point
            ],
            "Bot 3": [
                Piece("ELEPHANT_RED"),  # 12 points
                Piece("CHARIOT_BLACK"),  # 11 points
                Piece("HORSE_RED"),  # 10 points
                Piece("CANNON_BLACK"),  # 9 points
                Piece("SOLDIER_RED"),  # 1 point
                Piece("SOLDIER_RED"),  # 1 point
                Piece("SOLDIER_BLACK"),  # 1 point
                Piece("SOLDIER_BLACK"),  # 1 point
            ],
            "Bot 4": [
                Piece("CHARIOT_RED"),  # 11 points
                Piece("HORSE_BLACK"),  # 10 points
                Piece("CANNON_RED"),  # 9 points
                Piece("CANNON_BLACK"),  # 9 points
                Piece("SOLDIER_RED"),  # 1 point
                Piece("SOLDIER_RED"),  # 1 point
                Piece("SOLDIER_BLACK"),  # 1 point
                Piece("SOLDIER_BLACK"),  # 1 point
            ],
        }

        # Set current hands to be copies of initial hands
        for i, player in enumerate(self.players):
            player.hand = self.game.initial_hands[player.name].copy()
            player.declared = [2, 3, 2, 1][i]  # Declarations
            player.captured_piles = 0  # Start with 0 captured

    def test_empty_turn_history(self):
        """Test extraction when no turns have been played."""
        # No turn history set up
        turn_history = self.service.extract_turn_history(self.game, 1)

        assert isinstance(turn_history, list)
        assert len(turn_history) == 0

    def test_single_turn_extraction(self):
        """Test extraction of a single turn."""
        # Set up turn history with one complete turn
        self.game.turn_history_this_round = []
        self.game.turn_number = 1

        # Create turn plays for all players
        turn_plays = [
            TurnPlay(
                player=self.players[0], pieces=[Piece("SOLDIER_RED")], is_valid=True
            ),
            TurnPlay(
                player=self.players[1], pieces=[Piece("SOLDIER_BLACK")], is_valid=True
            ),
            TurnPlay(
                player=self.players[2], pieces=[Piece("ELEPHANT_RED")], is_valid=True
            ),
            TurnPlay(
                player=self.players[3], pieces=[Piece("SOLDIER_BLACK")], is_valid=True
            ),
        ]

        # Store the turn in history
        self.game.turn_history_this_round.append(
            {
                "turn_number": 1,
                "plays": turn_plays,
                "winner": self.players[2],  # Bot 3 wins with ELEPHANT
                "winner_play": turn_plays[2],
                "pieces_captured": 1,  # Single piece played
            }
        )

        # Update captured counts
        self.players[2].captured_piles = 1

        # Extract turn history
        turn_history = self.service.extract_turn_history(self.game, 1)

        assert len(turn_history) == 1

        turn_info = turn_history[0]
        assert turn_info.turn_number == 1
        assert len(turn_info.plays) == 4

        # Check winner
        assert turn_info.winner.player_name == "Bot 3"
        assert turn_info.winner.pieces_captured == 1
        assert len(turn_info.winner.winning_play) == 1
        assert turn_info.winner.winning_play[0].kind == "ELEPHANT_RED"

        # Check individual plays
        bot1_play = turn_info.plays[0]
        assert bot1_play.player_name == "Bot 1"
        assert len(bot1_play.pieces_played) == 1
        assert bot1_play.pieces_played[0].kind == "SOLDIER_RED"
        assert bot1_play.play_type == "SINGLE"

        # Check game state after turn
        assert turn_info.game_state_after["Bot 3"].captured == 1
        assert turn_info.game_state_after["Bot 3"].declared == 2

    def test_multiple_turns_extraction(self):
        """Test extraction of multiple turns."""
        self.game.turn_history_this_round = []
        self.game.turn_number = 3

        # Turn 1: Singles
        turn1_plays = [
            TurnPlay(
                player=self.players[0], pieces=[Piece("SOLDIER_RED")], is_valid=True
            ),
            TurnPlay(
                player=self.players[1], pieces=[Piece("SOLDIER_BLACK")], is_valid=True
            ),
            TurnPlay(
                player=self.players[2], pieces=[Piece("ELEPHANT_RED")], is_valid=True
            ),
            TurnPlay(
                player=self.players[3], pieces=[Piece("SOLDIER_BLACK")], is_valid=True
            ),
        ]

        self.game.turn_history_this_round.append(
            {
                "turn_number": 1,
                "plays": turn1_plays,
                "winner": self.players[2],
                "winner_play": turn1_plays[2],
                "pieces_captured": 1,
                "next_starter": self.players[2],
            }
        )
        self.players[2].captured_piles = 1

        # Turn 2: Pairs (Bot 3 starts)
        turn2_plays = [
            TurnPlay(
                player=self.players[2],
                pieces=[Piece("SOLDIER_RED"), Piece("SOLDIER_BLACK")],
                is_valid=True,
            ),
            TurnPlay(
                player=self.players[3],
                pieces=[Piece("SOLDIER_RED"), Piece("SOLDIER_BLACK")],
                is_valid=True,
            ),
            TurnPlay(
                player=self.players[0],
                pieces=[Piece("SOLDIER_RED"), Piece("SOLDIER_BLACK")],
                is_valid=True,
            ),
            TurnPlay(
                player=self.players[1],
                pieces=[Piece("SOLDIER_RED"), Piece("SOLDIER_BLACK")],
                is_valid=True,
            ),
        ]

        self.game.turn_history_this_round.append(
            {
                "turn_number": 2,
                "plays": turn2_plays,
                "winner": self.players[2],  # Bot 3 wins again (started the turn)
                "winner_play": turn2_plays[0],
                "pieces_captured": 2,
                "next_starter": self.players[2],
            }
        )
        self.players[2].captured_piles = 3  # Now has 3 total

        # Turn 3: Three pieces (straight)
        turn3_plays = [
            TurnPlay(
                player=self.players[2],
                pieces=[
                    Piece("CHARIOT_BLACK"),
                    Piece("HORSE_RED"),
                    Piece("CANNON_BLACK"),
                ],
                is_valid=True,
            ),
            TurnPlay(
                player=self.players[3],
                pieces=[
                    Piece("CHARIOT_RED"),
                    Piece("HORSE_BLACK"),
                    Piece("CANNON_RED"),
                ],
                is_valid=True,
            ),
            TurnPlay(
                player=self.players[0],
                pieces=[
                    Piece("CHARIOT_BLACK"),
                    Piece("HORSE_RED"),
                    Piece("CANNON_BLACK"),
                ],
                is_valid=True,
            ),
            TurnPlay(
                player=self.players[1],
                pieces=[
                    Piece("CHARIOT_RED"),
                    Piece("HORSE_BLACK"),
                    Piece("CANNON_RED"),
                ],
                is_valid=True,
            ),
        ]

        self.game.turn_history_this_round.append(
            {
                "turn_number": 3,
                "plays": turn3_plays,
                "winner": self.players[0],  # Bot 1 wins
                "winner_play": turn3_plays[2],
                "pieces_captured": 3,
                "next_starter": self.players[0],
            }
        )
        self.players[0].captured_piles = 3

        # Extract turn history
        turn_history = self.service.extract_turn_history(self.game, 1)

        assert len(turn_history) == 3

        # Verify turn 1
        assert turn_history[0].turn_number == 1
        assert turn_history[0].winner.player_name == "Bot 3"
        assert turn_history[0].winner.pieces_captured == 1
        assert turn_history[0].next_starter == "Bot 3"

        # Verify turn 2
        assert turn_history[1].turn_number == 2
        assert turn_history[1].winner.player_name == "Bot 3"
        assert turn_history[1].winner.pieces_captured == 2
        assert len(turn_history[1].plays[0].pieces_played) == 2  # Pair

        # Verify turn 3
        assert turn_history[2].turn_number == 3
        assert turn_history[2].winner.player_name == "Bot 1"
        assert turn_history[2].winner.pieces_captured == 3
        assert len(turn_history[2].plays[0].pieces_played) == 3  # Triple

        # Verify cumulative captures
        assert turn_history[2].game_state_after["Bot 3"].captured == 3
        assert turn_history[2].game_state_after["Bot 1"].captured == 3

    def test_hand_state_tracking(self):
        """Test that hand states before and after plays are tracked correctly."""
        # Set up a single turn
        self.game.turn_history_this_round = []
        self.game.turn_number = 1

        # Store initial hand states
        initial_hands = {}
        for player in self.players:
            initial_hands[player.name] = player.hand.copy()

        # Create turn plays
        turn_plays = []
        for i, player in enumerate(self.players):
            # Each player plays their last SOLDIER
            pieces_to_play = [p for p in player.hand if p.kind.startswith("SOLDIER")][
                0:1
            ]
            turn_plays.append(
                TurnPlay(player=player, pieces=pieces_to_play, is_valid=True)
            )

        # Store turn with hand state info
        self.game.turn_history_this_round.append(
            {
                "turn_number": 1,
                "plays": turn_plays,
                "winner": self.players[0],
                "winner_play": turn_plays[0],
                "pieces_captured": 1,
                "initial_hands": initial_hands,
                "hands_after_play": {
                    player.name: [
                        p
                        for p in initial_hands[player.name]
                        if p not in turn_plays[i].pieces
                    ]
                    for i, player in enumerate(self.players)
                },
            }
        )

        # Extract and verify
        turn_history = self.service.extract_turn_history(self.game, 1)

        assert len(turn_history) == 1
        turn_info = turn_history[0]

        # Check Bot 1's hand tracking
        bot1_play = turn_info.plays[0]
        assert len(bot1_play.hand_before) == 8  # Started with 8 pieces
        assert len(bot1_play.hand_after) == 7  # 8 - 1 played = 7

        # Verify the played piece was removed
        played_piece = bot1_play.pieces_played[0]
        assert any(p.kind == played_piece.kind for p in bot1_play.hand_before)
        assert not any(
            p.kind == played_piece.kind and p.point == played_piece.point
            for p in bot1_play.hand_after
        )

    def test_play_type_classification(self):
        """Test that play types are correctly classified."""
        self.game.turn_history_this_round = []

        # Create different play types
        play_types_data = [
            # Single
            ([Piece("SOLDIER_RED")], "SINGLE"),
            # Pair
            ([Piece("SOLDIER_RED"), Piece("SOLDIER_RED")], "PAIR"),
            # Three of a kind
            (
                [
                    Piece("SOLDIER_BLACK"),
                    Piece("SOLDIER_BLACK"),
                    Piece("SOLDIER_BLACK"),
                ],
                "THREE_OF_A_KIND",
            ),
            # Straight
            (
                [Piece("CHARIOT_RED"), Piece("HORSE_RED"), Piece("CANNON_RED")],
                "STRAIGHT",
            ),
        ]

        for turn_num, (pieces, expected_type) in enumerate(play_types_data, 1):
            turn_plays = []
            for player in self.players:
                # First player plays the test pieces, others play matching count
                if player == self.players[0]:
                    turn_plays.append(
                        TurnPlay(player=player, pieces=pieces, is_valid=True)
                    )
                else:
                    # Others play same number of soldiers
                    match_pieces = [Piece("SOLDIER_BLACK") for _ in range(len(pieces))]
                    turn_plays.append(
                        TurnPlay(player=player, pieces=match_pieces, is_valid=True)
                    )

            self.game.turn_history_this_round.append(
                {
                    "turn_number": turn_num,
                    "plays": turn_plays,
                    "winner": self.players[0],
                    "winner_play": turn_plays[0],
                    "pieces_captured": len(pieces),
                }
            )

        # Extract and verify
        turn_history = self.service.extract_turn_history(self.game, 1)

        assert len(turn_history) == 4

        # Verify each play type
        for i, (_, expected_type) in enumerate(play_types_data):
            assert turn_history[i].plays[0].play_type == expected_type
