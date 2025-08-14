# EventStore Removal Execution Checklist

This checklist provides exact steps to execute the EventStore removal plan.

## Pre-Execution Verification
- [ ] Confirm MIGRATION_MODE=v2_only in .env
- [ ] Run test game to verify v2 is working
- [ ] Backup current state with git commit

## Phase 1: Remove Non-Critical Components

### 1.1 Remove Debug Endpoints
- [ ] Edit `backend/api/routes/debug.py`
  - [ ] Remove route: `GET /debug/events/{room_id}`
  - [ ] Remove route: `GET /debug/events/{room_id}/stats`
  - [ ] Remove route: `GET /debug/events/{room_id}/replay`
  - [ ] Remove route: `GET /debug/recovery/{room_id}`
  - [ ] Remove route: `GET /debug/export/{room_id}`
  - [ ] Remove route: `GET /debug/turn/{room_id}/{round_number}/{turn_number}`
  - [ ] Remove route: `GET /debug/turn-analysis/{room_id}`
  - [ ] Remove route: `POST /debug/cleanup`
  - [ ] Remove associated handler functions
  - [ ] Remove event_store import

### 1.2 Simplify API Routes
- [ ] Edit `backend/api/routes/routes.py`
  - [ ] Remove route: `GET /recovery/events/{room_id}/{since_sequence}`
  - [ ] Remove route: `GET /recovery/state/{room_id}`
  - [ ] Remove route: `GET /event-store/room/{room_id}/events`
  - [ ] Remove route: `GET /event-store/stats`
  - [ ] Remove route: `POST /system/cleanup`
  - [ ] Keep health check endpoints but update to use v2 metrics
  - [ ] Remove event_store import after updating health checks

## Phase 2: Fix Critical Dependencies

### 2.1 Remove EventStorePlayHistoryService
- [ ] Delete file: `backend/services/event_store_play_history_service.py`
- [ ] Edit `backend/services/play_history_service.py`
  - [ ] Remove import of EventStorePlayHistoryService (line 47-49)
  - [ ] Remove self.event_store_service initialization (line 51)
  - [ ] Update to only use v2 play history service

### 2.2 Update Play History API
- [ ] Edit `backend/api/routes/play_history.py`
  - [ ] Remove code that creates EventStorePlayHistoryService (around line 245)
  - [ ] Remove fallback logic for v1 (lines 213-229)
  - [ ] Ensure only v2 service is used

## Phase 3: Simplify Core Architecture

### 3.1 Remove EventStore Class
- [ ] Delete file: `backend/api/services/event_store.py`
- [ ] Delete associated test files:
  - [ ] `backend/tests/test_event_buffer.py` (if it tests EventStore directly)
  - [ ] Any other test files that import EventStore

### 3.2 Simplify MigrationAdapter
- [ ] Edit `backend/services/migration_adapter.py`
  - [ ] Remove EventStore import (line 5)
  - [ ] Remove all mode checking logic
  - [ ] Remove v1_store initialization
  - [ ] Simplify __init__ to only create OptimizedEventStore
  - [ ] Simplify store_event to only use v2_store
  - [ ] Remove store_event_buffered logic for v1
  - [ ] Consider renaming class to EventStoreAdapter

### 3.3 Update shared_event_store.py
- [ ] Edit `backend/shared_event_store.py`
  - [ ] Remove MIGRATION_MODE check (lines 13-27)
  - [ ] Remove EventStore import
  - [ ] Simplify to always create MigrationAdapter
  - [ ] Update logging messages

## Phase 4: Clean Up Dependencies

### 4.1 Update Imports
- [ ] Edit `backend/api/main.py`
  - [ ] Remove line 259: `from backend.api.services.event_store import EventStore`
  - [ ] Verify shutdown still works with MigrationAdapter

### 4.2 Remove Legacy Files
- [ ] Delete `backend/services/historical_writer.py` (if v1-specific)
- [ ] Delete `backend/services/cached_event_store.py` (v1-specific caching)
- [ ] Delete `backend/services/event_store_play_history.py` (if exists)
- [ ] Delete test files:
  - [ ] `backend/tests/test_phase4_performance_benchmark.py` (if tests v1)
  - [ ] `test_database_optimization.py` (if tests v1)

### 4.3 Verify State Machine Integration
- [ ] Test `backend/engine/state_machine/base_state.py` still works
- [ ] Test `backend/engine/state_machine/action_queue.py` still works
- [ ] These should work unchanged as they use the interface

## Phase 5: Final Cleanup

### 5.1 Remove Unused Imports
- [ ] Search for any remaining "EventStore" imports
- [ ] Remove any unused imports in modified files

### 5.2 Update Documentation
- [ ] Update CLAUDE.md to reflect v2-only architecture
- [ ] Remove references to EventStore in any README files
- [ ] Update any architecture diagrams

### 5.3 Rename MigrationAdapter (Optional)
- [ ] Rename `migration_adapter.py` to `event_store_adapter.py`
- [ ] Update class name from MigrationAdapter to EventStoreAdapter
- [ ] Update all imports to use new name

## Validation After Each Phase

### After Phase 1:
- [ ] Start application
- [ ] Create new room and play a game
- [ ] Verify game works without debug endpoints

### After Phase 2:
- [ ] Test play history API: `GET /api/rooms/{room_id}/play-history`
- [ ] Verify it returns data correctly

### After Phase 3:
- [ ] Run full game from start to finish
- [ ] Check database for v2 events
- [ ] Verify no errors in logs

### After Phase 4:
- [ ] Run all remaining tests
- [ ] Verify no import errors
- [ ] Check no "EventStore" string remains (except in git history)

## Final Verification
- [ ] No references to EventStore class remain
- [ ] No references to event_store_play_history_service remain  
- [ ] Game creates, plays, and completes successfully
- [ ] Play history API works
- [ ] Database only has v2 schema data
- [ ] All tests pass

## Rollback Plan
If any issues occur:
```bash
git reset --hard HEAD
git clean -fd
```

## Expected File Changes Summary
- **Files to delete**: ~8-10 files
- **Files to modify**: ~8-10 files  
- **Lines to remove**: ~2000+
- **New files**: 0