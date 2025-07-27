"""
Unit tests for the event-to-broadcast mapper.

Tests the mapping of domain events to WebSocket broadcast formats.
"""

import pytest
from typing import Dict, Any
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from domain.events.base import EventMetadata
from domain.events.all_events import (
    RoomCreated, PlayerJoinedRoom, GameStarted, PhaseChanged,
    PiecesPlayed, TurnWinnerDetermined, ScoresCalculated,
    ConnectionHeartbeat, InvalidActionAttempted, RoomListUpdated
)
from infrastructure.events.event_broadcast_mapper import (
    EventBroadcastMapper, BroadcastInfo
)


class TestEventBroadcastMapper:
    """Test the EventBroadcastMapper functionality."""
    
    @pytest.fixture
    def mapper(self):
        """Create a mapper with test mappings."""
        mapper = EventBroadcastMapper()
        
        # Register some test mappings
        mapper.register(
            RoomCreated,
            "room_created",
            "response",
            lambda e, ctx: {
                "room_id": e.room_id,
                "host_name": e.host_name,
                "success": True
            }
        )
        
        mapper.register(
            PlayerJoinedRoom,
            "room_update",
            "room",
            lambda e, ctx: {
                "players": ctx.get("room_state", {}).get("players", []),
                "host_name": ctx.get("room_state", {}).get("host_name", "")
            },
            requires_state=True
        )
        
        mapper.register(
            InvalidActionAttempted,
            "error",
            "player",
            lambda e, ctx: {
                "message": e.reason,
                "action": e.action,
                "type": "invalid_action"
            }
        )
        
        return mapper
    
    @pytest.fixture
    def sample_context(self):
        """Create sample context for testing."""
        return {
            "room_state": {
                "room_id": "room123",
                "players": [
                    {"name": "Alice", "slot": "P1"},
                    {"name": "Bob", "slot": "P2"}
                ],
                "host_name": "Alice"
            },
            "timestamp": datetime.utcnow().timestamp()
        }
    
    def test_map_simple_event(self, mapper):
        """Test mapping a simple event without context."""
        metadata = EventMetadata(user_id="test_user")
        event = RoomCreated(
            room_id="room456",
            host_name="Charlie",
            metadata=metadata
        )
        
        result = mapper.map_event(event)
        
        assert result is not None
        assert result['event_name'] == "room_created"
        assert result['target_type'] == "response"
        assert result['target_id'] is None
        assert result['data'] == {
            "room_id": "room456",
            "host_name": "Charlie",
            "success": True
        }
    
    def test_map_event_with_context(self, mapper, sample_context):
        """Test mapping an event that requires context."""
        metadata = EventMetadata(user_id="test_user")
        event = PlayerJoinedRoom(
            room_id="room123",
            player_name="Carol",
            slot=3,
            metadata=metadata
        )
        
        result = mapper.map_event(event, sample_context)
        
        assert result is not None
        assert result['event_name'] == "room_update"
        assert result['target_type'] == "room"
        assert result['target_id'] == "room123"
        assert result['data']['players'] == sample_context['room_state']['players']
        assert result['data']['host_name'] == "Alice"
    
    def test_map_event_without_required_context(self, mapper):
        """Test mapping an event that requires context but none provided."""
        metadata = EventMetadata(user_id="test_user")
        event = PlayerJoinedRoom(
            room_id="room123",
            player_name="Carol",
            slot=3,
            metadata=metadata
        )
        
        # Should still work but with empty data
        result = mapper.map_event(event, {})
        
        assert result is not None
        assert result['data']['players'] == []
        assert result['data']['host_name'] == ""
    
    def test_map_unmapped_event(self, mapper):
        """Test mapping an event with no registered mapping."""
        metadata = EventMetadata(user_id="test_user")
        event = GameStarted(
            room_id="room123",
            round_number=1,
            starter_player="Alice",
            metadata=metadata
        )
        
        result = mapper.map_event(event)
        
        assert result is None
    
    def test_map_error_event(self, mapper):
        """Test mapping an error event."""
        metadata = EventMetadata(user_id="player123")
        event = InvalidActionAttempted(
            player_id="player123",
            action="play_pieces",
            reason="Not your turn",
            metadata=metadata
        )
        
        result = mapper.map_event(event)
        
        assert result is not None
        assert result['event_name'] == "error"
        assert result['target_type'] == "player"
        assert result['target_id'] == "player123"
        assert result['data'] == {
            "message": "Not your turn",
            "action": "play_pieces",
            "type": "invalid_action"
        }
    
    def test_custom_target_id_extractor(self, mapper):
        """Test custom target ID extraction."""
        def custom_extractor(event):
            return f"custom_{event.room_id}"
        
        mapper.register(
            GameStarted,
            "game_started",
            "room",
            lambda e, ctx: {"round": e.round_number},
            target_id_extractor=custom_extractor
        )
        
        metadata = EventMetadata(user_id="test")
        event = GameStarted(
            room_id="room789",
            round_number=1,
            starter_player="Alice",
            metadata=metadata
        )
        
        result = mapper.map_event(event)
        
        assert result['target_id'] == "custom_room789"
    
    def test_mapper_error_handling(self, mapper):
        """Test mapper handles errors gracefully."""
        # Register a mapper that throws an error
        mapper.register(
            PhaseChanged,
            "phase_change",
            "room",
            lambda e, ctx: {
                "error": 1 / 0  # This will raise ZeroDivisionError
            }
        )
        
        metadata = EventMetadata(user_id="test")
        event = PhaseChanged(
            room_id="room123",
            old_phase="PREPARATION",
            new_phase="DECLARATION",
            metadata=metadata
        )
        
        # Should return None on error
        result = mapper.map_event(event)
        assert result is None
    
    def test_get_registered_events(self, mapper):
        """Test getting list of registered event types."""
        registered = mapper.get_registered_events()
        
        assert RoomCreated in registered
        assert PlayerJoinedRoom in registered
        assert InvalidActionAttempted in registered
        assert GameStarted not in registered  # Not registered in fixture
    
    def test_complex_mapping_function(self, mapper):
        """Test a complex mapping function with multiple data transformations."""
        def complex_mapper(event: PiecesPlayed, context: Dict[str, Any]) -> Dict[str, Any]:
            # Complex transformation logic
            pieces_remaining = 8 - len(event.pieces)
            is_last_play = pieces_remaining == 0
            
            return {
                "player": event.player_name,
                "pieces_played": event.pieces,
                "pieces_count": len(event.pieces),
                "pieces_remaining": pieces_remaining,
                "is_last_play": is_last_play,
                "turn_number": context.get("turn_number", 0),
                "timestamp": context.get("timestamp", 0)
            }
        
        mapper.register(
            PiecesPlayed,
            "turn_played",
            "room",
            complex_mapper
        )
        
        metadata = EventMetadata(user_id="player1")
        event = PiecesPlayed(
            room_id="room123",
            player_name="Alice",
            pieces=["piece1", "piece2", "piece3"],
            metadata=metadata
        )
        
        context = {
            "turn_number": 5,
            "timestamp": 1234567890
        }
        
        result = mapper.map_event(event, context)
        
        assert result is not None
        assert result['data']['player'] == "Alice"
        assert result['data']['pieces_count'] == 3
        assert result['data']['pieces_remaining'] == 5
        assert result['data']['is_last_play'] is False
        assert result['data']['turn_number'] == 5


class TestBroadcastInfoValidation:
    """Test BroadcastInfo structure and validation."""
    
    def test_broadcast_info_structure(self):
        """Test the BroadcastInfo TypedDict structure."""
        info: BroadcastInfo = {
            'event_name': 'test_event',
            'data': {'key': 'value'},
            'target_type': 'room',
            'target_id': 'room123'
        }
        
        # Should have all required fields
        assert 'event_name' in info
        assert 'data' in info
        assert 'target_type' in info
        assert 'target_id' in info
    
    def test_target_types(self):
        """Test valid target types."""
        valid_types = ['room', 'player', 'lobby', 'response']
        
        for target_type in valid_types:
            info: BroadcastInfo = {
                'event_name': 'test',
                'data': {},
                'target_type': target_type,
                'target_id': None
            }
            assert info['target_type'] in valid_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])