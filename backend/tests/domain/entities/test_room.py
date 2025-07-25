"""
Tests for the Room aggregate root.
"""

import pytest
from domain.entities.room import (
    Room, RoomStatus, RoomCreated, PlayerJoinedRoom, 
    PlayerLeftRoom, HostMigrated, RoomStatusChanged, GameStartedInRoom
)
from domain.entities.player import Player
from domain.entities.game import Game


class TestRoom:
    """Test the Room entity."""
    
    def test_create_room(self):
        """Test creating a room."""
        room = Room(room_id="room123", host_name="Alice")
        
        assert room.room_id == "room123"
        assert room.host_name == "Alice"
        assert room.max_slots == 4
        assert room.status == RoomStatus.READY  # All 4 slots filled (1 host + 3 bots)
        assert room.game is None
        
        # Check initial slots - host + 3 bots
        assert room.slots[0].name == "Alice"
        assert room.slots[0].is_bot is False
        
        for i in range(1, 4):
            assert room.slots[i].name == f"Bot {i+1}"
            assert room.slots[i].is_bot is True
        
        # Check events
        events = room.events
        assert len(events) == 6  # RoomCreated + 4 PlayerJoinedRoom + 1 RoomStatusChanged
        
        assert isinstance(events[0], RoomCreated)
        assert events[0].host_name == "Alice"
        
        # First PlayerJoinedRoom should be host
        assert isinstance(events[1], PlayerJoinedRoom)
        assert events[1].player_name == "Alice"
        assert events[1].slot_index == 0
        assert events[1].is_bot is False
    
    def test_add_player_to_empty_slot(self):
        """Test adding a player to an empty slot."""
        room = Room(room_id="room123", host_name="Alice")
        
        # Clear a slot first
        room.slots[2] = None
        room._update_room_status()  # Update status after manual slot change
        room.clear_events()
        
        # Add player
        slot = room.add_player("Bob", is_bot=False)
        
        assert slot == 2
        assert room.slots[2].name == "Bob"
        assert room.slots[2].is_bot is False
        
        # Check event - should have PlayerJoinedRoom and RoomStatusChanged
        events = room.events
        assert len(events) == 2
        assert isinstance(events[0], PlayerJoinedRoom)
        assert events[0].player_name == "Bob"
        assert events[0].slot_index == 2
    
    def test_add_player_replaces_bot(self):
        """Test that human players replace bots."""
        room = Room(room_id="room123", host_name="Alice")
        room.clear_events()
        
        # Add human player - should replace first bot
        slot = room.add_player("Bob", is_bot=False)
        
        assert slot == 1  # First bot slot
        assert room.slots[1].name == "Bob"
        assert room.slots[1].is_bot is False
    
    def test_add_player_to_specific_slot(self):
        """Test adding a player to a specific slot."""
        room = Room(room_id="room123", host_name="Alice")
        room.clear_events()
        
        # Add to specific slot
        slot = room.add_player("Carol", is_bot=False, slot=3)
        
        assert slot == 3
        assert room.slots[3].name == "Carol"
        assert room.slots[3].is_bot is False
    
    def test_cannot_add_to_occupied_human_slot(self):
        """Test that we cannot add to a slot occupied by a human."""
        room = Room(room_id="room123", host_name="Alice")
        
        with pytest.raises(ValueError, match="occupied by human player"):
            room.add_player("Bob", is_bot=False, slot=0)
    
    def test_room_becomes_ready_when_full(self):
        """Test room status changes to READY when full."""
        room = Room(room_id="room123", host_name="Alice")
        
        # Replace all bots with humans
        room.add_player("Bob", is_bot=False)
        room.add_player("Carol", is_bot=False)
        room.add_player("Dave", is_bot=False)
        
        assert room.status == RoomStatus.READY
        assert room.is_full() is True
        
        # Check status change event
        events = room.events
        status_events = [e for e in events if isinstance(e, RoomStatusChanged)]
        assert any(e.new_status == "READY" for e in status_events)
    
    def test_remove_player(self):
        """Test removing a player from room."""
        room = Room(room_id="room123", host_name="Alice")
        room.add_player("Bob", is_bot=False)
        room.clear_events()
        
        # Remove Bob
        was_host = room.remove_player("Bob")
        
        assert was_host is False
        assert room.slots[1] is None
        
        # Check event
        events = room.events
        assert len(events) >= 1
        leave_event = next(e for e in events if isinstance(e, PlayerLeftRoom))
        assert leave_event.player_name == "Bob"
        assert leave_event.slot_index == 1
        assert leave_event.was_host is False
    
    def test_host_migration_on_host_leave(self):
        """Test host migration when host leaves."""
        room = Room(room_id="room123", host_name="Alice")
        room.add_player("Bob", is_bot=False)
        room.clear_events()
        
        # Remove host
        was_host = room.remove_player("Alice")
        
        assert was_host is True
        assert room.host_name == "Bob"  # Bob becomes new host
        
        # Check events
        events = room.events
        assert any(isinstance(e, PlayerLeftRoom) for e in events)
        assert any(isinstance(e, HostMigrated) for e in events)
        
        migrate_event = next(e for e in events if isinstance(e, HostMigrated))
        assert migrate_event.old_host == "Alice"
        assert migrate_event.new_host == "Bob"
    
    def test_host_migration_to_bot(self):
        """Test host migration to bot when no humans left."""
        room = Room(room_id="room123", host_name="Alice")
        room.clear_events()
        
        # Remove host (only human)
        room.remove_player("Alice")
        
        # Host should migrate to first bot
        assert room.host_name == "Bot 2"
        assert room.status == RoomStatus.ABANDONED
    
    def test_room_abandoned_when_no_humans(self):
        """Test room becomes abandoned when all humans leave."""
        room = Room(room_id="room123", host_name="Alice")
        room.add_player("Bob", is_bot=False)
        
        # Remove all humans
        room.remove_player("Alice")
        room.remove_player("Bob")
        
        assert room.status == RoomStatus.ABANDONED
        assert room.get_human_count() == 0
    
    def test_start_game(self):
        """Test starting a game."""
        room = Room(room_id="room123", host_name="Alice")
        
        # Fill room
        room.add_player("Bob", is_bot=False)
        room.add_player("Carol", is_bot=False)
        room.add_player("Dave", is_bot=False)
        
        assert room.status == RoomStatus.READY
        
        # Start game
        game = room.start_game()
        
        assert isinstance(game, Game)
        assert room.game is game
        assert room.status == RoomStatus.IN_GAME
        assert len(game.players) == 4
        
        # Check events
        events = room.events
        assert any(isinstance(e, GameStartedInRoom) for e in events)
        
        start_event = next(e for e in events if isinstance(e, GameStartedInRoom))
        assert "Alice" in start_event.player_names
    
    def test_cannot_start_game_with_empty_slots(self):
        """Test that game cannot start with empty slots."""
        room = Room(room_id="room123", host_name="Alice")
        room.slots[2] = None  # Create empty slot
        
        with pytest.raises(ValueError, match="Cannot start with empty slots"):
            room.start_game()
    
    def test_cannot_start_game_twice(self):
        """Test that game cannot be started twice."""
        room = Room(room_id="room123", host_name="Alice")
        
        # Fill and start
        for i in range(1, 4):
            room.add_player(f"Player{i}", is_bot=False)
        
        room.start_game()
        
        with pytest.raises(ValueError, match="Game already in progress"):
            room.start_game()
    
    def test_end_game(self):
        """Test ending a game."""
        room = Room(room_id="room123", host_name="Alice")
        
        # Fill and start
        for i in range(1, 4):
            room.add_player(f"Player{i}", is_bot=False)
        
        room.start_game()
        room.clear_events()
        
        # End game
        room.end_game()
        
        assert room.status == RoomStatus.COMPLETED
        
        # Check event
        events = room.events
        assert len(events) == 1
        assert isinstance(events[0], RoomStatusChanged)
        assert events[0].old_status == "IN_GAME"
        assert events[0].new_status == "COMPLETED"
    
    def test_get_player(self):
        """Test getting player by name."""
        room = Room(room_id="room123", host_name="Alice")
        room.add_player("Bob", is_bot=False)
        
        alice = room.get_player("Alice")
        assert alice.name == "Alice"
        
        bob = room.get_player("Bob")
        assert bob.name == "Bob"
        
        eve = room.get_player("Eve")
        assert eve is None
    
    def test_get_slot_index(self):
        """Test getting slot index for player."""
        room = Room(room_id="room123", host_name="Alice")
        room.add_player("Bob", is_bot=False)
        
        assert room.get_slot_index("Alice") == 0
        assert room.get_slot_index("Bob") == 1
        assert room.get_slot_index("Eve") is None
    
    def test_is_host(self):
        """Test checking if player is host."""
        room = Room(room_id="room123", host_name="Alice")
        room.add_player("Bob", is_bot=False)
        
        assert room.is_host("Alice") is True
        assert room.is_host("Bob") is False
        assert room.is_host("Eve") is False
    
    def test_player_counts(self):
        """Test human and bot counts."""
        room = Room(room_id="room123", host_name="Alice")
        
        assert room.get_human_count() == 1
        assert room.get_bot_count() == 3
        
        room.add_player("Bob", is_bot=False)
        
        assert room.get_human_count() == 2
        assert room.get_bot_count() == 2
    
    def test_to_dict(self):
        """Test converting room to dictionary."""
        room = Room(room_id="room123", host_name="Alice")
        room.add_player("Bob", is_bot=False)
        
        data = room.to_dict()
        
        assert data["room_id"] == "room123"
        assert data["host_name"] == "Alice"
        assert data["status"] == "READY"  # Room is full after adding Bob
        assert data["human_count"] == 2
        assert data["bot_count"] == 2
        assert data["game_active"] is False
        
        # Check slots
        assert len(data["slots"]) == 4
        assert data["slots"][0]["player"]["name"] == "Alice"
        assert data["slots"][1]["player"]["name"] == "Bob"
    
    def test_event_management(self):
        """Test event management."""
        room = Room(room_id="room123", host_name="Alice")
        
        # Should have initial events
        assert len(room.events) > 0
        
        # Clear events
        room.clear_events()
        assert len(room.events) == 0
        
        # Add player should create event
        room.add_player("Bob", is_bot=False)
        assert len(room.events) == 1