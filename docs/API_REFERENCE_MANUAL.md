# API Reference Manual

## Overview

This document provides comprehensive reference for all APIs, WebSocket events, and integration patterns in the Liap Tui game system.

## Table of Contents

1. [WebSocket API](#websocket-api)
2. [HTTP REST API](#http-rest-api)
3. [Event Reference](#event-reference)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Integration Examples](#integration-examples)
7. [Testing Guide](#testing-guide)

---

## WebSocket API

### Connection

**Endpoint**: `ws://localhost:8000/ws/{room_id}`

#### Connection Flow
1. Connect to WebSocket endpoint with room_id
2. Send `client_ready` event
3. Receive current room/game state
4. Begin sending/receiving game events

#### Special Rooms
- `lobby` - For room list updates and room management

### Message Protocol

#### Request Format
```json
{
  "event": "event_name",
  "data": {
    // Event-specific payload
  }
}
```

#### Response Format
```json
{
  "event": "event_type",
  "data": {
    "timestamp": 1705320600.123,
    "room_id": "ROOM123",
    "sequence": 42,
    "_ack_required": false,
    // Event-specific data
  }
}
```

---

## Event Reference

### System Events

#### `client_ready`
**Direction**: Client → Server  
**Purpose**: Signal client is ready for communication

**Request**:
```json
{
  "event": "client_ready",
  "data": {}
}
```

**Response**: Current room/game state

#### `ack`
**Direction**: Bidirectional  
**Purpose**: Message acknowledgment for reliable delivery

**Format**:
```json
{
  "event": "ack",
  "data": {
    "sequence": 42,
    "message_id": "uuid-1234"
  }
}
```

#### `sync_request`
**Direction**: Client → Server  
**Purpose**: Request complete state synchronization

**Request**:
```json
{
  "event": "sync_request",
  "data": {
    "last_sequence": 35
  }
}
```

**Response**: `sync_response` with complete state

### Room Management Events

#### `create_room`
**Direction**: Client → Server  
**Purpose**: Create new game room

**Request**:
```json
{
  "event": "create_room",
  "data": {
    "host_name": "Player1"
  }
}
```

**Response**:
```json
{
  "event": "room_created",
  "data": {
    "room_id": "ROOM123",
    "host_name": "Player1",
    "success": true
  }
}
```

#### `join_room`
**Direction**: Client → Server  
**Purpose**: Join existing room

**Request**:
```json
{
  "event": "join_room",
  "data": {
    "room_id": "ROOM123",
    "player_name": "Player2"
  }
}
```

**Response**: `room_update` event

#### `get_room_state`
**Direction**: Client → Server  
**Purpose**: Request current room state

**Request**:
```json
{
  "event": "get_room_state",
  "data": {}
}
```

**Response**: `room_update` with current state

#### `add_bot`
**Direction**: Client → Server  
**Purpose**: Add bot to room slot

**Request**:
```json
{
  "event": "add_bot",
  "data": {
    "slot_id": 2
  }
}
```

**Response**: `room_update` with bot added

#### `remove_player`
**Direction**: Client → Server  
**Purpose**: Remove player/bot from slot

**Request**:
```json
{
  "event": "remove_player",
  "data": {
    "slot_id": 3
  }
}
```

**Response**: `room_update` with player removed

#### `leave_room`
**Direction**: Client → Server  
**Purpose**: Leave current room

**Request**:
```json
{
  "event": "leave_room",
  "data": {
    "player_name": "Player2"
  }
}
```

**Response**: `room_update` or `room_closed`

#### `start_game`
**Direction**: Client → Server  
**Purpose**: Start game (host only)

**Request**:
```json
{
  "event": "start_game",
  "data": {}
}
```

**Response**: `game_started` event

### Game Events

#### `declare`
**Direction**: Client → Server  
**Purpose**: Make pile count declaration

**Request**:
```json
{
  "event": "declare",
  "data": {
    "player_name": "Player1",
    "value": 3
  }
}
```

**Validation**:
- `value` must be integer 0-8
- Must be player's turn to declare
- Last player cannot make total equal 8

**Response**: `phase_change` with updated declarations

#### `play` / `play_pieces`
**Direction**: Client → Server  
**Purpose**: Play pieces during turn

**Request**:
```json
{
  "event": "play",
  "data": {
    "player_name": "Player1",
    "pieces": [0, 2, 4]
  }
}
```

**Validation**:
- Must be player's turn
- Piece count must match required count (after first player)
- Pieces must form valid combination

**Response**: `phase_change` and custom `play` event

#### `redeal_decision`
**Direction**: Client → Server  
**Purpose**: Accept or decline redeal for weak hand

**Request**:
```json
{
  "event": "redeal_decision",
  "data": {
    "player_name": "Player1",
    "accept": true
  }
}
```

**Alternative Events**:
```json
{
  "event": "accept_redeal",
  "data": {
    "player_name": "Player1"
  }
}

{
  "event": "decline_redeal", 
  "data": {
    "player_name": "Player1"
  }
}
```

### Broadcast Events

#### `phase_change`
**Direction**: Server → All Clients  
**Purpose**: Automatic broadcast on any state change

**Format**:
```json
{
  "event": "phase_change",
  "data": {
    "phase": "turn",
    "phase_data": {
      "current_player": "Player2",
      "turn_order": ["Player1", "Player2", "Player3", "Player4"],
      "required_piece_count": 3,
      "turn_plays": {
        "Player1": {
          "pieces": [...],
          "value": 12,
          "type": "PAIR"
        }
      },
      "turn_complete": false,
      "current_turn_number": 5
    },
    "sequence": 42,
    "timestamp": 1705320600.123
  }
}
```

#### `room_update`
**Direction**: Server → Room Clients  
**Purpose**: Room state changes

**Format**:
```json
{
  "event": "room_update",
  "data": {
    "room_id": "ROOM123",
    "host_name": "Player1",
    "started": false,
    "players": [
      {
        "name": "Player1",
        "is_bot": false,
        "is_host": true
      },
      {
        "name": "Bot 2", 
        "is_bot": true,
        "is_host": false
      },
      null,
      {
        "name": "Player4",
        "is_bot": false,
        "is_host": false
      }
    ],
    "occupied_slots": 3,
    "total_slots": 4
  }
}
```

#### `room_closed`
**Direction**: Server → Room Clients  
**Purpose**: Room was deleted

**Format**:
```json
{
  "event": "room_closed",
  "data": {
    "room_id": "ROOM123",
    "reason": "Host left room",
    "message": "The room has been closed"
  }
}
```

#### `game_started`
**Direction**: Server → Room Clients  
**Purpose**: Game has begun

**Format**:
```json
{
  "event": "game_started",
  "data": {
    "room_id": "ROOM123",
    "game_id": "GAME456",
    "players": ["Player1", "Player2", "Player3", "Player4"]
  }
}
```

#### Custom Game Events

##### `play`
**Direction**: Server → Room Clients  
**Purpose**: Player made a play (enhanced UX)

```json
{
  "event": "play",
  "data": {
    "player": "Player1",
    "pieces": [
      {"id": 1, "kind": "GENERAL_RED", "point": 10},
      {"id": 5, "kind": "HORSE_RED", "point": 4}
    ],
    "play_value": 14,
    "play_type": "PAIR"
  }
}
```

##### `turn_complete`
**Direction**: Server → Room Clients  
**Purpose**: Turn finished with results

```json
{
  "event": "turn_complete",
  "data": {
    "winner": "Player2",
    "winning_play": {
      "pieces": [...],
      "value": 18,
      "type": "THREE_OF_A_KIND"
    },
    "player_piles": {
      "Player1": 2,
      "Player2": 5,
      "Player3": 1,
      "Player4": 0
    },
    "turn_number": 3,
    "next_starter": "Player2",
    "all_hands_empty": false
  }
}
```

---

## HTTP REST API

### Room Management

#### Create Room
**Endpoint**: `POST /create-room`

**Request**:
```json
{
  "host_name": "Player1"
}
```

**Response**:
```json
{
  "room_id": "ROOM123",
  "success": true
}
```

#### List Rooms
**Endpoint**: `GET /list-rooms`

**Response**:
```json
{
  "rooms": [
    {
      "room_id": "ROOM123",
      "host_name": "Player1", 
      "occupied_slots": 3,
      "total_slots": 4,
      "started": false
    }
  ]
}
```

#### Join Room
**Endpoint**: `POST /join-room`

**Request**:
```json
{
  "room_id": "ROOM123",
  "player_name": "Player2"
}
```

**Response**:
```json
{
  "success": true,
  "room": {
    "room_id": "ROOM123",
    "players": [...],
    "started": false
  }
}
```

---

## Data Models

### Player
```typescript
interface Player {
  name: string;
  hand: Piece[];
  declared: number;  // 0-8
  piles: number;     // Captured piles
  score: number;     // Total score
  is_bot: boolean;
  seat_number: number;  // 1-4
  zero_declares_in_a_row: number;  // Consecutive zero declarations
}
```

### Piece
```typescript
interface Piece {
  id: number;
  kind: string;  // e.g., "GENERAL_RED"
  name: string;  // e.g., "GENERAL"
  color: string; // "RED" or "BLACK"
  point: number; // Point value
  symbol: string; // Unicode character
}
```

### Room
```typescript
interface Room {
  room_id: string;
  host_name: string;
  players: (Player | null)[]; // 4 slots
  started: boolean;
  game?: Game;
  created_at: string;
  occupied_slots: number;
  total_slots: number;
}
```

### Game State
```typescript
interface GameState {
  // Connection
  isConnected: boolean;
  roomId: string | null;
  playerName: string;
  
  // Game phase
  phase: Phase;
  phaseData: any;
  
  // Players
  players: Player[];
  myPlayerData: Player | null;
  
  // Game data
  myHand: Piece[];
  playerPiles: Record<string, number>;
  declarations: Record<string, number>;
  totalScores: Record<string, number>;
  
  // Turn state
  currentPlayer: string | null;
  turnNumber: number;
  requiredPieceCount: number | null;
  
  // Meta
  gameStarted: boolean;
  roundNumber: number;
  turnHistory: TurnPlay[];
}
```

### Play Types
```typescript
enum PlayType {
  SINGLE = "SINGLE",
  PAIR = "PAIR", 
  THREE_OF_A_KIND = "THREE_OF_A_KIND",
  STRAIGHT = "STRAIGHT",
  FOUR_OF_A_KIND = "FOUR_OF_A_KIND",
  EXTENDED_STRAIGHT = "EXTENDED_STRAIGHT",
  EXTENDED_STRAIGHT_5 = "EXTENDED_STRAIGHT_5",
  FIVE_OF_A_KIND = "FIVE_OF_A_KIND",
  DOUBLE_STRAIGHT = "DOUBLE_STRAIGHT"
}
```

---

## Error Handling

### Error Response Format
```json
{
  "event": "error",
  "data": {
    "message": "Human-readable error message",
    "type": "error_category",
    "code": "ERROR_CODE",
    "details": {
      // Additional context
    }
  }
}
```

### Common Error Types

#### Room Errors
- `ROOM_NOT_FOUND` - Room ID doesn't exist
- `ROOM_FULL` - Cannot join, room at capacity
- `ROOM_ALREADY_STARTED` - Cannot join game in progress
- `NOT_HOST` - Action requires host privileges

#### Game Errors
- `INVALID_ACTION` - Action not allowed in current phase
- `NOT_YOUR_TURN` - Action attempted out of turn
- `INVALID_DECLARATION` - Declaration value out of range or violates rules
- `INVALID_PLAY` - Piece combination or count invalid
- `INSUFFICIENT_PIECES` - Cannot match required piece count

#### Connection Errors
- `AUTHENTICATION_FAILED` - Invalid credentials
- `RATE_LIMITED` - Too many requests
- `PROTOCOL_ERROR` - Malformed message
- `TIMEOUT` - Operation timed out

### Error Handling Patterns

#### Client Retry Logic
```javascript
async function sendWithRetry(event, data, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await networkService.send(roomId, event, data);
      return; // Success
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      // Exponential backoff
      await sleep(Math.pow(2, attempt) * 1000);
    }
  }
}
```

#### Server Error Responses
```python
async def handle_error(websocket, error_type: str, message: str):
    error_response = {
        "event": "error",
        "data": {
            "type": error_type,
            "message": message,
            "timestamp": time.time()
        }
    }
    await websocket.send_text(json.dumps(error_response))
```

---

## Integration Examples

### Basic Game Client
```javascript
class GameClient {
  constructor(roomId, playerName) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${roomId}`);
    this.roomId = roomId;
    this.playerName = playerName;
    this.setupEventHandlers();
  }
  
  setupEventHandlers() {
    this.ws.onopen = () => {
      this.send('client_ready', {});
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleEvent(message.event, message.data);
    };
  }
  
  send(event, data) {
    this.ws.send(JSON.stringify({ event, data }));
  }
  
  handleEvent(event, data) {
    switch (event) {
      case 'phase_change':
        this.handlePhaseChange(data);
        break;
      case 'room_update':
        this.handleRoomUpdate(data);
        break;
      case 'error':
        this.handleError(data);
        break;
    }
  }
  
  // Game actions
  makeDeclaration(value) {
    this.send('declare', {
      player_name: this.playerName,
      value: value
    });
  }
  
  playPieces(pieceIndices) {
    this.send('play', {
      player_name: this.playerName,
      pieces: pieceIndices
    });
  }
}
```

### React Integration
```jsx
function useGameConnection(roomId, playerName) {
  const [gameState, setGameState] = useState(initialState);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${roomId}`);
    wsRef.current = ws;
    
    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({
        event: 'client_ready',
        data: {}
      }));
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleGameEvent(message, setGameState);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
    };
    
    return () => ws.close();
  }, [roomId]);
  
  const sendAction = useCallback((event, data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event, data }));
    }
  }, []);
  
  return { gameState, isConnected, sendAction };
}
```

### Bot Integration
```python
class GameBot:
    def __init__(self, room_id: str, bot_name: str):
        self.room_id = room_id
        self.bot_name = bot_name
        self.game_state = {}
        
    async def connect(self):
        uri = f"ws://localhost:8000/ws/{self.room_id}"
        async with websockets.connect(uri) as websocket:
            await self.send_event(websocket, "client_ready", {})
            await self.listen_for_events(websocket)
    
    async def send_event(self, websocket, event: str, data: dict):
        message = {"event": event, "data": data}
        await websocket.send(json.dumps(message))
    
    async def handle_phase_change(self, websocket, data):
        phase = data.get("phase")
        
        if phase == "declaration":
            await self.make_declaration(websocket, data)
        elif phase == "turn":
            await self.make_play(websocket, data)
    
    async def make_declaration(self, websocket, data):
        # Bot decision logic
        declaration_value = self.calculate_declaration(data)
        
        await self.send_event(websocket, "declare", {
            "player_name": self.bot_name,
            "value": declaration_value
        })
```

---

## Testing Guide

### WebSocket Testing

#### Manual Testing with wscat
```bash
# Install wscat
npm install -g wscat

# Connect to room
wscat -c ws://localhost:8000/ws/ROOM123

# Send events
{"event": "client_ready", "data": {}}
{"event": "declare", "data": {"player_name": "TestPlayer", "value": 3}}
```

#### Automated Testing
```javascript
const WebSocket = require('ws');

describe('WebSocket API', () => {
  let ws;
  
  beforeEach(async () => {
    ws = new WebSocket('ws://localhost:8000/ws/TEST_ROOM');
    await new Promise(resolve => ws.on('open', resolve));
  });
  
  afterEach(() => {
    ws.close();
  });
  
  test('should handle client_ready event', (done) => {
    ws.on('message', (data) => {
      const message = JSON.parse(data);
      expect(message.event).toBe('room_update');
      done();
    });
    
    ws.send(JSON.stringify({
      event: 'client_ready',
      data: {}
    }));
  });
});
```

### Load Testing
```javascript
// Create multiple concurrent connections
async function loadTest(numClients = 100) {
  const clients = [];
  
  for (let i = 0; i < numClients; i++) {
    const client = new GameClient(`ROOM_${i}`, `Player_${i}`);
    clients.push(client);
  }
  
  // Simulate concurrent gameplay
  await Promise.all(clients.map(client => client.simulateGame()));
}
```

---

## Rate Limiting

### Connection Limits
- **Max connections per IP**: 10 concurrent
- **Max rooms per user**: 3 active
- **Message rate**: 100 messages per minute per connection

### Implementation
```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    if await is_rate_limited(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"}
        )
    
    return await call_next(request)
```

---

## Authentication

### Room-Based Security
- Room ID acts as access token
- Host privileges for room management
- Player name validation
- Action authorization per phase

### Production Considerations
- JWT tokens for user authentication
- Role-based access control
- Session management
- Secure WebSocket connections (WSS)

---

## Conclusion

This API reference provides complete documentation for integrating with the Liap Tui game system. The WebSocket-based architecture enables real-time multiplayer gameplay with automatic state synchronization and comprehensive error handling.

For implementation examples and architectural details, see the [Technical Architecture Deep Dive](TECHNICAL_ARCHITECTURE_DEEP_DIVE.md) and [Developer Onboarding Guide](DEVELOPER_ONBOARDING_GUIDE.md).

---

*Last updated: January 2024*