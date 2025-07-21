# Debug Logging for All-Bot Cleanup Investigation

## Purpose
To understand why players appear to disconnect immediately after game start, causing premature room cleanup.

## Debug Logs Added

### 1. Room State Checking (`room.py`)
In `has_any_human_players()`:
- 🔍 Logs each player's state (name, is_bot, is_connected)
- 🔍 Shows if human players are found or if all are bots
- 🔍 Helps identify the exact state when cleanup decision is made

### 2. Disconnect Handler (`ws.py`)
- 🔌 Logs disconnect time and WebSocket ID
- 🔍 Shows player state before and after bot conversion
- Tracks exact timing of disconnects

### 3. Connection Handler (`ws.py`)
- 🔗 Logs new WebSocket connections with ID and timestamp
- 🔗 Logs player registration for rooms
- ✅ Confirms successful registrations

## What to Look For in Logs

1. **Connection Sequence**: 
   - Are players connecting to the game room after game starts?
   - Do WebSocket IDs match between connect/disconnect?

2. **Timing Analysis**:
   - How much time between game start and disconnections?
   - Are disconnects happening before new connections establish?

3. **Player States**:
   - What does `has_any_human_players()` show for each player?
   - Are players already marked as bots before disconnect?

4. **Race Condition**:
   - Is there a gap between old connection closing and new connection opening?
   - Does cleanup happen during this gap?

## Expected Pattern
Normal game start should show:
1. Game starts in RoomPage
2. OLD WebSocket connections close (page navigation)
3. NEW WebSocket connections open (GamePage)
4. Players register with client_ready
5. Game continues normally

## Potential Issue
If cleanup happens between steps 2 and 4, the room gets deleted before players can reconnect.