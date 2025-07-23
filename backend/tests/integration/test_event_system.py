# tests/integration/test_event_system.py
"""
Integration tests for the event system.
"""

import pytest
import asyncio
from typing import List

from application.events import InMemoryEventBus
from application.events.game_event_handlers import (
    GameNotificationHandler,
    GameStateUpdateHandler,
    AuditLogHandler
)
from domain.events.game_events import (
    GameStartedEvent,
    TurnPlayedEvent,
    PhaseChangedEvent,
    GameEndedEvent
)
from domain.events.player_events import PlayerJoinedEvent
from infrastructure.events import (
    EventBusAdapter,
    DomainEventPublisher
)


class MockNotificationService:
    """Mock notification service to capture notifications."""
    
    def __init__(self):
        self.notifications = []
    
    async def notify_room(self, room_id: str, event_type: str, data: dict):
        self.notifications.append({
            "type": "room",
            "room_id": room_id,
            "event_type": event_type,
            "data": data
        })
    
    async def notify_player(self, player_id: str, event_type: str, data: dict):
        self.notifications.append({
            "type": "player",
            "player_id": player_id,
            "event_type": event_type,
            "data": data
        })


class MockRoomService:
    """Mock room service."""
    
    async def get_room(self, room_id: str):
        return {
            "id": room_id,
            "players": ["Player1", "Player2", "Player3", "Player4"]
        }


class EventCollector:
    """Collects events for testing."""
    
    def __init__(self):
        self.events: List[any] = []
    
    async def collect(self, event):
        self.events.append(event)
    
    def get_events_of_type(self, event_type):
        return [e for e in self.events if isinstance(e, event_type)]


class TestEventBusIntegration:
    """Test event bus with handlers."""
    
    @pytest.mark.asyncio
    async def test_event_bus_publishes_to_handlers(self):
        """Test event bus routes events to subscribed handlers."""
        # Setup
        event_bus = InMemoryEventBus()
        collector = EventCollector()
        
        # Subscribe
        event_bus.subscribe(GameStartedEvent, collector.collect)
        
        # Publish event
        event = GameStartedEvent(
            aggregate_id="game-123",
            players=[{"name": "Player1"}],
            initial_phase="PREPARATION"
        )
        
        await event_bus.publish(event)
        
        # Verify
        assert len(collector.events) == 1
        assert collector.events[0] == event
    
    @pytest.mark.asyncio
    async def test_event_bus_priority_ordering(self):
        """Test handlers execute in priority order."""
        event_bus = InMemoryEventBus()
        execution_order = []
        
        async def handler1(event):
            execution_order.append(1)
        
        async def handler2(event):
            execution_order.append(2)
        
        async def handler3(event):
            execution_order.append(3)
        
        # Subscribe with different priorities
        event_bus.subscribe(GameStartedEvent, handler2, priority=50)
        event_bus.subscribe(GameStartedEvent, handler1, priority=100)
        event_bus.subscribe(GameStartedEvent, handler3, priority=10)
        
        # Publish
        event = GameStartedEvent(
            aggregate_id="game-123",
            players=[],
            initial_phase="PREPARATION"
        )
        
        await event_bus.publish(event)
        
        # Verify priority order (100, 50, 10)
        assert execution_order == [1, 2, 3]
    
    @pytest.mark.asyncio
    async def test_event_bus_error_isolation(self):
        """Test one handler error doesn't affect others."""
        event_bus = InMemoryEventBus()
        collector = EventCollector()
        
        async def failing_handler(event):
            raise ValueError("Handler error")
        
        # Subscribe both handlers
        event_bus.subscribe(GameStartedEvent, failing_handler, priority=100)
        event_bus.subscribe(GameStartedEvent, collector.collect, priority=50)
        
        # Publish
        event = GameStartedEvent(
            aggregate_id="game-123",
            players=[],
            initial_phase="PREPARATION"
        )
        
        await event_bus.publish(event)
        
        # Verify second handler still executed
        assert len(collector.events) == 1
        assert event_bus.get_metrics().handler_errors == 1


class TestGameNotificationHandler:
    """Test game notification handler integration."""
    
    @pytest.mark.asyncio
    async def test_game_started_notification(self):
        """Test GameStartedEvent triggers notification."""
        # Setup
        notification_service = MockNotificationService()
        room_service = MockRoomService()
        
        handler = GameNotificationHandler(
            notification_service=notification_service,
            room_service=room_service
        )
        
        # Handle event
        event = GameStartedEvent(
            aggregate_id="room-123",
            players=[
                {"name": "Player1", "is_bot": False},
                {"name": "Player2", "is_bot": False}
            ],
            initial_phase="PREPARATION"
        )
        
        await handler.handle(event)
        
        # Verify notification
        assert len(notification_service.notifications) == 1
        notif = notification_service.notifications[0]
        assert notif["type"] == "room"
        assert notif["room_id"] == "room-123"
        assert notif["event_type"] == "game_started"
        assert notif["data"]["players"] == event.data["players"]
    
    @pytest.mark.asyncio
    async def test_phase_changed_notification(self):
        """Test PhaseChangedEvent triggers notification."""
        notification_service = MockNotificationService()
        room_service = MockRoomService()
        
        handler = GameNotificationHandler(
            notification_service=notification_service,
            room_service=room_service
        )
        
        event = PhaseChangedEvent(
            aggregate_id="room-123",
            old_phase="DECLARATION",
            new_phase="TURN",
            phase_data={"current_player": "Player1"}
        )
        
        await handler.handle(event)
        
        assert len(notification_service.notifications) == 1
        notif = notification_service.notifications[0]
        assert notif["event_type"] == "phase_changed"
        assert notif["data"]["old_phase"] == "DECLARATION"
        assert notif["data"]["new_phase"] == "TURN"


class TestDomainEventPublisher:
    """Test domain event publisher with event bus."""
    
    @pytest.mark.asyncio
    async def test_dual_mode_publishing(self):
        """Test publisher supports both sync and async modes."""
        # Setup
        event_bus = InMemoryEventBus()
        sync_collector = EventCollector()
        async_collector = EventCollector()
        
        # Create publisher
        publisher = DomainEventPublisher(
            event_bus=event_bus,
            enable_sync=True,
            enable_async=True
        )
        
        # Subscribe sync handler (in-memory)
        publisher.subscribe(GameStartedEvent, sync_collector)
        
        # Subscribe async handler (event bus)
        event_bus.subscribe(GameStartedEvent, async_collector.collect)
        
        # Publish event
        event = GameStartedEvent(
            aggregate_id="game-123",
            players=[],
            initial_phase="PREPARATION"
        )
        
        await publisher.publish(event)
        
        # Both should receive event
        assert len(sync_collector.events) == 1
        assert len(async_collector.events) == 1
        
        # Check metrics
        metrics = publisher.get_metrics()
        assert metrics["sync_published"] == 1
        assert metrics["async_published"] == 1
    
    @pytest.mark.asyncio
    async def test_disable_async_publishing(self):
        """Test disabling async publishing."""
        event_bus = InMemoryEventBus()
        async_collector = EventCollector()
        
        publisher = DomainEventPublisher(event_bus=event_bus)
        publisher.disable_async_publishing()
        
        event_bus.subscribe(GameStartedEvent, async_collector.collect)
        
        event = GameStartedEvent(
            aggregate_id="game-123",
            players=[],
            initial_phase="PREPARATION"
        )
        
        await publisher.publish(event)
        
        # Async handler should not receive event
        assert len(async_collector.events) == 0


class TestEventFlowIntegration:
    """Test complete event flow from domain to handlers."""
    
    @pytest.mark.asyncio
    async def test_complete_event_flow(self):
        """Test event flows from domain through all handlers."""
        # Setup infrastructure
        event_bus = InMemoryEventBus()
        notification_service = MockNotificationService()
        room_service = MockRoomService()
        
        # Create handlers
        notification_handler = GameNotificationHandler(
            notification_service=notification_service,
            room_service=room_service
        )
        
        audit_collector = EventCollector()
        
        # Subscribe handlers
        event_bus.subscribe(
            GameStartedEvent,
            notification_handler.handle,
            priority=100
        )
        event_bus.subscribe(
            GameStartedEvent,
            audit_collector.collect,
            priority=10
        )
        
        # Create publisher
        publisher = EventBusAdapter(event_bus)
        
        # Simulate domain publishing event
        event = GameStartedEvent(
            aggregate_id="room-123",
            players=[
                {"name": "Player1", "is_bot": False},
                {"name": "Player2", "is_bot": False}
            ],
            initial_phase="PREPARATION"
        )
        
        await publisher.publish(event)
        
        # Verify all handlers executed
        assert len(notification_service.notifications) == 1
        assert notification_service.notifications[0]["event_type"] == "game_started"
        
        assert len(audit_collector.events) == 1
        assert audit_collector.events[0] == event
        
        # Check metrics
        metrics = event_bus.get_metrics()
        assert metrics.events_published == 1
        assert metrics.handlers_executed == 2
        assert metrics.handler_errors == 0