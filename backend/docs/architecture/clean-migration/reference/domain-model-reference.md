# Domain Model Reference

This document lists the ACTUAL properties available in the domain entities to prevent AttributeError bugs.

## Room Entity (`domain/entities/room.py`)

### Properties
- `room_id: str` - The unique room identifier
- `host_name: str` - The name of the host player
- `max_slots: int` - Maximum number of players (default: 4)
- `slots: List[Optional[Player]]` - List of player slots
- `status: RoomStatus` - Current room status (WAITING, READY, IN_GAME, etc.)
- `game: Optional[Game]` - The game instance if one is active

### What Room Does NOT Have
- ❌ `id` - Use `room_id` instead
- ❌ `host_id` - Use `host_name` instead  
- ❌ `current_game` - Use `game` instead
- ❌ `settings` - No settings object
- ❌ `code` - Use `room_id` as the code
- ❌ `name` - Generate from `host_name` if needed
- ❌ `created_at` - Not tracked

### Methods
- `add_player(name: str, is_bot: bool, slot: Optional[int]) -> int`
- `remove_player(name: str) -> bool`
- `start_game() -> Game`
- `get_player(name: str) -> Optional[Player]`
- `is_host(name: str) -> bool`

## Player Entity (`domain/entities/player.py`)

### Properties
- `name: str` - The player's name
- `is_bot: bool` - Whether this is a bot player
- `hand: List[Piece]` - Current hand of pieces
- `score: int` - Current score
- `declared_piles: int` - Number of piles declared
- `captured_piles: int` - Number of piles captured
- `stats: PlayerStats` - Player statistics

### What Player Does NOT Have
- ❌ `id` - Use `name` as identifier or generate IDs in use cases
- ❌ `player_id` - Same as above
- ❌ `games_played` - Not tracked at entity level
- ❌ `games_won` - Not tracked at entity level
- ❌ `is_connected` - Not a domain concern
- ❌ `avatar_color` - Not a domain concern

## Game Entity (`domain/entities/game.py`)

### Properties
- `game_id: str` - Unique game identifier
- `room_id: str` - Associated room ID
- `players: List[Player]` - List of players in the game
- `round_number: int` - Current round number
- `turn_number: int` - Current turn number
- `phase: GamePhase` - Current game phase
- `deck: Deck` - The game deck
- `table_piles: List[Pile]` - Piles on the table

### What Game Does NOT Have
- ❌ `id` - Use `game_id` instead
- ❌ `current_player_id` - Calculate from game state
- ❌ `winner_id` - Calculate from game state

## Common Mistakes and Fixes

### Room References
```python
# WRONG
room.id → room.room_id
room.host_id → room.host_name
room.current_game → room.game
room.settings.max_players → room.max_slots
room.code → room.room_id
room.created_at → datetime.utcnow()

# CORRECT
room.room_id
room.host_name
room.game
room.max_slots
```

### Player References
```python
# WRONG
player.id → Generate: f"{room.room_id}_p{index}"
player.games_played → Use getattr(player, 'games_played', 0)
slot.id → Same as player.id

# CORRECT
player.name
player.is_bot
player.score
```

### Checking Host
```python
# WRONG
player.id == room.host_id

# CORRECT
player.name == room.host_name
```

## ID Generation Strategy

Since domain entities don't have IDs, generate them in use cases:

```python
# Player ID generation
player_id = f"{room.room_id}_p{slot_index}"

# Example for 4 players in room "ABC123":
# ABC123_p0 (host)
# ABC123_p1 
# ABC123_p2
# ABC123_p3
```

## Testing for Attribute Existence

When unsure if an attribute exists:

```python
# Safe attribute access
getattr(room, 'settings', None)
getattr(player, 'games_played', 0)
hasattr(game, 'winner_id')
```

## Next Steps

1. Update all use cases to use correct attributes
2. Add type hints to catch these errors
3. Create integration tests that verify use cases work with actual entities
4. Consider adding IDs to domain entities if they're truly needed