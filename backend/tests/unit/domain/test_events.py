# tests/unit/domain/test_events.py
"""
Unit tests for domain events.
"""

import pytest
from datetime import datetime

from domain.events.base import DomainEvent, AggregateEvent
from domain.events.game_events import (
    GameStartedEvent,
    TurnPlayedEvent,
    PhaseChangedEvent,
    RoundEndedEvent
)
from domain.events.player_events import (
    PlayerJoinedEvent,
    PlayerLeftEvent,
    HostTransferredEvent
)


class TestDomainEvents:
    """Test domain event functionality."""
    
    def test_domain_event_creation(self):
        """Test basic domain event creation."""
        event = DomainEvent(
            data={"key": "value"}
        )
        
        assert event.event_id is not None
        assert isinstance(event.timestamp, datetime)
        assert event.data == {"key": "value"}
        assert event.version == 1
    
    def test_aggregate_event_creation(self):
        """Test aggregate event creation."""
        event = AggregateEvent(
            aggregate_id="game-123",
            aggregate_type="Game",
            data={"action": "started"}
        )
        
        assert event.aggregate_id == "game-123"
        assert event.aggregate_type == "Game"
        assert event.aggregate_version == 0
        assert event.data == {"action": "started"}
    
    def test_game_started_event(self):
        """Test GameStartedEvent creation."""
        players = [
            {"name": "Player1", "is_bot": False},
            {"name": "Player2", "is_bot": False}
        ]
        
        event = GameStartedEvent(
            aggregate_id="game-123",
            players=players,
            initial_phase="PREPARATION"
        )
        
        assert event.aggregate_id == "game-123"
        assert event.aggregate_type == "Game"
        assert event.data["players"] == players
        assert event.data["initial_phase"] == "PREPARATION"
    
    def test_turn_played_event(self):
        """Test TurnPlayedEvent creation."""
        event = TurnPlayedEvent(
            aggregate_id="game-123",
            player="Player1",
            pieces=[3, 3],
            turn_number=5
        )
        
        assert event.data["player"] == "Player1"
        assert event.data["pieces"] == [3, 3]
        assert event.data["turn_number"] == 5
    
    def test_phase_changed_event(self):
        """Test PhaseChangedEvent creation."""
        phase_data = {"current_player": "Player1"}
        
        event = PhaseChangedEvent(
            aggregate_id="game-123",
            old_phase="DECLARATION",
            new_phase="TURN",
            phase_data=phase_data
        )
        
        assert event.data["old_phase"] == "DECLARATION"
        assert event.data["new_phase"] == "TURN"
        assert event.data["phase_data"] == phase_data
    
    def test_round_ended_event(self):
        """Test RoundEndedEvent creation."""
        scores = {"Player1": 10, "Player2": -5}
        total_scores = {"Player1": 30, "Player2": 15}
        
        event = RoundEndedEvent(
            aggregate_id="game-123",
            round_number=3,
            scores=scores,
            total_scores=total_scores
        )
        
        assert event.data["round_number"] == 3
        assert event.data["scores"] == scores
        assert event.data["total_scores"] == total_scores
    
    def test_player_joined_event(self):
        """Test PlayerJoinedEvent creation."""
        player_data = {"name": "Player3", "is_bot": False}
        all_players = [
            {"name": "Player1"},
            {"name": "Player2"},
            {"name": "Player3"}
        ]
        
        event = PlayerJoinedEvent(
            aggregate_id="room-123",
            player=player_data,
            players=all_players
        )
        
        assert event.aggregate_type == "Room"
        assert event.data["player"] == player_data
        assert event.data["players"] == all_players
    
    def test_player_left_event(self):
        """Test PlayerLeftEvent creation."""
        event = PlayerLeftEvent(
            aggregate_id="room-123",
            player="Player2",
            reason="disconnected",
            replacement="Bot2"
        )
        
        assert event.data["player"] == "Player2"
        assert event.data["reason"] == "disconnected"
        assert event.data["replacement"] == "Bot2"
    
    def test_host_transferred_event(self):
        """Test HostTransferredEvent creation."""
        event = HostTransferredEvent(
            aggregate_id="room-123",
            old_host="Player1",
            new_host="Player2",
            reason="host_left"
        )
        
        assert event.data["old_host"] == "Player1"
        assert event.data["new_host"] == "Player2"
        assert event.data["reason"] == "host_left"
    
    def test_event_equality(self):
        """Test event equality based on event_id."""
        event1 = DomainEvent(data={"test": 1})
        event2 = DomainEvent(data={"test": 1})
        
        # Different events even with same data
        assert event1 != event2
        assert event1.event_id != event2.event_id
        
        # Same event
        assert event1 == event1
    
    def test_event_string_representation(self):
        """Test event string representation."""
        event = GameStartedEvent(
            aggregate_id="game-123",
            players=[],
            initial_phase="PREPARATION"
        )
        
        str_repr = str(event)
        assert "GameStartedEvent" in str_repr
        assert "game-123" in str_repr