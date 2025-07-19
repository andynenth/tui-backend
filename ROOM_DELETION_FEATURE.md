# Room Deletion Feature - Implementation Guide

## Feature Description

When all human players have disconnected from a game room, leaving only bots, the room is automatically terminated to prevent zombie games and free up server resources. This includes stopping the game state machine, cleaning up bot handlers, and removing the room from the system.

## Current Implementation Analysis

### Core Mechanism

**Location**: `backend/api/routes/ws.py` (lines 120-145)

After handling disconnect and host migration:
```python
# Check if all players are now bots
if not room.has_human_players():
    logger.info(f"🤖 [Room {room_id}] All players are bots. Terminating game.")
    
    # Stop the game state machine
    if room.game_state_machine:
        await room.game_state_machine.stop()
    
    # Unregister from bot manager
    from engine.bot_manager import BotManager
    bot_manager = BotManager()
    bot_manager.unregister_game(room_id)
    
    # Broadcast game termination
    await broadcast(
        room_id,
        "game_terminated",
        {
            "reason": "all_players_disconnected",
            "message": "Game terminated: All players have disconnected"
        }
    )
    
    # Remove the room
    room_manager.delete_room(room_id)
    logger.info(f"🗑️ [Room {room_id}] Room removed after all players disconnected")
```

### Human Detection Logic

**Location**: `backend/engine/room.py` (lines 339-348)
```python
def has_human_players(self) -> bool:
    """
    Check if there are any human players (non-bots) in the room.
    Returns:
        bool: True if at least one human player exists, False otherwise.
    """
    for player in self.players:
        if player and not player.is_bot:
            return True
    return False
```

### Code Dependencies

1. **Room Class** (`backend/engine/room.py`):
   - `has_human_players()`: Detects if any humans remain
   - `game_state_machine`: Reference to active game state machine
   - `players`: List of all players in room

2. **GameStateMachine** (`backend/engine/state_machine/game_state_machine.py`):
   - `stop()`: Gracefully stops the state machine
   - Cancels processing tasks and exits current state

3. **BotManager** (`backend/engine/bot_manager.py`):
   - `unregister_game()`: Removes game from bot management
   - Stops bot AI processing for the room

4. **RoomManager** (`backend/engine/room_manager.py`):
   - `delete_room()`: Removes room from active rooms dictionary

## Step-by-Step Re-Implementation Guide

### Step 1: Add Human Player Detection

Add to Room class:
```python
# In backend/engine/room.py
def has_human_players(self) -> bool:
    """
    Check if there are any human players (non-bots) in the room.
    Returns:
        bool: True if at least one human player exists, False otherwise.
    """
    for player in self.players:
        if player and not player.is_bot:
            return True
    return False
```

### Step 2: Add Room Termination Check

In disconnect handler, after bot conversion and host migration:
```python
# In backend/api/routes/ws.py
# Check if all players are now bots
if not room.has_human_players():
    logger.info(f"🤖 [Room {room_id}] All players are bots. Terminating game.")
    
    # Proceed with termination...
```

### Step 3: Stop Game State Machine

```python
# Stop the game state machine
if room.game_state_machine:
    await room.game_state_machine.stop()
```

The `stop()` method should:
- Set `is_running = False`
- Cancel the processing task
- Call `on_exit()` for current state
- Clean up resources

### Step 4: Unregister from Bot Manager

```python
# Unregister from bot manager
from engine.bot_manager import BotManager
bot_manager = BotManager()
bot_manager.unregister_game(room_id)
```

### Step 5: Broadcast Termination Event

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

### Step 6: Delete Room

```python
# Remove the room
room_manager.delete_room(room_id)
logger.info(f"🗑️ [Room {room_id}] Room removed after all players disconnected")
```

## Termination Sequence

1. **Detect all players are bots** - `has_human_players()` returns False
2. **Stop state machine** - Prevents further game processing
3. **Unregister bot manager** - Stops AI from making moves
4. **Broadcast termination** - Notify any monitoring systems
5. **Delete room** - Free memory and remove from room list

## Edge Cases

1. **Reconnection during termination**
   - Once termination starts, it should complete
   - Reconnecting players redirected to lobby

2. **State machine already stopped**
   - Check if state machine exists before stopping
   - Handle gracefully if already stopped

3. **Broadcast failures**
   - Continue with cleanup even if broadcast fails
   - Log any broadcast errors

4. **Partial cleanup failure**
   - Each cleanup step should be independent
   - Continue even if one step fails

## Resource Cleanup

Ensure proper cleanup of:
- WebSocket connections
- Message queues
- Bot handler instances
- State machine tasks
- Room data structures

## Testing Guidelines

### Unit Tests

```python
def test_has_human_players_all_bots():
    room = Room("TEST", "Bot1")
    room.players = [
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True),
        Player("Bot4", is_bot=True)
    ]
    assert room.has_human_players() == False

def test_has_human_players_with_human():
    room = Room("TEST", "Human1")
    room.players = [
        Player("Human1", is_bot=False),
        Player("Bot2", is_bot=True),
        None,  # Empty slot
        Player("Bot4", is_bot=True)
    ]
    assert room.has_human_players() == True
```

### Integration Tests

1. **Test full termination flow**:
   - Start game with all humans
   - Disconnect all players one by one
   - Verify termination triggers on last disconnect
   - Verify all cleanup steps execute
   - Verify room no longer exists

2. **Test partial disconnections**:
   - Disconnect some but not all players
   - Verify game continues
   - Disconnect remaining players
   - Verify termination occurs

### Manual Testing

1. **All players close browsers**:
   - Start 4-player game
   - All players close browsers
   - Check server logs for termination
   - Verify room removed from room list

2. **Gradual player loss**:
   - Players disconnect one by one
   - Verify bots take over
   - Last player disconnects
   - Verify immediate termination

## Success Criteria

- ✅ Room terminates when last human disconnects
- ✅ State machine stops gracefully
- ✅ Bot manager cleaned up properly
- ✅ Termination event broadcast
- ✅ Room removed from system
- ✅ No memory leaks
- ✅ No zombie games with only bots
- ✅ Server resources freed immediately