# Bot Replacement Feature - Detailed Implementation Document

## Overview
This document provides a step-by-step implementation plan for the bot replacement feature in Liap Tui. When a player disconnects during an active game, they will be automatically replaced by a bot to ensure the game continues without interruption.

## Current System Architecture

### 1. WebSocket Architecture
The WebSocket system is defined in `/backend/api/routes/ws.py`:
- Single WebSocket endpoint: `@router.websocket("/ws/{room_id}")`
- Players connect to either "lobby" or specific room IDs
- Connection tracking handled by `socket_manager.py`

### 2. Player Model
The Player class is defined in `/backend/engine/player.py`:
```python
class Player:
    def __init__(self, name, is_bot=False):
        self.name = name
        self.hand = []
        self.score = 0
        self.declared = 0
        self.captured_piles = 0
        self.is_bot = is_bot  # Key field for bot control
        self.zero_declares_in_a_row = 0
        self.turns_won = 0
        self.perfect_rounds = 0
```

### 3. Bot System
The bot system consists of:
- `/backend/engine/bot_manager.py` - Singleton that manages bot actions
- `/backend/engine/ai.py` - Contains bot decision logic
- Bot actions are automatically triggered through the state machine

## Implementation Steps

### Step 1: Extend Player Class with Connection Tracking

**File**: `/backend/engine/player.py`

Add the following fields to the `Player.__init__` method after line 18:
```python
# Connection tracking for disconnect handling
self.is_connected = True  # Whether player is currently connected
self.disconnect_time = None  # When player disconnected
self.original_is_bot = is_bot  # Store original bot state for reconnection
```

**Rationale**: These fields track the player's connection status without requiring external systems.

### Step 2: Create WebSocket-to-Player Tracking

**File**: `/backend/api/routes/ws.py`

Add after line 21 (after `room_manager = shared_room_manager`):
```python
# WebSocket to player mapping for disconnect handling
websocket_players = {}  # {websocket_id: (room_id, player_name)}
```

### Step 3: Track Player-WebSocket Association

**File**: `/backend/api/routes/ws.py`

Find the `client_ready` event handler (around line 133). After a successful game join, add tracking:

Locate this section in the existing code:
```python
elif event_name == "client_ready":
    # Send initial room list when client connects to lobby
    available_rooms = room_manager.list_rooms()
```

We need to add tracking when players join game rooms. Find where players actually join games and add:
```python
# When a player successfully joins a game room
websocket_id = id(registered_ws)
websocket_players[websocket_id] = (room_id, player_name)
```

### Step 4: Implement Disconnect Handling

**File**: `/backend/api/routes/ws.py`

Replace the current disconnect handler (lines 1273-1284):
```python
except WebSocketDisconnect:
    unregister(room_id, websocket)
    if room_id == "lobby":
        pass
    else:
        pass
```

With:
```python
except WebSocketDisconnect:
    unregister(room_id, websocket)
    
    # Check if this websocket had an associated player in a game
    websocket_id = id(registered_ws)
    if websocket_id in websocket_players:
        tracked_room_id, player_name = websocket_players[websocket_id]
        del websocket_players[websocket_id]
        
        # Get the room and check if game is active
        room = room_manager.get_room(tracked_room_id)
        if room and room.started and room.game:
            # Find the player in the game
            player = next(
                (p for p in room.game.players if p.name == player_name),
                None
            )
            
            if player and not player.is_bot:
                # Store disconnect info
                player.original_is_bot = player.is_bot
                player.is_connected = False
                player.disconnect_time = datetime.now()
                
                # Convert to bot
                player.is_bot = True
                
                logger.info(f"Player {player_name} disconnected from active game in room {tracked_room_id}. Bot activated.")
                
                # Broadcast player status update
                await broadcast(
                    tracked_room_id,
                    "player_status_update",
                    {
                        "player_name": player_name,
                        "is_connected": False,
                        "is_bot_controlled": True,
                        "timestamp": datetime.now().isoformat()
                    }
                )
```

### Step 5: Implement Reconnection Handling

**File**: `/backend/api/routes/ws.py`

We need to handle reconnection when a player joins a game room. Find where game state is sent to joining players and add reconnection logic.

Look for where room state or game state is sent to newly connected clients, and add:
```python
# Check if this is a reconnection to an active game
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
        
        # Track the new websocket
        websocket_id = id(registered_ws)
        websocket_players[websocket_id] = (room_id, player_name)
        
        logger.info(f"Player {player_name} reconnected to game in room {room_id}")
        
        # Send full game state to reconnected player
        # (This would use existing game state serialization)
        
        # Broadcast reconnection to other players
        await broadcast(
            room_id,
            "player_status_update",
            {
                "player_name": player_name,
                "is_connected": True,
                "is_bot_controlled": False,
                "timestamp": datetime.now().isoformat()
            }
        )
```

### Step 6: Frontend Handling

The frontend should handle the new `player_status_update` event to show when players disconnect/reconnect.

**File**: `/frontend/src/pages/GamePage.jsx` (or relevant game component)

Add event listener:
```javascript
const handlePlayerStatusUpdate = (event) => {
    const { player_name, is_connected, is_bot_controlled } = event.detail.data;
    console.log(`Player ${player_name} status: connected=${is_connected}, bot=${is_bot_controlled}`);
    // Update UI to show bot indicator
};

networkService.addEventListener('player_status_update', handlePlayerStatusUpdate);
```

## How It Works

1. **Connection Tracking**: When a player joins a game, their WebSocket is mapped to their player name
2. **Disconnect Detection**: WebSocketDisconnect exception triggers bot activation
3. **Bot Takeover**: Setting `player.is_bot = True` automatically enables the existing BotManager
4. **Game Continuity**: The game continues with the bot making decisions through the state machine
5. **Reconnection**: When the player returns, they resume control by setting `is_bot = False`

## Testing Plan

### Manual Testing
1. Start a game with 4 human players
2. Close one player's browser during their turn
3. Verify bot takes over and makes a valid move
4. Reopen the browser and navigate back to the game
5. Verify human control is restored

### Edge Cases to Test
1. Disconnect during player's turn
2. Disconnect during other player's turn
3. Multiple simultaneous disconnects
4. Disconnect during state transitions
5. Reconnect after game ends

## No New Systems Required

This implementation reuses existing systems:
- **BotManager**: Already handles any player with `is_bot = True`
- **State Machine**: Already broadcasts game state changes
- **WebSocket System**: Already handles connections/disconnections
- **Game State**: Already serializable for state sync

## Summary

This implementation adds minimal code to achieve bot replacement:
1. 3 new fields in Player class
2. Simple WebSocket-to-player tracking dictionary
3. Disconnect handler that flips the `is_bot` flag
4. Reconnection handler that restores human control

Total new code: ~50 lines across 2 files, with no new classes or systems needed.