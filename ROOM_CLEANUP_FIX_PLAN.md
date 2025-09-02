# Room Cleanup Fix Plan

## Problem Analysis

The grace period implementation causes rooms with only disconnected players (pending bot takeover) to never be cleaned up. This happens because:

1. **Room Cleanup Logic** (`backend/api/routes/ws.py`):
   - Runs every 5 seconds via `room_cleanup_task()`
   - Calls `room.should_cleanup()` to determine if room should be removed
   - `should_cleanup()` only returns true if `cleanup_scheduled = True`

2. **Cleanup Scheduling** (`backend/engine/async_room.py`):
   - `mark_for_cleanup()` sets `cleanup_scheduled = True`
   - Only called when `has_any_human_players()` returns `False`

3. **Human Player Detection Issue**:
   - `has_any_human_players()` counts players where `is_bot = False` as humans
   - Grace period keeps `is_bot = False` for 5 seconds after disconnect
   - Room thinks it still has humans during grace period
   - Cleanup is never scheduled

## Root Cause

The `has_any_human_players()` method doesn't consider:
- Players can be disconnected (`is_connected = False`)
- Players can have pending bot takeover (`bot_takeover_scheduled = True`)
- These players are effectively "not human" for cleanup purposes

## Solution

Modify `has_any_human_players()` to check for ACTUALLY ACTIVE human players:
- A player counts as human only if:
  - `is_bot = False` AND
  - `is_connected = True` (they're actually connected)
  - OR `bot_takeover_scheduled = False` (no pending takeover)

## Implementation Steps

1. **Update `has_any_human_players()` in `async_room.py`**:
   - Check both `is_bot` and connection status
   - Consider pending bot takeover status
   - Properly identify rooms ready for cleanup

2. **Add Logging**:
   - Log when rooms are marked for cleanup due to grace period
   - Track cleanup scheduling for debugging

3. **Test Scenarios**:
   - All humans disconnect → room cleaned up after timeout
   - Human reconnects within grace period → cleanup cancelled
   - Mixed bot/human rooms → only cleaned when last human leaves

## Code Changes

### backend/engine/async_room.py

```python
def has_any_human_players(self) -> bool:
    """
    Check if there are ANY ACTIVE human players in the room.
    Players in grace period (disconnected, pending bot takeover) don't count.
    """
    if not self.game:
        logger.info(
            f"🎮 [ROOM_DEBUG] has_any_human_players: No game object for room '{self.room_id}'"
        )
        return False

    human_count = 0
    bot_count = 0
    grace_period_count = 0
    
    for player in self.game.players:
        if player:
            if player.is_bot:
                bot_count += 1
            elif player.bot_takeover_scheduled:
                # Player in grace period - not counted as active human
                grace_period_count += 1
            else:
                # Only count as human if connected and not pending bot takeover
                human_count += 1

    logger.info(
        f"👥 [ROOM_DEBUG] Room '{self.room_id}' player count: "
        f"{human_count} active humans, {grace_period_count} in grace period, {bot_count} bots"
    )
    return human_count > 0
```

## Expected Behavior After Fix

1. **Player Disconnects**:
   - Grace period starts (5 seconds)
   - Room immediately marked for cleanup if no other humans
   - Cleanup happens after timeout (60 seconds by default)

2. **Player Reconnects Within Grace**:
   - Grace period cancelled
   - Room cleanup cancelled (if scheduled)
   - Game continues normally

3. **All Humans Leave**:
   - Room marked for cleanup immediately
   - Bots continue playing during cleanup timeout
   - Room deleted after timeout expires

## Testing Plan

See `ROOM_CLEANUP_TEST_PLAN.md` for comprehensive test scenarios.