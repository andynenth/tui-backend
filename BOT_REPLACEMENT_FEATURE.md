# Bot Replacement Feature - Implementation Guide

## Feature Description

When a player disconnects from an active game, their character is automatically controlled by a bot to ensure the game can continue without interruption. The disconnected player can reconnect at any time and resume control.

## Current Implementation Analysis

### Core Mechanism

**Location**: `backend/api/routes/ws.py` (lines 75-87)

When a disconnection is detected:
```python
if player and not player.is_bot:
    # Store original bot state
    player.original_is_bot = player.is_bot
    player.is_connected = False
    player.disconnect_time = connection.disconnect_time
    
    # Convert to bot
    player.is_bot = True
    
    # Create message queue for the disconnected player
    await message_queue_manager.create_queue(room_id, connection.player_name)
```

### Code Dependencies

1. **Player Class** (`backend/engine/player.py`):
   - `is_bot`: Boolean flag indicating if player is bot-controlled
   - `is_connected`: Connection status tracking
   - `disconnect_time`: Timestamp of disconnection
   - `original_is_bot`: Stores original bot state for reconnection

2. **ConnectionManager** (`backend/api/websocket/connection_manager.py`):
   - Tracks WebSocket-to-player mappings
   - Returns player info on disconnect via `handle_disconnect()`

3. **MessageQueueManager** (`backend/api/websocket/message_queue.py`):
   - Creates queues to store game events during disconnect
   - Ensures player doesn't miss critical game updates

4. **BotManager** (`backend/engine/bot_manager.py`):
   - Already handles any player with `is_bot = True`
   - No modifications needed - automatically takes over

## Step-by-Step Re-Implementation Guide

### Step 1: Extend Player Class

Add disconnect tracking fields to the Player constructor:

```python
# In backend/engine/player.py
def __init__(self, name, is_bot=False):
    # ... existing fields ...
    
    # Connection tracking (for disconnect handling)
    self.is_connected = True  # Whether player is currently connected
    self.disconnect_time = None  # When player disconnected
    self.original_is_bot = is_bot  # Store original bot state for reconnection
```

### Step 2: Create WebSocket Tracking

In the WebSocket disconnect handler:

```python
# In backend/api/routes/ws.py
async def handle_disconnect(room_id: str, websocket: WebSocket):
    """Handle player disconnection with bot activation"""
    try:
        # Get player info from connection tracking
        connection = await connection_manager.handle_disconnect(websocket_id)
        
        if connection and room_id != "lobby":
            room = room_manager.get_room(room_id)
            if room and room.started and room.game:
                # Find the player in the game
                player = next(
                    (p for p in room.game.players if p.name == connection.player_name),
                    None
                )
                
                if player and not player.is_bot:
                    # Convert to bot
                    player.original_is_bot = player.is_bot
                    player.is_connected = False
                    player.disconnect_time = connection.disconnect_time
                    player.is_bot = True
```

### Step 3: Create Message Queue

Add message queue creation for disconnected players:

```python
# Create message queue for the disconnected player
await message_queue_manager.create_queue(room_id, connection.player_name)

logger.info(f"Player {connection.player_name} disconnected from game in room {room_id}. Bot activated.")
```

### Step 4: Handle Reconnection

In the `client_ready` event handler:

```python
# Check if reconnecting to an active game
if room.started and room.game:
    player = next(
        (p for p in room.game.players if p.name == player_name),
        None
    )
    if player and player.is_bot and not player.original_is_bot:
        # This is a human player reconnecting
        player.is_bot = False
        player.is_connected = True
        player.disconnect_time = None
        
        logger.info(f"Player {player_name} reconnected to game in room {room_id}")
```

## Edge Cases

1. **Player disconnects during their turn**
   - Bot should complete the turn following game rules
   - Turn timer continues normally

2. **Multiple disconnections**
   - Each player gets their own bot replacement
   - Game continues as long as at least one connection exists

3. **Disconnect during action processing**
   - Action should complete normally
   - Bot takes over for subsequent actions

4. **Network flicker (quick disconnect/reconnect)**
   - Message queue prevents missing events
   - Player resumes control seamlessly

## Testing Guidelines

### Unit Tests

```python
def test_player_disconnect_converts_to_bot():
    player = Player("TestPlayer", is_bot=False)
    
    # Simulate disconnect
    player.is_bot = True
    player.is_connected = False
    player.disconnect_time = datetime.now()
    
    assert player.is_bot == True
    assert player.is_connected == False
    assert player.original_is_bot == False
```

### Integration Tests

1. **Test bot takeover**:
   - Start game with human player
   - Disconnect the player
   - Verify bot makes valid moves
   - Verify game continues normally

2. **Test reconnection**:
   - Disconnect player
   - Let bot play a few turns
   - Reconnect player
   - Verify human control restored
   - Verify queued messages delivered

### Manual Testing

1. **Browser close test**:
   - Start game
   - Close browser tab
   - Check server logs for bot activation
   - Reopen game and verify reconnection

2. **Network interruption test**:
   - Start game
   - Disable network
   - Re-enable after 30 seconds
   - Verify seamless continuation

## Success Criteria

- ✅ Disconnected players immediately converted to bots
- ✅ Game continues without interruption
- ✅ No player actions lost during disconnect
- ✅ Reconnection restores human control
- ✅ Message queue delivers missed events
- ✅ Bot follows same rules as human players