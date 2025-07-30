# Issue 3: Fix Summary - Remove Bot Wrong Slot

## Problem Statement
When clicking "Remove" on a specific bot, the wrong bot was being removed from a different slot due to a dense vs sparse array mismatch between backend and frontend.

## Root Cause
The backend's `_format_room_info` function was creating a dense array (only occupied slots) instead of a sparse array (4 elements with nulls for empty slots). This caused position shifting when bots were removed.

## Solution Implemented
Modified `backend/application/websocket/use_case_dispatcher.py` in the `_format_room_info` function (lines 1080-1091):

```python
# Create sparse array with 4 elements, placing players at their seat_position index
players_array = [None] * 4
for p in room_info.players:
    if 0 <= p.seat_position < 4:
        players_array[p.seat_position] = {
            "player_id": p.player_id,
            "name": p.player_name,  # Frontend expects "name"
            "is_bot": p.is_bot,
            "is_host": p.is_host,
            "seat_position": p.seat_position,
            "avatar_color": getattr(p, "avatar_color", None),
        }
```

## Test Results
✅ All 13-step test sequence passed successfully:
- Bot 2 removed from slot 2 → Correct
- Bot 3 removed from slot 3 → Correct
- Bot 4 removed from slot 4 → Correct
- Bots added to correct slots → Correct
- No position shifting observed → Fixed

## Impact
- Frontend now receives consistent 4-element arrays
- Array indices directly map to slot positions (0-3)
- Empty slots are represented as `null`
- No more misalignment between visual slots and actual positions

## Status
✅ **FIXED** - The sparse array implementation resolves the issue completely.