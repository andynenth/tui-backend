# Task 2: Async Readiness - Liap Tui System

## Executive Summary

This document outlines the work required to prepare the Liap Tui system for full async compatibility, particularly for future database operations. Currently, the system has a mixed async/sync architecture where the API layer is fully async, but the core game engine remains largely synchronous.

**Current Readiness: 2/5** ⚠️
- API layer: ✅ Fully async
- State machine: ✅ Fully async
- Game engine: ❌ Mostly sync
- Room management: ⚠️ Mixed async/sync

## 1. Current Async Usage Survey

### 1.1 Fully Async Modules ✅
```
backend/api/
├── routes/
│   ├── ws.py              # WebSocket handlers
│   ├── routes.py          # REST endpoints
│   └── debug.py           # Debug endpoints
├── websocket/
│   ├── connection_manager.py
│   ├── message_queue.py
│   └── state_sync.py
├── services/
│   ├── event_store.py     # Event storage
│   ├── recovery_manager.py
│   └── health_monitor.py
└── middleware/
    ├── rate_limit.py
    └── websocket_rate_limit.py

backend/engine/state_machine/
├── base_state.py          # State base class
├── game_state_machine.py  # Main state machine
├── action_queue.py        # Action processing
└── states/               # All state implementations
```

### 1.2 Mixed Async/Sync Modules ⚠️
```
backend/engine/
├── bot_manager.py         # Has async methods but calls sync game methods
└── room.py               # Mix of async (start_game_safe) and sync methods
```

### 1.3 Purely Synchronous Modules ❌
```
backend/engine/
├── game.py               # Core game logic
├── player.py             # Player class
├── room_manager.py       # Room manager
├── rules.py              # Game rules
├── scoring.py            # Scoring logic
├── piece.py              # Piece class
├── ai.py                 # AI logic
├── turn_resolution.py    # Turn resolution
└── win_conditions.py     # Win conditions
```

## 2. Functions Requiring Async Conversion

### 2.1 High Priority - Direct WebSocket Call Chain 🔴

These sync methods are called directly from async WebSocket handlers:

**Room Class** (`backend/engine/room.py`):
```python
# Current sync methods that need conversion:
def join_room(self, player_name: str) -> Dict
def exit_room(self, player_name: str) -> Dict  
def start_game(self) -> Dict
def assign_slot(self, player_name: str, slot: int) -> Dict
```

**Room Manager** (`backend/engine/room_manager.py`):
```python
# Current sync methods that need conversion:
def create_room(self, host_name: str) -> str
def get_room(self, room_id: str) -> Optional[Room]
def delete_room(self, room_id: str) -> bool
```

### 2.2 Medium Priority - Game State Persistence 🟡

These methods will need database writes for state persistence:

**Game Class** (`backend/engine/game.py`):
```python
# Methods that modify game state:
def deal_pieces(self) -> None
def play_turn(self, player_name: str, pieces: List[str]) -> Dict
def calculate_scores(self) -> Dict[str, int]
def start_new_round(self) -> None
def check_game_over(self) -> Optional[str]
```

**Player Class** (`backend/engine/player.py`):
```python
# Methods that record player actions:
def record_declaration(self, value: int) -> None
def add_pieces_to_hand(self, pieces: List[Piece]) -> None
def remove_pieces_from_hand(self, pieces: List[Piece]) -> None
def reset_for_next_round(self) -> None
```

### 2.3 Low Priority - Pure Computation 🟢

These can remain synchronous as they're pure calculations:
- `rules.py` - All validation methods
- `scoring.py` - Score calculation algorithms
- `ai.py` - AI decision making (unless it needs DB lookups)
- `piece.py` - Piece comparisons

## 3. Sync Access Patterns in Real-Time Flow

### 3.1 Current Call Flow
```
WebSocket Handler (async)
    ↓
Room.join_room() [SYNC] ← Problem: Called from async context
    ↓
Game.add_player() [SYNC]
    ↓
Player.__init__() [SYNC]
```

### 3.2 Problematic Patterns Found

1. **Direct sync calls from async:**
   ```python
   # In ws.py (async)
   room = room_manager.get_room(room_id)  # Sync call
   result = room.join_room(player_name)   # Sync call
   ```

2. **Mixed async/sync in same class:**
   ```python
   # In room.py
   async def start_game_safe(self, broadcast_callback):  # Async
   def start_game(self):  # Sync - same functionality!
   ```

3. **No connection pooling preparation:**
   - All current code assumes single-threaded access
   - No consideration for connection pool limits

## 4. Specific Conversion Requirements

### 4.1 Room Management Chain
```python
# Current (sync)
def join_room(self, player_name: str) -> Dict:
    # Validation
    # Add player
    # Update state
    return result

# Required (async)
async def join_room(self, player_name: str) -> Dict:
    # Validation
    # Add player
    await self.event_store.store_event(...)  # DB write
    # Update state
    return result
```

### 4.2 Game State Updates
```python
# Current (sync)
def play_turn(self, player_name: str, pieces: List[str]) -> Dict:
    # Validate move
    # Update game state
    return result

# Required (async)
async def play_turn(self, player_name: str, pieces: List[str]) -> Dict:
    # Validate move
    async with self.db.transaction():  # DB transaction
        # Update game state
        await self.db.save_move(...)
    return result
```

### 4.3 State Machine Integration
```python
# Current state machine already async, but calls sync game methods
async def handle_action(self, action: GameAction):
    # This is async
    result = self.game.play_turn(...)  # But calls sync method!
    
# Need to convert to:
async def handle_action(self, action: GameAction):
    result = await self.game.play_turn(...)  # Async all the way
```

## 5. Risks and Side Effects

### 5.1 Performance Risks 🚨
- **Risk**: Async overhead for operations that don't need I/O
- **Mitigation**: Keep pure calculations synchronous
- **Impact**: Minor (<1ms) for most operations

### 5.2 Concurrency Risks 🚨
- **Risk**: Race conditions when multiple async operations modify same game
- **Mitigation**: Use async locks for game state modifications
- **Example**:
  ```python
  async def play_turn(self, ...):
      async with self.game_lock:  # Prevent concurrent modifications
          # Modify game state
  ```

### 5.3 Migration Risks 🚨
- **Risk**: Breaking existing code during conversion
- **Mitigation**: Gradual migration with compatibility layers
- **Strategy**: Keep both sync and async versions temporarily

### 5.4 Testing Complexity 🚨
- **Risk**: Async tests are more complex
- **Mitigation**: Comprehensive async test utilities
- **Required**: Update all tests to handle async

## 6. Step-by-Step Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Create async compatibility layer for gradual migration
- [ ] Add async locks to shared resources (rooms, games)
- [ ] Create async test utilities and fixtures
- [ ] Document async patterns and best practices

### Phase 2: Room Management (Week 2)
- [ ] Convert `RoomManager` to async:
  - [ ] `create_room()` → `async def create_room()`
  - [ ] `get_room()` → `async def get_room()`
  - [ ] `delete_room()` → `async def delete_room()`
- [ ] Convert `Room` class methods:
  - [ ] `join_room()` → `async def join_room()`
  - [ ] `exit_room()` → `async def exit_room()`
  - [ ] `start_game()` → `async def start_game()`
  - [ ] Remove duplicate `start_game_safe()`
- [ ] Update WebSocket handlers to use await
- [ ] Add comprehensive async tests

### Phase 3: Game Engine Core (Week 3)
- [ ] Convert `Game` class state-modifying methods:
  - [ ] `deal_pieces()` → `async def deal_pieces()`
  - [ ] `play_turn()` → `async def play_turn()`
  - [ ] `calculate_scores()` → `async def calculate_scores()`
  - [ ] `start_new_round()` → `async def start_new_round()`
- [ ] Update state machine to await game methods
- [ ] Ensure BotManager properly awaits async calls
- [ ] Test game flow end-to-end

### Phase 4: Player and Bot Management (Week 4)
- [ ] Convert Player state-tracking methods:
  - [ ] `record_declaration()` → `async def record_declaration()`
  - [ ] Add async player statistics tracking
- [ ] Update BotManager for full async:
  - [ ] Remove any remaining sync game calls
  - [ ] Add async bot decision making if needed
- [ ] Performance testing with concurrent games

### Phase 5: Integration and Optimization (Week 5)
- [ ] Add connection pooling preparation
- [ ] Implement async context managers for resources
- [ ] Add performance monitoring for async operations
- [ ] Create migration guide for plugins/extensions
- [ ] Load test with 100+ concurrent games
- [ ] Document all async patterns

## Success Criteria

1. **All I/O operations are async** ✅
2. **No sync database calls in async context** ✅
3. **Consistent async patterns throughout codebase** ✅
4. **Performance maintained or improved** ✅
5. **All tests passing with async** ✅
6. **Documentation updated** ✅

## Code Examples

### Before (Current Sync Pattern):
```python
# In WebSocket handler
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    room = room_manager.get_room(room_id)  # Sync call in async context
    if room:
        result = room.join_room(player_name)  # Another sync call
```

### After (Target Async Pattern):
```python
# In WebSocket handler
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    room = await room_manager.get_room(room_id)  # Async all the way
    if room:
        result = await room.join_room(player_name)  # Consistent async
```

### Compatibility Layer Example:
```python
class Room:
    # Temporary pattern during migration
    def join_room_sync(self, player_name: str) -> Dict:
        """Legacy sync method"""
        return asyncio.run(self.join_room(player_name))
    
    async def join_room(self, player_name: str) -> Dict:
        """New async method"""
        # Implementation
```

## Conclusion

Achieving full async readiness requires systematic conversion of the game engine from sync to async, starting with the most critical paths (Room management) and working down to game logic. The main challenge is maintaining compatibility during migration while avoiding performance degradation. With proper planning and the checklist above, the system can be prepared for efficient database operations while maintaining its real-time performance characteristics.