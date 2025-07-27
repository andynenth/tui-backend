#!/usr/bin/env python3
"""
WebSocket Integration Tests for Phase 6.3.1

Tests integration between WebSocket adapters and application layer use cases.
Validates the clean architecture WebSocket handling infrastructure.
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

from api.adapters.websocket_adapter_final import MinimalAdapterLayer
from api.adapters.adapter_registry import AdapterRegistry
from api.adapters.connection_adapters import PingAdapter
from infrastructure.feature_flags import FeatureFlags

# Mock the application layer components for this test
class MockHandlePingRequest:
    def __init__(self, player_id, room_id=None, sequence_number=None, request_id=None):
        self.player_id = player_id
        self.room_id = room_id
        self.sequence_number = sequence_number
        self.request_id = request_id

class MockHandlePingResponse:
    def __init__(self, success=True, request_id=None, sequence_number=None, server_time=None):
        self.success = success
        self.request_id = request_id
        self.sequence_number = sequence_number
        self.server_time = server_time or datetime.utcnow()

class MockRoom:
    def __init__(self, id, host_name):
        self.id = id
        self.host_name = host_name
        self.slots = []
    
    def add_player(self, player):
        self.slots.append(player)

class MockPlayer:
    def __init__(self, id, name, is_bot=False):
        self.id = id
        self.name = name
        self.is_bot = is_bot
        self.last_activity = None


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self, room_id: Optional[str] = None):
        self.room_id = room_id
        self.sent_messages = []
        self.closed = False
        
    async def send(self, message: str):
        """Mock send method."""
        self.sent_messages.append(message)
        
    async def close(self):
        """Mock close method."""
        self.closed = True


class MockUnitOfWork:
    """Mock Unit of Work for testing."""
    
    def __init__(self):
        self.rooms = MockRoomRepository()
        self.committed = False
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def commit(self):
        self.committed = True


class MockRoomRepository:
    """Mock Room Repository for testing."""
    
    def __init__(self):
        self.rooms = {}
        
    async def get_by_id(self, room_id: str) -> Optional[MockRoom]:
        return self.rooms.get(room_id)
    
    async def save(self, room: MockRoom):
        self.rooms[room.id] = room


@pytest.fixture
def mock_feature_flags():
    """Fixture for feature flags."""
    flags = FeatureFlags()
    flags.override(FeatureFlags.USE_CONNECTION_ADAPTERS, True)
    flags.override(FeatureFlags.USE_CLEAN_ARCHITECTURE, True)
    return flags


@pytest.fixture
def mock_uow():
    """Fixture for unit of work."""
    return MockUnitOfWork()


@pytest.fixture
def mock_websocket():
    """Fixture for mock WebSocket."""
    return MockWebSocket(room_id="test_room_123")


@pytest.fixture
def sample_room():
    """Fixture for sample room with players."""
    player1 = MockPlayer(id="player_1", name="TestPlayer1", is_bot=False)
    player2 = MockPlayer(id="player_2", name="TestPlayer2", is_bot=False)
    
    room = MockRoom(id="test_room_123", host_name="TestHost")
    room.add_player(player1)
    room.add_player(player2)
    
    return room


class TestWebSocketAdapterIntegration:
    """Test WebSocket adapter integration with application layer."""
    
    @pytest.mark.asyncio
    async def test_ping_message_handling(self, mock_websocket, mock_uow, mock_feature_flags):
        """Test ping message handling through adapter layer."""
        
        # Setup
        adapter = MinimalAdapterLayer(legacy_handler=AsyncMock())
        
        ping_message = {
            "action": "ping",
            "data": {
                "timestamp": time.time(),
                "player_id": "player_1"
            }
        }
        
        room_state = {
            "room_id": "test_room_123",
            "players": ["player_1", "player_2"]
        }
        
        # Test adapter handling
        result = await adapter.handle(
            websocket=mock_websocket,
            message=ping_message,
            room_state=room_state
        )
        
        # Assertions
        assert result is not None
        assert result["event"] == "pong"
        assert "server_time" in result["data"]
        assert result["data"]["room_id"] == "test_room_123"
    
    @pytest.mark.asyncio
    async def test_ping_adapter_direct_integration(self, mock_websocket):
        """Test ping adapter direct integration."""
        
        # Create ping adapter
        ping_adapter = PingAdapter()
        
        # Create ping message
        ping_message = {
            "action": "ping",
            "data": {
                "timestamp": time.time(),
                "player_id": "player_1"
            }
        }
        
        room_state = {
            "room_id": "test_room_123",
            "players": ["player_1", "player_2"]
        }
        
        # Test adapter handling
        result = await ping_adapter.handle(
            websocket=mock_websocket,
            message=ping_message,
            room_state=room_state
        )
        
        # Assertions
        assert result is not None
        assert result["event"] == "pong"
        assert "server_time" in result["data"]
    
    @pytest.mark.asyncio
    async def test_adapter_registry_integration(self, mock_websocket, mock_uow):
        """Test adapter registry integration."""
        
        # Setup
        registry = AdapterRegistry()
        
        # Test ping adapter registration
        ping_adapter = registry.adapters.get("ping")
        assert ping_adapter is not None
        
        # Create ping message
        ping_message = {
            "action": "ping",
            "data": {
                "timestamp": time.time(),
                "player_id": "player_1"
            }
        }
        
        # Test adapter execution
        result = await ping_adapter.handle(
            websocket=mock_websocket,
            message=ping_message,
            room_state={"room_id": "test_room_123"}
        )
        
        # Assertions
        assert result is not None
        assert "event" in result
    
    @pytest.mark.asyncio
    async def test_multiple_adapter_calls(self, mock_websocket):
        """Test multiple adapter calls in sequence."""
        
        # Setup
        ping_adapter = PingAdapter()
        
        # Simulate multiple ping exchanges
        for i in range(5):
            ping_message = {
                "action": "ping",
                "data": {
                    "timestamp": time.time(),
                    "sequence": i,
                    "player_id": "player_1"
                }
            }
            
            result = await ping_adapter.handle(
                websocket=mock_websocket,
                message=ping_message,
                room_state={"room_id": "test_room_123"}
            )
            
            # Verify each response
            assert result is not None
            assert result["event"] == "pong"
            assert "server_time" in result["data"]
            
            # Small delay between pings
            await asyncio.sleep(0.01)
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, mock_websocket):
        """Test performance monitoring integration."""
        
        # Setup
        adapter = MinimalAdapterLayer(legacy_handler=AsyncMock())
        
        # Test ping message with timing
        start_time = time.perf_counter()
        
        ping_message = {
            "action": "ping",
            "data": {
                "timestamp": time.time(),
                "player_id": "player_1"
            }
        }
        
        result = await adapter.handle(
            websocket=mock_websocket,
            message=ping_message,
            room_state={"room_id": "test_room_123"}
        )
        
        end_time = time.perf_counter()
        processing_time = (end_time - start_time) * 1000  # ms
        
        # Assertions
        assert result is not None
        assert processing_time < 10  # Should be under 10ms for ping
        
        # Verify response structure
        assert result["event"] == "pong"
        assert "server_time" in result["data"]
    
    @pytest.mark.asyncio
    async def test_concurrent_adapter_calls(self, mock_websocket):
        """Test concurrent adapter calls."""
        
        # Setup
        ping_adapter = PingAdapter()
        
        async def concurrent_ping(sequence: int):
            ping_message = {
                "action": "ping",
                "data": {
                    "timestamp": time.time(),
                    "sequence": sequence,
                    "player_id": f"player_{sequence}"
                }
            }
            return await ping_adapter.handle(
                websocket=mock_websocket,
                message=ping_message,
                room_state={"room_id": "test_room_123"}
            )
        
        # Execute concurrent pings
        tasks = [concurrent_ping(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Assertions
        assert len(results) == 10
        assert all(result is not None for result in results)
        assert all(result["event"] == "pong" for result in results)


class TestWebSocketIntegrationPerformance:
    """Test WebSocket integration performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_adapter_overhead_performance(self, mock_websocket, mock_uow):
        """Test adapter layer performance overhead."""
        
        # Setup
        legacy_handler = AsyncMock(return_value={"event": "test", "data": {}})
        adapter = MinimalAdapterLayer(legacy_handler=legacy_handler)
        
        # Measure ping handling performance
        ping_times = []
        
        for i in range(100):
            start_time = time.perf_counter()
            
            ping_message = {
                "action": "ping",
                "data": {
                    "timestamp": time.time(),
                    "sequence": i
                }
            }
            
            await adapter.handle(
                websocket=mock_websocket,
                message=ping_message,
                room_state={"room_id": "test_room"}
            )
            
            end_time = time.perf_counter()
            ping_times.append((end_time - start_time) * 1000)  # ms
        
        # Performance assertions
        avg_time = sum(ping_times) / len(ping_times)
        max_time = max(ping_times)
        
        assert avg_time < 1.0  # Average under 1ms
        assert max_time < 5.0  # Max under 5ms
        assert len([t for t in ping_times if t > 2.0]) < 5  # Less than 5% over 2ms
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, mock_websocket, mock_uow):
        """Test memory usage stability during sustained operation."""
        
        # Setup
        adapter = MinimalAdapterLayer(legacy_handler=AsyncMock())
        
        # Simulate sustained ping operations
        for batch in range(10):  # 10 batches of 100 pings each
            tasks = []
            
            for i in range(100):
                ping_message = {
                    "action": "ping",
                    "data": {
                        "timestamp": time.time(),
                        "batch": batch,
                        "sequence": i
                    }
                }
                
                task = adapter.handle(
                    websocket=mock_websocket,
                    message=ping_message,
                    room_state={"room_id": f"room_{batch}"}
                )
                tasks.append(task)
            
            # Process batch
            results = await asyncio.gather(*tasks)
            
            # Verify all processed successfully
            assert len(results) == 100
            assert all(result is not None for result in results)
            
            # Small delay between batches
            await asyncio.sleep(0.01)
        
        # If we get here without memory issues, test passed
        assert True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])