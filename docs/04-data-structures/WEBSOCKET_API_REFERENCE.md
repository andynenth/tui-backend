# WebSocket API Reference - Complete Guide

## Overview

This document is the authoritative reference for all WebSocket operations in Liap Tui. Since January 2025, WebSocket is the **ONLY** supported method for all game operations. REST endpoints exist only for monitoring and administrative functions.

## Table of Contents

1. [Connection](#connection)
2. [Message Protocol](#message-protocol)
3. [Connection Management](#connection-management)
4. [Room Operations](#room-operations)
5. [Game Actions](#game-actions)
6. [Server Events](#server-events)
7. [Error Handling](#error-handling)
8. [Data Models](#data-models)
9. [Integration Guide](#integration-guide)
10. [Testing](#testing)
11. [Migration Guide](#migration-guide)

## Connection

### WebSocket Endpoint
```
ws://localhost:8000/ws/{room_id}
```

**Parameters:**
- `room_id` - Game room identifier or `"lobby"` for lobby operations

**Connection Types:**
- **Lobby**: `ws://localhost:8000/ws/lobby` - Room browsing and management
- **Game Room**: `ws://localhost:8000/ws/{room_id}` - Gameplay operations

### Connection Flow

```javascript
// 1. Establish connection
const ws = new WebSocket('ws://localhost:8000/ws/ROOM123');

// 2. Wait for open
ws.onopen = () => {
    // 3. Send client ready
    ws.send(JSON.stringify({
        event: 'client_ready',
        data: {}
    }));
};

// 4. Handle messages
ws.onmessage = (message) => {
    const data = JSON.parse(message.data);
    handleServerEvent(data);
};
```

## Message Protocol

### Request Format (Client → Server)
```javascript
// Client message format
{
    event: string,           // Event name
    data: object,            // Event payload

    // Optional metadata
    sequence?: number,       // Client sequence number
    timestamp?: number       // Client timestamp
}
```

### Response Format (Server → Client)
```javascript
// Server message format
{
    event: string,           // Event type
    data: object,            // Event data

    // Optional fields
    error?: object,          // Error details
    room_id?: string,        // Room context
    sequence?: number,       // Echo client sequence
    server_time?: number     // Server timestamp
}
```

## Connection Management

### Initialization

#### `client_ready`
Signal client is ready to receive updates. **Always send after connecting.**

```json
{
    "event": "client_ready",
    "data": {}
}
```

### Keep-Alive

#### `ping`
Heartbeat to prevent timeout (auto-sent every 30s by NetworkService).

```json
{
    "event": "ping",
    "data": {
        "timestamp": 1752572748420
    }
}
```

**Response:** `pong`
```json
{
    "event": "pong",
    "data": {
        "timestamp": 1752572748420,
        "server_time": 1752572748.425
    }
}
```

### Synchronization

#### `sync_request`
Request state sync after disconnection.

```json
{
    "event": "sync_request",
    "data": {
        "client_id": "client_uuid",
        "last_sequence": 42
    }
}
```

## Room Operations

All room operations are WebSocket-only. No REST endpoints exist for these.

### Lobby Operations

These require connection to `ws://localhost:8000/ws/lobby`.

#### `request_room_list`
Get available rooms.

```json
{
    "event": "request_room_list",
    "data": {}
}
```

**Response:** [`room_list_update`](#room_list_update)

#### `create_room`
Create new game room.

```json
{
    "event": "create_room",
    "data": {
        "player_name": "Alice"
    }
}
```

**Validation:**
- `player_name`: 1-50 chars, alphanumeric + spaces

**Response:** [`room_created`](#room_created)

#### `join_room`
Join existing room.

```json
{
    "event": "join_room",
    "data": {
        "room_id": "ROOM123",
        "player_name": "Bob"
    }
}
```

**Validation:**
- `room_id`: 1-50 chars, alphanumeric
- `player_name`: 1-50 chars, no HTML

**Response:** [`room_joined`](#room_joined)

### Room Management

These require connection to specific room.

#### `get_room_state`
Request current state.

```json
{
    "event": "get_room_state",
    "data": {}
}
```

**Response:** [`room_update`](#room_update)

#### `add_bot`
Add bot player (host only).

```json
{
    "event": "add_bot",
    "data": {
        "slot_id": 3
    }
}
```

**Validation:**
- `slot_id`: 1-4, must be empty

#### `remove_player`
Remove player/bot (host only).

```json
{
    "event": "remove_player",
    "data": {
        "slot_id": 3
    }
}
```

**Validation:**
- Cannot remove host
- Must be host to remove

#### `leave_room`
Leave current room.

```json
{
    "event": "leave_room",
    "data": {}
}
```

#### `start_game`
Start game (host only, needs 4 players).

```json
{
    "event": "start_game",
    "data": {}
}
```

**Response:**
1. [`game_started`](#game_started)
2. [`phase_change`](#phase_change) with initial state

## Game Actions

### Declaration Phase

#### `declare`
Make pile count declaration.

```json
{
    "event": "declare",
    "data": {
        "player_name": "Alice",
        "value": 3
    }
}
```

**Validation:**
- `value`: 0-8
- Total ≠ 8
- Must be your turn

### Turn Phase

#### `play` / `play_pieces`
Play pieces during turn.

```json
{
    "event": "play",
    "data": {
        "player_name": "Alice",
        "indices": [0, 1]
    }
}
```

**Alternative:**
```json
{
    "event": "play_pieces",
    "data": {
        "player_name": "Alice",
        "piece_indices": [0, 1]
    }
}
```

**Validation:**
- `indices`: 1-6 items, valid hand indices
- Must match required piece count

### Redeal Actions

#### `request_redeal`
Request redeal for weak hand.

```json
{
    "event": "request_redeal",
    "data": {
        "player_name": "Alice"
    }
}
```

#### `accept_redeal` / `decline_redeal`
Respond to redeal opportunity.

```json
{
    "event": "accept_redeal",
    "data": {
        "player_name": "Alice"
    }
}
```

**Unified format:**
```json
{
    "event": "redeal_decision",
    "data": {
        "player_name": "Alice",
        "choice": "accept"
    }
}
```

## Server Events

### Connection Events

#### `error`
Error notification.

```json
{
    "event": "error",
    "data": {
        "message": "Invalid play: Must play 2 pieces",
        "type": "validation_error",
        "code": "INVALID_PLAY",
        "details": {
            "required_count": 2,
            "played_count": 1
        }
    }
}
```

### Room Events

#### `room_created`
Room creation confirmation.

```json
{
    "event": "room_created",
    "data": {
        "room_id": "ROOM123",
        "host_name": "Alice",
        "success": true
    }
}
```

#### `room_joined`
Join confirmation.

```json
{
    "event": "room_joined",
    "data": {
        "room_id": "ROOM123",
        "player_name": "Bob",
        "assigned_slot": 2,
        "success": true
    }
}
```

#### `room_update`
Room state change.

```json
{
    "event": "room_update",
    "data": {
        "room_id": "ROOM123",
        "host_name": "Alice",
        "started": false,
        "players": [
            {
                "slot": 1,
                "name": "Alice",
                "is_bot": false,
                "is_host": true,
                "is_connected": true
            }
        ]
    }
}
```

#### `room_list_update`
Available rooms (lobby only).

```json
{
    "event": "room_list_update",
    "data": {
        "rooms": [
            {
                "room_id": "ROOM123",
                "host_name": "Alice",
                "players": [...],
                "occupied_slots": 3,
                "total_slots": 4,
                "started": false
            }
        ]
    }
}
```

### Game Flow Events

#### `game_started`
Game begun.

```json
{
    "event": "game_started",
    "data": {
        "room_id": "ROOM123",
        "success": true
    }
}
```

#### `phase_change`
Primary game state update.

```json
{
    "event": "phase_change",
    "data": {
        "phase": "declaration",
        "round": 1,
        "sequence": 5,
        "timestamp": 1234567890.123,
        "reason": "All players ready",

        "allowed_actions": ["declare"],

        "phase_data": {
            // Phase-specific data
        },

        "players": {
            // Player states
        }
    }
}
```

**Phases:**
- `waiting` - Waiting for players
- `preparation` - Dealing and redeals
- `round_start` - Setting round starter
- `declaration` - Pile count declarations
- `turn` - Playing pieces
- `turn_results` - Turn outcome
- `scoring` - Round scoring
- `game_over` - Game complete

#### `game_ended`
Game finished.

```json
{
    "event": "game_ended",
    "data": {
        "reason": "winner_found",
        "winner": "Alice",
        "final_scores": {
            "Alice": 52,
            "Bob": 45
        }
    }
}
```

## Error Handling

### Error Format
```json
{
    "event": "error",
    "data": {
        "message": "Human-readable description",
        "type": "error_category",
        "code": "ERROR_CODE",
        "details": {}
    }
}
```

### Error Types
- `validation_error` - Invalid input
- `permission_error` - Unauthorized action
- `game_error` - Invalid game state
- `connection_error` - WebSocket issues

### Common Error Codes
| Code | Description |
|------|-------------|
| `ROOM_NOT_FOUND` | Room doesn't exist |
| `ROOM_FULL` | Room at capacity |
| `NOT_YOUR_TURN` | Out of turn action |
| `INVALID_PLAY` | Invalid piece combination |
| `PERMISSION_DENIED` | Unauthorized |
| `GAME_ALREADY_STARTED` | Can't modify started game |

## Data Models

### Player Model
```javascript
/**
 * @typedef {Object} Player
 * @property {string} name
 * @property {number} slot
 * @property {boolean} is_bot
 * @property {boolean} is_host
 * @property {boolean} is_connected
 * @property {number} [score]
 * @property {number} [declared]
 * @property {number} [captured_piles]
 * @property {number} [hand_size]
 */
```

### Piece Model
```javascript
/**
 * @typedef {Object} Piece
 * @property {string} kind - e.g., "GENERAL_RED"
 * @property {number} point
 * @property {string} [name] - "GENERAL"
 * @property {string} [color] - "RED"
 */
```

### Room Model
```javascript
/**
 * @typedef {Object} Room
 * @property {string} room_id
 * @property {string} host_name
 * @property {Player[]} players
 * @property {boolean} started
 * @property {number} occupied_slots
 * @property {number} total_slots
 */
```

## Integration Guide

### JavaScript
```javascript
class GameClient {
    constructor() {
        this.ws = null;
        this.roomId = null;
    }

    connect(roomId) {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(`ws://localhost:8000/ws/${roomId}`);
            this.roomId = roomId;

            this.ws.onopen = () => {
                this.send('client_ready', {});
                resolve();
            };

            this.ws.onerror = reject;
        });
    }

    send(event, data) {
        this.ws.send(JSON.stringify({ event, data }));
    }
}
```

### Python
```python
import asyncio
import websockets
import json

class GameClient:
    async def connect(self, room_id: str):
        uri = f"ws://localhost:8000/ws/{room_id}"
        self.ws = await websockets.connect(uri)
        await self.send("client_ready", {})

    async def send(self, event: str, data: dict):
        message = json.dumps({"event": event, "data": data})
        await self.ws.send(message)
```

### React Integration
```jsx
import { useWebSocket } from './hooks/useWebSocket';

function GameRoom({ roomId }) {
    const { connected, send, lastMessage } = useWebSocket(roomId);

    const handlePlay = (indices) => {
        send('play', {
            player_name: currentPlayer,
            indices
        });
    };

    return (
        <div>
            {connected ? 'Connected' : 'Connecting...'}
        </div>
    );
}
```

## Testing

### Unit Testing WebSocket Events
```javascript
// Mock WebSocket for testing
class MockWebSocket {
    constructor(url) {
        this.url = url;
        this.readyState = WebSocket.CONNECTING;
        setTimeout(() => {
            this.readyState = WebSocket.OPEN;
            this.onopen?.();
        }, 0);
    }

    send(data) {
        const message = JSON.parse(data);
        // Simulate server response
        this.onmessage?.({
            data: JSON.stringify({
                event: 'echo',
                data: message.data
            })
        });
    }
}
```

### Integration Testing
```python
import pytest
import asyncio
from test_utils import GameTestClient

@pytest.mark.asyncio
async def test_full_game_flow():
    client = GameTestClient()
    await client.connect("test_room")

    # Create room
    response = await client.send_and_wait("create_room", {
        "player_name": "TestPlayer"
    })
    assert response["event"] == "room_created"
```

### Load Testing
```bash
# WebSocket load test with Artillery
artillery run websocket-load-test.yml

# Simple Python load test
python tests/load/websocket_load_test.py --clients 100 --duration 60
```

## Migration Guide

For developers migrating from REST-based systems:

### Key Changes
1. **No REST endpoints** for game operations
2. **Persistent connections** instead of request/response
3. **Event-driven** architecture
4. **Real-time updates** without polling

### Migration Checklist
- [ ] Replace REST calls with WebSocket events
- [ ] Implement connection management
- [ ] Add heartbeat mechanism
- [ ] Handle reconnection logic
- [ ] Update error handling
- [ ] Test real-time features

### Common Pitfalls
1. **Forgetting `client_ready`** - Always send after connect
2. **No heartbeat** - Connection may timeout
3. **Synchronous thinking** - Events are asynchronous
4. **Missing reconnection** - Handle connection loss

## Performance Considerations

### Connection Pooling
- Reuse connections when possible
- Implement connection pooling for multiple rooms
- Clean up closed connections

### Message Batching
- Batch rapid updates when possible
- Use debouncing for user actions
- Implement message queuing

### Monitoring
- Track connection count
- Monitor message latency
- Log disconnection reasons
- Measure reconnection time

## Security

### Input Validation
- Sanitize all text inputs
- Validate array lengths
- Check numeric ranges
- Prevent injection attacks

### Rate Limiting
- Connection attempts limited
- Message frequency throttled
- Resource usage monitored

### Authentication (Future)
- Token-based authentication planned
- Session management via WebSocket
- Secure room access control

## Best Practices

1. **Always validate** inputs on both sides
2. **Handle all events** gracefully
3. **Implement reconnection** with exponential backoff
4. **Use structured logging** for debugging
5. **Test edge cases** like disconnection
6. **Monitor performance** metrics
7. **Document custom events** clearly

## Support Resources

- Example implementations in `/examples/websocket/`
- Test utilities in `/tests/websocket/`
- Performance tools in `/tools/websocket/`
- Debug mode for development

## Version History

- **v2.0** (Jan 2025) - WebSocket-only architecture
- **v1.0** - Mixed REST/WebSocket approach

---

*Last Updated: January 2025*
*This is the authoritative WebSocket API reference*
