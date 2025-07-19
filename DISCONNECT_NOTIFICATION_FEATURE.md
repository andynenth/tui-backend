# Disconnect Notification Feature - Implementation Guide

## Feature Description

Real-time WebSocket notifications inform all players when someone disconnects or reconnects to the game. This includes player disconnect events, reconnection events, host change notifications, and game termination alerts.

## Current Implementation Analysis

### Event Types

1. **player_disconnected** - When a player loses connection
2. **player_reconnected** - When a player regains connection
3. **host_changed** - When host privileges transfer
4. **game_terminated** - When game ends due to all players disconnecting

### Disconnect Notification

**Location**: `backend/api/routes/ws.py` (lines 96-106)
```python
# Broadcast disconnect event
await broadcast(
    room_id,
    "player_disconnected",
    {
        "player_name": connection.player_name,
        "ai_activated": True,
        "can_reconnect": True,
        "is_bot": True
    }
)
```

### Reconnect Notification

**Location**: `backend/api/routes/ws.py` (lines 524-532)
```python
# Broadcast reconnection
await broadcast(
    room_id,
    "player_reconnected",
    {
        "player_name": player_name,
        "resumed_control": True,
        "is_bot": False
    }
)
```

### Host Change Notification

**Location**: `backend/api/routes/ws.py` (lines 109-118)
```python
# Broadcast host change if migration occurred
if new_host:
    await broadcast(
        room_id,
        "host_changed",
        {
            "old_host": connection.player_name,
            "new_host": new_host,
            "message": f"{new_host} is now the host"
        }
    )
```

### Game Termination Notification

**Location**: `backend/api/routes/ws.py` (lines 134-141)
```python
# Broadcast game termination
await broadcast(
    room_id,
    "game_terminated",
    {
        "reason": "all_players_disconnected",
        "message": "Game terminated: All players have disconnected"
    }
)
```

### Code Dependencies

1. **SocketManager** (`backend/socket_manager.py`):
   - `broadcast()`: Sends events to all room connections
   - Manages WebSocket connections per room
   - Queues messages for reliable delivery

2. **WebSocket Format**:
   - All events follow format: `{"event": "event_name", "data": {...}}`
   - Data must be JSON serializable

## Step-by-Step Re-Implementation Guide

### Step 1: Define Event Constants

Create event type constants for consistency:
```python
# Event types
PLAYER_DISCONNECTED = "player_disconnected"
PLAYER_RECONNECTED = "player_reconnected"
HOST_CHANGED = "host_changed"
GAME_TERMINATED = "game_terminated"
```

### Step 2: Implement Disconnect Notification

In disconnect handler, after bot activation:
```python
# Broadcast disconnect event
await broadcast(
    room_id,
    PLAYER_DISCONNECTED,
    {
        "player_name": connection.player_name,
        "ai_activated": True,
        "can_reconnect": True,
        "is_bot": True,
        "timestamp": datetime.now().isoformat()
    }
)
```

### Step 3: Implement Host Change Notification

After host migration:
```python
# Broadcast host change if migration occurred
if new_host:
    await broadcast(
        room_id,
        HOST_CHANGED,
        {
            "old_host": connection.player_name,
            "new_host": new_host,
            "message": f"{new_host} is now the host",
            "timestamp": datetime.now().isoformat()
        }
    )
```

### Step 4: Implement Reconnect Notification

In client_ready handler, after restoring human control:
```python
# Broadcast reconnection
await broadcast(
    room_id,
    PLAYER_RECONNECTED,
    {
        "player_name": player_name,
        "resumed_control": True,
        "is_bot": False,
        "missed_events": len(queued_messages),
        "timestamp": datetime.now().isoformat()
    }
)
```

### Step 5: Implement Termination Notification

Before deleting room:
```python
# Broadcast game termination
await broadcast(
    room_id,
    GAME_TERMINATED,
    {
        "reason": "all_players_disconnected",
        "message": "Game terminated: All players have disconnected",
        "final_state": {
            "round": room.game.round_number if room.game else 0,
            "scores": {p.name: p.score for p in room.game.players if p} if room.game else {}
        },
        "timestamp": datetime.now().isoformat()
    }
)
```

### Step 6: Ensure Broadcast Function

The broadcast function should:
```python
async def broadcast(room_id: str, event: str, data: dict):
    """
    Broadcast a message to all connections in a room.
    
    Args:
        room_id: The ID of the room to broadcast to
        event: The event type to send
        data: The event data payload
    """
    await _socket_manager.broadcast(room_id, event, data)
```

## Event Data Specifications

### player_disconnected
```json
{
    "player_name": "string",
    "ai_activated": true,
    "can_reconnect": true,
    "is_bot": true,
    "timestamp": "ISO 8601 timestamp"
}
```

### player_reconnected
```json
{
    "player_name": "string",
    "resumed_control": true,
    "is_bot": false,
    "missed_events": 5,
    "timestamp": "ISO 8601 timestamp"
}
```

### host_changed
```json
{
    "old_host": "string",
    "new_host": "string",
    "message": "string",
    "timestamp": "ISO 8601 timestamp"
}
```

### game_terminated
```json
{
    "reason": "all_players_disconnected",
    "message": "string",
    "final_state": {
        "round": 5,
        "scores": {"Player1": 25, "Player2": 30}
    },
    "timestamp": "ISO 8601 timestamp"
}
```

## Client-Side Handling

Clients should listen for these events:
```javascript
websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.event) {
        case 'player_disconnected':
            // Show disconnect notification
            // Update player status UI
            break;
        case 'player_reconnected':
            // Show reconnect notification
            // Update player status UI
            break;
        case 'host_changed':
            // Update host indicator
            // Show host change message
            break;
        case 'game_terminated':
            // Show game over screen
            // Redirect to lobby
            break;
    }
};
```

## Edge Cases

1. **Broadcast during room deletion**
   - Termination event should send before connections close
   - Handle broadcast failures gracefully

2. **Multiple events in quick succession**
   - Events should maintain order
   - Use timestamps for sequencing

3. **Reconnection during disconnect broadcast**
   - Both events should be sent
   - Clients handle based on timestamps

## Testing Guidelines

### Unit Tests

```python
def test_disconnect_event_format():
    event_data = {
        "player_name": "TestPlayer",
        "ai_activated": True,
        "can_reconnect": True,
        "is_bot": True
    }
    # Verify all required fields present
    assert "player_name" in event_data
    assert "ai_activated" in event_data
    assert event_data["is_bot"] == True
```

### Integration Tests

1. **Test event delivery**:
   - Connect multiple clients to room
   - Trigger disconnect
   - Verify all clients receive event
   - Verify event data correct

2. **Test event ordering**:
   - Rapid disconnect/reconnect
   - Verify events arrive in order
   - Verify no events lost

### Manual Testing

1. **Multi-client notification**:
   - Open game in multiple browsers
   - Disconnect one player
   - Verify notification appears in all browsers
   - Check notification content

2. **Event storm test**:
   - Multiple players disconnect simultaneously
   - Verify all events delivered
   - Check server performance

## Success Criteria

- ✅ All players receive disconnect notifications
- ✅ All players receive reconnect notifications
- ✅ Host changes broadcast to entire room
- ✅ Game termination notifies all connections
- ✅ Events contain sufficient information
- ✅ Events delivered in correct order
- ✅ No events lost during high activity
- ✅ Clients can parse and display notifications