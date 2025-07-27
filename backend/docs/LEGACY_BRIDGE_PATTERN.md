# Legacy Bridge Pattern Documentation

## Overview

The Legacy Bridge Pattern provides a temporary synchronization mechanism between clean architecture repositories and legacy managers during the transition period. This pattern ensures that data created in the clean architecture is visible to legacy code, preventing "Room not found" warnings and maintaining compatibility.

## Problem Statement

During Phase 6 of the clean architecture migration:
- Clean architecture creates entities in its own repositories (`ApplicationRoomRepository`)
- Legacy code (`AsyncRoomManager`) doesn't know about these entities
- When legacy code checks for entity existence, it fails to find them
- This causes warnings in logs and potential functionality issues

## Solution: Repository Bridge

The `LegacyRepositoryBridge` provides bidirectional synchronization between the two architectures.

### Key Components

1. **Bridge Class** (`infrastructure/adapters/legacy_repository_bridge.py`)
   - Converts entities between clean and legacy formats
   - Provides sync methods for both directions
   - Handles error cases gracefully

2. **Integration Points**
   - Room adapters call `ensure_room_visible_to_legacy()` after operations
   - Bridge converts clean `Room` entities to legacy `AsyncRoom` objects
   - Legacy manager can then see and work with the rooms

### Usage Example

```python
# After creating a room in clean architecture
from infrastructure.adapters.legacy_repository_bridge import ensure_room_visible_to_legacy

# Create room using clean architecture
response_dto = await use_case.execute(request)

# Sync to legacy manager
await ensure_room_visible_to_legacy(response_dto.room_info.room_id)
```

## Implementation Details

### Entity Conversion

The bridge converts between:
- Clean `Room` → Legacy `AsyncRoom`
- Clean `Player` → Legacy `Player`
- Clean game references → Minimal legacy `AsyncGame`

### Sync Operations

1. **Room Creation**: Automatically synced after successful creation
2. **Player Join/Leave**: Room state synced after modifications
3. **Game Start**: Game object created in legacy format

### Error Handling

- Sync failures don't fail the main operation
- Warnings logged for debugging
- Bridge operations are idempotent

## Benefits

1. **Eliminates Warnings**: No more "Room not found" messages
2. **Maintains Compatibility**: Legacy code continues to work
3. **Gradual Migration**: Allows phased transition
4. **Debugging**: Both architectures see the same data

## Limitations

1. **Performance**: Additional overhead for conversion
2. **Complexity**: Two representations of the same data
3. **Temporary**: Will be removed in Phase 7

## Testing

Run the bridge test:
```bash
python test_legacy_bridge.py
```

This verifies:
- Room creation sync
- Player updates sync
- Legacy manager visibility

## Future Removal (Phase 7)

When legacy components are removed:
1. Delete `legacy_repository_bridge.py`
2. Remove `ensure_room_visible_to_legacy()` calls
3. Remove bridge imports from adapters
4. Clean up legacy managers

## Architecture Diagram

```
┌─────────────────────┐     ┌──────────────────────┐
│  Clean Architecture │     │    Legacy Code       │
│                     │     │                      │
│  ┌───────────────┐  │     │  ┌────────────────┐ │
│  │ Room UseCase  │  │     │  │ AsyncRoomMgr   │ │
│  └───────┬───────┘  │     │  └────────────────┘ │
│          │          │     │           ▲          │
│  ┌───────▼───────┐  │     │           │          │
│  │ Room Repo     │  │     │           │          │
│  └───────┬───────┘  │     │           │          │
│          │          │     │           │          │
└──────────┼──────────┘     └───────────┼──────────┘
           │                            │
           │    ┌─────────────────┐     │
           └───►│  Legacy Bridge  ├─────┘
                └─────────────────┘
                 Converts & Syncs
```

## Monitoring

Check logs for:
- `[ROOM_CREATE_DEBUG] Room synced to legacy manager` - Successful sync
- `Failed to sync room to legacy` - Sync failures (non-critical)
- `Synced room {id} to legacy manager` - Bridge operations

## Conclusion

The Legacy Bridge Pattern is a pragmatic solution for the transition period. It ensures system functionality while allowing gradual migration to clean architecture. Once Phase 7 is complete, this bridge will no longer be needed.