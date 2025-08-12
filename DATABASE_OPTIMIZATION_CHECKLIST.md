# Database Optimization Quick Checklist

## 🚀 Phase 1: Event Buffering (Week 1) - Quick Win
### Day 1-2: Core Implementation
- [ ] Create `event_buffer.py` with EventBuffer class
- [ ] Add buffer size limit (20 events)
- [ ] Add auto-flush timer (2 seconds)
- [ ] Implement thread-safe operations
- [ ] Write unit tests

### Day 3: Integration
- [ ] Add `store_event_buffered()` to EventStore
- [ ] Update base_state.py to use buffered writes
- [ ] Add flush on critical events (game_over)
- [ ] Test with bot games

### Day 4-5: Testing & Deploy
- [ ] Integration tests with buffer
- [ ] Performance benchmarks
- [ ] Deploy with feature flag
- [ ] Monitor metrics

**Expected Result**: 90% reduction in database writes

---

## 📦 Phase 2: Event Compression (Week 2)
### Day 1-2: Define Semantic Events
- [ ] Create semantic event types
- [ ] Map 126 events → ~15 events
- [ ] Define filtering rules

### Day 3: Implement Compression
- [ ] Create event_compressor.py
- [ ] Compress turn sequences
- [ ] Filter redundant updates

### Day 4-5: Update Systems
- [ ] Update state machines
- [ ] Fix Play History service
- [ ] Test end-to-end

**Expected Result**: 500KB → 100KB per game

---

## 🗄️ Phase 3: Schema Optimization (Week 3)
### Day 1-2: New Schema
- [ ] Design optimized tables
- [ ] Create migration scripts
- [ ] Test on dev database

### Day 3-4: Dual-Write Mode
- [ ] Implement adapter pattern
- [ ] Write to both schemas
- [ ] Verify data consistency

### Day 5: Migration
- [ ] Backup production data
- [ ] Run migration
- [ ] Verify Play History works

**Expected Result**: 10x faster queries

---

## 💾 Phase 4: Real-time Cache (Week 4)
### Day 1-2: Cache Layer
- [ ] In-memory game state cache
- [ ] Write-through to database
- [ ] Cache eviction policy

### Day 3-4: Historical Writer
- [ ] Async historical writes
- [ ] Batch processing
- [ ] Old game compression

### Day 5: Full Testing
- [ ] Load test all systems
- [ ] Verify metrics
- [ ] Final deployment

**Expected Result**: <100ms game latency

---

## 📊 Key Metrics to Track
- [ ] Database writes per round: 126 → 10-16 writes
  - **Minimum**: ~10 writes (3 fixed + 2-3 turns × 2-3 writes)
  - **Typical**: ~12-14 writes (3 fixed + 4-6 turns × 2 writes)
  - **Maximum**: 19 writes (3 fixed + 8 turns × 2 writes)
  - **Fixed writes**: round_start, declarations_complete, round_complete
- [ ] Storage per game: 500KB → 15-50KB
  - **Minimum**: ~15KB (quick games, 10-12 rounds)
  - **Typical**: ~25-30KB (average 15-20 rounds)
  - **Long games**: ~50KB (30+ rounds if scores are close)
- [ ] Game latency: 150ms → 100ms
- [ ] Play History API: <500ms maintained
- [ ] Turn validation: Enforce turn_count between 1-8

## 🚨 Quick Rollback Steps
1. **Buffer Issues**: Set `EVENT_BUFFER_ENABLED=false`
2. **Compression Issues**: Disable compression flag
3. **Schema Issues**: Switch to old schema reads
4. **Cache Issues**: Bypass cache layer

## ✅ Definition of Done
- [ ] All tests passing
- [ ] Performance metrics met
- [ ] Documentation updated
- [ ] Team trained on new system
- [ ] Monitoring in place
- [ ] Rollback tested