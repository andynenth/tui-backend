# Infrastructure WebSocket Components

## Overview

This directory contains pure infrastructure components for WebSocket handling, separated from business logic as part of the Phase 2 refactoring.

## Components

### websocket_server.py
Pure WebSocket infrastructure handling including:
- Connection acceptance and lifecycle management
- Message sending/receiving with basic validation
- Rate limiting integration
- Connection registration/unregistration
- Error handling and cleanup

### connection_singleton.py (Existing)
Provides singleton connection management:
- Global connection registry
- Room-based broadcasting
- Connection ID management

### connection_manager.py (Legacy - API layer)
Legacy connection tracking - to be refactored in Phase 3:
- Player-to-WebSocket mapping
- Connection metadata

## Key Design Principles

1. **No Business Logic**: These components handle only infrastructure concerns
2. **Protocol Agnostic**: Could work with any WebSocket application
3. **Testable**: All components can be unit tested in isolation
4. **Async First**: Full async/await support throughout

## Usage Example

```python
from infrastructure.websocket.websocket_server import WebSocketServer

# Initialize server
server = WebSocketServer()

# In your route handler
await server.accept_connection(websocket)
connection_id = await server.handle_connection(websocket, room_id)

# Message loop
while True:
    message = await server.receive_message(websocket)
    if message:
        # Process message (business logic)
        response = process_message(message)
        await server.send_message(websocket, response)
```

## Integration Points

- **With Application Layer**: Provides WebSocket infrastructure for MessageRouter
- **With API Layer**: Used by ws.py for connection handling
- **With Middleware**: Integrates with rate limiting middleware

## Configuration

Rate limiting can be configured via the WebSocketServer constructor:

```python
server = WebSocketServer(rate_limit_config={
    "enabled": True,
    "requests_per_minute": 60
})
```

## Testing

See `tests/infrastructure/websocket/` for comprehensive unit tests covering:
- Connection lifecycle
- Message validation
- Error handling
- Rate limiting

## Future Enhancements

1. **Connection Pooling**: Manage connection limits
2. **Metrics Collection**: Track connection stats
3. **Health Checks**: WebSocket-specific health monitoring
4. **Compression**: Message compression support