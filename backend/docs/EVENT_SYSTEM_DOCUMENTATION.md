# Event System Documentation

## Overview

The Liap Tui event system provides a decoupled, event-driven architecture that separates domain logic from infrastructure concerns. This document describes the event system components, patterns, and usage.

## Architecture

### Event Flow

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Domain Layer   │     │ Application  │     │Infrastructure│
│                 │     │    Layer     │     │    Layer     │
│  Domain Events  │────►│  Event Bus   │────►│   Handlers   │
│  & Publishers   │     │              │     │              │
└─────────────────┘     └──────────────┘     └─────────────┘
        ↓                                            ↓
   Event Store                                  WebSocket
                                               Notifications
```

### Key Components

1. **Domain Events** - Pure domain objects representing what happened
2. **Event Publishers** - Interface for publishing events from domain
3. **Event Bus** - Routes events to handlers in application layer
4. **Event Handlers** - React to events and produce side effects
5. **Event Store** - Persists events for replay and audit

## Domain Events

### Base Event Classes

```python
# domain/events/base.py

@dataclass
class DomainEvent:
    """Base class for all domain events."""
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    version: int = 1

@dataclass
class AggregateEvent(DomainEvent):
    """Event related to a specific aggregate."""
    aggregate_id: str
    aggregate_type: str
    aggregate_version: int = 0
```

### Game Events

Located in `domain/events/game_events.py`:

| Event | Description | Key Data |
|-------|-------------|----------|
| `GameStartedEvent` | Game has started | players, initial_phase |
| `RoundStartedEvent` | New round begun | round_number, dealer |
| `TurnPlayedEvent` | Player played turn | player, pieces |
| `PhaseChangedEvent` | Game phase changed | old_phase, new_phase |
| `PlayerDeclaredEvent` | Player made declaration | player, declared_piles |
| `RoundEndedEvent` | Round finished | round_number, scores |
| `GameEndedEvent` | Game completed | winner, final_scores |

### Player Events

Located in `domain/events/player_events.py`:

| Event | Description | Key Data |
|-------|-------------|----------|
| `PlayerJoinedEvent` | Player joined room | player, room_players |
| `PlayerLeftEvent` | Player left room | player, reason |
| `PlayerReadyEvent` | Player marked ready | player |
| `HostTransferredEvent` | Host role transferred | old_host, new_host |

## Event Publishers

### EventPublisher Interface

```python
# domain/interfaces/event_publisher.py

class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
```

### Usage in Domain

```python
# domain/entities/game.py

class Game:
    def __init__(self, event_publisher: EventPublisher):
        self._event_publisher = event_publisher
    
    async def start(self):
        # Game logic...
        
        # Publish event
        await self._event_publisher.publish(
            GameStartedEvent(
                aggregate_id=self.id,
                players=[p.to_dict() for p in self.players],
                initial_phase=self.current_phase.value
            )
        )
```

## Event Bus

### InMemoryEventBus

Located in `application/events/event_bus.py`:

**Features:**
- Priority-based handler execution
- Async and sync handler support
- Error isolation
- Circular event detection
- Metrics tracking

### Subscribing Handlers

```python
# api/dependencies.py

# Subscribe with priority
event_bus.subscribe(
    GameStartedEvent,
    notification_handler.handle,
    priority=100  # Higher priority executes first
)

# Subscribe with filter
event_bus.subscribe(
    TurnPlayedEvent,
    bot_handler.handle,
    filter_predicate=lambda e: e.data.get('is_bot_turn', False)
)
```

## Event Handlers

### Base Handler Classes

```python
# application/events/event_handler.py

class EventHandler(ABC, Generic[TEvent]):
    """Synchronous event handler."""
    @abstractmethod
    def handle(self, event: TEvent) -> None:
        pass

class AsyncEventHandler(ABC, Generic[TEvent]):
    """Asynchronous event handler."""
    @abstractmethod
    async def handle(self, event: TEvent) -> None:
        pass
```

### Built-in Handlers

#### GameNotificationHandler
Converts domain events to WebSocket notifications:
- Listens for all game events
- Sends appropriate WebSocket messages
- Maintains message format compatibility

#### GameStateUpdateHandler
Updates read models from events:
- Maintains query-optimized projections
- Enables fast state queries

#### BotActionHandler
Triggers bot actions:
- Watches for phase changes
- Initiates bot decision making

#### AuditLogHandler
Creates audit trail:
- Logs important events
- Provides compliance tracking

## Event Sourcing

### EventSourcedRepository

```python
# application/events/event_sourcing.py

class EventSourcedRepository:
    """Load and save aggregates via events."""
    
    async def load(self, aggregate_id: str, aggregate_type: Type[T]) -> Optional[T]:
        """Load aggregate by replaying events."""
        
    async def save(self, aggregate: Any, new_events: List[DomainEvent]) -> None:
        """Save aggregate by storing events."""
```

### Event Projections

```python
# application/events/event_sourcing.py

class GameEventProjector(EventProjector):
    """Build read models from events."""
    
    def get_active_games(self) -> List[Dict[str, Any]]:
        """Query active games from projection."""
```

## Usage Patterns

### Publishing Events

```python
# Simple event
await event_publisher.publish(
    PlayerJoinedEvent(
        aggregate_id=room_id,
        player=player_data
    )
)

# Multiple events
for event in [event1, event2, event3]:
    await event_publisher.publish(event)
```

### Creating Custom Handlers

```python
class CustomGameHandler(AsyncEventHandler[GameStartedEvent]):
    async def handle(self, event: GameStartedEvent) -> None:
        # Custom logic here
        logger.info(f"Game {event.aggregate_id} started!")
```

### Testing with Events

```python
# Unit test
async def test_game_start():
    mock_publisher = Mock(EventPublisher)
    game = Game(event_publisher=mock_publisher)
    
    await game.start()
    
    # Verify event published
    mock_publisher.publish.assert_called_once()
    event = mock_publisher.publish.call_args[0][0]
    assert isinstance(event, GameStartedEvent)
```

## Configuration

### Enabling/Disabling Features

```python
# Disable async publishing (useful for tests)
event_publisher.disable_async_publishing()

# Disable event store publishing
event_store.disable_publish_on_store()
```

### Metrics and Monitoring

```python
# Get event bus metrics
metrics = event_bus.get_metrics()
print(f"Events published: {metrics.events_published}")
print(f"Handler errors: {metrics.handler_errors}")

# Get publisher metrics
pub_metrics = event_publisher.get_metrics()
print(f"Total published: {pub_metrics['total_published']}")
```

## Best Practices

### 1. Event Design
- Events should be immutable
- Include all necessary data
- Use past tense naming (GameStarted, not StartGame)
- Version events for compatibility

### 2. Handler Design
- Handlers should be idempotent
- Handle errors gracefully
- Keep handlers focused (single responsibility)
- Use appropriate priority

### 3. Testing
- Test domain logic without infrastructure
- Use mock publishers for unit tests
- Test event flow in integration tests
- Verify handler execution

### 4. Performance
- Use filters to reduce handler calls
- Batch related events when possible
- Monitor event bus metrics
- Consider async handlers for I/O

## Troubleshooting

### Enable Debug Logging

```python
import logging

# Event bus logging
logging.getLogger("application.events").setLevel(logging.DEBUG)

# Handler logging
logging.getLogger("application.events.game_event_handlers").setLevel(logging.DEBUG)
```

### Common Issues

1. **Handler not called**
   - Check subscription is registered
   - Verify event type matches
   - Check filter predicate

2. **Circular events**
   - Event bus detects and prevents
   - Check handler logic

3. **Handler errors**
   - Errors logged but don't stop other handlers
   - Check error handler configuration

## Future Enhancements

1. **Event Versioning** - Handle schema evolution
2. **Event Replay UI** - Debug and recovery tools
3. **Distributed Events** - Cross-service events
4. **Event Analytics** - Track event patterns
5. **Snapshot Support** - Optimize replay performance