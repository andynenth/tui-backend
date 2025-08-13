# Plan: Clean Up Unused Migration Modes

## Overview
Since the project is permanently using `MIGRATION_MODE=v2_only`, we can remove all the other migration modes (`v1_only`, `dual_write`, `dual_read_v1`, `dual_read_v2`) from MigrationAdapter. This will simplify the code and remove unnecessary complexity.

## What to Clean Up

### 1. MigrationAdapter Class (`backend/services/migration_adapter.py`)

#### Remove from `__init__()`:
- Mode checking logic that initializes v1_store for non-v2_only modes
- The `self.v1_store` property entirely
- Complex if/else blocks for different modes

#### Simplify `store_event()`:
- Remove the entire if/elif/else structure for different modes
- Remove dual_write logic that writes to both stores
- Keep only the v2_store.store_event() call

#### Simplify `store_event_buffered()`:
- Remove mode checking
- Always delegate to v2_store

#### Remove unused methods:
- Any methods that were only used for v1 operations

### 2. Environment Variable Documentation (`.env`)
Update comments to reflect that only v2_only is supported:
```env
# Migration mode - Always v2_only (other modes removed)
MIGRATION_MODE=v2_only
```

### 3. shared_event_store.py
This can stay as is, but update the comment to clarify:
- MigrationAdapter is always used (never EventStore)
- The v1_only check is kept for safety but should never trigger

### 4. Remove Unused Imports
- Remove EventStore import from MigrationAdapter (if we're removing v1_store)

### 5. Update Error Messages
- Remove references to other modes in error messages or logging

## Implementation Steps

### Step 1: Simplify MigrationAdapter.__init__()
**Current** (~50 lines):
```python
def __init__(self):
    self.mode = os.getenv("MIGRATION_MODE", "v2_only").lower()
    
    # Initialize stores based on mode
    if self.mode in ["v1_only", "dual_write", "dual_read_v1", "dual_read_v2"]:
        self.v1_store = EventStore()
    else:
        self.v1_store = None
        
    if self.mode in ["v2_only", "dual_write", "dual_read_v1", "dual_read_v2"]:
        self.v2_store = OptimizedEventStore()
    else:
        self.v2_store = None
        
    # Validate configuration
    if not self.v1_store and not self.v2_store:
        raise ValueError(f"Invalid migration mode: {self.mode}")
```

**After** (~10 lines):
```python
def __init__(self):
    # Always use v2_only mode
    self.mode = "v2_only"
    self.v2_store = OptimizedEventStore()
    logger.info("MigrationAdapter initialized in v2_only mode")
```

### Step 2: Simplify store_event()
**Current** (~60 lines with all the mode checking):
```python
async def store_event(self, room_id, event_type, payload, player_id=None):
    if self.mode == "v1_only":
        # v1 logic
    elif self.mode == "v2_only":
        # v2 logic
    elif self.mode in ["dual_write", "dual_read_v1", "dual_read_v2"]:
        # dual mode logic
```

**After** (~10 lines):
```python
async def store_event(self, room_id, event_type, payload, player_id=None):
    logger.info(f"🔍 DEBUG: MigrationAdapter.store_event - room: {room_id}, type: {event_type}")
    await self.v2_store.store_event(room_id, event_type, payload, player_id)
```

### Step 3: Simplify store_event_buffered()
**Current** (~20 lines):
```python
async def store_event_buffered(self, room_id, event_type, payload, player_id=None):
    if self.mode == "v1_only" and self.v1_store:
        await self.v1_store.store_event_buffered(...)
    elif self.mode == "v2_only" and self.v2_store:
        await self.v2_store.store_event(...)
    else:
        await self.store_event(...)
```

**After** (~5 lines):
```python
async def store_event_buffered(self, room_id, event_type, payload, player_id=None):
    # V2 handles buffering internally
    await self.v2_store.store_event(room_id, event_type, payload, player_id)
```

## Expected Results

### Before:
- ~200 lines in MigrationAdapter
- Complex mode checking on every operation
- Support for 5 different modes
- Potential for configuration errors

### After:
- ~50-60 lines in MigrationAdapter (75% reduction)
- No mode checking - always uses v2
- Single, clear path for all events
- No possibility of misconfiguration

### Code Removed:
- All v1_store initialization and usage
- All dual mode logic
- Mode validation code
- Complex if/elif/else structures

### Benefits:
1. **Simpler code** - Easier to understand and maintain
2. **Better performance** - No mode checking overhead
3. **Clearer purpose** - MigrationAdapter is just a thin wrapper for v2
4. **No confusion** - Can't accidentally use wrong mode

## Not Changing

1. **Keep MigrationAdapter name** - It's referenced in many places
2. **Keep shared_event_store.py logic** - The v1_only check provides safety
3. **Keep the interface** - All the same methods remain available
4. **Keep EventStore class** - In case needed for reference or recovery

## Validation

After cleanup:
1. Run the application
2. Create a new game and play through
3. Verify events are stored in v2 schema
4. Check that play history works
5. Confirm no errors in logs

## Risk Assessment

- **Low risk** - We're only removing unused code paths
- **No functional change** - System already runs in v2_only mode
- **Easy rollback** - Can revert with git if needed