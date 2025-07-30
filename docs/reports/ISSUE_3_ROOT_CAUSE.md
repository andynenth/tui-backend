# Issue 3: Root Cause - Dense Array Problem

## The Problem

When bots are removed from a room, the backend sends a **dense array** of players (only occupied slots), but the frontend expects a **sparse array** with exactly 4 elements (with nulls for empty slots).

## Example Scenario

### Initial State:
- Slot 0: Player1 (player_id: "ROOM_p0")
- Slot 1: Bot 2 (player_id: "ROOM_p1") 
- Slot 2: Bot 3 (player_id: "ROOM_p2")
- Slot 3: Bot 4 (player_id: "ROOM_p3")

Frontend receives:
```javascript
players: [
  {player_id: "ROOM_p0", name: "Player1", ...},
  {player_id: "ROOM_p1", name: "Bot 2", ...},
  {player_id: "ROOM_p2", name: "Bot 3", ...},
  {player_id: "ROOM_p3", name: "Bot 4", ...}
]
```

### After Removing Bot 2 (slot 1):
Backend removes the player from slot 1, but when formatting the room update, it only includes occupied slots:

Backend sends:
```javascript
players: [
  {player_id: "ROOM_p0", name: "Player1", ...},
  {player_id: "ROOM_p2", name: "Bot 3", ...},
  {player_id: "ROOM_p3", name: "Bot 4", ...}
]
```

### The Mismatch:
Frontend maps this dense array by index:
- `players[0]` → Slot 1 (shows Player1) ✓
- `players[1]` → Slot 2 (shows Bot 3 with player_id "ROOM_p2") ❌
- `players[2]` → Slot 3 (shows Bot 4 with player_id "ROOM_p3") ❌
- `players[3]` → Slot 4 (undefined, shows as empty) ❌

Now when you try to remove "Bot 3" from visual slot 2, it sends player_id "ROOM_p2", which is correct for Bot 3, but Bot 3 is actually in backend slot 2, not visual slot 2!

## Why This Happens

1. **Backend Domain Model**: The Room entity maintains slots as a sparse array with nulls
2. **DTO Conversion**: When creating RoomInfo DTO, only non-null players are included
3. **Frontend Assumption**: Frontend assumes players array has exactly 4 elements with nulls for empty slots

## The Fix Required

The `_format_room_info` function needs to maintain the 4-slot structure by including null entries:

```python
def _format_room_info(self, room_info) -> Dict[str, Any]:
    # ... existing code ...
    
    # Create a 4-element array with nulls for empty slots
    players_array = [None] * 4
    
    for player in room_info.players:
        if player.seat_position is not None and 0 <= player.seat_position < 4:
            players_array[player.seat_position] = {
                "player_id": player.player_id,
                "name": player.player_name,
                "is_bot": player.is_bot,
                "is_host": player.is_host,
                "seat_position": player.seat_position,
                "avatar_color": getattr(player, "avatar_color", None),
            }
    
    return {
        # ... other fields ...
        "players": players_array,  # Now always 4 elements
        # ... other fields ...
    }
```

This ensures the frontend always receives a consistent 4-element array where the index matches the slot position.