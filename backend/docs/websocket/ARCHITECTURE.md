# WebSocket Architecture (Post-Phase 2)

## Date: 2025-01-28
## Status: Phase 2 Complete

### Overview

This document describes the WebSocket architecture after Phase 2 refactoring. The system now has clear separation between infrastructure and application concerns.

### Architecture Layers

```
┌─────────────────────────────────────────────┐
│            WebSocket Client                 │
└─────────────────────┬───────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│         API Layer (ws.py)                   │
│  - Thin orchestration                       │
│  - Route definition                         │
└─────────────────────┬───────────────────────┘
                      ↓
┌─────────────────────┴───────────────────────┐
│   Infrastructure Layer  │  Application Layer │
│                        │                    │
│  WebSocketServer       │  MessageRouter     │
│  - Connection mgmt     │  - Business routing│
│  - Message I/O         │  - Event dispatch  │
│  - Rate limiting       │  - Room validation │
│                        │                    │
│                        │  DisconnectHandler │
│                        │  - Player state    │
│                        │  - Bot activation  │
└────────────────────────┴────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│          Adapter System (Phase 3)           │
│  - Message transformation                   │
│  - Use case integration                     │
└─────────────────────┬───────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│         Clean Architecture                  │
│  - Use Cases                                │
│  - Domain Logic                             │
│  - Repositories                             │
└─────────────────────────────────────────────┘
```

## Component Responsibilities

### API Layer (`api/routes/ws.py`)

**Purpose**: Thin orchestration layer

**Responsibilities**:
- Define WebSocket route
- Orchestrate infrastructure and application components
- Handle top-level exceptions

**Not Responsible For**:
- Business logic
- Connection details
- Message validation

### Infrastructure Layer

#### WebSocketServer (`infrastructure/websocket/websocket_server.py`)

**Purpose**: Pure WebSocket infrastructure handling

**Responsibilities**:
- Accept WebSocket connections
- Generate connection IDs
- Send/receive messages
- Basic message validation
- Rate limiting checks
- Connection lifecycle management

**Not Responsible For**:
- Business logic
- Message routing decisions
- Room/player state

### Application Layer

#### MessageRouter (`application/websocket/message_router.py`)

**Purpose**: Business logic routing

**Responsibilities**:
- Route messages to appropriate handlers
- Validate event support
- Get room state for processing
- Handle message queuing
- Room existence validation

**Not Responsible For**:
- WebSocket connection management
- Low-level message I/O
- Infrastructure concerns

#### DisconnectHandler (`application/websocket/disconnect_handler.py`)

**Purpose**: Handle player disconnection business logic

**Responsibilities**:
- Process player disconnections
- Activate bots for disconnected players
- Handle host migration
- Broadcast disconnect events

**Not Responsible For**:
- Connection cleanup
- WebSocket closing

## Message Flow

### Connection Flow
1. Client connects to `/ws/{room_id}`
2. `ws.py` accepts connection via `WebSocketServer`
3. `WebSocketServer` generates connection ID and registers
4. `MessageRouter` validates room exists (if not lobby)
5. Connection ready for messages

### Message Processing Flow
1. `WebSocketServer` receives raw message
2. `WebSocketServer` validates message structure
3. `ws.py` passes message to `MessageRouter`
4. `MessageRouter` checks event support
5. `MessageRouter` gets room state if needed
6. `MessageRouter` routes to adapter system
7. Response flows back through layers

### Disconnection Flow
1. WebSocket disconnect detected
2. `ws.py` gets connection info
3. `WebSocketServer` handles infrastructure cleanup
4. `DisconnectHandler` processes business logic
5. Events broadcast to remaining players

## Integration Points

### With Adapter System
- `MessageRouter` calls `adapter_wrapper.try_handle_with_adapter()`
- Passes WebSocket, message, room_id, and room_state
- Receives response or None

### With Clean Architecture
- `MessageRouter` uses `RoomApplicationService` for room validation
- `DisconnectHandler` uses `RoomApplicationService` for player management
- Both use `UnitOfWork` for repository access

### With Legacy Components
- `connection_manager` for connection tracking (to be removed)
- `message_queue_manager` for queued messages (to be refactored)
- Helper functions in `ws.py` (to be moved)

## Configuration

### Environment Variables
- Rate limiting configuration (if enabled)
- WebSocket timeouts (future)
- Connection limits (future)

### Feature Flags
- Adapter system enabled/disabled
- Rate limiting enabled/disabled

## Error Handling

### Infrastructure Errors
- Connection failures
- Message send/receive errors
- Rate limit violations

### Application Errors
- Unsupported events
- Room not found
- Message routing failures

### Error Response Format
```json
{
    "event": "error",
    "data": {
        "message": "Human readable error",
        "type": "error_category",
        "details": "Optional additional info"
    }
}
```

## Testing Strategy

### Unit Tests
- `test_websocket_server.py` - Infrastructure component
- `test_message_router.py` - Application routing
- `test_disconnect_handler.py` - Disconnect logic

### Integration Tests
- `test_websocket_infrastructure.py` - Full flow testing

### E2E Tests
- Full game flow through WebSocket (Phase 4)

## Migration Notes

### From Pre-Phase 2
- All infrastructure code extracted from `ws.py`
- Business logic moved to application layer
- Clear separation of concerns achieved

### Remaining Work
- Phase 2.5: Analyze adapter system necessity
- Phase 3: Modernize or remove adapters
- Phase 4: Establish formal contracts

## Performance Considerations

- Minimal overhead in routing layer
- Direct pass-through where possible
- Async throughout for non-blocking I/O
- Connection pooling for database access

## Security Considerations

- Rate limiting at infrastructure layer
- Message validation before processing
- No direct access to internal components
- Sanitized error messages