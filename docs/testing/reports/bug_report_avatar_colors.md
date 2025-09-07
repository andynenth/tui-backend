# Bug Report: Avatar Colors Lost on WebSocket Reconnection

## Summary
When a page is refreshed during an active game, all player avatar colors are lost and show as `null`. Additionally, all players (including bots) are incorrectly marked as `is_bot: false` after reconnection.

## How to Reproduce
1. Create a new room
2. Start the game
3. Notice that human players have avatar colors (e.g., "pink", "blue") and bots have `null` colors
4. Refresh the page at any point during the game
5. After reconnection, all players show `avatar_color: null` and `is_bot: false`

## Root Cause Analysis

### The Bug
The issue is in the disconnect/reconnect handling in `backend/api/routes/ws.py`:

1. **During disconnect** (lines 102-111):
   ```python
   if player and not player.is_bot:  # Only processes human players!
       player.original_is_bot = player.is_bot
       player.original_avatar_color = getattr(player, 'avatar_color', None)
       player.is_bot = True  # Convert to bot during disconnect
   ```
   - Only human players get their `original_is_bot` and `original_avatar_color` saved
   - Bot players are skipped entirely

2. **During reconnection** (lines 699-707):
   ```python
   if player and player.is_bot and not player.original_is_bot:
       # This condition fails for everyone!
       player.is_bot = False
       player.avatar_color = player.original_avatar_color
   ```
   - For actual bots: They don't have `original_is_bot` set (defaults to True), so the condition fails
   - For humans: The condition works, but avatar restoration happens inside this block

3. **The phase_change broadcast** sends player data based on current state, so all players appear as humans with no colors

## Impact
- Visual confusion as all player avatars lose their colors
- Bot players appear as human players in the UI
- Game state becomes inconsistent with the original state

## Proposed Fix

In `ws.py`, the reconnection handler should:

1. Check if the player was originally a bot
2. Restore avatar colors for ALL players (not just reconnecting humans)
3. Properly handle bot vs human state restoration

```python
# During client_ready handling
if room.started and room.game:
    player = next((p for p in room.game.players if p.name == player_name), None)
    if player:
        # Check if this is a human player reconnecting
        if hasattr(player, 'original_is_bot') and not player.original_is_bot:
            # Human player reconnecting
            player.is_bot = False
            player.is_connected = True
            player.disconnect_time = None

            # Restore avatar color
            if hasattr(player, 'original_avatar_color'):
                player.avatar_color = player.original_avatar_color

        # For all players, ensure avatar colors are present
        # This handles the case where bot players lost their null avatar_color
        if not hasattr(player, 'avatar_color'):
            player.avatar_color = None  # Bots should have null
```

## Test Evidence

Console logs showing the issue:

**Before refresh:**
```
🎨 Declaration player data: TestPlayer avatar_color: pink is_bot: false
🎨 Declaration player data: Bot 2 avatar_color: null is_bot: true
```

**After refresh:**
```
🎨 Declaration player data: TestPlayer avatar_color: null is_bot: false
🎨 Declaration player data: Bot 2 avatar_color: null is_bot: false
```

All players incorrectly show as human (`is_bot: false`) with no avatar colors.
