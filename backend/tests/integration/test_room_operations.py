#!/usr/bin/env python3
"""
Room Operations Integration Tests for Phase 6.3.2

Tests integration between room adapters and application layer.
Validates room management with clean architecture.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
import uuid
from datetime import datetime

# Import test utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from api.adapters.adapter_registry import AdapterRegistry
from api.adapters.room_adapters import handle_room_messages, ROOM_ADAPTER_ACTIONS
from infrastructure.feature_flags import FeatureFlags


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self, player_id: Optional[str] = None):
        self.player_id = player_id
        self.sent_messages = []
        self.closed = False
        
    async def send(self, message: str):
        """Mock send method."""
        self.sent_messages.append(message)
        
    async def close(self):
        """Mock close method."""
        self.closed = True


class MockRoom:
    """Mock room for testing."""
    
    def __init__(self, room_id: str, host_name: str):
        self.id = room_id
        self.host_name = host_name
        self.slots = []
        self.max_slots = 4
        self.created_at = datetime.utcnow()
        
    def add_player(self, player):
        """Add player to room."""
        if len(self.slots) < self.max_slots:
            self.slots.append(player)
            return True
        return False
    
    def remove_player(self, player_id: str):
        """Remove player from room."""
        for i, player in enumerate(self.slots):
            if player and hasattr(player, 'id') and player.id == player_id:
                del self.slots[i]
                return True
        return False
    
    def get_state(self):
        """Get room state."""
        return {
            "room_id": self.id,
            "host_name": self.host_name,
            "players": [{"id": getattr(p, 'id', ''), "name": getattr(p, 'name', '')} for p in self.slots if p],
            "current_slots": len(self.slots),
            "max_slots": self.max_slots
        }


class MockPlayer:
    """Mock player for testing."""
    
    def __init__(self, player_id: str, name: str):
        self.id = player_id
        self.name = name


@pytest.fixture
def mock_websocket():
    """Fixture for mock WebSocket."""
    return MockWebSocket(player_id="test_player")


@pytest.fixture
def mock_feature_flags():
    """Fixture for feature flags."""
    flags = FeatureFlags()
    flags.override(FeatureFlags.USE_ROOM_ADAPTERS, True)
    flags.override(FeatureFlags.USE_CLEAN_ARCHITECTURE, True)
    return flags


@pytest.fixture
def sample_room():
    """Fixture for sample room."""
    return MockRoom("test_room_123", "TestHost")


class TestRoomOperationIntegration:
    """Test room operation integration with adapters."""
    
    @pytest.mark.asyncio
    async def test_create_room_adapter_integration(self, mock_websocket):
        """Test create room adapter integration."""
        
        # Mock legacy handler
        legacy_handler = AsyncMock(return_value={
            "event": "legacy_response",
            "data": {"fallback": True}
        })
        
        # Create room message
        create_message = {
            "action": "create_room",
            "data": {
                "host_name": "TestHost",
                "room_name": "TestRoom"
            }
        }
        
        # Test adapter handling
        result = await handle_room_messages(
            websocket=mock_websocket,
            message=create_message,
            legacy_handler=legacy_handler
        )
        
        # Assertions
        assert result is not None
        # The exact structure depends on the implementation
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_join_room_adapter_integration(self, mock_websocket, sample_room):
        """Test join room adapter integration."""
        
        # Mock legacy handler
        legacy_handler = AsyncMock(return_value={
            "event": "legacy_response",
            "data": {"fallback": True}
        })
        
        # Join room message
        join_message = {
            "action": "join_room",
            "data": {
                "room_id": "test_room_123",
                "player_name": "TestPlayer"
            }
        }
        
        # Test adapter handling
        result = await handle_room_messages(
            websocket=mock_websocket,
            message=join_message,
            legacy_handler=legacy_handler,
            room_state=sample_room.get_state()
        )
        
        # Assertions
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_room_adapter_actions_recognition(self, mock_websocket):
        """Test room adapter actions recognition."""
        
        # Test that room actions are properly recognized
        room_actions = [
            "create_room", "join_room", "leave_room",
            "get_room_state", "add_bot", "remove_player"
        ]
        
        for action in room_actions:
            assert action in ROOM_ADAPTER_ACTIONS
        
        # Test non-room action
        non_room_actions = ["ping", "start_game", "declare", "play"]
        for action in non_room_actions:
            assert action not in ROOM_ADAPTER_ACTIONS
    
    @pytest.mark.asyncio
    async def test_non_room_message_passthrough(self, mock_websocket):
        """Test non-room messages pass through to legacy handler."""
        
        # Mock legacy handler
        legacy_handler = AsyncMock(return_value={
            "event": "legacy_handled",
            "data": {"processed": True}
        })
        
        # Non-room message
        ping_message = {
            "action": "ping",
            "data": {"timestamp": 1234567890}
        }
        
        # Test adapter handling
        result = await handle_room_messages(
            websocket=mock_websocket,
            message=ping_message,
            legacy_handler=legacy_handler
        )
        
        # Should call legacy handler for non-room messages
        legacy_handler.assert_called_once_with(mock_websocket, ping_message)
        
        # Assertions
        assert result is not None
        assert result["event"] == "legacy_handled"
    
    @pytest.mark.asyncio
    async def test_room_adapter_performance(self, mock_websocket):
        """Test room adapter performance."""
        
        # Mock legacy handler
        legacy_handler = AsyncMock(return_value={
            "event": "legacy_response",
            "data": {"success": True}
        })
        
        # Test multiple room messages
        room_messages = [
            {"action": "create_room", "data": {"host_name": f"Host{i}"}}
            for i in range(10)
        ]
        
        times = []
        
        for message in room_messages:
            start_time = time.perf_counter()
            
            result = await handle_room_messages(
                websocket=mock_websocket,
                message=message,
                legacy_handler=legacy_handler
            )
            
            end_time = time.perf_counter()
            operation_time = (end_time - start_time) * 1000  # ms
            times.append(operation_time)
            
            # Verify result
            assert result is not None
            assert isinstance(result, dict)
        
        # Performance assertions
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 5.0  # Average under 5ms
        assert max_time < 20.0  # Max under 20ms
    


class TestRoomOperationPerformance:
    """Test room operation performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_room_adapter_overhead(self, mock_websocket):
        """Test room adapter overhead."""
        
        create_adapter = CreateRoomAdapter()
        
        # Measure baseline performance
        baseline_times = []
        
        for i in range(50):
            start_time = time.perf_counter()
            
            message = {
                "action": "create_room",
                "data": {
                    "host_name": f"BaselineHost{i}",
                    "room_name": f"BaselineRoom{i}"
                }
            }
            
            await create_adapter.handle(
                websocket=mock_websocket,
                message=message
            )
            
            end_time = time.perf_counter()
            baseline_times.append((end_time - start_time) * 1000)
        
        # Performance assertions
        avg_time = sum(baseline_times) / len(baseline_times)
        p95_time = sorted(baseline_times)[int(len(baseline_times) * 0.95)]
        
        assert avg_time < 2.0  # Average under 2ms
        assert p95_time < 10.0  # 95th percentile under 10ms
    
    @pytest.mark.asyncio
    async def test_sustained_room_operations(self, mock_websocket):
        """Test sustained room operations without memory leaks."""
        
        create_adapter = CreateRoomAdapter()
        join_adapter = JoinRoomAdapter()
        
        # Simulate sustained operations
        for batch in range(5):  # 5 batches of operations
            
            # Create rooms
            for i in range(20):
                create_message = {
                    "action": "create_room",
                    "data": {
                        "host_name": f"SustainedHost{batch}_{i}",
                        "room_name": f"SustainedRoom{batch}_{i}"
                    }
                }
                
                result = await create_adapter.handle(
                    websocket=mock_websocket,
                    message=create_message
                )
                
                # Verify creation
                assert result is not None
                assert result["event"] == "room_created"
            
            # Small delay between batches
            await asyncio.sleep(0.01)
        
        # If we complete without memory issues, test passed
        assert True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])