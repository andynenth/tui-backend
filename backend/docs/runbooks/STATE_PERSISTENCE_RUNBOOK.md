# State Persistence Operations Runbook

## Overview
This runbook provides procedures for operating and troubleshooting the state persistence system in production.

## Table of Contents
1. [System Overview](#system-overview)
2. [Common Operations](#common-operations)
3. [Troubleshooting](#troubleshooting)
4. [Emergency Procedures](#emergency-procedures)
5. [Monitoring and Alerts](#monitoring-and-alerts)
6. [Recovery Procedures](#recovery-procedures)

---

## System Overview

### Architecture
```
WebSocket → UseCase → StateAdapter → StatePersistenceManager
                                            ↓
                                    [Redis/DynamoDB Storage]
```

### Key Components
- **StateManagementAdapter**: Bridge between use cases and persistence
- **StatePersistenceManager**: Manages snapshots, events, and recovery
- **Circuit Breaker**: Protects against cascade failures
- **Metrics Collector**: Tracks performance and errors

### Feature Flags
- `FF_USE_STATE_PERSISTENCE`: Master switch for state persistence
- `FF_ENABLE_STATE_SNAPSHOTS`: Enable periodic snapshots
- `FF_ENABLE_STATE_RECOVERY`: Enable automatic recovery on startup

---

## Common Operations

### Enable State Persistence
```bash
# Set environment variables
export FF_USE_STATE_PERSISTENCE=true
export FF_ENABLE_STATE_SNAPSHOTS=true

# Verify
python scripts/enable_state_persistence.py
```

### Disable State Persistence (Emergency)
```bash
# Quick disable
export FF_USE_STATE_PERSISTENCE=false

# Full rollback procedure
python scripts/rollback_state_persistence.py
```

### Check System Status
```bash
# Check feature flags
python -c "
from infrastructure.feature_flags import FeatureFlags
flags = FeatureFlags()
print('State Persistence:', flags.is_enabled(flags.USE_STATE_PERSISTENCE, {}))
print('Snapshots:', flags.is_enabled(flags.ENABLE_STATE_SNAPSHOTS, {}))
"

# Check metrics
curl http://localhost:8000/metrics | grep state_

# Check circuit breaker
curl http://localhost:8000/api/health/circuit-breakers
```

### Manual Snapshot Creation
```python
# Create snapshot for specific game
from scripts.manual_snapshot import create_game_snapshot
await create_game_snapshot("game-id-123", reason="manual_backup")
```

### View Game State
```python
# Retrieve current state
from scripts.view_game_state import get_game_state
state = await get_game_state("game-id-123")
print(json.dumps(state, indent=2))
```

---

## Troubleshooting

### Issue: High Error Rate

**Symptoms:**
- Alert: "State management error rate above 5%"
- Games failing to persist state

**Diagnosis:**
1. Check error logs:
   ```bash
   grep "ERROR.*state_persistence" /var/log/app.log | tail -100
   ```

2. Check circuit breaker status:
   ```bash
   curl http://localhost:8000/api/health/circuit-breakers | jq '.state_management'
   ```

3. Check storage connectivity:
   ```bash
   # For Redis
   redis-cli ping
   
   # For DynamoDB
   aws dynamodb describe-table --table-name game-states
   ```

**Resolution:**
1. If circuit breaker is open:
   - Wait for recovery timeout (30s)
   - Check underlying storage health
   - Reset circuit breaker if needed

2. If storage issues:
   - Check connection pool exhaustion
   - Verify credentials/permissions
   - Check network connectivity

3. If persistent errors:
   - Enable debug logging
   - Run rollback procedure
   - Investigate root cause offline

### Issue: Slow State Operations

**Symptoms:**
- Alert: "99th percentile latency above 100ms"
- Game actions feel sluggish

**Diagnosis:**
1. Check operation metrics:
   ```bash
   curl http://localhost:8000/metrics | grep state_operation_duration
   ```

2. Check cache performance:
   ```bash
   curl http://localhost:8000/metrics | grep state_cache
   ```

3. Check storage latency:
   ```bash
   # Redis latency
   redis-cli --latency
   ```

**Resolution:**
1. If cache misses high:
   - Increase cache size
   - Check cache eviction policy
   - Warm cache after restarts

2. If storage slow:
   - Check storage load
   - Scale storage tier
   - Enable read replicas

3. If serialization slow:
   - Enable compression
   - Reduce snapshot frequency
   - Optimize state structure

### Issue: State Recovery Failures

**Symptoms:**
- Games not recovering after restart
- Alert: "State recovery failure rate above 1%"

**Diagnosis:**
1. Check recovery logs:
   ```bash
   grep "recovery" /var/log/app.log | grep -E "ERROR|WARN"
   ```

2. List available snapshots:
   ```python
   from scripts.list_snapshots import list_game_snapshots
   snapshots = await list_game_snapshots("game-id-123")
   ```

3. Validate snapshot integrity:
   ```python
   from scripts.validate_snapshot import validate_snapshot
   is_valid = await validate_snapshot("snapshot-id")
   ```

**Resolution:**
1. If snapshots corrupted:
   - Use older snapshot
   - Reconstruct from event log
   - Mark game for manual review

2. If snapshots missing:
   - Check retention policy
   - Verify snapshot creation
   - Enable more frequent snapshots

3. If version mismatch:
   - Run migration scripts
   - Update compatibility matrix
   - Use versioned recovery

---

## Emergency Procedures

### Complete System Failure

**When to use:** Multiple games failing, cascading errors

**Procedure:**
1. **Immediate mitigation:**
   ```bash
   # Disable state persistence
   export FF_USE_STATE_PERSISTENCE=false
   
   # Restart application
   systemctl restart game-server
   ```

2. **Notify stakeholders:**
   - Send incident notification
   - Update status page
   - Alert on-call team

3. **Investigate:**
   - Collect logs from last hour
   - Check monitoring dashboards
   - Review recent changes

4. **Recovery:**
   - Fix root cause
   - Test in staging
   - Gradual re-enable with monitoring

### Storage Outage

**When to use:** Redis/DynamoDB unavailable

**Procedure:**
1. **Verify outage:**
   ```bash
   # Check storage health
   redis-cli ping  # or AWS CLI for DynamoDB
   ```

2. **Enable fallback:**
   - Circuit breaker will auto-open
   - Games continue without persistence
   - Monitor for recovery

3. **Post-recovery:**
   - Verify storage health
   - Check for data loss
   - Run consistency checks

### Memory Leak

**Symptoms:** Growing memory usage, OOM kills

**Procedure:**
1. **Immediate relief:**
   ```bash
   # Reduce cache size
   export STATE_CACHE_SIZE=100
   
   # Restart with lower memory
   systemctl restart game-server
   ```

2. **Investigate:**
   - Heap dump analysis
   - Check for unbounded growth
   - Review recent changes

3. **Fix:**
   - Patch memory leak
   - Add memory limits
   - Implement cleanup jobs

---

## Monitoring and Alerts

### Key Metrics to Watch

| Metric | Normal Range | Alert Threshold |
|--------|--------------|-----------------|
| Error Rate | < 0.1% | > 5% |
| P99 Latency | < 50ms | > 100ms |
| Cache Hit Rate | > 90% | < 80% |
| Recovery Success | > 99.9% | < 99% |
| Storage Size | < 5GB | > 10GB |

### Dashboard Links
- [State Management Overview](http://grafana.internal/d/state-mgmt)
- [Performance Metrics](http://grafana.internal/d/state-perf)
- [Error Analysis](http://grafana.internal/d/state-errors)

### Alert Response Times

| Severity | Response Time | Examples |
|----------|--------------|----------|
| Critical | < 5 min | Circuit breaker open, recovery failures |
| Warning | < 30 min | High latency, cache misses |
| Info | < 2 hours | Storage growth, version mismatches |

---

## Recovery Procedures

### Restore from Snapshot

```python
# Find latest snapshot
from scripts.restore_game import restore_from_snapshot

# List available snapshots
snapshots = await list_snapshots("game-id-123")

# Restore specific snapshot
await restore_from_snapshot("game-id-123", "snapshot-id")
```

### Rebuild from Event Log

```python
# Replay events from beginning
from scripts.rebuild_state import rebuild_from_events

state = await rebuild_from_events("game-id-123")
```

### Manual State Correction

```python
# For critical games needing manual intervention
from scripts.manual_correction import correct_game_state

# Load current state
state = await get_game_state("game-id-123")

# Apply corrections
state["phase"] = "TURN"
state["current_player"] = "player-2"

# Save corrected state
await save_corrected_state("game-id-123", state, reason="manual_correction")
```

---

## Appendix

### Useful Commands

```bash
# View real-time logs
tail -f /var/log/app.log | grep state_persistence

# Check Redis memory usage
redis-cli info memory

# List active games
redis-cli keys "game:*"

# Export metrics
curl http://localhost:8000/metrics > metrics_$(date +%s).txt

# Generate state report
python scripts/generate_state_report.py --last-hour
```

### Contact Information

- **On-Call**: PagerDuty rotation "backend-oncall"
- **Slack Channel**: #game-state-issues
- **Escalation**: Engineering Manager
- **Subject Matter Expert**: State Management Team

### Related Documentation

- [State Persistence Architecture](../architecture/STATE_PERSISTENCE.md)
- [Monitoring Setup Guide](../monitoring/SETUP.md)
- [Disaster Recovery Plan](../disaster-recovery/STATE_RECOVERY.md)