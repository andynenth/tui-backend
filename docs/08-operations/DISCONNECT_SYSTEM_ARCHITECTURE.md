# WebSocket Disconnect and Reconnection System Architecture

## Overview

The disconnect/reconnection system in Liap Tui allows players to maintain their game session even after network disconnects, browser refreshes, or temporary connection losses. The system consists of backend WebSocket tracking, frontend session storage, and automatic bot activation/deactivation.

## Key Components

### 1. WebSocket ID Assignment (`backend/api/routes/ws.py`)

```python
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # Generate unique ID for this websocket
    websocket._ws_id = str(uuid.uuid4())  # Line 269
```

- Each WebSocket connection gets a unique UUID when established
- This ID is stored as `_ws_id` attribute on the WebSocket object
- Used to track which player is associated with which WebSocket

### 2. Connection Manager (`backend/api/websocket/connection_manager.py`)

**Key Data Structures:**
```python
# Track connections by room_id -> player_name -> PlayerConnection
self.connections: Dict[str, Dict[str, PlayerConnection]] = {}

# Track websocket to player mapping
self.websocket_to_player: Dict[str, tuple[str, str]] = {}  # ws_id -> (room_id, player_name)
```

**Connection Registration:**
- When a player joins a room, their connection is registered
- Maps WebSocket ID to (room_id, player_name) tuple
- Stores PlayerConnection object with status tracking

### 3. Disconnect Handling Flow

#### Step 1: WebSocket Disconnect Event
```python
async def handle_disconnect(room_id: str, websocket: WebSocket):
    websocket_id = getattr(websocket, "_ws_id", None)  # Line 59
    
    if websocket_id:
        connection = await connection_manager.handle_disconnect(websocket_id)  # Line 73
```

#### Step 2: Connection Manager Updates
```python
async def handle_disconnect(self, websocket_id: str) -> Optional[PlayerConnection]:
    # Find player from websocket ID
    room_id, player_name = self.websocket_to_player[websocket_id]  # Line 93
    
    # Remove websocket mapping
    del self.websocket_to_player[websocket_id]  # Line 96
    
    # Update connection state
    connection.connection_status = ConnectionStatus.DISCONNECTED  # Line 101
    connection.disconnect_time = datetime.now()  # Line 102
    connection.websocket_id = None  # Line 103
```

#### Step 3: Game State Updates (In-Game Disconnect)
```python
if room and room.started:  # Only treat as in-game if game started!
    # Store original state for ALL players
    player.original_is_bot = player.is_bot  # Line 104
    player.original_avatar_color = getattr(player, 'avatar_color', None)  # Line 105
    
    # Only process human players for disconnect
    if not player.is_bot:
        player.is_connected = False  # Line 109
        player.disconnect_time = connection.disconnect_time  # Line 110
        
        # Convert human to bot during disconnect
        player.is_bot = True  # Line 113
```

#### Step 4: Message Queue Creation
```python
# Create message queue for the disconnected player
await message_queue_manager.create_queue(
    room_id, connection.player_name
)  # Lines 116-118
```

#### Step 5: Broadcast Disconnect Event
```python
await broadcast(
    room_id,
    "player_disconnected",
    {
        "player_name": connection.player_name,
        "ai_activated": True,
        "can_reconnect": True,
        "is_bot": True,
    },
)  # Lines 135-144
```

### 4. Pre-Game vs In-Game Disconnects

**Pre-Game Disconnect:**
```python
else:
    # This is a pre-game disconnect - treat as leave_room
    await process_leave_room(room_id, connection.player_name)  # Line 175
```
- Player is removed from the room
- Room is deleted if host leaves
- No bot activation

**In-Game Disconnect:**
- Player remains in game
- Bot takes over player's actions
- Connection marked as disconnected
- Message queue created for missed events

### 5. Frontend Session Storage (`frontend/src/utils/sessionStorage.js`)

**Session Data Structure:**
```javascript
const sessionData = {
    roomId,
    playerName,
    sessionId,
    createdAt: Date.now(),
    lastActivity: Date.now(),
    gamePhase,
};
```

**Storage in LocalStorage:**
- Stores session data when player joins room
- Updates activity timestamp periodically
- Survives browser refresh
- 24-hour expiry time

### 6. Reconnection Flow

#### Step 1: Frontend Reconnection Request
```javascript
// Frontend sends reconnect event with stored session data
{
    event: "reconnect",
    data: {
        player_name: session.playerName,
        session_id: session.sessionId,
        request_full_state: true
    }
}
```

#### Step 2: Backend Reconnection Handling (`ws.py` lines 697-760)
```python
# Check if player is reconnecting
is_reconnecting = await connection_manager.check_reconnection(room_id, player_name)

if is_reconnecting:
    # Register the player connection
    await connection_manager.register_player(room_id, player_name, websocket._ws_id)
    
    # Restore player state in game
    if room.game:
        player = next((p for p in room.game.players if p.name == player_name), None)
        if player:
            # Restore original state
            player.is_bot = player.original_is_bot
            player.is_connected = True
            player.disconnect_time = None
```

#### Step 3: Game State Restoration
```python
if room.started and room.game_state_machine:
    current_phase = room.game_state_machine.get_current_phase()
    phase_data = room.game_state_machine.get_phase_data()
    
    # Send phase_change event with complete game state
    await registered_ws.send_json({
        "event": "phase_change",
        "data": {
            "phase": current_phase.value,
            "allowed_actions": allowed_actions,
            "phase_data": phase_data,
            "players": players_data,
            "round": current_round,
        },
    })
```

### 7. Bot Activation/Deactivation

**Bot Activation on Disconnect:**
- `player.is_bot = True` - Bot takes control
- Original state preserved in `player.original_is_bot`
- Bot can make declarations, play pieces, etc.

**Bot Deactivation on Reconnect:**
- `player.is_bot = player.original_is_bot` - Restore original state
- `player.is_connected = True` - Mark as connected
- Player resumes control

### 8. Host Migration

```python
# Check if disconnecting player was the host
new_host = None
if room.is_host(connection.player_name):
    new_host = await room.migrate_host()  # Line 127
```

- If host disconnects, another connected player becomes host
- Preference given to human players over bots
- Broadcast host change event

### 9. Room Cleanup

```python
# Check if all remaining players are bots and mark for cleanup
if not room.has_any_human_players():
    room.mark_for_cleanup()  # Line 160
```

- Rooms with only bots are marked for cleanup
- Cleanup happens after timeout period
- Prevents zombie rooms from consuming resources

## Key Design Decisions

1. **Unlimited Reconnection Time**: Players can reconnect anytime while game is active
2. **Automatic Bot Activation**: Bots immediately take over to keep game flowing
3. **State Preservation**: Original player state (bot/human) is preserved
4. **Message Queuing**: Missed events are queued for disconnected players
5. **Session Storage**: Frontend stores session data in LocalStorage for browser refresh handling
6. **WebSocket ID Tracking**: Each connection has unique ID for precise tracking
7. **Phase Data Serialization**: Game state is made JSON-safe using `_make_json_safe()` method

## Error Handling

1. **Missing WebSocket ID**: Fallback disconnect detection (line 75-82)
2. **Connection Not Found**: Warning logged, graceful handling
3. **JSON Serialization**: Fixed with `_make_json_safe()` method in game_state_machine.py
4. **Rate Limiting**: Disconnects don't trigger rate limits
5. **Cleanup Failures**: Logged but don't break game flow

## Security Considerations

1. Session IDs are UUID v4 (cryptographically random)
2. Player names validated on reconnection
3. Room existence checked before allowing reconnection
4. Original bot/human state preserved to prevent cheating
5. WebSocket IDs not exposed to clients