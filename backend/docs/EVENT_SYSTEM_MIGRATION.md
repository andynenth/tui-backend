# Event System Migration Guide

## Overview

This guide explains how to migrate from direct WebSocket broadcasting to the new event-driven architecture.

## Architecture Changes

### Before: Direct Broadcasting
```python
# Old pattern - tight coupling
from backend.socket_manager import broadcast

async def process_turn(self, player_name: str, pieces: List[int]):
    # Process turn...
    
    # Direct broadcast - infrastructure concern in domain
    await broadcast(self.room_id, "turn_played", {
        "player": player_name,
        "pieces": pieces
    })
```

### After: Event-Driven
```python
# New pattern - decoupled
async def process_turn(self, player_name: str, pieces: List[int]):
    # Process turn...
    
    # Publish domain event
    await self.event_publisher.publish(
        TurnPlayedEvent(
            aggregate_id=self.room_id,
            player=player_name,
            pieces=pieces
        )
    )
```

## Migration Steps

### 1. Replace Direct Broadcasts in Domain

**Location**: Domain entities and services should not know about broadcasting.

```python
# ❌ OLD: Domain knows about infrastructure
class Game:
    async def play_turn(self, player: str, pieces: List[int]):
        # ... game logic ...
        await broadcast(self.room_id, "turn_played", data)

# ✅ NEW: Domain publishes events
class Game:
    def __init__(self, event_publisher: EventPublisher):
        self._event_publisher = event_publisher
    
    async def play_turn(self, player: str, pieces: List[int]):
        # ... game logic ...
        await self._event_publisher.publish(
            TurnPlayedEvent(
                aggregate_id=self.id,
                player=player,
                pieces=pieces
            )
        )
```

### 2. Replace Broadcasts in State Machine

**Location**: `infrastructure/state_machine/state_adapter.py`

The state machine adapter already overrides the broadcast method to use NotificationService:

```python
# Already implemented in StateAdapter
async def broadcast_phase_change(self, old_phase: str, new_phase: str):
    await self._notification_service.notify_room(
        self._room_id,
        "phase_change",
        {
            "old_phase": old_phase,
            "new_phase": new_phase,
            "phase_data": self.get_phase_data()
        }
    )
```

### 3. Event Handler Automatically Broadcasts

The `GameNotificationHandler` listens for domain events and sends WebSocket notifications:

```python
# application/events/game_event_handlers.py
async def _handle_TurnPlayedEvent(self, event: TurnPlayedEvent):
    await self._notification_service.notify_room(
        event.aggregate_id,
        "turn_played",  # Same event type as before
        {
            "room_id": event.aggregate_id,
            "player": event.data["player"],
            "pieces": event.data["pieces"],
            "timestamp": event.timestamp.isoformat()
        }
    )
```

## Common Patterns

### 1. Simple Event Publishing

```python
# Publish a single event
await self._event_publisher.publish(
    GameStartedEvent(
        aggregate_id=game.id,
        players=[p.to_dict() for p in game.players],
        initial_phase="PREPARATION"
    )
)
```

### 2. Multiple Events

```python
# Publish multiple related events
events = [
    RoundEndedEvent(aggregate_id=game.id, round_number=round_num, scores=scores),
    GameEndedEvent(aggregate_id=game.id, winner=winner, reason="score_limit")
]

for event in events:
    await self._event_publisher.publish(event)
```

### 3. Conditional Events

```python
# Publish events based on conditions
if player.is_ready:
    await self._event_publisher.publish(
        PlayerReadyEvent(
            aggregate_id=room.id,
            player=player.name
        )
    )
```

## Benefits of Event-Driven Architecture

1. **Decoupling**: Domain doesn't know about WebSockets
2. **Testability**: Easy to test without infrastructure
3. **Extensibility**: Add new handlers without changing domain
4. **Audit Trail**: All events can be logged/stored
5. **Event Sourcing**: Ready for event sourcing if needed

## Event Flow

```
Domain Entity
    ↓ publishes
Domain Event
    ↓ routed by
Event Bus
    ↓ handled by
Event Handlers
    ├── GameNotificationHandler → WebSocket broadcast
    ├── GameStateUpdateHandler → Update read models
    ├── BotActionHandler → Trigger bot actions
    └── AuditLogHandler → Create audit logs
```

## Testing

### Unit Tests
```python
# Test domain without infrastructure
async def test_game_publishes_event():
    mock_publisher = Mock(EventPublisher)
    game = Game(event_publisher=mock_publisher)
    
    await game.start()
    
    mock_publisher.publish.assert_called_once()
    event = mock_publisher.publish.call_args[0][0]
    assert isinstance(event, GameStartedEvent)
```

### Integration Tests
```python
# Test full event flow
async def test_event_triggers_notification():
    container = DependencyContainer()
    
    # Subscribe test handler
    notifications = []
    async def capture_notification(event):
        notifications.append(event)
    
    container.event_bus.subscribe(
        GameStartedEvent,
        capture_notification
    )
    
    # Trigger domain action
    await container.game_service.start_game(room_id)
    
    # Verify notification sent
    assert len(notifications) == 1
```

## Debugging

Enable event bus logging:
```python
import logging
logging.getLogger("application.events").setLevel(logging.DEBUG)
```

This will show:
- Event publishing
- Handler execution
- Any errors in handlers

## Migration Checklist

- [ ] Remove all `from backend.socket_manager import broadcast` imports
- [ ] Replace `broadcast()` calls with event publishing
- [ ] Inject EventPublisher into domain entities that need it
- [ ] Verify all WebSocket message types are handled by event handlers
- [ ] Test that frontend still receives all expected messages
- [ ] Update any custom broadcast logic to use events
- [ ] Document any new event types created

## Next Steps

1. Complete migration of remaining broadcast calls
2. Add custom event handlers for specific use cases
3. Implement event persistence for replay capability
4. Consider adding event versioning for future compatibility