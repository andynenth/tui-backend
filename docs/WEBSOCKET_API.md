# WebSocket API Documentation

This document provides a complete reference for the Liap Tui WebSocket API, including all events, message formats, and validation rules.

## Connection

### WebSocket Endpoint
```
ws://localhost:8000/ws/{room_id}
```

**Parameters:**
- `room_id` - The game room identifier or `"lobby"` for the lobby connection

**Example:**
```javascript
// Connect to lobby
const lobbyWs = new WebSocket('ws://localhost:8000/ws/lobby');

// Connect to game room
const gameWs = new WebSocket('ws://localhost:8000/ws/room_abc123');
```

## Message Format

### Request Format (Client → Server)
```json
{
  "event": "event_name",
  "data": {
    // Event-specific payload
  }
}
```

### Response Format (Server → Client)
```json
{
  "event": "event_type",
  "data": {
    // Event-specific data
  }
}
```

## Client → Server Events

### Connection Management

#### `client_ready`
Signal that the client is ready to receive game updates.

**Request:**
```json
{
  "event": "client_ready",
  "data": {}
}
```

**Purpose:** Ensures client receives initial state after connection.

#### `sync_request`
Request state synchronization (for reliability features).

**Request:**
```json
{
  "event": "sync_request",
  "data": {
    "client_id": "client_uuid"
  }
}
```

#### `ack`
Acknowledge message receipt (reliability system).

**Request:**
```json
{
  "event": "ack",
  "data": {
    "sequence": 12345,
    "client_id": "client_uuid"
  }
}
```

### Lobby Events

#### `request_room_list` / `get_rooms`
Request list of available game rooms.

**Request:**
```json
{
  "event": "request_room_list",
  "data": {}
}
```

**Response:** Server sends `room_list_update` event.

#### `create_room`
Create a new game room.

**Request:**
```json
{
  "event": "create_room",
  "data": {
    "player_name": "Alice"
  }
}
```

**Validation:**
- `player_name`: Required, 1-50 characters, no HTML/special characters

**Response:** Server sends `room_created` event.

#### `join_room`
Join an existing game room.

**Request:**
```json
{
  "event": "join_room",
  "data": {
    "room_id": "room_abc123",
    "player_name": "Bob"
  }
}
```

**Validation:**
- `room_id`: Required, 1-50 characters, alphanumeric
- `player_name`: Required, 1-50 characters, no HTML/special characters

**Response:** Server sends `room_joined` event.

### Room Management Events

#### `get_room_state`
Request current room state.

**Request:**
```json
{
  "event": "get_room_state",
  "data": {}
}
```

**Response:** Server sends `room_state_update` event.

#### `add_bot`
Add a bot player to a room slot.

**Request:**
```json
{
  "event": "add_bot",
  "data": {
    "slot_id": 3
  }
}
```

**Validation:**
- `slot_id`: Required, integer 1-4

**Response:** Server sends `room_update` event.

#### `remove_player`
Remove a player or bot from a slot.

**Request:**
```json
{
  "event": "remove_player",
  "data": {
    "slot_id": 3
  }
}
```

**Validation:**
- `slot_id`: Required, integer 1-4

**Response:** Server sends `room_update` event.

#### `leave_room`
Leave the current room.

**Request:**
```json
{
  "event": "leave_room",
  "data": {
    "player_name": "Alice"  // Optional
  }
}
```

**Response:** Server sends `player_left` event.

#### `start_game`
Start the game (host only).

**Request:**
```json
{
  "event": "start_game",
  "data": {}
}
```

**Response:** Server sends `game_started` event, followed by `phase_change`.

### Game Action Events

#### `declare`
Make a pile count declaration.

**Request:**
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
- `player_name`: Required, must match connected player
- `value`: Required, integer 0-8

**Rules:**
- Last player cannot declare a value that makes total equal 8
- Players with 2 consecutive zero declarations must declare non-zero

#### `play` / `play_pieces`
Play pieces during turn phase.

**Request:**
```json
{
  "event": "play",
  "data": {
    "player_name": "Alice",
    "indices": [0, 1]  // or "piece_indices"
  }
}
```

**Validation:**
- `player_name`: Required, must match connected player
- `indices`: Required, array of 1-6 integers (0-31)

**Rules:**
- Must play exact number of pieces if responding to a play
- Pieces must form valid combinations (singles, pairs, triples, etc.)

#### `request_redeal`
Request redeal for weak hand (no piece > 9 points).

**Request:**
```json
{
  "event": "request_redeal",
  "data": {
    "player_name": "Alice"
  }
}
```

**Response:** Server processes and sends `redeal_success` or error.

#### `accept_redeal` / `decline_redeal`
Respond to redeal opportunity.

**Request:**
```json
{
  "event": "accept_redeal",  // or "decline_redeal"
  "data": {
    "player_name": "Alice"
  }
}
```

**Alternative format:**
```json
{
  "event": "redeal_decision",
  "data": {
    "player_name": "Alice",
    "choice": "accept"  // or "decline"
  }
}
```

#### `player_ready`
Signal readiness in various game phases.

**Request:**
```json
{
  "event": "player_ready",
  "data": {
    "player_name": "Alice"
  }
}
```

#### `leave_game`
Leave the current game (return to lobby).

**Request:**
```json
{
  "event": "leave_game",
  "data": {
    "player_name": "Alice"
  }
}
```

## Server → Client Events

### Connection Events

#### `error`
Error notification.

**Response:**
```json
{
  "event": "error",
  "data": {
    "message": "Invalid play: Must play 2 pieces",
    "type": "validation_error"
  }
}
```

### Room Events

#### `room_created`
Room successfully created.

**Response:**
```json
{
  "event": "room_created",
  "data": {
    "room_id": "room_abc123",
    "host_name": "Alice",
    "success": true
  }
}
```

#### `room_joined`
Successfully joined room.

**Response:**
```json
{
  "event": "room_joined",
  "data": {
    "room_id": "room_abc123",
    "player_name": "Bob",
    "assigned_slot": 2,
    "success": true
  }
}
```

#### `room_update`
Room state changed.

**Response:**
```json
{
  "event": "room_update",
  "data": {
    "players": [
      {
        "slot": 1,
        "name": "Alice",
        "is_bot": false,
        "is_connected": true
      },
      {
        "slot": 2,
        "name": "Bot 1",
        "is_bot": true,
        "is_connected": true
      }
    ],
    "host_name": "Alice",
    "room_id": "room_abc123",
    "started": false
  }
}
```

#### `room_list_update`
Available rooms list (lobby connection).

**Response:**
```json
{
  "event": "room_list_update",
  "data": {
    "rooms": [
      {
        "id": "room_abc123",
        "host": "Alice",
        "players": 2,
        "max_players": 4,
        "started": false
      }
    ],
    "timestamp": 1234567890
  }
}
```

#### `room_closed`
Room was deleted.

**Response:**
```json
{
  "event": "room_closed",
  "data": {
    "message": "Room closed - host left",
    "reason": "host_left"
  }
}
```

### Game Flow Events

#### `game_started`
Game has begun.

**Response:**
```json
{
  "event": "game_started",
  "data": {
    "room_id": "room_abc123",
    "success": true
  }
}
```

#### `phase_change`
Game phase transition (automatic broadcast).

**Response:**
```json
{
  "event": "phase_change",
  "data": {
    "phase": "declaration",
    "allowed_actions": ["declare"],
    "phase_data": {
      "current_declarer": "Alice",
      "declarations": {
        "Bob": 2
      },
      "declaration_order": ["Alice", "Bob", "Bot 1", "Bot 2"]
    },
    "players": {
      "Alice": {
        "hand": ["CANNON_RED", "CHARIOT_BLACK", ...],
        "hand_size": 8,
        "declared": 0,
        "captured_piles": 0,
        "score": 15
      }
    },
    "round": 1,
    "sequence": 5,
    "timestamp": 1234567890.123,
    "reason": "Bob declared 2 piles"
  }
}
```

**Phases:**
- `preparation` - Dealing and redeal decisions
- `declaration` - Players declare target pile counts  
- `turn` - Turn-based piece playing
- `scoring` - Round scoring and win checking

#### `game_ended`
Game has finished.

**Response:**
```json
{
  "event": "game_ended",
  "data": {
    "reason": "winner_found",
    "message": "Alice wins with 52 points!"
  }
}
```

### Custom Game Events

#### `play`
Broadcast when a player makes a play.

**Response:**
```json
{
  "event": "play",
  "data": {
    "player": "Alice",
    "pieces": ["CANNON_RED", "CANNON_BLACK"],
    "valid": true,
    "play_value": 16,
    "play_type": "PAIR"
  }
}
```

#### `turn_complete`
Turn has finished.

**Response:**
```json
{
  "event": "turn_complete",
  "data": {
    "winner": "Bob",
    "winning_play": {
      "pieces": ["SOLDIER_BLACK", "SOLDIER_BLACK"],
      "type": "PAIR",
      "value": 4
    },
    "player_piles": {
      "Alice": 1,
      "Bob": 2
    },
    "turn_number": 3,
    "next_starter": "Bob",
    "all_hands_empty": false
  }
}
```

## Validation Rules

### Input Sanitization
- **Player Names**: 1-50 characters, alphanumeric + spaces, no HTML/special chars
- **Room IDs**: 1-50 characters, alphanumeric only
- **Text Fields**: No `<`, `>`, `&`, quotes to prevent XSS
- **Arrays**: Maximum 100 items to prevent resource exhaustion

### Game-Specific Validation
- **Declaration Values**: Integer 0-8
- **Slot IDs**: Integer 1-4
- **Piece Indices**: Integer 0-31, max 6 per play
- **Redeal Choices**: Exactly "accept" or "decline"

### Security Features
- XSS prevention through input sanitization
- SQL injection prevention (though using NoSQL)
- Buffer overflow protection via length limits
- Resource exhaustion prevention via array size limits

## Rate Limiting

The API implements rate limiting to prevent abuse:

### Connection Limits
- **5 connections per minute** per IP address
- Exceeding limit results in WebSocket close with code 1008 (Policy Violation)

### Message Limits
| Event Type | Limit | Period |
|------------|-------|--------|
| General messages | 120 | per minute |
| Declarations | 10 | per minute |
| Plays | 30 | per minute |

### Rate Limit Errors
When rate limited, you'll receive:
```json
{
  "event": "error",
  "data": {
    "message": "Rate limit exceeded for ws_play. Slow down!",
    "type": "rate_limit_error"
  }
}
```

### REST API Rate Limits
REST endpoints include rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait (on 429 responses)

## Error Handling

All errors follow this format:
```json
{
  "event": "error",
  "data": {
    "message": "Human-readable error description",
    "type": "error_category",
    "details": "Additional context (optional)"
  }
}
```

**Error Types:**
- `validation_error` - Invalid input data
- `permission_error` - Action not allowed for player
- `game_error` - Invalid game state for action
- `connection_error` - WebSocket connection issues

## Connection Best Practices

1. **Always send `client_ready` after connecting** to receive initial state
2. **Handle reconnection** - Store room_id and player_name to rejoin
3. **Listen for `phase_change`** - Primary source of game state updates
4. **Validate locally** before sending to reduce server rejections
5. **Handle `room_closed`** gracefully - Return user to lobby

## Example Integration

```javascript
// Connect to game room
const ws = new WebSocket('ws://localhost:8000/ws/room_abc123');

// Send client ready on connection
ws.onopen = () => {
  ws.send(JSON.stringify({
    event: 'client_ready',
    data: {}
  }));
};

// Handle messages
ws.onmessage = (message) => {
  const { event, data } = JSON.parse(message.data);
  
  switch(event) {
    case 'phase_change':
      updateGameState(data);
      break;
    case 'error':
      showError(data.message);
      break;
    // ... handle other events
  }
};

// Make a play
function playPieces(indices) {
  ws.send(JSON.stringify({
    event: 'play',
    data: {
      player_name: currentPlayer,
      indices: indices
    }
  }));
}
```