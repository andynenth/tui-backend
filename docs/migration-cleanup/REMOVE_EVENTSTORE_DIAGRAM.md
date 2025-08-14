# EventStore Removal - Architecture Comparison

## Current Architecture (BEFORE)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Game Events                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    shared_event_store.py                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ if MIGRATION_MODE != "v1_only":                         │   │
│  │     event_store = MigrationAdapter()  ← We use this     │   │
│  │ else:                                                   │   │
│  │     event_store = EventStore()       ← Never used      │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MigrationAdapter                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Supports multiple modes:                                │   │
│  │ - v1_only    → Uses EventStore      ← Never used       │   │
│  │ - v2_only    → Uses OptimizedEventStore  ← Always used │   │
│  │ - dual_write → Uses both            ← Never used       │   │
│  │ - dual_read  → Uses both            ← Never used       │   │
│  └─────────────────────────────────────────────────────────┘   │
│  Problem: Only implements write methods, not read methods!      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OptimizedEventStore                           │
│         (Compression + Buffering + V2 Schema)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Problems with Current Architecture:
1. **EventStore class exists but is never used** (only when MIGRATION_MODE=v1_only)
2. **MigrationAdapter has unnecessary complexity** for modes we don't use
3. **Read methods are missing** causing API endpoints to fail
4. **Confusing architecture** with multiple paths that aren't used

## Target Architecture (AFTER)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Game Events                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    shared_event_store.py                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ # Simple and clear - always use v2                      │   │
│  │ from backend.services.event_adapter import EventAdapter │   │
│  │ event_store = EventAdapter()                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│               EventAdapter (renamed from MigrationAdapter)       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ # Simple wrapper that delegates to OptimizedEventStore  │   │
│  │ def __init__(self):                                     │   │
│  │     self.store = OptimizedEventStore()                 │   │
│  │                                                         │   │
│  │ def store_event(self, ...):                            │   │
│  │     return self.store.store_event(...)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OptimizedEventStore                           │
│         (Compression + Buffering + V2 Schema)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Benefits of New Architecture:
1. **No unused code** - EventStore completely removed
2. **Simple and clear** - One path for all events
3. **No confusion** - Only v2 implementation exists
4. **Maintainable** - Less code, clearer purpose

## API Endpoints Changes

### BEFORE: Many endpoints that don't work with v2
```
/api/recovery/events/{room_id}/{since_sequence}  ← Fails with AttributeError
/api/recovery/state/{room_id}                    ← Fails with AttributeError  
/api/event-store/room/{room_id}/events          ← Fails with AttributeError
/api/debug/events/{room_id}                      ← Fails with AttributeError
/api/debug/replay/{room_id}                      ← Fails with AttributeError
... (many more debug endpoints)
```

### AFTER: Only working endpoints remain
```
/api/health                    ← Works with v2
/api/rooms/{room_id}/play-history  ← Works with v2 schema
/api/monitoring/*              ← Works with v2 metrics
```

## Database Schema Impact

### BEFORE: Two schemas exist
```
Old Schema (v1):                    New Schema (v2):
- game_events (huge table)          - game_events_v2 (minimal)
  * Every action stored               * Only key events
  * No compression                    * 90% compression
  * Millions of rows                  * Thousands of rows
                                    - game_summaries
                                    - round_snapshots
```

### AFTER: Only v2 schema used
```
New Schema (v2):
- game_events_v2 (minimal events)
- game_summaries (game metadata)
- round_snapshots (complete round data)
- turn_details (optional turn data)

Old v1 tables can be dropped from database
```

## Code Reduction

### Files to Delete (Complete Removal):
1. `backend/api/services/event_store.py` (~1000 lines)
2. `backend/services/event_store_play_history_service.py` (~400 lines)
3. `backend/services/cached_event_store.py` (~200 lines)
4. `backend/services/historical_writer.py` (~150 lines)
5. Various test files (~500 lines)

### Files to Simplify:
1. `backend/services/migration_adapter.py` (200 lines → 50 lines)
2. `backend/shared_event_store.py` (33 lines → 10 lines)
3. `backend/api/routes/debug.py` (400 lines → 100 lines)
4. `backend/api/routes/routes.py` (remove ~100 lines)

### Total Reduction: ~2000+ lines of code removed