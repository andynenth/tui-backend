# backend/domain/entities/test_room.py
import pytest

from .room import Room, RoomStatus
from .player import Player


class TestRoomCreation:
    """Test room creation and initialization"""
    
    def test_room_created_with_defaults(self):
        """Room should initialize with sensible defaults"""
        room = Room()
        
        assert room.room_id is not None
        assert room.max_players == 4
        assert room.players == []
        assert room.status == RoomStatus.WAITING
        assert room.current_game is None
        assert room.creator_name == ""
    
    def test_room_created_with_custom_values(self):
        """Room should accept custom configuration"""
        from uuid import uuid4
        room_id = uuid4()
        room = Room(room_id=room_id, max_players=6)
        
        assert room.room_id == room_id
        assert room.max_players == 6
        assert room.status == RoomStatus.WAITING
    
    def test_room_validates_min_players(self):
        """Room must allow at least 2 players"""
        with pytest.raises(ValueError, match="at least 2 players"):
            Room(max_players=1)
    
    def test_room_validates_max_players(self):
        """Room cannot exceed 8 players"""
        with pytest.raises(ValueError, match="cannot exceed 8 players"):
            Room(max_players=9)


class TestPlayerManagement:
    """Test player addition and removal"""
    
    def test_add_first_player_sets_creator(self):
        """First player added becomes room creator"""
        room = Room(max_players=4)
        player = Player(name="Alice")
        
        result = room.add_player(player)
        
        assert result is True
        assert len(room.players) == 1
        assert room.creator_name == "Alice"
        assert room.status == RoomStatus.WAITING
    
    def test_add_player_until_full(self):
        """Room should transition to FULL when max players reached"""
        room = Room(max_players=2)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        assert room.status == RoomStatus.WAITING
        
        room.add_player(bob)
        assert room.status == RoomStatus.FULL
        assert len(room.players) == 2
    
    def test_cannot_add_player_when_full(self):
        """Cannot add players beyond max capacity"""
        room = Room(max_players=2)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        charlie = Player(name="Charlie")
        
        room.add_player(alice)
        room.add_player(bob)
        
        result = room.add_player(charlie)
        assert result is False
        assert len(room.players) == 2
    
    def test_cannot_add_duplicate_player_names(self):
        """Cannot add players with same name"""
        room = Room(max_players=4)
        alice1 = Player(name="Alice")
        alice2 = Player(name="Alice")  # Same name, should fail
        
        room.add_player(alice1)
        
        with pytest.raises(ValueError, match="Alice already in room"):
            room.add_player(alice2)
    
    def test_cannot_add_player_during_game(self):
        """Cannot add players when game is in progress"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        charlie = Player(name="Charlie")
        
        room.add_player(alice)
        room.add_player(bob)
        room.start_game()  # This sets status to IN_GAME
        
        with pytest.raises(ValueError, match="Cannot add players when room is in_game"):
            room.add_player(charlie)
    
    def test_remove_player_success(self):
        """Successfully remove a player from room"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        
        result = room.remove_player("Alice")
        
        assert result is True
        assert len(room.players) == 1
        assert room.players[0].name == "Bob"
    
    def test_remove_nonexistent_player(self):
        """Removing non-existent player returns False"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        room.add_player(alice)
        
        result = room.remove_player("Bob")
        assert result is False
        assert len(room.players) == 1
    
    def test_remove_creator_transfers_ownership(self):
        """When creator leaves, ownership transfers to next player"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)  # Alice becomes creator
        room.add_player(bob)
        
        room.remove_player("Alice")
        
        assert room.creator_name == "Bob"
        assert len(room.players) == 1
    
    def test_remove_last_player_abandons_room(self):
        """Removing last player (creator) abandons room"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        room.add_player(alice)
        
        room.remove_player("Alice")
        
        assert room.status == RoomStatus.ABANDONED
        assert len(room.players) == 0
    
    def test_remove_player_transitions_from_full_to_waiting(self):
        """Room transitions from FULL back to WAITING when player leaves"""
        room = Room(max_players=2)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        assert room.status == RoomStatus.FULL
        
        room.remove_player("Bob")
        assert room.status == RoomStatus.WAITING
    
    def test_cannot_remove_player_during_game(self):
        """Cannot remove players during active game"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        room.start_game()
        
        with pytest.raises(ValueError, match="Cannot remove players during active game"):
            room.remove_player("Alice")


class TestGameLifecycle:
    """Test game starting, running, and finishing"""
    
    def test_can_start_game_with_min_players(self):
        """Can start game with minimum 2 players"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        
        assert room.can_start_game() is True
    
    def test_cannot_start_game_with_one_player(self):
        """Cannot start game with only 1 player"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        room.add_player(alice)
        
        assert room.can_start_game() is False
    
    def test_start_game_creates_game_instance(self):
        """Starting game creates Game instance with all players"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        
        game = room.start_game()
        
        assert game is not None
        assert room.current_game == game
        assert len(game.players) == 2
        assert room.status == RoomStatus.IN_GAME
    
    def test_cannot_start_game_when_already_active(self):
        """Cannot start new game when one is already active"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        room.start_game()
        
        assert room.can_start_game() is False
        with pytest.raises(ValueError, match="Cannot start game"):
            room.start_game()
    
    def test_finish_game_updates_status(self):
        """Finishing game updates room status"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        game = room.start_game()
        
        # Simulate game completion by setting game phase to finished
        # This is a simple approach for testing
        from ..value_objects.game_phase import GamePhase
        game.phase = GamePhase.FINISHED
        
        room.finish_game()
        assert room.status == RoomStatus.FINISHED
    
    def test_cannot_finish_non_existent_game(self):
        """Cannot finish game when none exists"""
        room = Room(max_players=4)
        
        with pytest.raises(ValueError, match="No active game to finish"):
            room.finish_game()
    
    def test_cannot_finish_active_game(self):
        """Cannot finish game that is still active"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        room.start_game()
        
        # Game is still active, not finished
        with pytest.raises(ValueError, match="Cannot finish game that is still active"):
            room.finish_game()
    
    def test_reset_for_new_game(self):
        """Can reset room after game finishes"""
        room = Room(max_players=2)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        game = room.start_game()
        
        # Simulate game completion
        from ..value_objects.game_phase import GamePhase
        game.phase = GamePhase.FINISHED
        room.finish_game()
        
        room.reset_for_new_game()
        
        assert room.current_game is None
        assert room.status == RoomStatus.FULL  # 2 players in 2-player room
        assert len(room.players) == 2  # Players stay in room


class TestRoomQueries:
    """Test room information queries"""
    
    def test_is_waiting_for_players(self):
        """Correctly identifies when room is waiting for players"""
        room = Room(max_players=3)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        assert room.is_waiting_for_players() is True
        
        room.add_player(alice)
        assert room.is_waiting_for_players() is True
        
        room.add_player(bob)
        assert room.is_waiting_for_players() is True
        
        charlie = Player(name="Charlie")
        room.add_player(charlie)  # Now full
        assert room.is_waiting_for_players() is False
    
    def test_is_full(self):
        """Correctly identifies when room is full"""
        room = Room(max_players=2)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        assert room.is_full() is False
        
        room.add_player(alice)
        assert room.is_full() is False
        
        room.add_player(bob)
        assert room.is_full() is True
    
    def test_is_active_game(self):
        """Correctly identifies when room has active game"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        
        assert room.is_active_game() is False
        
        room.start_game()
        assert room.is_active_game() is True
    
    def test_get_player_names(self):
        """Returns list of all player names"""
        room = Room(max_players=4)
        alice = Player(name="Alice")
        bob = Player(name="Bob")
        
        room.add_player(alice)
        room.add_player(bob)
        
        names = room.get_player_names()
        assert names == ["Alice", "Bob"]
    
    def test_get_room_info(self):
        """Returns comprehensive room information"""
        room = Room(max_players=3)
        alice = Player(name="Alice")
        room.add_player(alice)
        
        info = room.get_room_info()
        
        assert info["room_id"] == str(room.room_id)
        assert info["status"] == "waiting"
        assert info["player_count"] == 1
        assert info["max_players"] == 3
        assert info["players"] == ["Alice"]
        assert info["creator"] == "Alice"
        assert info["has_active_game"] is False
        assert info["can_start_game"] is False  # Need 2+ players
        assert info["is_accepting_players"] is True