"""
Basic tests for application layer use cases.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from application.use_cases.connection import HandlePingUseCase
from application.use_cases.room_management import CreateRoomUseCase
from application.dto.connection import HandlePingRequest, HandlePingResponse
from application.dto.room_management import CreateRoomRequest
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector


class MockUnitOfWork:
    """Mock unit of work for testing."""
    
    def __init__(self):
        self.rooms = Mock()
        self.games = Mock()
        self.player_stats = Mock()
        self.committed = False
        self.rolled_back = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
    
    async def commit(self):
        self.committed = True
    
    async def rollback(self):
        self.rolled_back = True


@pytest.mark.asyncio
async def test_handle_ping_use_case():
    """Test the HandlePing use case."""
    # Arrange
    uow = MockUnitOfWork()
    uow.rooms.get_by_id = AsyncMock(return_value=None)
    
    metrics = Mock(spec=MetricsCollector)
    use_case = HandlePingUseCase(uow, metrics)
    
    request = HandlePingRequest(
        player_id="player1",
        room_id="room1",
        sequence_number=42
    )
    
    # Act
    response = await use_case.execute(request)
    
    # Assert
    assert isinstance(response, HandlePingResponse)
    assert response.success is True
    assert response.sequence_number == 42
    assert isinstance(response.server_time, datetime)
    
    # Verify metrics were recorded
    metrics.increment.assert_called_once_with(
        "ping.received",
        tags={"room_id": "room1"}
    )


@pytest.mark.asyncio
async def test_create_room_use_case():
    """Test the CreateRoom use case."""
    # Arrange
    uow = MockUnitOfWork()
    uow.rooms.find_by_player = AsyncMock(return_value=None)
    uow.rooms.get_by_code = AsyncMock(return_value=None)
    uow.rooms.save = AsyncMock()
    
    event_publisher = Mock(spec=EventPublisher)
    event_publisher.publish = AsyncMock()
    
    use_case = CreateRoomUseCase(uow, event_publisher)
    
    request = CreateRoomRequest(
        host_player_id="player1",
        host_player_name="Player One",
        room_name="Test Room"
    )
    
    # Act
    response = await use_case.execute(request)
    
    # Assert
    assert response.success is True
    assert response.room_info is not None
    assert response.room_info.host_id.endswith("_p0")  # First player is host
    assert response.room_info.room_name == "Player One's Room"  # Default naming
    assert len(response.join_code) == 6
    
    # Verify room was saved
    uow.rooms.save.assert_called_once()
    
    # Verify event was published
    event_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_use_case_error_handling():
    """Test that use cases handle errors properly."""
    # Arrange
    uow = MockUnitOfWork()
    uow.rooms.find_by_player = AsyncMock(side_effect=Exception("Database error"))
    
    event_publisher = Mock(spec=EventPublisher)
    use_case = CreateRoomUseCase(uow, event_publisher)
    
    request = CreateRoomRequest(
        host_player_id="player1",
        host_player_name="Player One"
    )
    
    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await use_case.execute(request)
    
    assert "Database error" in str(exc_info.value)
    assert uow.rolled_back is True