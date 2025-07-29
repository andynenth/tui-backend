# Frontend Data Contracts Analysis

**Date**: Session Analysis  
**Purpose**: Complete Investigation of Frontend Data Expectations and Backend Contracts  
**Status**: Comprehensive Analysis Complete  

## Executive Summary

Comprehensive analysis of all frontend pages revealed specific data contract requirements and WebSocket event dependencies. Investigation found multiple competing ID generation systems causing frontend display issues, plus detailed requirements for each page's data expectations.

## Frontend Data Contract Requirements

### Player Object Structure

The frontend expects player objects in this exact format:

```json
{
  "player_id": "ROOM123_p0",
  "name": "PlayerName",
  "is_bot": false,
  "is_host": true,
  "seat_position": 0,
  "avatar_color": null
}
```

### Critical Field Requirements

- **`name`**: Must be `"name"`, NOT `"player_name"`
- **`seat_position`**: Must be 0-indexed (0, 1, 2, 3) for proper slot ordering
- **`player_id`**: Must be consistent across all WebSocket messages
- **`is_host`**: Required for host identification (seat 0 = host)
- **`is_bot`**: Required for bot vs human player distinction

## WebSocket Event Contracts

### Events Frontend Listens For

1. **`room_created`** - Initial room setup with complete player data
2. **`client_ready_ack`** - Room state synchronization on connection
3. **`room_joined`** - Player addition/update notifications

### Expected Event Structure

```json
{
  "event": "room_created",
  "data": {
    "room_id": "ROOM123",
    "room_code": "ROOM123", 
    "host_name": "PlayerName",
    "success": true,
    "room_info": {
      "room_id": "ROOM123",
      "players": [
        {
          "player_id": "ROOM123_p0",
          "name": "HostPlayer",
          "is_bot": false,
          "is_host": true,
          "seat_position": 0,
          "avatar_color": null
        }
      ],
      "max_players": 4,
      "game_in_progress": false,
      "status": "waiting"
    }
  }
}
```

## ID System Analysis

### Current ID Generation Systems Found

1. **Slot-based IDs (Correct System)**
   ```python
   # PropertyMapper.generate_player_id()
   f"{room_id}_p{slot_index}"  # e.g., "ROOM123_p0", "ROOM123_p1"
   ```

2. **Counter-based IDs (Problematic Mystery System)**
   ```
   "lobby_p17", "lobby_p29", "2DUBXV_p24", "2DUBXV_p57"
   ```

3. **Anonymous Lobby IDs**
   ```python
   f"anonymous_{websocket._ws_id[:8]}"  # e.g., "anonymous_a1b2c3d4"
   "anonymous"  # Simplified use case version
   ```

4. **WebSocket Infrastructure IDs**
   ```python
   websocket._ws_id = uuid.uuid4().hex[:8]  # e.g., "a1b2c3d4"
   ```

### ID System Problems

- **Counter-based IDs break seat logic**: Frontend expects p0-p3, gets p17, p24
- **Multiple ID sources**: Different layers generate different IDs for same player
- **Inconsistent player_id**: Same player gets different IDs in different messages
- **No single source of truth**: Multiple systems compete for ID generation

## Root Cause Analysis: "Waiting" Slot Display

### Frontend Shows "Waiting" When:

1. **Missing Required Fields**: Player objects lack `name`, `seat_position`, etc.
2. **Inconsistent Player IDs**: Backend sends different `player_id` values across messages
3. **Incomplete Player Array**: `room_info.players` array is empty/incomplete
4. **Event Delivery Issues**: WebSocket events don't reach frontend properly
5. **Counter-based ID Mismatches**: Player IDs don't match expected slot positions

### Current Backend Code Issues

#### In `use_case_dispatcher.py` - `_format_room_info()`:
```python
# Correctly maps player_name to "name" field
"name": p.player_name,  # Frontend expects "name"
```

#### In `message_router.py` - `_get_room_state()`:
```python
# Correctly generates slot-based player IDs
"player_id": f"{room_id}_p{i}",
```

#### Mystery Counter System:
- **Source**: Unknown - not found in examined code
- **Effect**: Generates p17, p24, p57 instead of p0, p1, p2, p3
- **Impact**: Frontend can't match players to slots

## Data Flow Mapping

### Expected Flow
```
User Action → Backend Processing → WebSocket Event → Frontend Update → Slot Display
```

### Current Issues in Flow

1. **Room Creation**:
   ```
   User creates room → CreateRoomUseCase → room_created event → Frontend
   ```
   **Problem**: Player data may be incomplete in room_created event

2. **Player Connection**:
   ```
   Player connects → client_ready → MarkClientReadyUseCase → client_ready_ack → Frontend
   ```
   **Problem**: Inconsistent player_id between connection and room state

3. **Room State Sync**:
   ```
   Frontend requests state → GetRoomStateUseCase → room_state event → Frontend
   ```
   **Problem**: Player IDs don't match between different events

## Technical Implementation Details

### Backend Code Locations

- **ID Generation**: `backend/application/utils/property_mapper.py`
- **Room Formatting**: `backend/application/websocket/use_case_dispatcher.py:910`
- **Room State**: `backend/application/websocket/message_router.py:230`
- **Client Ready**: `backend/application/use_cases/connection/mark_client_ready.py`

### Frontend Integration Points

- **NetworkService**: Handles WebSocket communication
- **Room Display**: Expects complete player objects for slot rendering
- **Event Handling**: Listens for room_created, room_joined, client_ready_ack

## Action Items and Recommendations

### Immediate Fixes Required

1. **Find Counter-based ID Source**: Locate where lobby_p17, p24 IDs are generated
2. **Ensure Complete Player Data**: Verify CreateRoomUseCase populates all player fields
3. **Standardize ID Generation**: Use only slot-based IDs for game rooms
4. **Test Event Delivery**: Verify frontend receives complete room_info data

### Long-term Improvements

1. **Single ID Strategy**: Implement one ID system across all layers
2. **Data Contract Validation**: Add validation for player object completeness
3. **Frontend Type Safety**: Add TypeScript interfaces for WebSocket events
4. **Documentation**: Document all WebSocket event structures

### Critical Player ID Strategy

**Recommended Standard**:
- **Lobby**: `lobby:{player_name}`
- **Game Rooms**: `{room_id}:seat{N}` (seat0, seat1, seat2, seat3)
- **Eliminate**: Counter-based, anonymous websocket IDs from business logic

## Conclusion

The "waiting" slot display issue stems from the frontend not receiving complete, consistently-formatted player data. Multiple competing ID systems create confusion and mismatches. A standardized ID strategy and complete player object population will resolve these issues.

## Complete Frontend Page Data Requirements

### StartPage.jsx (lines 1-206)

**Found in**: `/Users/nrw/python/tui-project/liap-tui/frontend/src/pages/StartPage.jsx`

**Data Dependencies**:
- **AppContext**: `app.playerName` (lines 28, 36, 46, 59)
- **ThemeContext**: `currentTheme.uiElements.startIcon.*` (lines 82, 88, 94)
- **No WebSocket Events**: StartPage does not listen to any WebSocket events
- **No Backend Calls**: StartPage makes no direct backend communication

**Evidence**:
```javascript
// Line 28: Form default values
defaultValues: {
  playerName: app.playerName || '',
}

// Lines 46-49: Only updates local context
app.updatePlayerName(data.playerName);
navigate('/lobby');
```

### LobbyPage.jsx (lines 1-438)

**Found in**: `/Users/nrw/python/tui-project/liap-tui/frontend/src/pages/LobbyPage.jsx`

**Data Dependencies**:
- **NetworkService Connection**: `networkService.connectToRoom('lobby')` (line 33)
- **AppContext**: `app.playerName` for player identification (lines 152, 163, 171)

**WebSocket Events Expected** (lines 46-123):
1. **`room_list_update`** (lines 46-59):
   ```javascript
   const roomListData = eventData.data;
   setRooms(roomListData.rooms || []);
   ```

2. **`room_created`** (lines 62-93):
   ```javascript
   const roomData = eventData.data;
   // Expects: roomData.room_id
   if (roomData.room_id && roomData.room_id !== 'lobby') {
     navigate(`/room/${roomData.room_id}`);
   }
   ```

3. **`room_joined`** (lines 96-109):
   ```javascript
   const joinData = eventData.data;
   // Expects: joinData.room_id
   if (joinData.room_id) {
     navigate(`/room/${joinData.room_id}`);
   }
   ```

4. **`error`** (lines 112-123):
   ```javascript
   const errorData = eventData.data;
   // Expects: errorData.message
   alert(errorData?.message || 'An error occurred');
   ```

**Room Object Structure Expected** (lines 175-183, 225-281):
```javascript
// Line 177-179: Player count calculation
const playerCount = room.players
  ? room.players.filter((player) => player !== null).length
  : room.occupied_slots || 0;

// Lines 241-243: Host name extraction  
room.host_name ||
room.players?.find((p) => p?.is_host)?.name ||
'Unknown'

// Lines 255-256: Player slot structure
const player = room.players?.[slot];
// Expects player to have: name, is_bot, is_host properties
```

**Outgoing WebSocket Messages** (lines 127, 141, 151-154, 161-164, 169-172):
```javascript
networkService.send('lobby', 'get_rooms', {});
networkService.send('lobby', 'create_room', { player_name: app.playerName });
networkService.send('lobby', 'join_room', { room_id: roomId, player_name: app.playerName });
```

### RoomPage.jsx (lines 1-300)

**Found in**: `/Users/nrw/python/tui-project/liap-tui/frontend/src/pages/RoomPage.jsx`

**Data Dependencies**:
- **NetworkService Connection**: `networkService.connectToRoom(roomId, {playerName: app.playerName})` (lines 39-41)
- **AppContext**: `app.playerName` for player identification (lines 30, 142, 147)
- **URL Parameters**: `roomId` from React Router (line 15)

**WebSocket Events Expected** (lines 69-115):
1. **`room_update`** (lines 69-87):
   ```javascript
   const roomUpdate = eventData.data;
   // Expects: roomUpdate.players array
   setRoomData(roomUpdate);
   ```

2. **`game_started`** (lines 89-94):
   ```javascript
   // Triggers navigation to game page
   navigate(`/game/${roomId}`);
   ```

3. **`room_closed`** (lines 96-105):
   ```javascript
   const closeData = eventData.data;
   // Expects: closeData.reason, closeData.message
   navigate('/lobby');
   ```

**Room Data Structure Expected** (lines 18, 23-31, 202-212):
```javascript
// Line 24: Player filtering
roomData?.players?.filter((player) => player !== null).length

// Lines 29-31: Host detection
roomData?.players?.some(
  (player) => player?.name === app.playerName && player?.is_host
)

// Lines 203-211: Player slot data
const player = roomData?.players?.[position - 1];
// Expects: player.is_host, player.is_bot, player.name, player.avatar_color
```

**Outgoing WebSocket Messages** (lines 45, 122, 128, 134, 141-143):
```javascript
networkService.send(roomId, 'get_room_state', { room_id: roomId });
networkService.send(roomId, 'start_game', {});
networkService.send(roomId, 'add_bot', { slot_id: slotId });
networkService.send(roomId, 'remove_player', { slot_id: slotId });
networkService.send(roomId, 'leave_room', { player_name: app.playerName });
```

## Data Flow Architecture Analysis

### NetworkService → Pages Direct Flow

**Found in**: All three pages import and use NetworkService directly

**Evidence**:
- StartPage: No NetworkService usage (line 10 imports but not used)
- LobbyPage: `import { networkService } from '../services';` (line 10)
- RoomPage: `import { networkService } from '../services';` (line 10)

### GameService Integration

**From GameService.ts analysis**: GameService listens to NetworkService events and processes them for game state, but the room management pages (StartPage, LobbyPage, RoomPage) bypass GameService and communicate directly with NetworkService.

**Evidence**: None of the three pages import or use GameService - they handle WebSocket events directly through NetworkService event listeners.

## Critical Frontend Requirements Summary

### Lobby Page Requirements
1. **Room List Structure**: Array of room objects with `players`, `host_name`, `room_id` properties
2. **Player Objects**: Must contain `name`, `is_bot`, `is_host` properties  
3. **Events**: Must receive `room_list_update`, `room_created`, `room_joined`, `error` events

### Room Page Requirements  
1. **Room Data**: Object with `players` array (4-element array, null for empty slots)
2. **Player Objects**: Must contain `name`, `is_bot`, `is_host`, `avatar_color` properties
3. **Events**: Must receive `room_update`, `game_started`, `room_closed` events

### Data Contract Violations Found
1. **Inconsistent Player IDs**: Frontend expects player objects but backend may send mismatched IDs
2. **Missing Player Properties**: Frontend expects `avatar_color` but backend may not provide it
3. **Array vs Object Confusion**: Frontend expects `players` as array, backend may send as object

## Comprehensive Frontend-Backend Data Contracts

### OUTBOUND DATA (Frontend → Backend)

#### 1. WebSocket Message Structure

**ENDPOINT**: WebSocket `/ws/{roomId}`  
**FILE**: `frontend/src/services/NetworkService.ts:209-215`  
**DIRECTION**: OUTBOUND  
**DATA_TYPE**: WebSocket JSON message  
**STRUCTURE**:
```typescript
interface NetworkMessage {
  event: string;
  data: Record<string, any>;
  sequence: number;
  timestamp: number;
  id: string;
}
```
**CODE_EVIDENCE**:
```typescript
const message: NetworkMessage = {
  event,
  data,
  sequence: sequenceNumber,
  timestamp: Date.now(),
  id: crypto.randomUUID(),
};
connectionData.websocket.send(JSON.stringify(message));
```
**USAGE**: All frontend-to-backend communication uses this wrapper structure

#### 2. Lobby Operations

**ENDPOINT**: WebSocket `/ws/lobby`  
**FILE**: `frontend/src/pages/LobbyPage.jsx:127,151-172`  
**DIRECTION**: OUTBOUND  
**DATA_TYPE**: WebSocket event payloads  

**2a. Get Rooms Request**
**STRUCTURE**: `{}`  
**CODE_EVIDENCE**: `networkService.send('lobby', 'get_rooms', {});`

**2b. Create Room Request**  
**STRUCTURE**: `{ player_name: string }`  
**CODE_EVIDENCE**: 
```javascript
networkService.send('lobby', 'create_room', {
  player_name: app.playerName,
});
```

**2c. Join Room Request**  
**STRUCTURE**: `{ room_id: string, player_name: string }`  
**CODE_EVIDENCE**:
```javascript
networkService.send('lobby', 'join_room', {
  room_id: roomId,
  player_name: app.playerName,
});
```

#### 3. Room Management Operations

**ENDPOINT**: WebSocket `/ws/{roomId}`  
**FILE**: `frontend/src/pages/RoomPage.jsx:45,122-143`  
**DIRECTION**: OUTBOUND  
**DATA_TYPE**: WebSocket event payloads  

**3a. Get Room State Request**  
**STRUCTURE**: `{ room_id: string }`  
**CODE_EVIDENCE**: `networkService.send(roomId, 'get_room_state', { room_id: roomId });`

**3b. Start Game Request**  
**STRUCTURE**: `{}`  
**CODE_EVIDENCE**: `networkService.send(roomId, 'start_game', {});`

**3c. Add Bot Request**  
**STRUCTURE**: `{ slot_id: number }`  
**CODE_EVIDENCE**: `networkService.send(roomId, 'add_bot', { slot_id: slotId });`

**3d. Remove Player Request**  
**STRUCTURE**: `{ slot_id: number }`  
**CODE_EVIDENCE**: `networkService.send(roomId, 'remove_player', { slot_id: slotId });`

**3e. Leave Room Request**  
**STRUCTURE**: `{ player_name: string }`  
**CODE_EVIDENCE**: 
```javascript
networkService.send(roomId, 'leave_room', {
  player_name: app.playerName,
});
```

#### 4. Game Actions

**ENDPOINT**: WebSocket `/ws/{roomId}`  
**FILE**: `frontend/src/services/GameService.ts:158-242`  
**DIRECTION**: OUTBOUND  
**DATA_TYPE**: Game action payloads  

**4a. Accept Redeal**  
**STRUCTURE**: `{ player_name: string }`  
**CODE_EVIDENCE**: `this.sendAction('accept_redeal', { player_name: this.state.playerName });`

**4b. Decline Redeal**  
**STRUCTURE**: `{ player_name: string }`  
**CODE_EVIDENCE**: `this.sendAction('decline_redeal', { player_name: this.state.playerName });`

**4c. Make Declaration**  
**STRUCTURE**: `{ value: number, player_name: string }`  
**CODE_EVIDENCE**: `this.sendAction('declare', { value, player_name: this.state.playerName });`

**4d. Play Pieces**  
**FILE**: `frontend/src/services/GameService.ts:237-241`  
**STRUCTURE**: `{ piece_indices: number[], player_name: string, play_value: number }`  
**CODE_EVIDENCE**:
```typescript
this.sendAction('play', {
  piece_indices: indices,
  player_name: this.state.playerName,
  play_value: totalValue,
});
```

**4e. Start Next Round**  
**STRUCTURE**: `{}`  
**CODE_EVIDENCE**: `this.sendAction('start_next_round', {});`

#### 5. Connection & Recovery

**5a. Client Ready Signal**  
**FILE**: `frontend/src/services/NetworkService.ts:128-134`  
**STRUCTURE**: `{ room_id: string, player_name?: string, is_reconnection: boolean }`  
**CODE_EVIDENCE**:
```typescript
this.send(roomId, 'client_ready', {
  room_id: roomId,
  player_name: connectionData?.playerName,
  is_reconnection: connectionData?.isReconnection || false,
});
```

**5b. Ping Heartbeat**  
**FILE**: `frontend/src/services/NetworkService.ts:589`  
**STRUCTURE**: `{ timestamp: number }`  
**CODE_EVIDENCE**: `this.send(roomId, 'ping', { timestamp: Date.now() });`

**5c. Recovery Request**  
**FILE**: `frontend/src/services/RecoveryService.ts:550-552`  
**STRUCTURE**: `{ from_sequence: number, to_sequence: number }`  
**CODE_EVIDENCE**:
```typescript
networkService.send(roomId, 'request_recovery', {
  from_sequence: fromSequence,
  to_sequence: this.roomStates.get(roomId)?.lastSequence || fromSequence,
});
```

### INBOUND DATA (Backend → Frontend)

#### 1. WebSocket Message Structure

**ENDPOINT**: WebSocket `/ws/{roomId}`  
**FILE**: `frontend/src/services/NetworkService.ts:382,393-409`  
**DIRECTION**: INBOUND  
**DATA_TYPE**: JSON WebSocket messages  
**STRUCTURE**: Same as outbound `NetworkMessage` interface  
**CODE_EVIDENCE**:
```typescript
const message = JSON.parse(event.data) as NetworkMessage;
this.dispatchEvent(
  new CustomEvent<NetworkEventDetail>(message.event, {
    detail: {
      roomId,
      data: message.data,
      message,
      timestamp: Date.now(),
    },
  })
);
```
**USAGE**: All backend messages parsed and dispatched as events

#### 2. Lobby Responses

**FILE**: `frontend/src/pages/LobbyPage.jsx:46-123`  
**DIRECTION**: INBOUND  

**2a. Room List Update**  
**STRUCTURE**: `{ rooms: Array<RoomObject> }`  
**CODE_EVIDENCE**:
```javascript
const roomListData = eventData.data;
setRooms(roomListData.rooms || []);
```

**2b. Room Created Response**  
**STRUCTURE**: `{ room_id: string, ... }`  
**CODE_EVIDENCE**:
```javascript
const roomData = eventData.data;
if (roomData.room_id && roomData.room_id !== 'lobby') {
  navigate(`/room/${roomData.room_id}`);
}
```

**2c. Room Joined Response**  
**STRUCTURE**: `{ room_id: string, ... }`  
**CODE_EVIDENCE**:
```javascript
const joinData = eventData.data;
if (joinData.room_id) {
  navigate(`/room/${joinData.room_id}`);
}
```

**2d. Error Response**  
**STRUCTURE**: `{ message: string, ... }`  
**CODE_EVIDENCE**:
```javascript
const errorData = eventData.data;
alert(errorData?.message || 'An error occurred');
```

#### 3. Room Management Responses

**FILE**: `frontend/src/pages/RoomPage.jsx:69-115`  
**DIRECTION**: INBOUND  

**3a. Room Update**  
**STRUCTURE**: Room object with players array  
**CODE_EVIDENCE**:
```javascript
const roomUpdate = eventData.data;
setRoomData(roomUpdate);
// Expected: roomUpdate.players array with player objects
```

**3b. Game Started**  
**STRUCTURE**: Game start data (STRUCTURE_NOT_CLEAR_IN_CODE)  
**CODE_EVIDENCE**: `navigate(\`/game/${roomId}\`);`

**3c. Room Closed**  
**STRUCTURE**: `{ reason: string, message: string }`  
**CODE_EVIDENCE**:
```javascript
const closeData = eventData.data;
console.log('🏠 ROOM_CLOSED: Reason:', closeData.reason);
console.log('🏠 ROOM_CLOSED: Message:', closeData.message);
```

#### 4. Game State Updates

**FILE**: `frontend/src/services/GameService.ts:301-316,642-1036`  
**DIRECTION**: INBOUND  
**DATA_TYPE**: Game event responses  

**4a. Phase Change Events**  
**STRUCTURE**: Complex PhaseData structure from types.ts:226-284  
**CODE_EVIDENCE**:
```typescript
// Line 642: phase_change event handling
newState.phase = data.phase;
newState.currentRound = data.round || state.currentRound;
// Extract my hand from players data
if (data.players && state.playerName && data.players[state.playerName]) {
  const myPlayerData = data.players[state.playerName];
  if (myPlayerData.hand) {
    // Convert string pieces back to objects
    const unsortedHand = myPlayerData.hand.map((pieceStr: string, index: number) => {
      const match = pieceStr.match(/^(.+)\((\d+)\)$/);
      // Returns GamePiece objects
    });
  }
}
```

**4b. Player Action Events**  
**STRUCTURE**: Action-specific data structures  
**CODE_EVIDENCE**:
```typescript
// declare event (lines 1088-1128)
const newDeclarations = {
  ...state.declarations,
  [data.player]: data.value,
};

// play event (lines 1152-1158)  
const playData = {
  player: data.player,
  cards: data.pieces || [],
  isValid: data.is_valid,
  playType: data.play_type,
  totalValue: data.play_value || 0,
};
```

#### 5. Connection Events

**5a. Pong Response**  
**FILE**: `frontend/src/services/NetworkService.ts:387-390`  
**STRUCTURE**: `{ timestamp: number }`  
**CODE_EVIDENCE**:
```typescript
if (message.event === 'pong' && message.data?.timestamp) {
  connectionData.latency = Date.now() - message.data.timestamp;
  return;
}
```

**5b. Room Not Found Error**  
**FILE**: `frontend/src/services/GameService.ts:477-517`  
**STRUCTURE**: `{ message: string, suggestion: string }`  
**CODE_EVIDENCE**:
```typescript
const message = data?.message || 'This game room no longer exists';
const suggestion = data?.suggestion || 'Please return to the start page';
this.setState({
  ...this.state,
  error: `${message}. ${suggestion}`,
  phase: 'waiting' as const,
}, 'ROOM_NOT_FOUND');
```

### Data Contract Issues Identified

1. **STRUCTURE_NOT_CLEAR_IN_CODE**: Room object structure expected by frontend  
2. **STRUCTURE_NOT_CLEAR_IN_CODE**: Complete PhaseData.players format  
3. **NEEDS_VERIFICATION**: Player ID consistency between outbound/inbound data  
4. **NEEDS_VERIFICATION**: Complete list of supported WebSocket events  

---

**Next Steps**: Implement recommended ID standardization and verify complete player data delivery to frontend. Ensure all WebSocket events contain the exact data structures expected by frontend pages.