"""
Tests for message queue functionality.

These tests verify that messages are properly queued for disconnected
players and delivered when they reconnect.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from domain.entities.message_queue import PlayerQueue, QueuedMessage
from domain.value_objects import PlayerId, RoomId
from domain.events import MessageQueued, MessageQueueOverflow, QueuedMessagesDelivered
from application.use_cases.connection import QueueMessageForPlayerUseCase
from application.dto.connection import QueueMessageRequest
from application.services import MessageQueueService
from infrastructure.unit_of_work import InMemoryUnitOfWork


@pytest.mark.asyncio
async def test_queue_message_success():
    """Test successfully queueing a message."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()

    use_case = QueueMessageForPlayerUseCase(uow, event_publisher)

    # Create queue
    async with uow:
        await uow.message_queues.create_queue("room-123", "player1")

    # Act
    request = QueueMessageRequest(
        room_id="room-123",
        player_name="player1",
        event_type="game_state_update",
        event_data={"turn": 5, "phase": "TURN"},
        is_critical=True,
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success
    assert response.queued
    assert response.queue_size == 1

    # Verify message in queue
    async with uow:
        queue = await uow.message_queues.get_queue("room-123", "player1")
        assert len(queue.messages) == 1
        assert queue.messages[0].event_type == "game_state_update"
        assert queue.messages[0].is_critical == True

    # Verify event published
    event_publisher.publish_batch.assert_called_once()
    events = event_publisher.publish_batch.call_args[0][0]
    assert isinstance(events[0], MessageQueued)


@pytest.mark.asyncio
async def test_queue_message_overflow():
    """Test queue overflow when queue is full."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()

    use_case = QueueMessageForPlayerUseCase(uow, event_publisher)

    # Create queue and fill it
    queue = PlayerQueue(
        player_id=PlayerId("player1"),
        room_id=RoomId("room-123"),
        max_size=5,  # Small size for testing
    )

    # Fill the queue
    for i in range(5):
        queue.add_message(
            QueuedMessage(
                event_type=f"event_{i}",
                data={"index": i},
                timestamp=datetime.utcnow(),
                is_critical=False,
            )
        )

    async with uow:
        await uow.message_queues.save_queue(queue)

    # Act - Try to add one more message
    request = QueueMessageRequest(
        room_id="room-123",
        player_name="player1",
        event_type="overflow_event",
        event_data={"will_overflow": True},
        is_critical=False,
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success
    assert not response.queued  # Message not queued
    assert response.queue_size == 5  # Still at max

    # Verify overflow event published
    event_publisher.publish_batch.assert_called_once()
    events = event_publisher.publish_batch.call_args[0][0]
    assert isinstance(events[0], MessageQueueOverflow)
    assert events[0].dropped_event_type == "overflow_event"


@pytest.mark.asyncio
async def test_queue_critical_message_replaces_non_critical():
    """Test critical message replaces non-critical when queue full."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()

    use_case = QueueMessageForPlayerUseCase(uow, event_publisher)

    # Create queue and fill with non-critical messages
    queue = PlayerQueue(
        player_id=PlayerId("player1"), room_id=RoomId("room-123"), max_size=3
    )

    # Fill with non-critical messages
    for i in range(3):
        queue.add_message(
            QueuedMessage(
                event_type=f"non_critical_{i}",
                data={"index": i},
                timestamp=datetime.utcnow(),
                is_critical=False,
            )
        )

    async with uow:
        await uow.message_queues.save_queue(queue)

    # Act - Add critical message
    request = QueueMessageRequest(
        room_id="room-123",
        player_name="player1",
        event_type="critical_event",
        event_data={"important": True},
        is_critical=True,
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success
    assert response.queued
    assert response.queue_size == 3  # Still 3 messages

    # Verify critical message added and oldest non-critical removed
    async with uow:
        updated_queue = await uow.message_queues.get_queue("room-123", "player1")
        assert any(msg.event_type == "critical_event" for msg in updated_queue.messages)
        assert not any(
            msg.event_type == "non_critical_0" for msg in updated_queue.messages
        )


@pytest.mark.asyncio
async def test_message_queue_service_delivery():
    """Test message delivery through service."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()

    service = MessageQueueService(uow, event_publisher)

    # Queue some messages
    await service.queue_message(
        room_id="room-123",
        player_name="player1",
        event_type="event1",
        event_data={"data": 1},
        is_critical=False,
    )
    await service.queue_message(
        room_id="room-123",
        player_name="player1",
        event_type="event2",
        event_data={"data": 2},
        is_critical=True,
    )

    # Act - Deliver messages
    messages = await service.deliver_messages("room-123", "player1")

    # Assert
    assert len(messages) == 2
    assert messages[0]["event_type"] == "event1"
    assert messages[1]["event_type"] == "event2"
    assert messages[1]["is_critical"] == True

    # Verify queue cleared
    remaining = await service.get_queued_messages("room-123", "player1")
    assert len(remaining) == 0

    # Verify delivery event
    delivery_calls = [
        call
        for call in event_publisher.publish_batch.call_args_list
        if isinstance(call[0][0][0], QueuedMessagesDelivered)
    ]
    assert len(delivery_calls) == 1


@pytest.mark.asyncio
async def test_message_queue_service_stats():
    """Test queue statistics collection."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()

    service = MessageQueueService(uow, event_publisher)

    # Create room
    from domain.entities.room import Room
    from domain.entities.player import Player

    room = Room(room_id="room-123", host_name="player1")
    room.add_player(Player("player1"))
    room.add_player(Player("player2"))

    async with uow:
        await uow.rooms.save(room)

    # Queue messages for different players
    await service.queue_message("room-123", "player1", "event1", {}, False)
    await service.queue_message("room-123", "player1", "event2", {}, True)
    await service.queue_message("room-123", "player2", "event3", {}, True)

    # Act
    stats = await service.get_queue_stats("room-123")

    # Assert
    assert stats["room_id"] == "room-123"
    assert stats["total_queues"] == 2
    assert stats["total_messages"] == 3
    assert len(stats["players"]) == 2

    player1_stats = next(p for p in stats["players"] if p["player_name"] == "player1")
    assert player1_stats["queue_size"] == 2
    assert player1_stats["critical_messages"] == 1


@pytest.mark.asyncio
async def test_message_queue_cleanup_old_messages():
    """Test cleaning up old messages."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()

    service = MessageQueueService(uow, event_publisher)

    # Create room
    from domain.entities.room import Room
    from domain.entities.player import Player

    room = Room(room_id="room-123", host_name="player1")
    room.add_player(Player("player1"))

    async with uow:
        await uow.rooms.save(room)

    # Create queue with old and new messages
    queue = PlayerQueue(player_id=PlayerId("player1"), room_id=RoomId("room-123"))

    # Old message (will be cleaned)
    old_msg = QueuedMessage(
        event_type="old_event",
        data={},
        timestamp=datetime.utcnow() - timedelta(minutes=35),
        is_critical=False,
    )
    queue.messages.append(old_msg)

    # Recent message (will be kept)
    new_msg = QueuedMessage(
        event_type="new_event",
        data={},
        timestamp=datetime.utcnow() - timedelta(minutes=5),
        is_critical=False,
    )
    queue.messages.append(new_msg)

    async with uow:
        await uow.message_queues.save_queue(queue)

    # Act
    cleaned = await service.cleanup_old_messages("room-123", max_age_minutes=30)

    # Assert
    assert cleaned == 1

    # Verify old message removed
    async with uow:
        updated_queue = await uow.message_queues.get_queue("room-123", "player1")
        assert len(updated_queue.messages) == 1
        assert updated_queue.messages[0].event_type == "new_event"


@pytest.mark.asyncio
async def test_message_queue_prioritization():
    """Test critical message prioritization."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()

    service = MessageQueueService(uow, event_publisher)

    # Queue mixed messages
    await service.queue_message("room-123", "player1", "normal1", {}, False)
    await service.queue_message("room-123", "player1", "critical1", {}, True)
    await service.queue_message("room-123", "player1", "normal2", {}, False)
    await service.queue_message("room-123", "player1", "critical2", {}, True)

    # Act
    await service.prioritize_critical_messages("room-123", "player1")

    # Assert - Critical messages should be first
    messages = await service.get_queued_messages("room-123", "player1")
    assert messages[0]["event_type"] == "critical1"
    assert messages[1]["event_type"] == "critical2"
    assert messages[2]["event_type"] == "normal1"
    assert messages[3]["event_type"] == "normal2"


@pytest.mark.asyncio
async def test_queue_message_no_queue_creates_new():
    """Test queueing message creates queue if doesn't exist."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()

    use_case = QueueMessageForPlayerUseCase(uow, event_publisher)

    # Act - Queue message without creating queue first
    request = QueueMessageRequest(
        room_id="room-123",
        player_name="player1",
        event_type="test_event",
        event_data={"test": True},
        is_critical=False,
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success
    assert response.queued
    assert response.queue_size == 1

    # Verify queue was created
    async with uow:
        queue = await uow.message_queues.get_queue("room-123", "player1")
        assert queue is not None
        assert len(queue.messages) == 1
