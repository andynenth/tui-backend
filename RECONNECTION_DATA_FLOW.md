# Reconnection Implementation Data Flow

## Overview

This document traces the complete data flow for the disconnect/reconnect functionality in Liap Tui.

## Data Flow Diagram

```
┌─────────────────┐
│   Player (Bob)  │
│   WebSocket     │
└────────┬────────┘
         │ Disconnect
         ▼
┌─────────────────────────────┐
│   WebSocket Handler (ws.py)  │
│   handle_disconnect()        │
└────────┬────────────────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│ ConnectionManager │  │   Player Object   │
│ - Set DISCONNECTED│  │ - is_bot = True   │
│ - Track ws_id    │  │ - is_connected=False│
└──────────────────┘  └──────────────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│  Message Queue   │  │    Broadcast     │
│  Created for Bob │  │ player_disconnected│
└──────────────────┘  └──────────────────┘
         │
         │ Game Events While Disconnected
         ▼
┌─────────────────────────────┐
│     Message Queue Stores:    │
│ - phase_change (critical)    │
│ - turn_resolved (critical)   │
│ - play events                │
│ - score_update (critical)    │
└─────────────────────────────┘
         │
         │ Bob Reconnects
         ▼
┌─────────────────────────────┐
│   WebSocket Handler (ws.py)  │
│   client_ready event         │
└────────┬────────────────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│ Check Reconnection│  │ Retrieve Queued  │
│ - Unlimited time  │  │    Messages      │
└──────────────────┘  └──────────────────┘
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│  Restore Player  │  │ Send Queued Msgs │
│ - is_bot = False │  │  to Client       │
│ - is_connected=True│ └──────────────────┘
└──────────────────┘
         │
         ▼
┌─────────────────────────────┐
│      Clear Message Queue     │
│   Broadcast player_reconnected│
└─────────────────────────────┘
```

## Detailed Step-by-Step Trace

### 1. Initial State
- Bob is connected with WebSocket ID `ws_002`
- ConnectionManager tracks: `{room_id: "test_room", player_name: "Bob", status: CONNECTED}`
- Player object: `{name: "Bob", is_bot: false, is_connected: true}`

### 2. Disconnect Event
**Trigger**: WebSocket connection lost

**Actions**:
```python
# In ws.py handle_disconnect()
connection = await connection_manager.handle_disconnect("ws_002")
# Returns: PlayerConnection with status=DISCONNECTED
```

### 3. Bot Activation
**Data Changes**:
```python
player.original_is_bot = False  # Store original state
player.is_bot = True           # Activate bot
player.is_connected = False    # Mark disconnected
player.disconnect_time = datetime.now()
```

### 4. Message Queue Creation
```python
await message_queue_manager.create_queue("test_room", "Bob")
# Creates: PlayerQueue with max_size=100
```

### 5. Event Broadcasting
```python
await broadcast("test_room", "player_disconnected", {
    "player_name": "Bob",
    "ai_activated": True,
    "can_reconnect": True,
    "is_bot": True
})
```

### 6. Game Events While Disconnected
Each game event is queued:
```python
# Critical events (preserved in queue overflow)
await message_queue_manager.queue_message(
    "test_room", "Bob", "phase_change", 
    {"phase": "TURN", "current_player": "Charlie"}
)

# Non-critical events (may be dropped if queue full)
await message_queue_manager.queue_message(
    "test_room", "Bob", "play",
    {"player": "Charlie", "pieces": [1, 2]}
)
```

### 7. Reconnection Attempt
**Trigger**: Bob reconnects with new WebSocket ID `ws_005`

**Validation**:
```python
can_reconnect = await connection_manager.check_reconnection("test_room", "Bob")
# Returns: True (unlimited reconnection time)
```

### 8. Message Retrieval
```python
queued_messages = await message_queue_manager.get_queued_messages("test_room", "Bob")
# Returns: List of messages with timestamps and sequences
```

### 9. State Restoration
```python
# Player object restored
player.is_bot = False
player.is_connected = True
player.disconnect_time = None

# New connection registered
await connection_manager.register_player("test_room", "Bob", "ws_005")
```

### 10. Client Update
```python
# Send queued messages to client
await websocket.send_json({
    "event": "queued_messages",
    "data": {
        "messages": queued_messages,
        "count": len(queued_messages)
    }
})
```

### 11. Cleanup
```python
# Clear message queue
await message_queue_manager.clear_queue("test_room", "Bob")

# Broadcast reconnection
await broadcast("test_room", "player_reconnected", {
    "player_name": "Bob",
    "resumed_control": True,
    "is_bot": False
})
```

## Frontend Data Flow

### 1. Disconnect Detection
```javascript
// GameService.ts receives event
handlePlayerDisconnected(state, data) {
    // Add to disconnected players list
    disconnectedPlayers.push(data.player_name)
    
    // Update player state
    player.is_bot = true
    player.is_connected = false
}
```

### 2. UI Updates
```javascript
// Components react to state changes
<PlayerAvatar 
    player={player}
    isBot={player.is_bot}  // Shows robot icon
/>

<ConnectionIndicator
    disconnectedPlayers={state.disconnectedPlayers}
    // Shows "AI Playing for: Bob"
/>
```

### 3. Reconnection Handling
```javascript
// GameService.ts processes reconnection
handlePlayerReconnected(state, data) {
    // Remove from disconnected list
    disconnectedPlayers = disconnectedPlayers.filter(
        name => name !== data.player_name
    )
    
    // Restore player state
    player.is_bot = false
    player.is_connected = true
}
```

## Key Data Structures

### PlayerConnection (Backend)
```python
@dataclass
class PlayerConnection:
    room_id: str
    player_name: str
    websocket_id: str
    connection_status: ConnectionStatus
    connect_time: datetime
    disconnect_time: Optional[datetime]
    last_activity: datetime
```

### QueuedMessage (Backend)
```python
@dataclass
class QueuedMessage:
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    sequence: int
    is_critical: bool
```

### Player State (Frontend)
```typescript
interface Player {
    name: string;
    is_bot: boolean;
    is_connected?: boolean;
    disconnect_time?: string;
    original_is_bot?: boolean;
}
```

### GameState (Frontend)
```typescript
interface GameState {
    // ... other fields
    disconnectedPlayers: string[];
    host: string | null;
}
```

## Verification Points

The trace test verifies:

1. **Unlimited Reconnection**: ✓ No time limit enforced
2. **Bot Activation**: ✓ Bot takes over on disconnect
3. **Message Queuing**: ✓ 5 messages queued (3 critical)
4. **State Restoration**: ✓ Player control restored
5. **Queue Cleanup**: ✓ Queue cleared after delivery
6. **Multiple Disconnects**: ✓ All players can reconnect
7. **Queue Overflow**: ✓ Limited to 100 messages
8. **Rapid Cycles**: ✓ Handles rapid disconnect/reconnect

## Performance Metrics

From the trace test:
- Disconnect handling: < 1ms
- Queue operations: < 1ms per message
- Reconnection validation: < 1ms
- State restoration: < 1ms
- Total reconnection time: < 10ms (excluding network latency)