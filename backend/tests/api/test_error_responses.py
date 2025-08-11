# backend/tests/api/test_error_responses.py
"""
Test standardized error responses for play history API.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.shared_instances import shared_room_manager
from backend.models.error_responses import ErrorCodes
import asyncio
import json


client = TestClient(app)


class TestStandardizedErrors:
    """Test standardized error response format."""
    
    def test_room_not_found_error(self):
        """Test standardized error for room not found."""
        response = client.get("/api/rooms/INVALID-ROOM-ID/play-history")
        
        assert response.status_code == 404
        data = response.json()
        
        # Check error structure
        assert "error" in data
        assert "request_id" in data
        assert "timestamp" in data
        assert "path" in data
        
        # Check error details
        error = data["error"]
        assert error["code"] == ErrorCodes.ROOM_NOT_FOUND
        assert "Room with ID 'INVALID-ROOM-ID' not found" in error["message"]
        assert error["context"]["room_id"] == "INVALID-ROOM-ID"
        
        # Check request_id is a valid UUID
        import uuid
        try:
            uuid.UUID(data["request_id"])
        except ValueError:
            pytest.fail("request_id is not a valid UUID")
    
    def test_no_active_game_error(self):
        """Test standardized error for room without active game."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create room without game
        room_id = loop.run_until_complete(shared_room_manager.create_room("Test Player"))
        
        response = client.get(f"/api/rooms/{room_id}/play-history")
        
        assert response.status_code == 400
        data = response.json()
        
        # Check error structure
        assert "error" in data
        error = data["error"]
        assert error["code"] == ErrorCodes.NO_ACTIVE_GAME
        assert f"Room '{room_id}' has no active game" in error["message"]
        assert error["context"]["room_id"] == room_id
    
    def test_invalid_range_error(self):
        """Test standardized error for invalid range parameters."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create a room with game
        from backend.engine.game import Game
        from backend.engine.player import Player
        
        players = [Player(f"Bot {i+1}", is_bot=True) for i in range(4)]
        room_id = loop.run_until_complete(shared_room_manager.create_room("Bot 1"))
        room = loop.run_until_complete(shared_room_manager.get_room(room_id))
        room.game = Game(players)
        
        # Request with invalid range
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=5&to=2")
        
        assert response.status_code == 400
        data = response.json()
        
        # Check error details
        error = data["error"]
        assert error["code"] == ErrorCodes.INVALID_RANGE
        assert "'from' must be less than or equal to 'to'" in error["message"]
        assert error["field"] == "from"
        assert error["context"]["from"] == 5
        assert error["context"]["to"] == 2
    
    def test_missing_parameter_error(self):
        """Test validation error for missing required parameter."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create a room with game
        from backend.engine.game import Game
        from backend.engine.player import Player
        
        players = [Player(f"Bot {i+1}", is_bot=True) for i in range(4)]
        room_id = loop.run_until_complete(shared_room_manager.create_room("Bot 1"))
        room = loop.run_until_complete(shared_room_manager.get_room(room_id))
        room.game = Game(players)
        
        # Request without 'to' parameter
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=1")
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        
        # Our standardized validation error format
        assert "errors" in data
        assert isinstance(data["errors"], list)
        assert len(data["errors"]) > 0
        
        # Check that it's about the missing 'to' parameter
        error = data["errors"][0]
        assert error["code"] == ErrorCodes.INVALID_PARAMETER
        assert error["field"] == "to"
        assert "required" in error["message"].lower()
        assert error["context"]["type"] == "missing"
    
    def test_error_response_consistency(self):
        """Test that all error responses have consistent structure."""
        # Test multiple error scenarios
        error_responses = []
        
        # 404 error
        resp1 = client.get("/api/rooms/INVALID/play-history")
        if resp1.status_code != 200:
            error_responses.append(resp1.json())
        
        # 400 error
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        room_id = loop.run_until_complete(shared_room_manager.create_room("Test"))
        resp2 = client.get(f"/api/rooms/{room_id}/play-history")
        if resp2.status_code != 200:
            error_responses.append(resp2.json())
        
        # Check all have consistent structure
        for error_data in error_responses:
            assert "error" in error_data
            assert "request_id" in error_data
            assert "timestamp" in error_data
            
            error = error_data["error"]
            assert "code" in error
            assert "message" in error
            # context and field are optional
    
    def test_error_context_information(self):
        """Test that errors include helpful context information."""
        # Test room not found
        response = client.get("/api/rooms/TEST-ROOM-123/play-history")
        data = response.json()
        
        # Should include room_id in context
        assert data["error"]["context"]["room_id"] == "TEST-ROOM-123"
        
        # Should include request path
        assert "/api/rooms/TEST-ROOM-123/play-history" in data["path"]
    
    def test_negative_round_validation(self):
        """Test validation for negative round numbers."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from backend.engine.game import Game
        from backend.engine.player import Player
        
        players = [Player(f"Bot {i+1}", is_bot=True) for i in range(4)]
        room_id = loop.run_until_complete(shared_room_manager.create_room("Bot 1"))
        room = loop.run_until_complete(shared_room_manager.get_room(room_id))
        room.game = Game(players)
        
        # Negative from
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=-1&to=2")
        assert response.status_code == 422
        
        # Negative to
        response = client.get(f"/api/rooms/{room_id}/play-history/rounds?from=1&to=-2")
        assert response.status_code == 422
    
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(shared_room_manager, 'rooms'):
            shared_room_manager.rooms.clear()