# Application WebSocket Components

## Overview

This directory contains application-layer components for WebSocket message handling, implementing business logic separated from infrastructure concerns as part of Phase 2 refactoring.

## Components

### message_router.py
Routes WebSocket messages to appropriate handlers:
- Event validation and categorization
- Room state retrieval for handlers
- Integration with adapter system
- Message queue checking
- Error response formatting

### route_registry.py
Defines all supported WebSocket events:
- Event-to-handler mappings
- Event categorization (connection, room, lobby, game)
- Support checking utilities

### disconnect_handler.py
Handles business logic for player disconnections:
- Pre-game vs in-game disconnect logic
- Bot activation for disconnected players
- Host migration when needed
- Event broadcasting for state changes

## Architecture

```
WebSocket Message
       ↓
MessageRouter.route_message()
       ↓
Check event support (route_registry)
       ↓
Get room state if needed
       ↓
Route to adapter system
       ↓
Return response
```

## Supported Events

Total of 22 events across 4 categories:

- **Connection** (4): ping, client_ready, ack, sync_request
- **Room** (6): create_room, join_room, leave_room, get_room_state, add_bot, remove_player
- **Lobby** (2): request_room_list, get_rooms
- **Game** (10): start_game, declare, play, play_pieces, request_redeal, accept_redeal, decline_redeal, redeal_decision, player_ready, leave_game

## Key Design Principles

1. **Business Logic Only**: No infrastructure concerns
2. **Stateless Routing**: Each request handled independently
3. **Clean Architecture Integration**: Uses application services and DTOs
4. **Error Resilience**: Graceful error handling with meaningful responses

## Usage Example

```python
from application.websocket.message_router import MessageRouter

# Initialize router
router = MessageRouter()

# Route a message
response = await router.route_message(
    websocket,
    {"event": "create_room", "data": {...}},
    "lobby"
)

# Handle room validation
valid = await router.handle_room_validation(websocket, room_id)
```

## Integration Points

- **With Infrastructure**: Receives validated messages from WebSocketServer
- **With Adapters**: Routes messages to adapter system
- **With Clean Architecture**: Uses RoomApplicationService, UnitOfWork

## Error Handling

All errors return standardized format:
```json
{
    "event": "error",
    "data": {
        "message": "Human readable error",
        "type": "error_category",
        "details": "Optional details"
    }
}
```

Error types:
- `routing_error`: General routing failures
- `unsupported_event`: Unknown event type
- `validation_error`: Invalid message format
- `room_not_found`: Room doesn't exist

## Testing

See `tests/application/websocket/` for unit tests covering:
- Message routing logic
- Error handling
- Room validation
- Event categorization

## Future Enhancements

1. **Event Versioning**: Support multiple versions of events
2. **Custom Routing Rules**: Dynamic routing configuration
3. **Circuit Breakers**: Protect against handler failures
4. **Metrics Collection**: Track routing performance