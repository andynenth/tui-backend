# Bot Takeover Flow - Seamless Player Substitution

This diagram illustrates how the system seamlessly handles player disconnections with automatic bot substitution.

```mermaid
sequenceDiagram
    participant Player
    participant WebSocket
    participant DisconnectHandler as Disconnect Handler
    participant ConnectionMgr as Connection Manager
    participant GameState as Game State
    participant BotFlag as Bot Flag Manager
    participant MessageQueue as Message Queue
    participant BotManager as Bot Manager
    participant OtherPlayers as Other Players

    Player->>WebSocket: Connection lost<br/>(network/refresh)
    WebSocket->>DisconnectHandler: WebSocket disconnect event

    DisconnectHandler->>DisconnectHandler: Get websocket._ws_id
    DisconnectHandler->>ConnectionMgr: handle_disconnect(ws_id)

    ConnectionMgr->>ConnectionMgr: Find player from ws_id:<br/>(room_id, player_name)

    alt In-Game Disconnect
        ConnectionMgr->>GameState: Check game started
        GameState-->>ConnectionMgr: Yes, in-game

        ConnectionMgr->>BotFlag: Store original state:<br/>player.original_is_bot = player.is_bot<br/>player.original_avatar_color = avatar_color

        ConnectionMgr->>BotFlag: Activate bot mode:<br/>player.is_bot = True<br/>player.is_connected = False<br/>player.disconnect_time = now()

        ConnectionMgr->>MessageQueue: create_queue(room_id, player_name)
        Note over MessageQueue: Store missed events<br/>for reconnection

        ConnectionMgr->>OtherPlayers: broadcast("player_disconnected", {<br/>  "ai_activated": true,<br/>  "can_reconnect": true<br/>})

        Note over BotManager: Bot immediately takes over:<br/>- Makes declarations<br/>- Plays pieces<br/>- Maintains game flow

        Player->>WebSocket: Reconnect attempt
        WebSocket->>DisconnectHandler: reconnect event with:<br/>- player_name<br/>- session_id<br/>- request_full_state

        DisconnectHandler->>ConnectionMgr: check_reconnection(room_id, player_name)
        ConnectionMgr-->>DisconnectHandler: Is reconnecting ✓

        DisconnectHandler->>BotFlag: Restore original state:<br/>player.is_bot = player.original_is_bot<br/>player.is_connected = True<br/>player.disconnect_time = None

        DisconnectHandler->>GameState: Get current game state
        DisconnectHandler->>Player: Send phase_change with:<br/>- Current phase data<br/>- All player states<br/>- Allowed actions

        DisconnectHandler->>MessageQueue: Deliver queued events
        MessageQueue-->>Player: Missed game events

    else Pre-Game Disconnect
        ConnectionMgr->>GameState: Check game started
        GameState-->>ConnectionMgr: No, pre-game

        ConnectionMgr->>ConnectionMgr: process_leave_room()<br/>(Remove from room)

        ConnectionMgr->>OtherPlayers: broadcast("player_left")
    end

    Note over Player,OtherPlayers: Key Features:<br/>• Unlimited reconnection time<br/>• Seamless bot substitution<br/>• State preservation<br/>• Message queuing<br/>• Session storage (24hr)
```

## Key Components

### 1. WebSocket ID Tracking
```python
# Each WebSocket gets a unique ID
websocket._ws_id = str(uuid.uuid4())

# Mapping maintained in ConnectionManager
self.websocket_to_player[ws_id] = (room_id, player_name)
```

### 2. State Preservation
```python
# Store original state before bot takeover
player.original_is_bot = player.is_bot
player.original_avatar_color = player.avatar_color

# Activate bot mode
player.is_bot = True
player.is_connected = False
player.disconnect_time = datetime.now()
```

### 3. Message Queue System
```python
# Create queue for disconnected player
await message_queue_manager.create_queue(room_id, player_name)

# On reconnection, deliver missed events
queued_messages = await message_queue_manager.get_messages(room_id, player_name)
```

### 4. Session Storage (Frontend)
```javascript
// Store session data in localStorage
const sessionData = {
    roomId,
    playerName,
    sessionId,
    createdAt: Date.now(),
    lastActivity: Date.now(),
    gamePhase,
};
localStorage.setItem('gameSession', JSON.stringify(sessionData));
```

## Disconnect Scenarios

### In-Game Disconnect
1. Player marked as disconnected but remains in game
2. Bot immediately takes control
3. Game continues without interruption
4. Player can reconnect anytime
5. Full state restored on reconnection

### Pre-Game Disconnect
1. Player removed from room
2. No bot activation
3. Host migration if necessary
4. Room deleted if empty

## Benefits

1. **Zero Game Interruption**: Bots maintain game flow during disconnects
2. **Unlimited Reconnection**: Players can return anytime during active game
3. **State Consistency**: Original player state perfectly preserved
4. **Message Integrity**: No game events lost during disconnect
5. **Browser Refresh Support**: Session survives page reloads
6. **Automatic Cleanup**: Rooms with only bots are cleaned up after timeout
