# WebSocket Architecture Guide

## Overview

This guide documents the WebSocket architecture after the Phase 3 migration from adapter-based to direct use case routing, and the Phase 4 establishment of clear architectural boundaries.

## Architecture Layers

### 1. API Layer (`api/`)
- **Purpose**: HTTP/WebSocket entry points and protocol handling
- **Responsibilities**:
  - WebSocket endpoint management
  - HTTP REST endpoints
  - Request/response formatting
  - Protocol-specific error handling
- **Key Components**:
  - `routes/ws.py`: Main WebSocket endpoint
  - `routes/metrics.py`: Metrics API endpoints
  - `validation/`: Message validation

### 2. Application Layer (`application/`)
- **Purpose**: Business logic orchestration and use case implementation
- **Responsibilities**:
  - Use case execution
  - DTO transformation
  - Business rule enforcement
  - Event publishing
- **Key Components**:
  - `websocket/use_case_dispatcher.py`: Routes events to use cases
  - `websocket/message_router.py`: Message routing logic
  - `interfaces/websocket_contracts.py`: Application layer contracts
  - `use_cases/`: All business use cases

### 3. Domain Layer (`domain/` and `engine/`)
- **Purpose**: Core business logic and game rules
- **Responsibilities**:
  - Game state management
  - Rule validation
  - Domain events
  - Pure business logic
- **Key Components**:
  - `engine/game.py`: Core game logic
  - `engine/state_machine/`: Game state management
  - `domain/entities/`: Domain entities
  - `domain/value_objects/`: Value objects

### 4. Infrastructure Layer (`infrastructure/`)
- **Purpose**: External service integration and technical concerns
- **Responsibilities**:
  - WebSocket connection management
  - Message broadcasting
  - Persistence
  - Monitoring and metrics
- **Key Components**:
  - `websocket/connection_singleton.py`: Connection management
  - `monitoring/websocket_metrics.py`: Metrics collection
  - `interfaces/websocket_infrastructure.py`: Infrastructure contracts
  - `repositories/`: Data persistence

## Message Flow

### 1. Incoming WebSocket Message
```
Client → WebSocket Endpoint → Validation → Message Router → Use Case Dispatcher → Use Case → Domain
```

### 2. Outgoing WebSocket Message
```
Domain Event → Event Publisher → Broadcaster → WebSocket Connections → Clients
```

### Detailed Flow

1. **WebSocket Connection** (`api/routes/ws.py`)
   - Client connects to `/ws/{room_id}`
   - Connection registered in infrastructure
   - Validation bypass checked for use case events

2. **Message Routing** (`application/websocket/message_router.py`)
   - Event type extracted from message
   - Metrics tracking initiated
   - Routed to appropriate handler

3. **Use Case Execution** (`application/websocket/use_case_dispatcher.py`)
   - DTO created from message data
   - Use case executed with dependencies
   - Response formatted for WebSocket

4. **Domain Processing** (`engine/` and `domain/`)
   - Business rules applied
   - State changes made
   - Domain events emitted

## Contracts and Interfaces

### Application Layer Contracts

```python
# IMessageHandler - Handles WebSocket messages
class IMessageHandler(ABC):
    async def handle_message(message: WebSocketMessage, context: Dict) -> WebSocketResponse
    def can_handle(event: str) -> bool
    def get_supported_events() -> List[str]

# IMessageRouter - Routes messages to handlers
class IMessageRouter(ABC):
    async def route(message: WebSocketMessage, context: Dict) -> WebSocketResponse
    def register_handler(handler: IMessageHandler) -> None
    def get_handler_for_event(event: str) -> IMessageHandler

# IEventPublisher - Publishes events to WebSocket clients
class IEventPublisher(ABC):
    async def publish_event(event_name: str, data: Dict, room_id: str) -> None
    async def publish_to_room(room_id: str, event_name: str, data: Dict) -> None
    async def publish_to_player(player_id: str, event_name: str, data: Dict) -> None
```

### Infrastructure Layer Contracts

```python
# IWebSocketConnection - Abstracts WebSocket implementation
class IWebSocketConnection(ABC):
    async def send_json(data: Dict) -> None
    async def receive_json() -> Dict
    async def accept() -> None
    async def close(code: int, reason: str) -> None
    def is_connected() -> bool

# IConnectionManager - Manages WebSocket connections
class IConnectionManager(ABC):
    async def register_connection(connection_id: str, websocket: IWebSocketConnection, room_id: str) -> None
    async def unregister_connection(connection_id: str) -> None
    def get_connection(connection_id: str) -> IWebSocketConnection
    def get_connections_in_room(room_id: str) -> Dict[str, IWebSocketConnection]

# IBroadcaster - Broadcasts messages to connections
class IBroadcaster(ABC):
    async def broadcast_to_room(room_id: str, message: Dict, exclude: Set[str]) -> int
    async def send_to_connection(connection_id: str, message: Dict) -> bool
```

## Event Configuration

### Migrated Events (22 total)

All events now use direct use case routing:

**Connection Events**:
- `ping`: Keep-alive heartbeat
- `client_ready`: Client initialization
- `ack`: Message acknowledgment
- `sync_request`: State synchronization

**Lobby Events**:
- `request_room_list`: Get available rooms
- `get_rooms`: Alias for request_room_list

**Room Management Events**:
- `create_room`: Create new game room
- `join_room`: Join existing room
- `leave_room`: Leave current room
- `get_room_state`: Get room information
- `add_bot`: Add bot player
- `remove_player`: Remove player/bot

**Game Events**:
- `start_game`: Start game in room
- `declare`: Declare pile count
- `play`/`play_pieces`: Play game pieces
- `request_redeal`: Request hand redeal
- `accept_redeal`: Accept redeal request
- `decline_redeal`: Decline redeal request
- `redeal_decision`: Redeal vote
- `player_ready`: Player ready status
- `leave_game`: Leave active game

## Monitoring and Metrics

### Metrics Collection

The system automatically collects:
- **Connection Metrics**: Total, active, disconnections, duration
- **Message Metrics**: Sent, received, broadcasts
- **Event Metrics**: Count, duration, success rate, errors
- **Performance Metrics**: Slow events, error-prone events

### Metrics Endpoints

- `GET /api/metrics/summary`: Complete metrics summary
- `GET /api/metrics/events/{event_name}`: Specific event metrics
- `GET /api/metrics/connections`: Connection statistics
- `GET /api/metrics/messages`: Message traffic stats
- `GET /api/metrics/time-series`: Historical data
- `GET /api/metrics/performance`: Performance analysis
- `GET /api/metrics/health`: System health status

### Metrics Integration

```python
# Automatic metrics collection in message router
async with MetricsContext(event) as ctx:
    response = await route_message(event, data)
    # Metrics automatically recorded
```

## Configuration

### Environment Variables

```bash
# WebSocket routing mode
WEBSOCKET_ROUTING_MODE=migration  # or "use_case" for all events

# Validation bypass for use case events
BYPASS_VALIDATION_FOR_USE_CASES=true

# Metrics window size
METRICS_WINDOW_MINUTES=5
```

### WebSocket Configuration

```python
# websocket_config.py manages:
- Event routing decisions
- Validation bypass settings
- Migration configuration
```

## Best Practices

### 1. Layer Separation
- Infrastructure doesn't import from Application
- Application doesn't import from API
- Domain has no external dependencies

### 2. Contract Usage
- Use interfaces for cross-layer communication
- Implement contracts for testability
- Keep implementations separate from interfaces

### 3. Event Handling
- Use DTOs for data transfer
- Transform at layer boundaries
- Keep domain models pure

### 4. Metrics and Monitoring
- Track all events automatically
- Monitor performance thresholds
- Use health endpoints for alerts

### 5. Error Handling
- Handle errors at appropriate layers
- Use typed errors when possible
- Log errors with context

## Migration Guide

### Adding New Events

1. **Define Use Case** in `application/use_cases/`
2. **Create DTOs** in `application/dto/`
3. **Add Handler** in `use_case_dispatcher.py`
4. **Configure Event** in `websocket_config.py`
5. **Test** with validation bypass enabled

### Example:

```python
# 1. Use Case
class NewEventUseCase:
    async def execute(self, request: NewEventRequest) -> NewEventResponse:
        # Business logic here
        pass

# 2. DTOs
@dataclass
class NewEventRequest:
    player_id: str
    data: Dict[str, Any]

# 3. Dispatcher Handler
async def _handle_new_event(self, data: Dict, context: DispatchContext):
    request = NewEventRequest(
        player_id=context.player_id,
        data=data
    )
    response = await self.new_event_use_case.execute(request)
    return format_response(response)

# 4. Configuration
self.use_case_events.add("new_event")
```

## Troubleshooting

### Common Issues

1. **"No handler for event"**
   - Check event is in `use_case_events`
   - Verify handler exists in dispatcher

2. **Validation Errors**
   - Enable validation bypass
   - Check DTO field mapping

3. **Metrics Not Showing**
   - Ensure metrics router is included
   - Check MetricsContext usage

4. **Connection Issues**
   - Verify WebSocket path
   - Check room exists
   - Review connection logs

## Future Enhancements

1. **Event Versioning**: Support multiple event versions
2. **Player-Specific Messaging**: Direct player messaging
3. **Advanced Metrics**: Custom metric dimensions
4. **Circuit Breakers**: Automatic failure handling
5. **Event Replay**: Replay events for debugging

## Conclusion

The WebSocket architecture provides a clean, maintainable system for real-time communication. The direct use case routing eliminates unnecessary abstraction while maintaining clear boundaries through contracts. The comprehensive metrics system enables monitoring and optimization of the real-time features.