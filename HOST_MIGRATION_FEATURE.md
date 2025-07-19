# Host Migration Feature - Implementation Guide

## Feature Description

When the game host disconnects, host privileges are automatically transferred to another player to ensure game administration continues. The system prioritizes human players over bots when selecting a new host.

## Current Implementation Analysis

### Core Mechanism

**Location**: `backend/api/routes/ws.py` (lines 89-94) and `backend/engine/room.py` (lines 350-375)

When host disconnects:
```python
# Check if disconnecting player was the host
new_host = None
if room.is_host(connection.player_name):
    new_host = room.migrate_host()
    if new_host:
        logger.info(f"Host migrated to {new_host} in room {room_id}")
```

### Migration Logic

**Location**: `backend/engine/room.py`
```python
def migrate_host(self) -> Optional[str]:
    # First, try to find a human player who isn't the current host
    for player in self.players:
        if player and not player.is_bot and player.name != self.host_name:
            old_host = self.host_name
            self.host_name = player.name
            return self.host_name
    
    # If no human players available, select the first bot
    for player in self.players:
        if player and player.is_bot:
            old_host = self.host_name
            self.host_name = player.name
            return self.host_name
    
    # No suitable host found (room is empty?)
    return None
```

### Code Dependencies

1. **Room Class** (`backend/engine/room.py`):
   - `host_name`: Stores current host player name
   - `is_host()`: Checks if player is the host
   - `migrate_host()`: Implements migration logic

2. **Player Class** (`backend/engine/player.py`):
   - `is_bot`: Used to prioritize humans over bots
   - `name`: Player identifier for host assignment

3. **WebSocket Broadcasting**:
   - Notifies all clients about host change
   - Updates UI to reflect new host privileges

## Step-by-Step Re-Implementation Guide

### Step 1: Add Host Checking Method

Add to Room class:
```python
# In backend/engine/room.py
def is_host(self, player_name: str) -> bool:
    """
    Check if a player is the current host.
    Args:
        player_name (str): The name of the player to check.
    Returns:
        bool: True if the player is the host, False otherwise.
    """
    return self.host_name == player_name
```

### Step 2: Implement Host Migration Method

Add to Room class:
```python
def migrate_host(self) -> Optional[str]:
    """
    Migrates host privileges to the next suitable player.
    Prefers human players over bots.
    Returns:
        Optional[str]: Name of the new host, or None if no suitable host found.
    """
    # First, try to find a human player who isn't the current host
    for player in self.players:
        if player and not player.is_bot and player.name != self.host_name:
            old_host = self.host_name
            self.host_name = player.name
            print(f"🔄 [Room {self.room_id}] Host migrated from '{old_host}' to '{self.host_name}'")
            return self.host_name
    
    # If no human players available, select the first bot
    for player in self.players:
        if player and player.is_bot:
            old_host = self.host_name
            self.host_name = player.name
            print(f"🔄 [Room {self.room_id}] Host migrated from '{old_host}' to bot '{self.host_name}'")
            return self.host_name
    
    # No suitable host found (room is empty?)
    print(f"⚠️ [Room {self.room_id}] No suitable host found for migration")
    return None
```

### Step 3: Add Migration to Disconnect Handler

In WebSocket disconnect handler:
```python
# In backend/api/routes/ws.py, after bot conversion
# Check if disconnecting player was the host
new_host = None
if room.is_host(connection.player_name):
    new_host = room.migrate_host()
    if new_host:
        logger.info(f"Host migrated to {new_host} in room {room_id}")
```

### Step 4: Broadcast Host Change

After migration:
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

### Step 5: Update Room Summary

Ensure room summary includes host information:
```python
# In Room.summary() method
def summary(self):
    return {
        "room_id": self.room_id,
        "host_name": self.host_name,  # Current host
        "started": self.started,
        "slots": {
            f"P{i+1}": slot_info(p, i)
            for i, p in enumerate(self.players)
        },
        # ... other fields ...
    }
```

## Edge Cases

1. **All human players disconnect**
   - Host migrates to first available bot
   - Bot can act as host for game continuity

2. **Host reconnects after migration**
   - Original host does NOT automatically regain host status
   - New host retains privileges

3. **No players available**
   - Migration returns None
   - Room should be cleaned up separately

4. **Simultaneous disconnections**
   - Migration happens sequentially
   - First disconnect triggers first migration

## Migration Priority

1. **First Priority**: Another human player (not current host)
2. **Second Priority**: First available bot
3. **No Migration**: If room is empty

## Testing Guidelines

### Unit Tests

```python
def test_host_migration_prefers_humans():
    room = Room("TEST", "Host1")
    room.players = [
        Player("Host1", is_bot=False),  # Current host
        Player("Human2", is_bot=False),  # Should become new host
        Player("Bot3", is_bot=True),
        Player("Bot4", is_bot=True)
    ]
    
    new_host = room.migrate_host()
    assert new_host == "Human2"
    assert room.host_name == "Human2"

def test_host_migration_to_bot_when_no_humans():
    room = Room("TEST", "Host1")
    room.players = [
        Player("Host1", is_bot=False),  # Current host disconnecting
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True),
        Player("Bot4", is_bot=True)
    ]
    
    new_host = room.migrate_host()
    assert new_host == "Bot2"
    assert room.host_name == "Bot2"
```

### Integration Tests

1. **Test host disconnect flow**:
   - Create room with multiple players
   - Disconnect host
   - Verify migration occurs
   - Verify broadcast sent
   - Verify new host in room state

2. **Test priority system**:
   - Mix of humans and bots
   - Disconnect host
   - Verify human selected over bot

### Manual Testing

1. **Host browser close**:
   - Create room as host
   - Have other players join
   - Close host's browser
   - Verify host badge moves to new player
   - Verify game controls available to new host

2. **Chain migration**:
   - Host disconnects → migrates to Player2
   - Player2 disconnects → migrates to Player3
   - Verify each migration works correctly

## Success Criteria

- ✅ Host migration happens immediately on disconnect
- ✅ Human players prioritized over bots
- ✅ Host change event broadcast to all clients
- ✅ New host can perform host actions
- ✅ No race conditions during migration
- ✅ Room state remains consistent
- ✅ Original host doesn't regain status on reconnect