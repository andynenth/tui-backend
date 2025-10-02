# Lock Acquisition Flow - Atomic Operations

This diagram demonstrates how atomic operations prevent race conditions through proper lock management.

```mermaid
sequenceDiagram
    participant Request1 as Request 1<br/>(Create Room)
    participant Request2 as Request 2<br/>(Delete Room)
    participant AsyncLock as asyncio.Lock<br/>(manager_lock)
    participant CriticalSection as Critical Section<br/>(rooms dict)
    participant Operations as Atomic Operations
    participant Cleanup as Cleanup/Rollback

    Request1->>AsyncLock: async with self._manager_lock
    AsyncLock->>AsyncLock: Check lock availability
    AsyncLock-->>Request1: Lock acquired ✓

    Note over Request1,CriticalSection: Request 1 has exclusive access

    Request2->>AsyncLock: async with self._manager_lock
    AsyncLock->>AsyncLock: Lock unavailable
    AsyncLock-->>Request2: Wait in queue...

    Request1->>CriticalSection: Read current state
    CriticalSection-->>Request1: Current rooms dict

    Request1->>Operations: Perform atomic operations:<br/>1. Add room to dict<br/>2. Update stats<br/>3. Log operation

    alt Success Path
        Operations-->>Request1: Operations successful
        Request1->>AsyncLock: Release lock (automatic)
        Note over AsyncLock: Context manager<br/>ensures release
    else Error Path
        Operations-->>Request1: Exception raised
        Request1->>Cleanup: Rollback changes:<br/>- Remove partial updates<br/>- Restore original state
        Cleanup-->>Request1: State restored
        Request1->>AsyncLock: Release lock (automatic)
        Note over AsyncLock: Lock released even<br/>on exception
    end

    AsyncLock-->>Request2: Lock acquired ✓
    Request2->>CriticalSection: Perform delete operation

    Note over Request1,Cleanup: Lock patterns used:<br/>• _manager_lock: rooms dict modifications<br/>• _room_creation_lock: unique ID generation<br/>• processing_lock: action queue processing
```

## Key Lock Types in the System

### 1. Manager Lock (`self._manager_lock`)
- **Purpose**: Protects the rooms dictionary from concurrent modifications
- **Usage**: Creating, deleting, or modifying room entries
- **Pattern**: `async with self._manager_lock:`

### 2. Room Creation Lock (`self._room_creation_lock`)
- **Purpose**: Ensures unique room ID generation
- **Usage**: During room creation to prevent ID collisions
- **Pattern**: Sequential room ID generation

### 3. Processing Lock (`self.processing_lock`)
- **Purpose**: Ensures action queue processes one batch at a time
- **Usage**: In the action queue's `process_actions()` method
- **Pattern**: Prevents concurrent action processing

## Code Examples

```python
# AsyncRoomManager - Atomic room operations
async def create_room(self, host_name: str) -> str:
    async with self._room_creation_lock:
        # Generate unique room ID
        room_id = await self._generate_unique_room_id()

        # Create async room
        room = AsyncRoom(room_id, host_name)

        # Add to rooms dict with lock
        async with self._manager_lock:
            self.rooms[room_id] = room
            self._stats["rooms_created"] += 1
            self._stats["total_operations"] += 1

# ActionQueue - Atomic action processing
async def process_actions(self) -> List[GameAction]:
    async with self.processing_lock:
        self.processing = True
        processed_actions = []
        try:
            while not self.queue.empty():
                action = await self.queue.get()
                processed_actions.append(action)
                self.queue.task_done()
        finally:
            self.processing = False
        return processed_actions
```

## Benefits

1. **Race Condition Prevention**: Only one operation can modify critical sections at a time
2. **Automatic Cleanup**: Context managers ensure locks are always released
3. **Exception Safety**: Locks released even if operations fail
4. **Deadlock Prevention**: Consistent lock ordering and timeouts
5. **Transaction-like Behavior**: All-or-nothing operations with rollback capability
