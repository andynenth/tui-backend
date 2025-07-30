"""
Tests for the Game entity.
"""

import pytest
from domain.entities.game import Game, GamePhase, WinConditionType, TurnPlay
from domain.entities.player import Player
from domain.value_objects.piece import Piece
from domain.events.game_events import (
    GameStarted,
    GameEnded,
    RoundStarted,
    RoundCompleted,
    PhaseChanged,
    TurnStarted,
    TurnCompleted,
    TurnWinnerDetermined,
    PiecesDealt,
    WeakHandDetected,
    RedealExecuted,
)


class TestGame:
    """Test the Game entity."""

    def create_test_players(self, names=None):
        """Create test players."""
        if names is None:
            names = ["Alice", "Bob", "Carol", "Dave"]
        return [Player(name=name) for name in names]

    def test_create_game(self):
        """Test creating a game."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        assert game.room_id == "room123"
        assert len(game.players) == 4
        assert game.win_condition_type == WinConditionType.FIRST_TO_REACH_50
        assert game.max_score == 50
        assert game.max_rounds == 20
        assert game.round_number == 1
        assert game.turn_number == 0
        assert game.current_phase == GamePhase.NOT_STARTED

    def test_start_game(self):
        """Test starting a game."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        game.start_game()

        assert game.current_phase == GamePhase.PREPARATION

        # Check events
        events = game.events
        assert len(events) == 2

        # GameStarted event
        assert isinstance(events[0], GameStarted)
        assert events[0].player_names == ["Alice", "Bob", "Carol", "Dave"]
        assert events[0].win_condition == "FIRST_TO_REACH_50"

        # PhaseChanged event
        assert isinstance(events[1], PhaseChanged)
        assert events[1].old_phase == "NOT_STARTED"
        assert events[1].new_phase == "PREPARATION"

    def test_cannot_start_game_twice(self):
        """Test that game cannot be started twice."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        game.start_game()

        with pytest.raises(ValueError, match="Game already started"):
            game.start_game()

    def test_start_round(self):
        """Test starting a round."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        game.start_round()

        # Each player should have 8 pieces
        for player in game.players:
            assert len(player.hand) == 8

        # Check events
        events = game.events
        assert any(isinstance(e, RoundStarted) for e in events)
        assert any(isinstance(e, PiecesDealt) for e in events)

        # Should have determined round starter
        assert game.round_starter is not None

    def test_first_round_starter(self):
        """Test that player with red general starts first round."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Give red general to Bob
        players[1].hand = [Piece.create("GENERAL_RED")]

        game.round_number = 1
        game.start_round()

        # Bob should be the starter (but pieces will be redealt)
        # Need to find who got red general after dealing
        red_general_player = None
        for player in game.players:
            if player.has_red_general():
                red_general_player = player.name
                break

        assert game.round_starter == red_general_player

    def test_weak_hand_detection(self):
        """Test weak hand detection."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Give Alice a weak hand (all pieces <= 9 points)
        players[0].hand = [
            Piece.create("SOLDIER_RED"),
            Piece.create("SOLDIER_BLACK"),
            Piece.create("CANNON_RED"),
            Piece.create("CANNON_BLACK"),
        ]

        # Give Bob a strong hand
        players[1].hand = [Piece.create("GENERAL_RED"), Piece.create("ADVISOR_RED")]

        # Give Carol and Dave strong hands too
        players[2].hand = [Piece.create("ELEPHANT_RED")]
        players[3].hand = [
            Piece.create("ELEPHANT_RED")
        ]  # Changed from CHARIOT_BLACK (7 points) to ELEPHANT_RED (10 points)

        weak_players = game.get_weak_hand_players()

        assert len(weak_players) == 1
        assert weak_players[0]["name"] == "Alice"
        assert weak_players[0]["hand_strength"] == 10  # 2+1+4+3

    def test_redeal_execution(self):
        """Test executing a redeal."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Give players some hands
        for player in players:
            player.hand = [Piece.create("SOLDIER_RED")] * 4

        initial_multiplier = game.redeal_multiplier

        game.execute_redeal(acceptors=["Alice", "Bob"], decliners=["Carol", "Dave"])

        # Multiplier should increase
        assert game.redeal_multiplier == initial_multiplier + 0.5

        # New starter should be first decliner
        assert game.round_starter == "Carol"

        # Check event
        events = game.events
        redeal_event = next(e for e in events if isinstance(e, RedealExecuted))
        assert redeal_event.acceptors == ["Alice", "Bob"]
        assert redeal_event.decliners == ["Carol", "Dave"]
        assert redeal_event.new_starter_name == "Carol"

    def test_phase_changes(self):
        """Test changing game phases."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        game.change_phase(GamePhase.DECLARATION)
        assert game.current_phase == GamePhase.DECLARATION

        game.change_phase(GamePhase.TURN)
        assert game.current_phase == GamePhase.TURN

        # Check events
        events = game.events
        phase_events = [e for e in events if isinstance(e, PhaseChanged)]
        assert len(phase_events) == 2
        assert phase_events[0].new_phase == "DECLARATION"
        assert phase_events[1].new_phase == "TURN"

    def test_all_players_declared(self):
        """Test checking if all players have declared."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        assert game.all_players_declared() is False

        # Make declarations
        for i, player in enumerate(players):
            player.declare_piles(i + 1, room_id="room123")

        assert game.all_players_declared() is True

    def test_get_player(self):
        """Test getting player by name."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        alice = game.get_player("Alice")
        assert alice.name == "Alice"

        with pytest.raises(ValueError, match="Player 'Eve' not found"):
            game.get_player("Eve")

    def test_player_order(self):
        """Test getting player order from specific player."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        order = game.get_player_order_from("Carol")
        assert order == ["Carol", "Dave", "Alice", "Bob"]

        order = game.get_player_order_from("Alice")
        assert order == ["Alice", "Bob", "Carol", "Dave"]

    def test_start_turn(self):
        """Test starting a turn."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)
        game.round_starter = "Bob"

        game.start_turn()

        assert game.turn_number == 1
        assert len(game.current_turn_plays) == 0
        assert game.required_piece_count is None
        assert game.turn_order == ["Bob", "Carol", "Dave", "Alice"]

        # Check event
        events = game.events
        turn_event = next(e for e in events if isinstance(e, TurnStarted))
        assert turn_event.turn_number == 1
        assert turn_event.turn_order == ["Bob", "Carol", "Dave", "Alice"]

    def test_play_turn(self):
        """Test playing a turn."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Give Alice some pieces
        alice = players[0]
        alice.hand = [
            Piece.create("GENERAL_RED"),
            Piece.create("SOLDIER_BLACK"),
            Piece.create("HORSE_RED"),
        ]

        # Play turn
        turn_play = game.play_turn("Alice", [0, 2])  # Play GENERAL_RED and HORSE_RED

        assert turn_play.player_name == "Alice"
        assert len(turn_play.pieces) == 2
        assert turn_play.pieces[0].kind == "GENERAL_RED"
        assert turn_play.pieces[1].kind == "HORSE_RED"
        assert turn_play.total_points == 20  # 14 + 6

        # Required piece count should be set
        assert game.required_piece_count == 2

        # Alice should have only SOLDIER_BLACK left
        assert len(alice.hand) == 1
        assert alice.hand[0].kind == "SOLDIER_BLACK"

    def test_invalid_play_turn(self):
        """Test invalid turn plays."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        alice = players[0]
        alice.hand = [Piece.create("GENERAL_RED")]

        # Invalid index
        with pytest.raises(ValueError, match="Invalid piece indices"):
            game.play_turn("Alice", [5])

        # Set required piece count
        game.required_piece_count = 2

        # Wrong number of pieces
        with pytest.raises(ValueError, match="Must play 2 pieces"):
            game.play_turn("Alice", [0])

    def test_complete_turn(self):
        """Test completing a full turn."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Give each player some pieces
        for i, player in enumerate(players):
            player.hand = [Piece.create(f"SOLDIER_{'RED' if i % 2 == 0 else 'BLACK'}")]

        # Each player plays their piece
        for player in players:
            game.play_turn(player.name, [0])

        # Turn should be complete
        assert game.last_turn_winner is not None

        # Winner should have captured a pile
        winner = game.get_player(game.last_turn_winner)
        assert winner.captured_piles == 1

        # Check events
        events = game.events
        assert any(isinstance(e, TurnWinnerDetermined) for e in events)
        assert any(isinstance(e, TurnCompleted) for e in events)

    def test_turn_play_comparison(self):
        """Test TurnPlay comparison."""
        play1 = TurnPlay(
            player_name="Alice",
            pieces=[Piece.create("GENERAL_RED"), Piece.create("ADVISOR_RED")],
        )

        play2 = TurnPlay(
            player_name="Bob",
            pieces=[Piece.create("SOLDIER_RED"), Piece.create("SOLDIER_BLACK")],
        )

        assert play1.beats(play2) is True
        assert play2.beats(play1) is False

        # Different piece counts
        play3 = TurnPlay(player_name="Carol", pieces=[Piece.create("GENERAL_RED")])
        assert play1.beats(play3) is False  # Different counts

    def test_round_completion(self):
        """Test completing a round."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Set up some state
        players[0].declared_piles = 3
        players[0].captured_piles = 3  # Perfect round
        players[1].declared_piles = 2
        players[1].captured_piles = 1

        initial_round = game.round_number

        scores = {"Alice": 15, "Bob": -5, "Carol": 10, "Dave": 0}

        game.complete_round(scores)

        # Round number should increment
        assert game.round_number == initial_round + 1
        assert game.turn_number == 0
        assert game.redeal_multiplier == 1.0

        # Scores should be updated
        assert players[0].score == 15
        assert players[1].score == -5

        # Perfect round should be recorded
        assert players[0].stats.perfect_rounds == 1

        # Last round winner should be set
        assert game.last_round_winner == "Alice"

        # Players should be reset
        for player in players:
            assert player.declared_piles == 0
            assert player.captured_piles == 0
            assert len(player.hand) == 0

        # Check event
        events = game.events
        round_event = next(e for e in events if isinstance(e, RoundCompleted))
        assert round_event.round_scores == scores
        assert round_event.round_winner == "Alice"

    def test_is_round_complete(self):
        """Test checking if round is complete."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Give players pieces
        for player in players:
            player.hand = [Piece.create("SOLDIER_RED")]

        assert game.is_round_complete() is False

        # Empty all hands
        for player in players:
            player.hand = []

        assert game.is_round_complete() is True

    def test_game_over_by_score(self):
        """Test game over by score limit."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        assert game.is_game_over() is False

        # Give Alice winning score
        players[0].score = 50

        assert game.is_game_over() is True
        assert game.get_winner() == "Alice"

    def test_game_over_by_rounds(self):
        """Test game over by round limit."""
        players = self.create_test_players()
        game = Game(
            room_id="room123",
            players=players,
            win_condition_type=WinConditionType.HIGHEST_AFTER_20_ROUNDS,
        )

        assert game.is_game_over() is False

        # Set round beyond limit
        game.round_number = 21

        assert game.is_game_over() is True

        # Give Bob highest score
        players[1].score = 45
        players[0].score = 40

        assert game.get_winner() == "Bob"

    def test_game_over_tie(self):
        """Test game over with tie."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Give two players same winning score
        players[0].score = 50
        players[1].score = 50

        assert game.is_game_over() is True
        assert game.get_winner() is None  # Tie

    def test_end_game(self):
        """Test ending the game."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Cannot end if not over
        with pytest.raises(ValueError, match="Game is not over yet"):
            game.end_game()

        # Make game over
        players[0].score = 50
        game.end_game()

        assert game.current_phase == GamePhase.GAME_OVER

        # Check event
        events = game.events
        end_event = next(e for e in events if isinstance(e, GameEnded))
        assert end_event.winner_name == "Alice"
        assert end_event.final_scores["Alice"] == 50
        assert end_event.end_reason == "score_limit"

    def test_to_dict(self):
        """Test converting game to dictionary."""
        players = self.create_test_players()
        game = Game(
            room_id="room123",
            players=players,
            win_condition_type=WinConditionType.HIGHEST_AFTER_20_ROUNDS,
        )

        game.round_number = 5
        game.turn_number = 3
        game.current_phase = GamePhase.TURN
        game.round_starter = "Bob"
        game.last_round_winner = "Carol"

        data = game.to_dict()

        assert data["room_id"] == "room123"
        assert len(data["players"]) == 4
        assert data["win_condition_type"] == "HIGHEST_AFTER_20_ROUNDS"
        assert data["round_number"] == 5
        assert data["turn_number"] == 3
        assert data["current_phase"] == "TURN"
        assert data["round_starter"] == "Bob"
        assert data["last_round_winner"] == "Carol"

    def test_event_management(self):
        """Test event management."""
        players = self.create_test_players()
        game = Game(room_id="room123", players=players)

        # Should start with no events
        assert len(game.events) == 0

        # Do some actions
        game.start_game()
        game.change_phase(GamePhase.DECLARATION)

        # Should have events
        events = game.events
        assert len(events) == 3  # GameStarted, PhaseChanged x2

        # Events should be copies
        events.append("dummy")
        assert len(game.events) == 3  # Original unchanged

        # Clear events
        game.clear_events()
        assert len(game.events) == 0
