# Database Optimization Implementation Plan

## Overview
This document outlines the implementation plan for optimizing database writes in the Liap Tui game system. Currently, the game performs ~126 database writes per single round, causing unnecessary I/O overhead and database bloat.

### Goals
- **Reduce database writes by 90%** (from 126 to ~15 per game round)
- **Maintain data integrity** for Play History API
- **Improve game performance** by removing synchronous I/O from game loop
- **Optimize storage** with better schema design

### Success Metrics
- [x] Database writes per round: < 20 ✅ (Achieved: 10-19 writes)
- [ ] Game latency reduction: > 30%
- [x] Storage per game: < 100KB (from 500KB) ✅ (Achieved: ~100KB)
- [ ] Play History API response time: < 500ms

---

## ✅ Phase 1: Event Buffering System (Week 1) ✅ COMPLETE

### Objective
Implement an event buffer to batch database writes without changing the current schema or event structure.

### Status: COMPLETE ✅
- Achieved 90% reduction in database writes
- From 126 writes per round → 10-19 writes per round
- EventBuffer with 20 event batch size and 2-second flush interval

### Tasks

#### 1.1 Create Event Buffer Class ✅
- [x] Create `backend/services/event_buffer.py`
- [x] Implement `EventBuffer` class with:
  - [x] `add_event()` method
  - [x] `flush()` method
  - [x] Auto-flush timer (2 seconds)
  - [x] Max buffer size (20 events)
- [x] Add thread-safe locking for buffer operations
- [x] Add error handling for flush failures
- [x] Write unit tests for EventBuffer

#### 1.2 Integrate Buffer with EventStore ✅
- [x] Modify `backend/api/services/event_store.py`:
  - [x] Add `_event_buffer` instance variable
  - [x] Create `store_event_buffered()` method
  - [x] Add configuration flag `ENABLE_EVENT_BUFFERING`
  - [x] Implement graceful shutdown to flush pending events
- [x] Update `event_store` singleton initialization
- [x] Add metrics logging for buffer performance

#### 1.3 Update State Machine Integration ✅
- [x] Modify `backend/engine/state_machine/base_state.py`:
  - [x] Replace `store_event()` calls with `store_event_buffered()`
  - [x] Add buffer flush on critical events (game_over, round_complete)
- [x] Update `backend/engine/state_machine/action_queue.py`:
  - [x] Use buffered storage for state events
- [x] Test bot games with buffering enabled

#### 1.4 Testing & Monitoring ✅
- [x] Create integration tests for buffered events
- [x] Add buffer metrics to health endpoint
- [x] Test game recovery from buffered events
- [x] Verify Play History API still works correctly
- [x] Load test with 10 concurrent games
- [x] Document buffer tuning parameters

---

## ✅ Phase 2: Event Compression & Filtering (Week 2) ✅ COMPLETE

### Objective
Reduce event volume by storing only semantically meaningful game events.

### Status: COMPLETE ✅
- Achieved 75% compression ratio
- From ~126 granular events → ~15 semantic events per round
- Storage reduced from 500KB → 100KB per game

### Tasks

#### 2.1 Define Semantic Event Types ✅
- [x] Create `backend/models/semantic_events.py`:
  - [x] Define `SemanticEventType` enum
  - [x] Map current events to semantic events
  - [x] Create event importance levels
- [x] Document event mapping rules
- [x] Create event filtering configuration

#### 2.2 Implement Event Compressor ✅
- [x] Create `backend/services/event_compressor.py`:
  - [x] `compress_turn_events()` - Combine turn plays into single event
  - [x] `compress_phase_updates()` - Merge redundant updates
  - [x] `should_store_event()` - Filtering logic
- [x] Add compression metrics
- [x] Write unit tests for compression logic

#### 2.3 Update State Machine Events ✅
- [x] Modify turn_state.py:
  - [x] Store single "turn_completed" event instead of 7 updates
  - [x] Include all turn data in one payload
- [x] Modify declaration_state.py:
  - [x] Store single "declarations_completed" event
  - [x] Remove individual declaration updates
- [x] Update preparation_state.py:
  - [x] hands_dealt already optimized (kept as semantic event)

#### 2.4 Update Play History Service ✅
- [x] Modify `event_store_play_history_service.py`:
  - [x] Add handlers for new semantic events
  - [x] Maintain backward compatibility
  - [x] Update event extraction logic
- [x] Test with compressed events
- [x] Verify all game data is still available

---

## Phase 3: Database Schema Optimization (Week 3)

### Objective
Implement optimized schema with separate tables for different concerns.

### Tasks

#### 3.1 Design New Schema
- [ ] Create `backend/migrations/002_optimized_schema.sql`:
  ```sql
  -- Core events table (minimal)
  CREATE TABLE game_events_v2 (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      room_id TEXT NOT NULL,
      event_type TEXT NOT NULL,
      round_number INTEGER,
      timestamp REAL NOT NULL,
      created_at TEXT NOT NULL
  );
  
  -- Game summaries (one row per game)
  CREATE TABLE game_summaries (
      room_id TEXT PRIMARY KEY,
      players JSON NOT NULL,
      total_rounds INTEGER DEFAULT 0,
      final_scores JSON,
      winner TEXT,
      started_at REAL NOT NULL,
      completed_at REAL,
      game_config JSON
  );
  
  -- Round snapshots (one row per round)
  CREATE TABLE round_snapshots (
      room_id TEXT NOT NULL,
      round_number INTEGER NOT NULL,
      starter_player TEXT NOT NULL,
      initial_hands JSON NOT NULL,
      declarations JSON NOT NULL,
      turn_sequence JSON NOT NULL,
      round_scores JSON NOT NULL,
      created_at TEXT NOT NULL,
      PRIMARY KEY (room_id, round_number)
  );
  
  -- Indexes
  CREATE INDEX idx_events_room_time ON game_events_v2(room_id, timestamp);
  CREATE INDEX idx_summaries_completed ON game_summaries(completed_at);
  ```

#### 3.2 Create Migration System
- [ ] Create `backend/services/db_migrator.py`:
  - [ ] `run_migrations()` method
  - [ ] `get_current_version()` method
  - [ ] `apply_migration()` method
- [ ] Add migration tracking table
- [ ] Create rollback procedures
- [ ] Test migration on copy of production DB

#### 3.3 Implement Dual-Write Adapter
- [ ] Create `backend/services/event_store_v2.py`:
  - [ ] Implement new schema methods
  - [ ] Add dual-write mode (both schemas)
  - [ ] Add feature flag for schema version
- [ ] Update event storage to use adapter
- [ ] Verify both schemas stay in sync

#### 3.4 Update Play History Service
- [ ] Create `backend/services/play_history_v2.py`:
  - [ ] Read from optimized schema
  - [ ] Use round_snapshots for fast queries
  - [ ] Fall back to event reconstruction if needed
- [ ] Add performance metrics
- [ ] Compare query times with old schema

---

## Phase 4: Real-time vs Historical Separation (Week 4)

### Objective
Separate real-time game state from historical records for optimal performance.

### Tasks

#### 4.1 Implement Write-Through Cache
- [ ] Create `backend/services/game_state_cache.py`:
  - [ ] In-memory game state storage
  - [ ] Write-through to database
  - [ ] TTL-based eviction (1 hour)
- [ ] Add cache warming on game start
- [ ] Implement cache invalidation

#### 4.2 Create Historical Writer Service
- [ ] Create `backend/services/historical_writer.py`:
  - [ ] Async queue for historical writes
  - [ ] Batch writing to round_snapshots
  - [ ] Compression for old games
- [ ] Add monitoring for write queue
- [ ] Implement backpressure handling

#### 4.3 Update Game Recovery
- [ ] Modify recovery to use:
  - [ ] Cache first (if available)
  - [ ] Recent events (< 1 hour)
  - [ ] Round snapshots (older games)
- [ ] Test recovery scenarios
- [ ] Measure recovery performance

#### 4.4 Monitoring & Alerting
- [ ] Add metrics dashboard:
  - [ ] Write latency percentiles
  - [ ] Buffer queue depth
  - [ ] Cache hit rate
  - [ ] Schema query performance
- [ ] Set up alerts for:
  - [ ] Buffer overflow
  - [ ] Write failures
  - [ ] Cache memory usage

---

## Testing Plan

### Unit Tests
- [ ] EventBuffer class
- [ ] EventCompressor class
- [ ] Schema migration logic
- [ ] Cache operations
- [ ] Play History with new events

### Integration Tests
- [ ] Full game with buffering
- [ ] Game recovery from compressed events
- [ ] Play History API with all optimizations
- [ ] Concurrent game handling
- [ ] Database failover scenarios

### Performance Tests
- [ ] Measure write reduction percentage
- [ ] Game latency improvements
- [ ] Database query performance
- [ ] Memory usage with caching
- [ ] Load test with 50 concurrent games

### Backward Compatibility Tests
- [ ] Old schema → New schema migration
- [ ] Mixed event types in same game
- [ ] Play History with legacy games
- [ ] Rollback procedures

---

## Rollback Plan

### Phase 1 Rollback
1. Set `ENABLE_EVENT_BUFFERING=false`
2. Flush any pending buffers
3. Restart backend services

### Phase 2 Rollback
1. Disable event compression flag
2. Revert to storing all events
3. Update Play History to handle both formats

### Phase 3 Rollback
1. Switch to dual-write mode
2. Keep using old schema for reads
3. Plan data migration for next window

### Phase 4 Rollback
1. Disable cache usage
2. Revert to direct database reads
3. Clear cache data

---

## Deployment Plan

### Phase 1 Deployment (Low Risk)
- Deploy during low-traffic window
- Enable for 10% of games initially
- Monitor buffer metrics
- Gradual rollout to 100%

### Phase 2 Deployment (Medium Risk)
- Deploy with feature flag disabled
- Enable for bot-only games first
- Test with QA team
- Enable for all games

### Phase 3 Deployment (High Risk)
- Full database backup required
- Deploy during maintenance window
- Run migration scripts
- Verify data integrity
- Keep dual-write for 1 week

### Phase 4 Deployment (Low Risk)
- Deploy cache layer
- Monitor memory usage
- Tune cache parameters
- Enable historical writer

---

## Configuration Parameters

### Event Buffer Settings
```env
# Enable event buffering
EVENT_BUFFER_ENABLED=true

# Buffer size before auto-flush
EVENT_BUFFER_SIZE=20

# Auto-flush interval (seconds)
EVENT_BUFFER_FLUSH_INTERVAL=2.0

# Critical events that bypass buffer
EVENT_BUFFER_CRITICAL_EVENTS=game_over,round_complete,player_disconnect
```

### Event Compression Settings
```env
# Enable semantic event compression
EVENT_COMPRESSION_ENABLED=true

# Event importance threshold (0-1)
EVENT_IMPORTANCE_THRESHOLD=0.7

# Compress turn sequences
COMPRESS_TURN_SEQUENCES=true
```

### Schema Settings
```env
# Database schema version
DB_SCHEMA_VERSION=2

# Enable dual-write mode
DB_DUAL_WRITE_MODE=true

# Migration batch size
DB_MIGRATION_BATCH_SIZE=1000
```

### Cache Settings
```env
# Enable game state cache
GAME_STATE_CACHE_ENABLED=true

# Cache TTL (seconds)
GAME_STATE_CACHE_TTL=3600

# Max cache size (MB)
GAME_STATE_CACHE_MAX_SIZE=100
```

---

## Timeline Summary

- **Week 1**: Event Buffering (Quick Win)
  - Days 1-3: Implementation
  - Days 4-5: Testing & Deployment
  
- **Week 2**: Event Compression
  - Days 1-3: Event mapping & compression
  - Days 4-5: Play History updates
  
- **Week 3**: Schema Optimization
  - Days 1-2: Schema design & migration
  - Days 3-4: Dual-write implementation
  - Day 5: Testing
  
- **Week 4**: Real-time Separation
  - Days 1-2: Cache implementation
  - Days 3-4: Historical writer
  - Day 5: Full system test

---

## Success Criteria

### Performance Metrics
- [ ] Database writes per round: 10-16 writes (from 126)
  - **Variable based on gameplay**: 2-8 turns per round
  - **Per turn**: 2 writes (turn_start + turn_complete)
  - **Fixed per round**: 3 writes (round_start, declarations_complete, round_complete)
  - **Formula**: 3 fixed + (number_of_turns × 2) = 7-19 total
- [ ] Write latency: < 10ms p99 (from 50ms)
- [ ] Game latency: < 100ms p95 (from 150ms)
- [ ] Storage per game: 15-50KB (from 500KB)
  - **Per round**: 1-1.6KB depending on turn count
  - **Per game**: Varies with number of rounds until someone reaches 50 points
  - **Quick games**: ~15KB (10-12 rounds, someone gets lucky)
  - **Typical games**: ~25-30KB (15-20 rounds)
  - **Long games**: ~50KB (30+ rounds with close competition)

### Operational Metrics
- [ ] Zero data loss during migration
- [ ] Play History API maintains < 500ms response
- [ ] Game recovery works for all scenarios
- [ ] No increase in error rates

### Business Metrics
- [ ] Player experience unchanged or improved
- [ ] Support ticket volume stable
- [ ] Infrastructure costs reduced by 30%
- [ ] System can handle 2x current load

---

## Risk Mitigation

### Data Loss Risk
- Implement comprehensive backup before migrations
- Test on staging environment first
- Keep dual-write mode for safety
- Monitor data consistency metrics

### Performance Degradation Risk
- Gradual rollout with feature flags
- Real-time monitoring of key metrics
- Automated rollback triggers
- Load testing before full deployment

### Compatibility Risk
- Maintain backward compatibility
- Support both event formats
- Gradual deprecation of old format
- Clear communication of changes

---

## Post-Implementation Review

### Week 5 Tasks
- [ ] Analyze performance improvements
- [ ] Document lessons learned
- [ ] Update runbooks
- [ ] Plan next optimizations
- [ ] Knowledge transfer session
- [ ] Update monitoring dashboards

### Long-term Maintenance
- [ ] Monthly performance reviews
- [ ] Quarterly schema optimization
- [ ] Annual data retention review
- [ ] Continuous monitoring setup