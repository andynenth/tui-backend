# Clean Architecture Implementation Guide

## Overview

This guide documents the clean architecture implementation for the Liap-TUI backend, providing a structured approach to gradually migrate from the legacy codebase to a domain-driven, testable architecture.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Layer Responsibilities](#layer-responsibilities)
3. [Migration Strategy](#migration-strategy)
4. [Feature Flags](#feature-flags)
5. [Usage Examples](#usage-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Architecture Overview

The clean architecture implementation follows the hexagonal/onion architecture pattern with these layers:

```
┌─────────────────────────────────────────────────────┐
│                  Presentation Layer                  │
│              (WebSocket Handlers)                    │
├─────────────────────────────────────────────────────┤
│                 Application Layer                    │
│         (Use Cases, DTOs, App Services)             │
├─────────────────────────────────────────────────────┤
│                   Domain Layer                       │
│      (Entities, Value Objects, Domain Events)       │
├─────────────────────────────────────────────────────┤
│               Infrastructure Layer                   │
│   (Repositories, External Services, Adapters)       │
└─────────────────────────────────────────────────────┘
```

### Key Principles

1. **Dependency Rule**: Dependencies point inward. Inner layers know nothing about outer layers.
2. **Domain Isolation**: Business logic is isolated in the domain layer.
3. **Use Case Focus**: Each use case represents a single user action.
4. **Interface Segregation**: Layers communicate through well-defined interfaces.

### Core Systems

1. **Connection Management**: Player disconnect/reconnect with bot substitution
2. **Message Queuing**: Offline message storage and delivery
3. **Game State Management**: Turn-based gameplay with state machine
4. **Event Broadcasting**: Real-time updates via domain events

## Layer Responsibilities

### Domain Layer (`/domain`)
- **Entities**: Core business objects (Room, Game, Player)
- **Value Objects**: Immutable values (RoomId, GameId, PlayerId)
- **Domain Events**: Things that happen (RoomCreated, GameStarted)
- **Domain Services**: Complex business logic
- **Exceptions**: Domain-specific errors

### Application Layer (`/application`)
- **Use Cases**: Single business operations
- **DTOs**: Data transfer objects for layer boundaries
- **Application Services**: Orchestration logic
- **Interfaces**: Contracts for infrastructure

### Infrastructure Layer (`/infrastructure`)
- **Repositories**: Data persistence
- **External Services**: WebSocket, notifications, etc.
- **Adapters**: Bridge between legacy and new code
- **Feature Flags**: Gradual rollout control

## Migration Strategy

### Phase 1: Parallel Implementation
Run new architecture alongside legacy code using feature flags:

```python
# In WebSocket handler
if feature_flags.is_enabled(FeatureFlags.USE_CLEAN_ARCHITECTURE):
    # Use clean architecture adapter
    response = await adapter.handle_event(event_type, data, context)
else:
    # Use legacy handler
    response = await legacy_handler(data, context)
```

### Phase 2: Gradual Rollout
Enable features progressively:

1. **Shadow Mode**: Run both implementations, compare results
2. **Percentage Rollout**: Enable for % of users
3. **Feature-by-Feature**: Enable specific features
4. **Full Migration**: Remove legacy code

### Phase 3: Legacy Removal
Once validated, remove legacy implementations.

## Feature Flags

### Configuration
Feature flags can be configured via:

1. **Environment Variables**:
```bash
export FF_USE_CLEAN_ARCHITECTURE=true
export FF_USE_CONNECTION_ADAPTERS=true
```

2. **Configuration File**:
```json
{
  "use_clean_architecture": true,
  "use_connection_adapters": {
    "enabled": true,
    "percentage": 50
  }
}
```

3. **Runtime Override**:
```python
feature_flags.override(FeatureFlags.USE_CLEAN_ARCHITECTURE, True)
```

### Available Flags

| Flag | Description | Default |
|------|-------------|---------|
| `USE_CLEAN_ARCHITECTURE` | Master switch for clean architecture | `false` |
| `USE_DOMAIN_EVENTS` | Enable domain event publishing | `false` |
| `USE_APPLICATION_LAYER` | Use application layer use cases | `false` |
| `USE_CONNECTION_ADAPTERS` | Use clean arch for connection events | `false` |
| `USE_ROOM_ADAPTERS` | Use clean arch for room management | `false` |
| `USE_GAME_ADAPTERS` | Use clean arch for game operations | `false` |

## Usage Examples

### Creating a Room

```python
# Legacy approach
async def handle_create_room(data, context):
    room = room_manager.create_room(data['player_name'])
    await broadcast(room.id, 'room_created', room.to_dict())
    return {'room_id': room.id}

# Clean architecture approach
async def handle_create_room(data, context):
    use_case = CreateRoomUseCase(unit_of_work, event_publisher)
    request = CreateRoomRequest(
        host_player_id=context['player_id'],
        host_player_name=data['player_name'],
        room_name=data.get('room_name')
    )
    response = await use_case.execute(request)
    return response.to_dict()
```

### Starting a Game

```python
# Using the clean architecture
async def start_game(room_id: str, player_id: str):
    async with unit_of_work:
        # Use case handles all business logic
        use_case = StartGameUseCase(unit_of_work, event_publisher)
        response = await use_case.execute(
            StartGameRequest(
                room_id=room_id,
                requesting_player_id=player_id
            )
        )
        
        if response.success:
            # Events are automatically published
            return response.to_dict()
        else:
            raise GameException(response.error)
```

### Handling Player Reconnection

```python
# Clean architecture approach for reconnection
async def handle_player_reconnect(room_id: str, player_name: str, websocket_id: str):
    # Use case handles all reconnection logic
    use_case = HandlePlayerReconnectUseCase(unit_of_work, event_publisher)
    response = await use_case.execute(
        HandlePlayerReconnectRequest(
            room_id=room_id,
            player_name=player_name,
            websocket_id=websocket_id
        )
    )
    
    if response.success:
        # Bot was deactivated if needed
        # Queued messages are in response.queued_messages
        # Events automatically published
        return {
            'reconnected': True,
            'queued_messages': response.queued_messages,
            'bot_deactivated': response.bot_deactivated
        }
```

### Testing

```python
# Easy to test with mocks
async def test_create_room():
    # Arrange
    uow = Mock(spec=UnitOfWork)
    publisher = Mock(spec=EventPublisher)
    use_case = CreateRoomUseCase(uow, publisher)
    
    # Act
    response = await use_case.execute(
        CreateRoomRequest(
            host_player_id="test_player",
            host_player_name="Test Player"
        )
    )
    
    # Assert
    assert response.success is True
    assert response.room_id is not None
    publisher.publish.assert_called_once()
```

## Best Practices

### 1. Use Dependency Injection
```python
# Good
class CreateRoomUseCase:
    def __init__(self, uow: UnitOfWork, publisher: EventPublisher):
        self._uow = uow
        self._publisher = publisher

# Bad
class CreateRoomUseCase:
    def __init__(self):
        self._uow = InMemoryUnitOfWork()  # Hard dependency
```

### 2. Keep Use Cases Focused
```python
# Good - Single responsibility
class JoinRoomUseCase:
    async def execute(self, request: JoinRoomRequest) -> JoinRoomResponse:
        # Only handles joining a room

# Bad - Multiple responsibilities
class RoomManagementUseCase:
    async def create_room(self, ...):
    async def join_room(self, ...):
    async def leave_room(self, ...):
```

### 3. Use DTOs at Boundaries
```python
# Good - Clear contract
@dataclass
class CreateRoomRequest:
    host_player_id: str
    host_player_name: str
    room_name: Optional[str] = None

# Bad - Passing raw dicts
async def create_room(self, data: Dict[str, Any]):
    # No type safety or validation
```

### 4. Emit Domain Events
```python
# In domain entity
def start_game(self):
    self._phase = GamePhase.PREPARATION
    self._events.append(
        GameStarted(
            game_id=self.game_id.value,
            room_id=self.room_id.value,
            timestamp=datetime.utcnow()
        )
    )
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure PYTHONPATH includes the backend directory
   - Check for circular imports between layers

2. **Transaction Issues**
   - Always use UnitOfWork as context manager
   - Don't nest transactions

3. **Event Publishing**
   - Events are published after successful commit
   - Check feature flags for event sourcing

4. **Performance**
   - Use repository methods efficiently
   - Consider caching for read-heavy operations

### Debug Mode

Enable debug logging:
```python
# In feature flags
LOG_ADAPTER_CALLS = True
ENABLE_PERFORMANCE_MONITORING = True
```

### Support

For questions or issues:
1. Check the [migration guide](MIGRATION_GUIDE.md)
2. Review [examples](examples/)
3. Contact the architecture team

## Next Steps

1. Review the [Migration Guide](MIGRATION_GUIDE.md)
2. Try the [Tutorial](TUTORIAL.md)
3. Check [API Reference](API_REFERENCE.md)
4. See [Rollout Plan](ROLLOUT_PLAN.md)