# backend/domain/value_objects/test_game_state.py
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from .game_state import GameState, PlayerState, TurnState
from .game_phase import GamePhase
from ..entities.piece import Piece, PieceColor


class TestPlayerState:
    """Test PlayerState value object"""
    
    def test_player_state_creation(self):
        """PlayerState creates with correct defaults"""
        player_state = PlayerState(
            name="Alice",
            score=10,
            hand_size=5
        )
        
        assert player_state.name == "Alice"
        assert player_state.score == 10
        assert player_state.hand_size == 5
        assert player_state.pieces_played_this_turn == tuple()
        assert player_state.has_declared is False
        assert player_state.is_active_turn is False
        assert player_state.position_in_game == 0
    
    def test_player_state_immutable(self):
        """PlayerState is immutable (frozen)"""
        player_state = PlayerState(name="Alice", score=10, hand_size=5)
        
        with pytest.raises(AttributeError):
            player_state.score = 15  # Should fail - frozen dataclass
    
    def test_player_state_equality(self):
        """PlayerState has value-based equality"""
        player1 = PlayerState(name="Alice", score=10, hand_size=5)
        player2 = PlayerState(name="Alice", score=10, hand_size=5)
        player3 = PlayerState(name="Alice", score=15, hand_size=5)
        
        assert player1 == player2  # Same values = equal
        assert player1 != player3  # Different score = not equal


class TestTurnState:
    """Test TurnState value object"""
    
    def test_turn_state_creation(self):
        """TurnState creates with correct values"""
        pieces = (Piece(5, PieceColor.RED), Piece(3, PieceColor.BLACK))
        turn_state = TurnState(
            current_player_name="Alice",
            turn_number=1,
            phase=GamePhase.PLAYING,
            can_play_pieces=True,
            can_redeal=False,
            can_declare=True,
            pieces_on_table=pieces
        )
        
        assert turn_state.current_player_name == "Alice"
        assert turn_state.turn_number == 1
        assert turn_state.phase == GamePhase.PLAYING
        assert turn_state.can_play_pieces is True
        assert turn_state.can_redeal is False
        assert turn_state.can_declare is True
        assert turn_state.pieces_on_table == pieces
    
    def test_turn_state_immutable(self):
        """TurnState is immutable (frozen)"""
        turn_state = TurnState(
            current_player_name="Alice",
            turn_number=1,
            phase=GamePhase.PLAYING,
            can_play_pieces=True,
            can_redeal=False,
            can_declare=True
        )
        
        with pytest.raises(AttributeError):
            turn_state.turn_number = 2  # Should fail - frozen dataclass


class TestGameStateCreation:
    """Test GameState creation and validation"""
    
    def test_create_initial_state(self):
        """Factory method creates valid initial state"""
        game_id = uuid4()
        created_at = datetime.now()
        
        state = GameState.create_initial_state(
            game_id=game_id,
            max_players=4,
            created_at=created_at
        )
        
        assert state.game_id == game_id
        assert state.created_at == created_at
        assert state.max_players == 4
        assert state.player_count == 0
        assert state.players == tuple()
        assert state.is_game_over is False
        assert state.last_action == "Game created"
    
    def test_create_game_over_state(self):
        """Factory method creates valid game over state"""
        game_id = uuid4()
        initial_state = GameState.create_initial_state(
            game_id=game_id,
            max_players=4,
            created_at=datetime.now()
        )
        
        # Add some players to previous state
        players = (
            PlayerState(name="Alice", score=20, hand_size=0),
            PlayerState(name="Bob", score=15, hand_size=2)
        )
        previous_state = GameState(
            game_id=game_id,
            created_at=initial_state.created_at,
            max_players=4,
            players=players,
            player_count=2,
            total_turns_played=10
        )
        
        game_over_state = GameState.create_game_over_state(
            previous_state=previous_state,
            winner_name="Alice",
            reason="Player reached max score"
        )
        
        assert game_over_state.is_game_over is True
        assert game_over_state.winner_name == "Alice"
        assert game_over_state.game_over_reason == "Player reached max score"
        assert game_over_state.turn_state is None
        assert game_over_state.players == players
        assert game_over_state.total_turns_played == 10
        assert "Game ended" in game_over_state.last_action
    
    def test_game_state_validates_player_count(self):
        """GameState validates player count matches players list"""
        game_id = uuid4()
        players = (PlayerState(name="Alice", score=0, hand_size=5),)
        
        with pytest.raises(ValueError, match="Player count mismatch"):
            GameState(
                game_id=game_id,
                created_at=datetime.now(),
                max_players=4,
                players=players,
                player_count=2  # Mismatch: 1 player but count=2
            )
    
    def test_game_state_validates_max_players(self):
        """GameState validates player count doesn't exceed max"""
        game_id = uuid4()
        players = (
            PlayerState(name="Alice", score=0, hand_size=5),
            PlayerState(name="Bob", score=0, hand_size=5),
            PlayerState(name="Charlie", score=0, hand_size=5)
        )
        
        with pytest.raises(ValueError, match="Player count exceeds max players"):
            GameState(
                game_id=game_id,
                created_at=datetime.now(),
                max_players=2,  # Max 2 but 3 players
                players=players,
                player_count=3
            )
    
    def test_game_state_validates_winner_exists(self):
        """GameState validates winner is one of the players"""
        game_id = uuid4()
        players = (PlayerState(name="Alice", score=0, hand_size=5),)
        
        with pytest.raises(ValueError, match="Winner must be one of the players"):
            GameState(
                game_id=game_id,
                created_at=datetime.now(),
                max_players=4,
                players=players,
                player_count=1,
                is_game_over=True,
                winner_name="Bob"  # Bob not in players list
            )
    
    def test_game_state_validates_active_player_exists(self):
        """GameState validates current player is one of the players"""
        game_id = uuid4()
        players = (PlayerState(name="Alice", score=0, hand_size=5),)
        turn_state = TurnState(
            current_player_name="Bob",  # Bob not in players
            turn_number=1,
            phase=GamePhase.PLAYING,
            can_play_pieces=True,
            can_redeal=False,
            can_declare=False
        )
        
        with pytest.raises(ValueError, match="Active player must be one of the players"):
            GameState(
                game_id=game_id,
                created_at=datetime.now(),
                max_players=4,
                players=players,
                player_count=1,
                turn_state=turn_state
            )


class TestGameStateQueries:
    """Test GameState query methods"""
    
    def test_get_player_state(self):
        """Can retrieve specific player state"""
        players = (
            PlayerState(name="Alice", score=20, hand_size=3),
            PlayerState(name="Bob", score=15, hand_size=5)
        )
        state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=players,
            player_count=2
        )
        
        alice_state = state.get_player_state("Alice")
        bob_state = state.get_player_state("Bob")
        missing_state = state.get_player_state("Charlie")
        
        assert alice_state == players[0]
        assert bob_state == players[1]
        assert missing_state is None
    
    def test_get_current_player(self):
        """Can retrieve current player state"""
        players = (
            PlayerState(name="Alice", score=20, hand_size=3, is_active_turn=True),
            PlayerState(name="Bob", score=15, hand_size=5)
        )
        turn_state = TurnState(
            current_player_name="Alice",
            turn_number=1,
            phase=GamePhase.PLAYING,
            can_play_pieces=True,
            can_redeal=False,
            can_declare=False
        )
        state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=players,
            player_count=2,
            turn_state=turn_state
        )
        
        current_player = state.get_current_player()
        assert current_player == players[0]
        assert current_player.name == "Alice"
    
    def test_get_current_player_no_turn_state(self):
        """Returns None when no turn state exists"""
        state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=tuple(),
            player_count=0
        )
        
        assert state.get_current_player() is None
    
    def test_get_player_scores(self):
        """Returns dictionary of player scores"""
        players = (
            PlayerState(name="Alice", score=20, hand_size=3),
            PlayerState(name="Bob", score=15, hand_size=5),
            PlayerState(name="Charlie", score=25, hand_size=2)
        )
        state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=players,
            player_count=3
        )
        
        scores = state.get_player_scores()
        expected = {"Alice": 20, "Bob": 15, "Charlie": 25}
        assert scores == expected
    
    def test_get_leaderboard(self):
        """Returns players sorted by score (highest first)"""
        players = (
            PlayerState(name="Alice", score=20, hand_size=3),
            PlayerState(name="Bob", score=15, hand_size=5),
            PlayerState(name="Charlie", score=25, hand_size=2)
        )
        state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=players,
            player_count=3
        )
        
        leaderboard = state.get_leaderboard()
        expected = [("Charlie", 25), ("Alice", 20), ("Bob", 15)]
        assert leaderboard == expected


class TestGameStateComparison:
    """Test GameState comparison methods"""
    
    def test_has_scores_changed_true(self):
        """Detects when scores have changed"""
        game_id = uuid4()
        created_at = datetime.now()
        
        state1 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            players=(PlayerState(name="Alice", score=10, hand_size=5),),
            player_count=1
        )
        
        state2 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            players=(PlayerState(name="Alice", score=15, hand_size=5),),  # Score changed
            player_count=1
        )
        
        assert state1.has_scores_changed(state2) is True
    
    def test_has_scores_changed_false(self):
        """Detects when scores haven't changed"""
        game_id = uuid4()
        created_at = datetime.now()
        
        state1 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            players=(PlayerState(name="Alice", score=10, hand_size=5),),
            player_count=1
        )
        
        state2 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            players=(PlayerState(name="Alice", score=10, hand_size=3),),  # Only hand size changed
            player_count=1
        )
        
        assert state1.has_scores_changed(state2) is False
    
    def test_comparison_validates_same_game(self):
        """Comparison methods validate states are from same game"""
        state1 = GameState(
            game_id=uuid4(),  # Different game ID
            created_at=datetime.now(),
            max_players=4,
            players=tuple(),
            player_count=0
        )
        
        state2 = GameState(
            game_id=uuid4(),  # Different game ID
            created_at=datetime.now(),
            max_players=4,
            players=tuple(),
            player_count=0
        )
        
        with pytest.raises(ValueError, match="Cannot compare states from different games"):
            state1.has_scores_changed(state2)
    
    def test_has_turn_changed(self):
        """Detects when turn has changed"""
        game_id = uuid4()
        created_at = datetime.now()
        
        turn_state1 = TurnState(
            current_player_name="Alice",
            turn_number=1,
            phase=GamePhase.PLAYING,
            can_play_pieces=True,
            can_redeal=False,
            can_declare=False
        )
        
        turn_state2 = TurnState(
            current_player_name="Bob",  # Different player
            turn_number=2,  # Different turn
            phase=GamePhase.PLAYING,
            can_play_pieces=True,
            can_redeal=False,
            can_declare=False
        )
        
        state1 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            players=(PlayerState(name="Alice", score=0, hand_size=5), PlayerState(name="Bob", score=0, hand_size=5)),
            player_count=2,
            turn_state=turn_state1
        )
        
        state2 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            players=(PlayerState(name="Alice", score=0, hand_size=5), PlayerState(name="Bob", score=0, hand_size=5)),
            player_count=2,
            turn_state=turn_state2
        )
        
        assert state1.has_turn_changed(state2) is True
    
    def test_has_phase_changed(self):
        """Detects when phase has changed"""
        game_id = uuid4()
        created_at = datetime.now()
        
        turn_state1 = TurnState(
            current_player_name="Alice",
            turn_number=1,
            phase=GamePhase.PLAYING,  # Playing phase
            can_play_pieces=True,
            can_redeal=False,
            can_declare=False
        )
        
        turn_state2 = TurnState(
            current_player_name="Alice",
            turn_number=1,
            phase=GamePhase.DECLARATION,  # Declaration phase
            can_play_pieces=False,
            can_redeal=False,
            can_declare=True
        )
        
        state1 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            players=(PlayerState(name="Alice", score=0, hand_size=5),),
            player_count=1,
            turn_state=turn_state1
        )
        
        state2 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            players=(PlayerState(name="Alice", score=0, hand_size=5),),
            player_count=1,
            turn_state=turn_state2
        )
        
        assert state1.has_phase_changed(state2) is True


class TestGameStateStatus:
    """Test GameState status query methods"""
    
    def test_is_waiting_for_players(self):
        """Correctly identifies when waiting for players"""
        state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=(PlayerState(name="Alice", score=0, hand_size=5),),
            player_count=1,
            is_game_over=False
        )
        
        assert state.is_waiting_for_players() is True
        
        # Game over = not waiting
        game_over_state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=(PlayerState(name="Alice", score=0, hand_size=5),),
            player_count=1,
            is_game_over=True
        )
        
        assert game_over_state.is_waiting_for_players() is False
    
    def test_is_in_progress(self):
        """Correctly identifies when game is in progress"""
        turn_state = TurnState(
            current_player_name="Alice",
            turn_number=1,
            phase=GamePhase.PLAYING,
            can_play_pieces=True,
            can_redeal=False,
            can_declare=False
        )
        
        state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=(
                PlayerState(name="Alice", score=0, hand_size=5),
                PlayerState(name="Bob", score=0, hand_size=5)
            ),
            player_count=2,
            is_game_over=False,
            turn_state=turn_state
        )
        
        assert state.is_in_progress() is True
    
    def test_can_action_be_taken(self):
        """Correctly identifies when actions can be taken"""
        turn_state = TurnState(
            current_player_name="Alice",
            turn_number=1,
            phase=GamePhase.PLAYING,
            can_play_pieces=True,
            can_redeal=False,
            can_declare=False
        )
        
        state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=(PlayerState(name="Alice", score=0, hand_size=5),),
            player_count=1,
            turn_state=turn_state
        )
        
        assert state.can_action_be_taken() is True
        
        # No actions possible
        no_action_turn = TurnState(
            current_player_name="Alice",
            turn_number=1,
            phase=GamePhase.PLAYING,
            can_play_pieces=False,
            can_redeal=False,
            can_declare=False
        )
        
        no_action_state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=tuple(),
            player_count=0,
            turn_state=no_action_turn
        )
        
        assert no_action_state.can_action_be_taken() is False
    
    def test_get_game_duration(self):
        """Calculates game duration correctly"""
        created_at = datetime.now()
        snapshot_at = created_at + timedelta(seconds=300)  # 5 minutes later
        
        state = GameState(
            game_id=uuid4(),
            created_at=created_at,
            snapshot_at=snapshot_at,
            max_players=4,
            players=tuple(),
            player_count=0
        )
        
        assert state.get_game_duration() == 300.0


class TestGameStateImmutability:
    """Test GameState immutability"""
    
    def test_game_state_is_immutable(self):
        """GameState cannot be modified after creation"""
        state = GameState(
            game_id=uuid4(),
            created_at=datetime.now(),
            max_players=4,
            players=tuple(),
            player_count=0
        )
        
        with pytest.raises(AttributeError):
            state.player_count = 5  # Should fail - frozen dataclass
    
    def test_game_state_equality(self):
        """GameState has value-based equality"""
        game_id = uuid4()
        created_at = datetime.now()
        snapshot_at = datetime.now()  # Use same timestamp for both
        
        state1 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            snapshot_at=snapshot_at,  # Explicit timestamp to avoid microsecond differences
            players=tuple(),
            player_count=0
        )
        
        state2 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            snapshot_at=snapshot_at,  # Same timestamp
            players=tuple(),
            player_count=0
        )
        
        state3 = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=6,  # Different max_players
            snapshot_at=snapshot_at,
            players=tuple(),
            player_count=0
        )
        
        assert state1 == state2  # Same values = equal
        assert state1 != state3  # Different max_players = not equal
    
    def test_game_state_to_dict(self):
        """to_dict exports state correctly"""
        game_id = uuid4()
        created_at = datetime.now()
        players = (PlayerState(name="Alice", score=10, hand_size=5),)
        
        state = GameState(
            game_id=game_id,
            created_at=created_at,
            max_players=4,
            players=players,
            player_count=1,
            last_action="Player joined"
        )
        
        data = state.to_dict()
        
        assert data["game_id"] == str(game_id)
        assert data["max_players"] == 4
        assert data["player_count"] == 1
        assert len(data["players"]) == 1
        assert data["players"][0]["name"] == "Alice"
        assert data["last_action"] == "Player joined"
        assert "game_duration_seconds" in data