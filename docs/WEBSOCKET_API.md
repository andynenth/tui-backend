# WebSocket API Documentation

This document serves as the official WebSocket API reference for the Liap Tui game. All room management and gameplay functionality is handled through WebSocket connections.

> **Important**: As of January 2025, WebSocket is the **ONLY** supported method for all game operations. REST API endpoints for room management and game actions have been completely removed. The remaining REST endpoints are only for health monitoring and administrative functions.

## Table of Contents

1. [Connection](#connection)
2. [Message Format](#message-format)
3. [Connection Management](#connection-management)
4. [Room Management](#room-management-websocket-only)
5. [Game Actions](#game-action-events)
6. [Server Events](#server--client-events)
7. [Validation Rules](#validation-rules)
8. [Error Handling](#error-handling)
9. [Best Practices](#connection-best-practices)
10. [Complete Examples](#complete-examples)

## Connection

### WebSocket Endpoint
```
ws://localhost:8000/ws/{room_id}
```

**Parameters:**
- `room_id` - The game room identifier or `"lobby"` for the lobby connection

**Connection Types:**
- **Lobby Connection**: `ws://localhost:8000/ws/lobby` - For browsing and managing rooms
- **Room Connection**: `ws://localhost:8000/ws/{room_id}` - For game room and gameplay

**Example:**
```javascript
// Connect to lobby for room browsing
const lobbyWs = new WebSocket('ws://localhost:8000/ws/lobby');

// Connect to specific game room
const gameWs = new WebSocket('ws://localhost:8000/ws/ROOM123');
```

## Message Format

All WebSocket messages use JSON format with a consistent structure.

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

## Connection Management

### Client Ready
Signal that the client is ready to receive game updates. **Always send this after connecting.**

#### `client_ready`
**Request:**
```json
{
  "event": "client_ready",
  "data": {}
}
```

**Purpose:** Ensures client receives initial state after connection.

### Heartbeat/Keep-Alive

The WebSocket connection includes an automatic heartbeat mechanism to prevent connection timeouts.

#### `ping`
Client heartbeat to keep connection alive.

**Request:**
```json
{
  "event": "ping",
  "data": {
    "timestamp": 1752572748420
  }
}
```

**Notes:**
- Sent automatically by NetworkService every 30 seconds
- Prevents proxy/firewall timeouts (typically 60-120 seconds)
- All connections automatically get heartbeat monitoring

#### `pong` (Server → Client)
Server response to client ping.

**Response:**
```json
{
  "event": "pong",
  "data": {
    "timestamp": 1752572748420,      // Echo of client timestamp
    "server_time": 1752572748.425    // Server's current time
  }
}
```

### Synchronization & Reliability

#### `sync_request`
Request state synchronization (for recovery after disconnection).

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

## Room Management (WebSocket Only)

All room operations are performed through WebSocket events. There are **NO** REST API endpoints for room management.

### Room Operations Summary

| Operation | WebSocket Event | Required Connection | Who Can Use |
|-----------|----------------|-------------------|-------------|
| List Rooms | `request_room_list` | Lobby | Anyone |
| Create Room | `create_room` | Lobby | Anyone |
| Join Room | `join_room` | Lobby | Anyone |
| Get Room State | `get_room_state` | Room | Room members |
| Add Bot | `add_bot` | Room | Host only |
| Remove Player | `remove_player` | Room | Host only |
| Leave Room | `leave_room` | Room | Room members |
| Start Game | `start_game` | Room | Host only |

### Lobby Operations

These events require a connection to the lobby (`ws://localhost:8000/ws/lobby`).

#### `request_room_list`
Get list of available game rooms.

**Request:**
```json
{
  "event": "request_room_list",
  "data": {}
}
```

**Response:** Server sends [`room_list_update`](#room_list_update) event.

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
- `player_name`: Required, 1-50 characters, alphanumeric + spaces, no HTML

**Response:** Server sends [`room_created`](#room_created) event.

**Example Flow:**
1. Connect to lobby
2. Send `create_room`
3. Receive `room_created` with room_id
4. Disconnect from lobby
5. Connect to new room using room_id

#### `join_room`
Join an existing game room.

**Request:**
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
- `room_id`: Required, 1-50 characters, alphanumeric only
- `player_name`: Required, 1-50 characters, no HTML/special characters

**Response:** Server sends [`room_joined`](#room_joined) event.

### Room Management Operations

These events require a connection to a specific room (`ws://localhost:8000/ws/{room_id}`).

#### `get_room_state`
Request current room state (players, status, etc).

**Request:**
```json
{
  "event": "get_room_state",
  "data": {}
}
```

**Response:** Server sends [`room_update`](#room_update) event with full room state.

#### `add_bot`
Add a bot player to an empty slot (host only).

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
- Must be host to add bots
- Slot must be empty

**Response:** Server sends [`room_update`](#room_update) to all room members.

#### `remove_player`
Remove a player or bot from a slot (host only).

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
- Must be host to remove players
- Cannot remove the host

**Response:** Server sends [`room_update`](#room_update) to all room members.

#### `leave_room`
Leave the current room.

**Request:**
```json
{
  "event": "leave_room",
  "data": {
    "player_name": "Alice"  // Optional, server knows who you are
  }
}
```

**Notes:**
- If host leaves, room is closed
- Other players receive [`player_left`](#player_left) or [`room_closed`](#room_closed) event

#### `start_game`
Start the game (host only, requires 4 players).

**Request:**
```json
{
  "event": "start_game",
  "data": {}
}
```

**Validation:**
- Must be host
- Exactly 4 players required (humans or bots)
- Game not already started

**Response:** 
1. Server sends [`game_started`](#game_started) to all players
2. Immediately followed by [`phase_change`](#phase_change) with initial game state

## Game Action Events

These events are used during active gameplay.

### Declaration Phase

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
- `player_name`: Must match your player name
- `value`: Integer 0-8
- Must be your turn to declare

**Game Rules:**
- Total declarations cannot equal 8 (last player restricted)
- After 2 consecutive zeros, must declare non-zero
- Declaration represents target pile count

### Turn Phase

#### `play` / `play_pieces`
Play pieces during your turn.

**Request:**
```json
{
  "event": "play",
  "data": {
    "player_name": "Alice",
    "indices": [0, 1]  // Indices of pieces in your hand
  }
}
```

**Alternative format (also accepted):**
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
- `player_name`: Must match your player name
- `indices`: Array of 1-6 integers (0-based index in hand)
- Must be your turn

**Game Rules:**
- First play of turn: 1-6 pieces of valid combination
- Subsequent plays: Must match piece count of current turn
- Valid combinations: Single, Pair, Triple, Straight, etc.

### Preparation Phase (Redeal)

#### `request_redeal`
Request redeal for weak hand (only during preparation phase).

**Request:**
```json
{
  "event": "request_redeal",
  "data": {
    "player_name": "Alice"
  }
}
```

**Validation:**
- Must have weak hand (no piece > 9 points)
- Only available in preparation phase

#### `accept_redeal` / `decline_redeal`
Respond to redeal opportunity when multiple players have weak hands.

**Request:**
```json
{
  "event": "accept_redeal",
  "data": {
    "player_name": "Alice"
  }
}
```

**Alternative unified format:**
```json
{
  "event": "redeal_decision",
  "data": {
    "player_name": "Alice",
    "choice": "accept"  // or "decline"
  }
}
```

### Other Game Actions

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
Leave the current game and return to lobby.

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

These events are sent by the server to update clients about game state changes.

### Connection & Error Events

#### `error`
Error notification for any invalid action.

**Response:**
```json
{
  "event": "error",
  "data": {
    "message": "Invalid play: Must play 2 pieces",
    "type": "validation_error",
    "details": {
      "required_count": 2,
      "played_count": 1
    }
  }
}
```

**Error Types:**
- `validation_error` - Invalid input data
- `permission_error` - Action not allowed for player
- `game_error` - Invalid game state for action
- `connection_error` - WebSocket connection issues

### Room Events

#### `room_created`
Confirmation that room was created successfully.

**Response:**
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
Confirmation that you joined a room successfully.

**Response:**
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
Broadcast when room state changes (player joins/leaves, bot added, etc).

**Response:**
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
      },
      {
        "slot": 2,
        "name": "Bob",
        "is_bot": false,
        "is_host": false,
        "is_connected": true
      },
      {
        "slot": 3,
        "name": "Bot 1",
        "is_bot": true,
        "is_host": false,
        "is_connected": true
      },
      null  // Empty slot 4
    ]
  }
}
```

#### `room_list_update`
List of available rooms (sent to lobby connections).

**Response:**
```json
{
  "event": "room_list_update",
  "data": {
    "rooms": [
      {
        "room_id": "ROOM123",
        "host_name": "Alice",
        "players": [
          {"name": "Alice", "is_bot": false},
          {"name": "Bob", "is_bot": false},
          {"name": "Bot 1", "is_bot": true},
          null
        ],
        "occupied_slots": 3,
        "total_slots": 4,
        "started": false
      }
    ],
    "timestamp": 1234567890
  }
}
```

#### `room_closed`
Room was closed (usually because host left).

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

#### `player_left`
A player left the room.

**Response:**
```json
{
  "event": "player_left",
  "data": {
    "player_name": "Bob",
    "slot": 2
  }
}
```

### Game Flow Events

#### `game_started`
Game has begun successfully.

**Response:**
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
The primary game state update event. Sent automatically whenever game phase changes.

**Response:**
```json
{
  "event": "phase_change",
  "data": {
    "phase": "declaration",
    "round": 1,
    "sequence": 5,
    "timestamp": 1234567890.123,
    "reason": "All players ready, starting declarations",
    
    "allowed_actions": ["declare"],
    
    "phase_data": {
      "current_declarer": "Alice",
      "declaration_order": ["Alice", "Bob", "Bot 1", "Bot 2"],
      "declarations": {
        "Bob": 2,
        "Bot 1": 1
      },
      "total_declared": 3,
      "redeal_multiplier": 1.0
    },
    
    "players": {
      "Alice": {
        "name": "Alice",
        "hand": ["GENERAL_RED", "CANNON_BLACK", "SOLDIER_RED", ...],
        "hand_size": 8,
        "declared": null,
        "captured_piles": 0,
        "score": 15,
        "is_bot": false,
        "is_connected": true
      },
      "Bob": {
        "name": "Bob",
        "hand_size": 8,  // Other players' hands are hidden
        "declared": 2,
        "captured_piles": 1,
        "score": 20,
        "is_bot": false,
        "is_connected": true
      }
      // ... other players
    }
  }
}
```

**Game Phases:**
- `waiting` - Waiting for players
- `preparation` - Dealing cards and handling redeals
- `declaration` - Players declare target pile counts
- `turn` - Turn-based piece playing
- `turn_results` - Show results of each turn
- `scoring` - Calculate round scores
- `game_over` - Game finished

#### `game_ended`
Game has finished.

**Response:**
```json
{
  "event": "game_ended",
  "data": {
    "reason": "winner_found",
    "message": "Alice wins with 52 points!",
    "final_scores": {
      "Alice": 52,
      "Bob": 45,
      "Bot 1": 38,
      "Bot 2": 41
    },
    "winner": "Alice"
  }
}
```

### Turn-Specific Events

#### `play`
Broadcast when a player makes a play during turn phase.

**Response:**
```json
{
  "event": "play",
  "data": {
    "player": "Alice",
    "pieces": ["CANNON_RED", "CANNON_BLACK"],
    "piece_indices": [0, 3],
    "valid": true,
    "play_value": 16,
    "play_type": "PAIR"
  }
}
```

#### `turn_complete`
Turn has finished, showing results.

**Response:**
```json
{
  "event": "turn_complete",
  "data": {
    "turn_number": 3,
    "winner": "Bob",
    "winning_play": {
      "player": "Bob",
      "pieces": ["SOLDIER_BLACK", "SOLDIER_BLACK"],
      "type": "PAIR",
      "value": 4
    },
    "all_plays": [
      {
        "player": "Alice",
        "pieces": ["GENERAL_RED", "GENERAL_BLACK"],
        "type": "PAIR",
        "value": 28
      },
      {
        "player": "Bob",
        "pieces": ["SOLDIER_BLACK", "SOLDIER_BLACK"],
        "type": "PAIR",
        "value": 4
      }
      // ... other players
    ],
    "pile_pieces": 8,  // Total pieces in this turn's pile
    "player_piles": {
      "Alice": 1,
      "Bob": 2,
      "Bot 1": 0,
      "Bot 2": 1
    },
    "next_starter": "Bob",
    "all_hands_empty": false
  }
}
```

### Redeal Events

#### `weak_hand_detected`
Players with weak hands have been identified.

**Response:**
```json
{
  "event": "weak_hand_detected",
  "data": {
    "weak_players": ["Alice", "Bot 2"],
    "awaiting_decisions": true
  }
}
```

#### `redeal_decision_made`
A player has made their redeal decision.

**Response:**
```json
{
  "event": "redeal_decision_made",
  "data": {
    "player": "Alice",
    "choice": "accept"
  }
}
```

#### `redeal_complete`
Redeal process has finished.

**Response:**
```json
{
  "event": "redeal_complete",
  "data": {
    "players_redealt": ["Bot 2"],
    "new_starter": "Bot 2",
    "redeal_multiplier": 1.5
  }
}
```

## Validation Rules

### Input Sanitization
- **Player Names**: 1-50 characters, alphanumeric + spaces, no HTML/special chars
- **Room IDs**: 1-50 characters, alphanumeric only (usually 6 chars)
- **Text Fields**: No `<`, `>`, `&`, quotes to prevent XSS
- **Arrays**: Maximum 100 items to prevent resource exhaustion

### Game-Specific Validation
- **Declaration Values**: Integer 0-8
- **Slot IDs**: Integer 1-4
- **Piece Indices**: Integer 0-31, max 6 per play
- **Redeal Choices**: Exactly "accept" or "decline"

### Security Features
- XSS prevention through input sanitization
- SQL injection prevention
- Buffer overflow protection via length limits
- Resource exhaustion prevention via array size limits
- Rate limiting on connection attempts

## Error Handling

### Standard Error Format
```json
{
  "event": "error",
  "data": {
    "message": "Human-readable error description",
    "type": "error_category",
    "code": "ERROR_CODE",
    "details": {
      // Optional additional context
    }
  }
}
```

### Common Error Codes
- `ROOM_NOT_FOUND` - Room doesn't exist
- `ROOM_FULL` - Room already has 4 players
- `NOT_YOUR_TURN` - Action attempted out of turn
- `INVALID_PLAY` - Pieces don't form valid combination
- `PERMISSION_DENIED` - Not authorized for this action
- `GAME_ALREADY_STARTED` - Cannot modify started game

## Connection Best Practices

1. **Connection Lifecycle**
   ```javascript
   // 1. Connect
   const ws = new WebSocket('ws://localhost:8000/ws/lobby');
   
   // 2. Wait for connection
   ws.onopen = () => {
     // 3. Send client_ready
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
   
   // 5. Handle disconnection
   ws.onclose = () => {
     // Implement reconnection logic
   };
   ```

2. **State Management**
   - Store `room_id` and `player_name` for reconnection
   - Keep track of current game phase
   - Cache player hand for display

3. **Error Recovery**
   - Implement exponential backoff for reconnection
   - Show connection status to user
   - Queue actions during temporary disconnection

4. **Performance**
   - Validate inputs locally before sending
   - Debounce rapid user actions
   - Use heartbeat to detect connection issues early

## Complete Examples

### Example 1: Create Room and Start Game
```javascript
class GameClient {
  constructor() {
    this.lobbyWs = null;
    this.gameWs = null;
    this.playerName = null;
    this.roomId = null;
  }

  async createRoomAndStart(playerName) {
    this.playerName = playerName;
    
    // 1. Connect to lobby
    this.lobbyWs = new WebSocket('ws://localhost:8000/ws/lobby');
    
    await new Promise((resolve) => {
      this.lobbyWs.onopen = () => {
        this.lobbyWs.send(JSON.stringify({
          event: 'client_ready',
          data: {}
        }));
        resolve();
      };
    });
    
    // 2. Set up lobby message handler
    this.lobbyWs.onmessage = (message) => {
      const { event, data } = JSON.parse(message.data);
      
      if (event === 'room_created') {
        this.roomId = data.room_id;
        this.connectToRoom();
      }
    };
    
    // 3. Create room
    this.lobbyWs.send(JSON.stringify({
      event: 'create_room',
      data: { player_name: playerName }
    }));
  }
  
  async connectToRoom() {
    // 4. Disconnect from lobby
    this.lobbyWs.close();
    
    // 5. Connect to room
    this.gameWs = new WebSocket(`ws://localhost:8000/ws/${this.roomId}`);
    
    this.gameWs.onopen = () => {
      this.gameWs.send(JSON.stringify({
        event: 'client_ready',
        data: {}
      }));
    };
    
    this.gameWs.onmessage = (message) => {
      const { event, data } = JSON.parse(message.data);
      
      switch(event) {
        case 'room_update':
          this.handleRoomUpdate(data);
          break;
        case 'game_started':
          console.log('Game started!');
          break;
        case 'phase_change':
          this.handlePhaseChange(data);
          break;
      }
    };
  }
  
  addBot(slotId) {
    this.gameWs.send(JSON.stringify({
      event: 'add_bot',
      data: { slot_id: slotId }
    }));
  }
  
  startGame() {
    this.gameWs.send(JSON.stringify({
      event: 'start_game',
      data: {}
    }));
  }
}
```

### Example 2: Game Action Handler
```javascript
class GameActionHandler {
  constructor(ws, playerName) {
    this.ws = ws;
    this.playerName = playerName;
    this.currentPhase = null;
    this.hand = [];
  }
  
  handlePhaseChange(data) {
    this.currentPhase = data.phase;
    
    // Update hand if available
    if (data.players[this.playerName]?.hand) {
      this.hand = data.players[this.playerName].hand;
    }
    
    // Handle phase-specific UI updates
    switch(data.phase) {
      case 'declaration':
        if (data.phase_data.current_declarer === this.playerName) {
          this.showDeclarationUI();
        }
        break;
        
      case 'turn':
        if (data.phase_data.current_player === this.playerName) {
          this.showPlayUI(data.phase_data.required_piece_count);
        }
        break;
        
      case 'preparation':
        if (data.phase_data.weak_hand_players?.includes(this.playerName)) {
          this.showRedealUI();
        }
        break;
    }
  }
  
  declare(value) {
    this.ws.send(JSON.stringify({
      event: 'declare',
      data: {
        player_name: this.playerName,
        value: value
      }
    }));
  }
  
  playPieces(indices) {
    this.ws.send(JSON.stringify({
      event: 'play',
      data: {
        player_name: this.playerName,
        indices: indices
      }
    }));
  }
  
  acceptRedeal() {
    this.ws.send(JSON.stringify({
      event: 'accept_redeal',
      data: {
        player_name: this.playerName
      }
    }));
  }
}
```

### Example 3: Reconnection Handler
```javascript
class ReconnectionHandler {
  constructor(roomId, playerName) {
    this.roomId = roomId;
    this.playerName = playerName;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
  }
  
  connect() {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${this.roomId}`);
    
    this.ws.onopen = () => {
      console.log('Connected successfully');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      
      // Send client ready
      this.ws.send(JSON.stringify({
        event: 'client_ready',
        data: {}
      }));
      
      // Request state sync
      this.ws.send(JSON.stringify({
        event: 'sync_request',
        data: {
          client_id: this.getClientId()
        }
      }));
    };
    
    this.ws.onclose = () => {
      console.log('Connection lost');
      this.attemptReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    // Set up heartbeat
    this.startHeartbeat();
  }
  
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }
    
    this.reconnectAttempts++;
    console.log(`Reconnecting in ${this.reconnectDelay}ms... (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);
    
    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }
  
  startHeartbeat() {
    setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          event: 'ping',
          data: {
            timestamp: Date.now()
          }
        }));
      }
    }, 30000); // Every 30 seconds
  }
  
  getClientId() {
    // Get or generate persistent client ID
    let clientId = localStorage.getItem('client_id');
    if (!clientId) {
      clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('client_id', clientId);
    }
    return clientId;
  }
}
```

## Migration Notes

For developers migrating from the old REST-based system:

1. **Room Management**: All room operations (create, join, list) now use WebSocket events via lobby connection
2. **Game Actions**: All game moves (declare, play) use WebSocket events on room connection
3. **State Updates**: Listen for `phase_change` events instead of polling
4. **Error Handling**: Errors come through WebSocket `error` events, not HTTP status codes
5. **Connection Management**: Maintain persistent WebSocket connections instead of individual HTTP requests

## Support

For questions or issues with the WebSocket API:
- Review error messages carefully - they include helpful details
- Check browser console for WebSocket connection status
- Ensure you're sending `client_ready` after connecting
- Verify your event names match exactly (case-sensitive)
- Test with the example code provided above