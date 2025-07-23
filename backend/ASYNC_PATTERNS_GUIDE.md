# Async Patterns Guide - Liap Tui

## Overview

This guide documents the async patterns and best practices for the Liap Tui codebase during the migration from synchronous to asynchronous architecture.

## Table of Contents
1. [Migration Strategy](#migration-strategy)
2. [Compatibility Layer](#compatibility-layer)
3. [Common Patterns](#common-patterns)
4. [Best Practices](#best-practices)
5. [Testing Async Code](#testing-async-code)
6. [Troubleshooting](#troubleshooting)

## Migration Strategy

### Gradual Migration Approach

We're using a gradual migration strategy that allows sync and async code to coexist:

1. **Wrap existing sync classes** with async-compatible wrappers
2. **Maintain backward compatibility** during transition
3. **Convert critical paths first** (WebSocket handlers → Room operations → Game logic)
4. **Test thoroughly** at each step

### Priority Order

1. **Phase 1**: Foundation (compatibility layer, locks, testing) ✅
2. **Phase 2**: Room Management (RoomManager, Room)
3. **Phase 3**: Game Engine (Game class methods)
4. **Phase 4**: Player and Bot Management
5. **Phase 5**: Integration and Optimization

## Compatibility Layer

### AsyncCompatRoomManager

Wraps the synchronous RoomManager to provide async methods:

```python
# Old sync code
room_manager = RoomManager()
room_id = room_manager.create_room("Host")
room = room_manager.get_room(room_id)

# New async code
async_manager = AsyncCompatRoomManager(room_manager)
room_id = await async_manager.create_room("Host")
room = await async_manager.get_room(room_id)  # Returns AsyncCompatRoom
```

### AsyncCompatRoom

Wraps synchronous Room objects:

```python
# Async operations on room
slot = await room.join_room("Player1")
await room.assign_slot(2, "Player2")
is_host = await room.exit_room("Player1")

# Access sync properties directly
print(room.room_id)
print(room.host_name)
print(room.players)
```

## Common Patterns

### Pattern 1: Sync to Async Decorator

For standalone functions:

```python
from engine.async_compat import run_sync_in_async

@run_sync_in_async
def calculate_score(player_data):
    # Expensive sync calculation
    return sum(player_data.values())

# Can now be used in async context
async def process_scores():
    score = await calculate_score(data)
```

### Pattern 2: Async Method Creation

For class methods:

```python
from engine.async_compat import create_async_method

class GameLogic:
    def process_turn(self, player, action):
        # Sync implementation
        return result
    
    # Create async version
    process_turn_async = create_async_method(process_turn)

# Usage
game = GameLogic()
result = await game.process_turn_async(player, action)
```

### Pattern 3: Lock Usage

Prevent race conditions in concurrent operations:

```python
class AsyncRoom:
    def __init__(self):
        self._join_lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()
    
    async def join_room(self, player_name):
        async with self._join_lock:
            # Only one join at a time
            return self._add_player(player_name)
    
    async def modify_state(self):
        async with self._state_lock:
            # Protected state modification
            self._update_game_state()
```

### Pattern 4: WebSocket Integration

Typical WebSocket handler pattern:

```python
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # Get room using async manager
    room = await async_room_manager.get_room(room_id)
    if not room:
        await websocket.close(code=4004, reason="Room not found")
        return
    
    # Join room asynchronously
    try:
        slot = await room.join_room(player_name)
        await websocket.send_json({
            "type": "joined",
            "slot": slot
        })
    except ValueError as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
```

### Pattern 5: Concurrent Operations

Handle multiple async operations:

```python
# Run operations concurrently
results = await asyncio.gather(
    room.join_room("Player1"),
    room.join_room("Player2"),
    room.join_room("Player3"),
    return_exceptions=True
)

# Check for errors
for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"Player{i+1} failed to join: {result}")
```

## Best Practices

### 1. Always Use Async Context Managers

```python
# Good
async with self._lock:
    await self.modify_state()

# Bad - can lead to deadlocks
self._lock.acquire()
await self.modify_state()
self._lock.release()
```

### 2. Avoid Blocking Operations

```python
# Bad - blocks event loop
def get_ai_move(game_state):
    time.sleep(1)  # Simulate thinking
    return move

# Good - non-blocking
async def get_ai_move(game_state):
    await asyncio.sleep(1)  # Simulate thinking
    return move
```

### 3. Use asyncio.gather for Concurrent Operations

```python
# Good - concurrent execution
results = await asyncio.gather(
    process_player1(),
    process_player2(),
    process_player3()
)

# Less efficient - sequential execution
result1 = await process_player1()
result2 = await process_player2()
result3 = await process_player3()
```

### 4. Handle Timeouts

```python
# Set reasonable timeouts
try:
    result = await asyncio.wait_for(
        room.start_game(),
        timeout=30.0
    )
except asyncio.TimeoutError:
    logger.error("Game start timed out")
```

### 5. Error Propagation

```python
# Errors propagate through async wrappers
try:
    await room.join_room("Player")
except ValueError as e:
    # Handle room full error
    logger.info(f"Join failed: {e}")
```

## Testing Async Code

### Basic Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_room_operations():
    manager = AsyncCompatRoomManager(RoomManager())
    
    # Test room creation
    room_id = await manager.create_room("TestHost")
    assert room_id is not None
    
    # Test room retrieval
    room = await manager.get_room(room_id)
    assert room.host_name == "TestHost"
```

### Testing Concurrent Operations

```python
@pytest.mark.asyncio
async def test_concurrent_joins():
    room = AsyncCompatRoom(Room("TEST", "Host"))
    
    # Join multiple players concurrently
    results = await asyncio.gather(
        room.join_room("Player1"),
        room.join_room("Player2"),
        room.join_room("Player3"),
        return_exceptions=True
    )
    
    # Verify results
    successful = [r for r in results if not isinstance(r, Exception)]
    assert len(successful) == 3
```

### Using Test Utilities

```python
from tests.async_test_utils import AsyncTestHelper

@pytest.mark.asyncio
async def test_no_deadlock():
    helper = AsyncTestHelper()
    room = AsyncCompatRoom(Room("TEST", "Host"))
    
    # Ensure operation completes without deadlock
    await helper.assert_no_deadlock(
        lambda: room.join_room("Player"),
        timeout=1.0
    )
```

## Troubleshooting

### Common Issues

1. **"RuntimeError: This event loop is already running"**
   - Don't use `asyncio.run()` inside async functions
   - Use `await` instead

2. **Deadlocks**
   - Always use async context managers for locks
   - Avoid nested locks or acquire in consistent order

3. **"coroutine was never awaited"**
   - Remember to use `await` with async functions
   - Check for missing `await` keywords

4. **Performance degradation**
   - Use thread pool for CPU-bound sync operations
   - Don't block the event loop with sync I/O

### Debug Helpers

```python
# Check if object is async-compatible
from engine.async_compat import is_async_compatible

if is_async_compatible(room):
    # Can use async methods
    await room.join_room(player)
else:
    # Need to wrap first
    async_room = AsyncCompatRoom(room)
    await async_room.join_room(player)
```

### Logging Async Operations

```python
import logging

logger = logging.getLogger(__name__)

async def join_room_with_logging(room, player):
    logger.info(f"Starting join for {player}")
    try:
        slot = await room.join_room(player)
        logger.info(f"{player} joined slot {slot}")
        return slot
    except Exception as e:
        logger.error(f"Join failed for {player}: {e}")
        raise
```

## Next Steps

After Phase 1 is complete:
1. Begin converting RoomManager methods to native async
2. Update WebSocket handlers to use async room operations
3. Remove sync compatibility methods once migration is complete
4. Performance test with concurrent games

Remember: The goal is zero breaking changes during migration. All existing sync code should continue to work while we gradually introduce async capabilities.