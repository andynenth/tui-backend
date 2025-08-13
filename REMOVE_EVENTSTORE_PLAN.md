# Plan: Remove Legacy EventStore from Codebase

## Executive Summary

This document outlines a comprehensive plan to remove the legacy EventStore from the codebase. The project has migrated to a v2 event storage system that uses an optimized schema with 85-90% fewer database writes. Since the project will permanently use `MIGRATION_MODE=v2_only` and historical v1 data will be removed, we can eliminate the legacy EventStore entirely.

## Current Architecture

### Event Storage Stack
```
Game Events
    ↓
shared_event_store (singleton)
    ↓
MigrationAdapter (when MIGRATION_MODE != v1_only)
    ↓
OptimizedEventStore
    ↓
EventCompressor + EventBuffer
    ↓
EventStoreV2
    ↓
SQLite Database (v2 schema)
```

### Key Components
- **EventStore**: Legacy implementation using single-table schema
- **MigrationAdapter**: Router that supports multiple migration modes
- **OptimizedEventStore**: New implementation with compression and buffering
- **EventStoreV2**: Database layer for optimized schema

## Problem Analysis

### 1. Incomplete v2_only Implementation
The current v2_only mode only implements **write operations**. Read operations are missing, causing API endpoints to fail with `AttributeError`.

### 2. API Endpoints Depending on EventStore Read Methods
- **Recovery endpoints**: `/api/rooms/{room_id}/events/{since_sequence}`
- **Debug endpoints**: `/api/debug/events/{room_id}`, `/api/debug/replay/{room_id}`
- **Monitoring endpoints**: `/api/event-store/stats`, health checks
- **Play history**: EventStorePlayHistoryService uses `get_room_events()`

### 3. Architectural Confusion
Having both EventStore and OptimizedEventStore creates confusion about which to use, even though EventStore is never used in v2_only mode.

## Removal Plan

### Phase 1: Remove Non-Critical Components

#### 1.1 Remove Debug Endpoints
**Files to modify**: `backend/api/routes/debug.py`
- Remove all endpoints that depend on event-level queries
- These are debug-only endpoints not needed in production
- The v2 schema doesn't support event-level queries anyway

#### 1.2 Simplify API Routes
**Files to modify**: `backend/api/routes/routes.py`
- Remove `/api/recovery/*` endpoints (event-based recovery not compatible with v2)
- Remove `/api/event-store/*` endpoints (v1-specific operations)
- Keep only health check endpoints that can work with v2

### Phase 2: Fix Critical Dependencies

#### 2.1 Update EventStorePlayHistoryService
**Files to modify**: `backend/services/event_store_play_history_service.py`
- Option A: Remove this service entirely and use v2's round snapshots directly
- Option B: Update to read from v2 schema tables instead of event table
- Recommended: Option A (simpler and aligns with v2 architecture)

#### 2.2 Update Play History API
**Files to modify**: `backend/api/routes/play_history.py`
- Remove fallback to EventStorePlayHistoryService
- Use only the v2 play history service
- This already works as the code checks for v2 data first

### Phase 3: Simplify Core Architecture

#### 3.1 Remove EventStore Class
**Files to delete**: `backend/api/services/event_store.py`
- Delete the entire file (~1000+ lines)
- Remove associated models like GameEvent

#### 3.2 Simplify MigrationAdapter
**Files to modify**: `backend/services/migration_adapter.py`
- Remove all mode handling except v2_only
- Remove EventStore import
- Rename to something clearer like `EventStoreAdapter`
- Simplify to just delegate all calls to OptimizedEventStore

#### 3.3 Update shared_event_store.py
**Files to modify**: `backend/shared_event_store.py`
- Remove MIGRATION_MODE check
- Remove EventStore import
- Always create MigrationAdapter (or renamed adapter)
- Simplify to ~10 lines

### Phase 4: Clean Up Dependencies

#### 4.1 Update Imports
**Files to modify**:
- `backend/api/main.py` - Remove EventStore import on line 259
- `backend/services/historical_writer.py` - Update or remove
- `backend/services/cached_event_store.py` - Remove (v1-specific caching)

#### 4.2 Remove Test Files
**Files to delete**:
- Test files that specifically test EventStore functionality
- Update integration tests to work with v2 only

#### 4.3 Update State Machine
**Files to verify**: 
- `backend/engine/state_machine/base_state.py`
- `backend/engine/state_machine/action_queue.py`
- These should continue to work as they use the event_store interface

## Implementation Order

1. **Start with Phase 1**: Remove non-critical debug/recovery endpoints
2. **Then Phase 2**: Fix play history to use v2 directly
3. **Then Phase 3**: Remove EventStore and simplify architecture
4. **Finally Phase 4**: Clean up all remaining dependencies

## Validation Steps

After each phase:
1. Run the application and create a new game
2. Verify game events are stored in v2 schema
3. Test play history API endpoints
4. Check that no errors occur during gameplay
5. Verify database has 0 entries in old event tables

## Risk Mitigation

1. **Git backup**: Can rollback if needed
2. **Phased approach**: Each phase can be tested independently
3. **V2 already proven**: System already runs in v2_only mode
4. **No data migration needed**: Historical data will be removed anyway

## Expected Outcome

- **~2000 lines removed**: EventStore + related code
- **Simpler architecture**: One clear path for event storage
- **No confusion**: Only v2 implementation remains
- **Better performance**: Already achieved with v2
- **Cleaner codebase**: Remove all legacy migration code

## Not In Scope

- Migrating historical v1 data (will be deleted)
- Maintaining backward compatibility (not needed)
- Supporting other migration modes (permanent v2_only)

## Success Criteria

1. ✅ EventStore class completely removed
2. ✅ All game functionality works with v2 only
3. ✅ Play history API returns data correctly
4. ✅ No references to EventStore remain in codebase
5. ✅ Simplified architecture with single event storage path