# WebSocket Message Routing

## Date: 2025-01-28
## Status: Phase 2 Complete

### Overview

This document describes how WebSocket messages are routed through the system after Phase 2 refactoring.

## Routing Architecture

```
Message arrives with event/action
            ↓
    MessageRouter checks support
            ↓
    Get room state if needed
            ↓
    Route to adapter system
            ↓
    Transform and dispatch
            ↓
    Return response
```

## Supported Events

### Connection Events (4)
| Event | Handler | Purpose |
|-------|---------|---------|
| `ping` | `connection_adapters.ping` | Keep-alive check |
| `client_ready` | `connection_adapters.client_ready` | Client initialization |
| `ack` | `connection_adapters.ack` | Message acknowledgment |
| `sync_request` | `connection_adapters.sync_request` | State synchronization |

### Room Management Events (6)
| Event | Handler | Purpose |
|-------|---------|---------|
| `create_room` | `room_adapters.create_room` | Create new game room |
| `join_room` | `room_adapters.join_room` | Join existing room |
| `leave_room` | `room_adapters.leave_room` | Leave current room |
| `get_room_state` | `room_adapters.get_room_state` | Get room information |
| `add_bot` | `room_adapters.add_bot` | Add bot to room |
| `remove_player` | `room_adapters.remove_player` | Remove player/bot |

### Lobby Events (2)
| Event | Handler | Purpose |
|-------|---------|---------|
| `request_room_list` | `lobby_adapters.request_room_list` | Request available rooms |
| `get_rooms` | `lobby_adapters.get_rooms` | Get room list (alias) |

### Game Events (10)
| Event | Handler | Purpose |
|-------|---------|---------|
| `start_game` | `game_adapters.start_game` | Start the game |
| `declare` | `game_adapters.declare` | Declare target piles |
| `play` | `game_adapters.play` | Play pieces |
| `play_pieces` | `game_adapters.play_pieces` | Play pieces (alias) |
| `request_redeal` | `game_adapters.request_redeal` | Request new deal |
| `accept_redeal` | `game_adapters.accept_redeal` | Accept redeal |
| `decline_redeal` | `game_adapters.decline_redeal` | Decline redeal |
| `redeal_decision` | `game_adapters.redeal_decision` | Redeal decision |
| `player_ready` | `game_adapters.player_ready` | Mark ready |
| `leave_game` | `game_adapters.leave_game` | Leave active game |

## Routing Logic

### 1. Message Reception
```python
# Message arrives with either 'event' or 'action' field
{
    "event": "create_room",  # or "action": "create_room"
    "data": {
        "player_name": "Player1",
        "room_config": {...}
    }
}
```

### 2. Event Extraction
- Check for `event` field first
- Fall back to `action` field for compatibility
- Return error if neither exists

### 3. Support Check
- Verify event is in `ALL_EVENTS` set
- Return `unsupported_event` error if not

### 4. Room State Retrieval
- Skip for lobby connections
- Get full room state for game rooms
- Convert to adapter-expected format

### 5. Adapter Routing
- Pass to `adapter_wrapper.try_handle_with_adapter()`
- Include WebSocket, message, room_id, room_state
- Adapter determines specific handler

### 6. Response Handling
- Adapter returns response dict or None
- Response sent back through WebSocket
- Errors wrapped in standard format

## Message Formats

### Incoming Message
```json
{
    "event": "string",     // Event name
    "data": {              // Event-specific data
        // Varies by event
    }
}
```

### Success Response
```json
{
    "event": "response_event",
    "data": {
        // Event-specific response data
    }
}
```

### Error Response
```json
{
    "event": "error",
    "data": {
        "message": "Human readable error",
        "type": "error_type",
        "details": "Optional details"
    }
}
```

## Error Types

| Type | Description |
|------|-------------|
| `routing_error` | General routing failure |
| `validation_error` | Invalid message format |
| `unsupported_event` | Unknown event type |
| `room_not_found` | Room doesn't exist |
| `adapter_error` | Adapter processing failed |

## Room State Format

When room state is needed, it's provided in this format:

```json
{
    "room_id": "ROOM123",
    "host": "player_id",
    "players": [
        {
            "player_id": "id",
            "name": "Player Name",
            "is_bot": false,
            "is_host": true,
            "seat_position": 0
        }
    ],
    "status": "waiting",
    "game_config": {
        "max_players": 4,
        "max_score": 50,
        "allow_bot_start": true
    },
    "current_round": 1,
    "max_players": 4
}
```

## Special Cases

### Lobby Connections
- Room ID is "lobby"
- No room state needed
- Limited to lobby events

### Room Validation
- Non-lobby connections validate room exists
- Send `room_not_found` if invalid
- Connection stays open for client handling

### Message Queuing
- Check for queued messages after routing
- Send any pending messages to reconnected players
- Handled automatically by router

## Performance Optimizations

1. **Event Set Lookups**: O(1) event support checks
2. **Category Classification**: Quick event categorization
3. **Lazy Room State**: Only fetch when needed
4. **Direct Routing**: Minimal indirection

## Future Enhancements

1. **Event Versioning**: Support multiple event versions
2. **Custom Routing Rules**: Dynamic routing configuration
3. **Event Metrics**: Track usage patterns
4. **Circuit Breakers**: Protect against handler failures