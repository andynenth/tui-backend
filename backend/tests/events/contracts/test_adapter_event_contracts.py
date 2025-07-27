"""
Contract tests for event-based adapters.

These tests verify that event-based adapters produce the same outputs
as the original direct adapters, ensuring 100% compatibility.
"""

import pytest
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Import both direct and event-based adapters
from api.adapters.connection_adapters import (
    PingAdapter, ClientReadyAdapter, AckAdapter, SyncRequestAdapter
)
from api.adapters.connection_adapters_event import (
    PingAdapterEvent, ClientReadyAdapterEvent, 
    AckAdapterEvent, SyncRequestAdapterEvent
)

from api.adapters.room_adapters import (
    _handle_create_room, _handle_join_room, _handle_leave_room,
    _handle_get_room_state, _handle_add_bot, _handle_remove_player
)
from api.adapters.room_adapters_event import (
    CreateRoomAdapterEvent, JoinRoomAdapterEvent, LeaveRoomAdapterEvent,
    GetRoomStateAdapterEvent, AddBotAdapterEvent, RemovePlayerAdapterEvent
)

from infrastructure.events.in_memory_event_bus import reset_event_bus


class MockWebSocket:
    """Mock WebSocket for testing."""
    def __init__(self, player_id: str = "player123", room_id: str = None):
        self.id = f"ws_{player_id}"
        self.player_id = player_id
        self.room_id = room_id


class TestConnectionAdapterContracts:
    """Contract tests for connection adapters."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset event bus before each test."""
        reset_event_bus()
    
    @pytest.fixture
    def websocket(self):
        """Create a mock websocket."""
        return MockWebSocket()
    
    @pytest.mark.asyncio
    async def test_ping_adapter_contract(self, websocket):
        """Test PingAdapter produces same output as PingAdapterEvent."""
        # Test data
        message = {
            "action": "ping",
            "data": {
                "timestamp": 1234567890
            }
        }
        room_state = {
            "room_id": "room123"
        }
        
        # Get responses from both adapters
        direct_adapter = PingAdapter()
        event_adapter = PingAdapterEvent()
        
        direct_response = await direct_adapter.handle(websocket, message, room_state)
        event_response = await event_adapter.handle(websocket, message, room_state)
        
        # Responses should match (except for server_time which will differ slightly)
        assert direct_response["event"] == event_response["event"]
        assert direct_response["data"]["timestamp"] == event_response["data"]["timestamp"]
        assert direct_response["data"]["room_id"] == event_response["data"]["room_id"]
        assert "server_time" in direct_response["data"]
        assert "server_time" in event_response["data"]
    
    @pytest.mark.asyncio
    async def test_client_ready_adapter_contract(self, websocket):
        """Test ClientReadyAdapter produces same output as ClientReadyAdapterEvent."""
        # Test with room state
        message = {
            "action": "client_ready",
            "data": {
                "player_name": "Alice"
            }
        }
        room_state = {
            "room_id": "room123",
            "players": [
                {"name": "Alice", "slot": "P1"},
                {"name": "Bob", "slot": "P2"}
            ],
            "host_name": "Alice"
        }
        
        direct_adapter = ClientReadyAdapter()
        event_adapter = ClientReadyAdapterEvent()
        
        direct_response = await direct_adapter.handle(websocket, message, room_state)
        event_response = await event_adapter.handle(websocket, message, room_state)
        
        # Responses should match exactly
        assert direct_response == event_response
        
        # Test without room state
        direct_response2 = await direct_adapter.handle(websocket, message, None)
        event_response2 = await event_adapter.handle(websocket, message, None)
        
        assert direct_response2 == event_response2
    
    @pytest.mark.asyncio
    async def test_ack_adapter_contract(self, websocket):
        """Test AckAdapter produces same output as AckAdapterEvent."""
        message = {
            "action": "ack",
            "data": {
                "sequence": 42,
                "client_id": "client123"
            }
        }
        
        direct_adapter = AckAdapter()
        event_adapter = AckAdapterEvent()
        
        direct_response = await direct_adapter.handle(websocket, message)
        event_response = await event_adapter.handle(websocket, message)
        
        # Both should return None
        assert direct_response is None
        assert event_response is None
    
    @pytest.mark.asyncio
    async def test_sync_request_adapter_contract(self, websocket):
        """Test SyncRequestAdapter produces same output as SyncRequestAdapterEvent."""
        message = {
            "action": "sync_request",
            "data": {
                "client_id": "client123"
            }
        }
        room_state = {
            "room_id": "room123",
            "game_state": {
                "phase": "TURN",
                "current_player": "Alice"
            }
        }
        
        direct_adapter = SyncRequestAdapter()
        event_adapter = SyncRequestAdapterEvent()
        
        direct_response = await direct_adapter.handle(websocket, message, room_state)
        event_response = await event_adapter.handle(websocket, message, room_state)
        
        # Compare structure (timestamps will differ)
        assert direct_response["event"] == event_response["event"]
        assert direct_response["data"]["room_state"] == event_response["data"]["room_state"]
        assert direct_response["data"]["client_id"] == event_response["data"]["client_id"]
        assert "timestamp" in direct_response["data"]
        assert "timestamp" in event_response["data"]


class TestRoomAdapterContracts:
    """Contract tests for room adapters."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset event bus before each test."""
        reset_event_bus()
    
    @pytest.fixture
    def websocket(self):
        """Create a mock websocket."""
        return MockWebSocket()
    
    @pytest.mark.asyncio
    async def test_create_room_adapter_contract(self, websocket):
        """Test create_room produces same output structure."""
        message = {
            "action": "create_room",
            "data": {
                "player_name": "Alice"
            }
        }
        
        # Direct adapter
        direct_response = await _handle_create_room(websocket, message, None, None)
        
        # Event adapter
        event_adapter = CreateRoomAdapterEvent()
        event_response = await event_adapter.handle(websocket, message, None)
        
        # Structure should match
        assert direct_response["event"] == event_response["event"]
        assert direct_response["data"]["host_name"] == event_response["data"]["host_name"]
        assert direct_response["data"]["success"] == event_response["data"]["success"]
        # Room IDs will differ due to UUID generation
        assert "room_id" in direct_response["data"]
        assert "room_id" in event_response["data"]
    
    @pytest.mark.asyncio
    async def test_create_room_error_contract(self, websocket):
        """Test create_room error handling matches."""
        message = {
            "action": "create_room",
            "data": {}  # Missing player_name
        }
        
        direct_response = await _handle_create_room(websocket, message, None, None)
        
        event_adapter = CreateRoomAdapterEvent()
        event_response = await event_adapter.handle(websocket, message, None)
        
        # Error responses should match
        assert direct_response == event_response
        assert direct_response["event"] == "error"
    
    @pytest.mark.asyncio
    async def test_join_room_adapter_contract(self, websocket):
        """Test join_room produces same output."""
        message = {
            "action": "join_room",
            "data": {
                "room_id": "room123",
                "player_name": "Bob"
            }
        }
        
        direct_response = await _handle_join_room(websocket, message, None, None)
        
        event_adapter = JoinRoomAdapterEvent()
        event_response = await event_adapter.handle(websocket, message, None)
        
        # Responses should match
        assert direct_response["event"] == event_response["event"]
        assert direct_response["data"]["room_id"] == event_response["data"]["room_id"]
        assert direct_response["data"]["player_name"] == event_response["data"]["player_name"]
        assert direct_response["data"]["success"] == event_response["data"]["success"]
        assert direct_response["data"]["slot"] == event_response["data"]["slot"]
    
    @pytest.mark.asyncio
    async def test_add_bot_adapter_contract(self, websocket):
        """Test add_bot produces same output."""
        websocket.room_id = "room123"
        message = {
            "action": "add_bot",
            "data": {
                "difficulty": "hard"
            }
        }
        
        direct_response = await _handle_add_bot(websocket, message, None, None)
        
        event_adapter = AddBotAdapterEvent()
        event_response = await event_adapter.handle(websocket, message, None)
        
        # Bot names should match pattern
        assert direct_response["event"] == event_response["event"]
        assert direct_response["data"]["difficulty"] == event_response["data"]["difficulty"]
        assert direct_response["data"]["success"] == event_response["data"]["success"]
        assert "Bot_" in direct_response["data"]["bot_name"]
        assert "Bot_" in event_response["data"]["bot_name"]


class TestContractTestHelpers:
    """Helper functions for contract testing."""
    
    def normalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a response for comparison by removing variable fields.
        
        Fields like timestamps, UUIDs, etc. that vary between runs.
        """
        if not response:
            return response
        
        normalized = response.copy()
        
        # Remove timestamp fields
        if "data" in normalized:
            data = normalized["data"].copy()
            for field in ["timestamp", "server_time"]:
                if field in data:
                    data[field] = "<normalized>"
            
            # Normalize UUIDs in room_id
            if "room_id" in data and data["room_id"].startswith("room_"):
                data["room_id"] = "room_<uuid>"
            
            normalized["data"] = data
        
        return normalized
    
    def assert_responses_match(self, direct: Dict[str, Any], event: Dict[str, Any]):
        """Assert two responses match after normalization."""
        normalized_direct = self.normalize_response(direct)
        normalized_event = self.normalize_response(event)
        
        assert normalized_direct == normalized_event, (
            f"Responses don't match:\n"
            f"Direct: {json.dumps(normalized_direct, indent=2)}\n"
            f"Event:  {json.dumps(normalized_event, indent=2)}"
        )


class TestEventPublishingVerification:
    """Verify that event adapters actually publish events."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset event bus and set up event tracking."""
        reset_event_bus()
        self.published_events = []
        
        # Subscribe to all events
        from infrastructure.events.in_memory_event_bus import get_event_bus
        from domain.events.base import DomainEvent
        
        async def track_event(event: DomainEvent):
            self.published_events.append(event)
        
        bus = get_event_bus()
        bus.subscribe(DomainEvent, track_event)
    
    @pytest.mark.asyncio
    async def test_create_room_publishes_event(self):
        """Verify CreateRoomAdapterEvent publishes RoomCreated event."""
        websocket = MockWebSocket()
        message = {
            "action": "create_room",
            "data": {"player_name": "Alice"}
        }
        
        adapter = CreateRoomAdapterEvent()
        await adapter.handle(websocket, message)
        
        # Should have published RoomCreated
        assert len(self.published_events) == 1
        event = self.published_events[0]
        
        from domain.events.all_events import RoomCreated
        assert isinstance(event, RoomCreated)
        assert event.host_name == "Alice"
        assert event.room_id.startswith("room_")
    
    @pytest.mark.asyncio
    async def test_error_publishes_invalid_action_event(self):
        """Verify error cases publish InvalidActionAttempted events."""
        websocket = MockWebSocket()
        message = {
            "action": "create_room",
            "data": {}  # Missing player_name
        }
        
        adapter = CreateRoomAdapterEvent()
        await adapter.handle(websocket, message)
        
        # Should have published InvalidActionAttempted
        assert len(self.published_events) == 1
        event = self.published_events[0]
        
        from domain.events.all_events import InvalidActionAttempted
        assert isinstance(event, InvalidActionAttempted)
        assert event.action_type == "create_room"
        assert "required" in event.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])