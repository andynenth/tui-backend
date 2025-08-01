# State Persistence On-Call Playbook

## 🚨 Quick Reference

**Escalation Path:**
1. Primary On-Call: Check PagerDuty
2. Secondary On-Call: If no response in 5 minutes
3. Engineering Manager: If critical and no response in 15 minutes
4. CTO: If complete system failure

**Key Commands:**
```bash
# Disable state persistence (emergency)
export FF_USE_STATE_PERSISTENCE=false

# Check system health
curl http://prod-server/api/health/state-management

# View recent errors
grep "ERROR.*state_persistence" /var/log/app.log | tail -50

# Emergency rollback
python scripts/rollback_state_persistence.py
```

---

## Alert Response Procedures

### 🔴 CRITICAL: Circuit Breaker Open

**Alert:** `CircuitBreakerOpen - State management circuit breaker is open`

**Impact:** Games continuing without state persistence, potential data loss on crash

**Response Time:** < 5 minutes

**Steps:**
1. **Acknowledge alert** in PagerDuty
2. **Check circuit breaker status:**
   ```bash
   curl http://prod-server/api/health/circuit-breakers | jq '.state_management'
   ```
3. **Identify root cause:**
   ```bash
   # Check storage connectivity
   redis-cli -h prod-redis ping  # For Redis
   aws dynamodb describe-table --table-name game-states  # For DynamoDB
   
   # Check recent errors
   grep "circuit.*breaker.*opened" /var/log/app.log -B 10
   ```
4. **Fix underlying issue:**
   - If storage down: Check with infrastructure team
   - If connection pool exhausted: Scale connections
   - If timeout issues: Check storage performance
5. **Monitor recovery:**
   - Circuit breaker should auto-recover after 30s
   - Watch for successful state operations
6. **Verify normal operation:**
   ```bash
   curl http://prod-server/metrics | grep -E "state_transitions_total|state_errors"
   ```

### 🔴 CRITICAL: High State Error Rate

**Alert:** `HighStateErrorRate - State management error rate above 5%`

**Impact:** Game states may not be persisting, recovery failures possible

**Response Time:** < 5 minutes

**Steps:**
1. **Assess severity:**
   ```bash
   # Get exact error rate
   curl http://prod-server/metrics | grep state_errors_total
   
   # Check error types
   grep "ERROR.*state_persistence" /var/log/app.log | \
     grep -oE "error_type:[a-zA-Z_]+" | sort | uniq -c
   ```

2. **Quick mitigation (if > 20% error rate):**
   ```bash
   # Disable state persistence temporarily
   export FF_USE_STATE_PERSISTENCE=false
   kubectl rollout restart deployment/game-server  # Or your restart command
   ```

3. **Investigate common causes:**
   - **Serialization errors:** Check for new game state fields
   - **Storage errors:** Verify storage health
   - **Validation errors:** Check state validation rules
   - **Version conflicts:** Check for deployment mismatches

4. **Apply fix:**
   - Deploy hotfix if code issue
   - Scale storage if capacity issue
   - Fix configuration if misconfigured

5. **Re-enable gradually:**
   ```bash
   # Enable for 10% of traffic first
   export FF_USE_STATE_PERSISTENCE=true
   export STATE_PERSISTENCE_PERCENTAGE=10
   ```

### 🟡 WARNING: Slow State Operations

**Alert:** `SlowStateOperations - 99th percentile latency above 100ms`

**Impact:** Game actions may feel sluggish, player experience degraded

**Response Time:** < 30 minutes

**Steps:**
1. **Measure impact:**
   ```bash
   # Get latency percentiles
   curl http://prod-server/metrics | grep state_operation_duration_ms
   
   # Check operation types
   curl http://prod-server/metrics | grep -E "operation=\"[^\"]+\"" | \
     awk -F'"' '{print $2}' | sort | uniq -c
   ```

2. **Check cache performance:**
   ```bash
   # Cache hit rate
   curl http://prod-server/metrics | grep state_cache
   
   # If low hit rate, check cache size
   redis-cli info memory | grep used_memory
   ```

3. **Common optimizations:**
   - Increase cache size if hit rate < 80%
   - Enable compression if not enabled
   - Reduce snapshot frequency if too aggressive
   - Add read replicas if read-heavy

4. **Monitor improvement:**
   - Watch p99 latency trend
   - Ensure no increase in errors

### 🟡 WARNING: State Recovery Failures

**Alert:** `StateRecoveryFailures - State recovery failure rate above 1%`

**Impact:** Games may not restore properly after server restarts

**Response Time:** < 30 minutes

**Steps:**
1. **Check recovery logs:**
   ```bash
   grep "recovery.*failed" /var/log/app.log | tail -20
   ```

2. **Common issues:**
   - **Corrupted snapshots:** Validate snapshot integrity
   - **Version mismatches:** Check deployment versions
   - **Missing data:** Verify retention policies

3. **Manual recovery for affected games:**
   ```python
   # Use recovery script
   python scripts/recover_game_state.py --game-id <id> --source backup
   ```

4. **Prevent future failures:**
   - Adjust snapshot frequency
   - Increase retention period
   - Add validation checks

---

## Common Scenarios

### Scenario: Mass Recovery After Outage

**Situation:** Server crashed, need to recover multiple games

**Steps:**
1. **List affected games:**
   ```bash
   # Games active in last hour
   redis-cli --scan --pattern "game:*" | \
     xargs -I {} redis-cli hget {} last_updated | \
     awk '$1 > (systime() - 3600)'
   ```

2. **Bulk recovery:**
   ```bash
   python scripts/bulk_recovery.py --time-range "1h" --parallel 10
   ```

3. **Verify recovery:**
   ```bash
   # Check recovery success rate
   curl http://prod-server/metrics | grep state_recoveries_total
   ```

### Scenario: Storage Migration

**Situation:** Need to migrate from Redis to DynamoDB (or vice versa)

**Steps:**
1. **Create full backup:**
   ```bash
   python scripts/backup_state_data.py backup --name pre_migration
   ```

2. **Enable dual-write mode:**
   ```bash
   export STATE_DUAL_WRITE=true
   export STATE_PRIMARY_BACKEND=redis
   export STATE_SECONDARY_BACKEND=dynamodb
   ```

3. **Verify dual writes:**
   ```bash
   # Check both storages have same count
   redis-cli dbsize
   aws dynamodb scan --table-name game-states --select COUNT
   ```

4. **Switch primary:**
   ```bash
   export STATE_PRIMARY_BACKEND=dynamodb
   ```

5. **Disable old backend:**
   ```bash
   export STATE_DUAL_WRITE=false
   ```

### Scenario: Memory Leak Investigation

**Situation:** State persistence causing memory growth

**Steps:**
1. **Identify leak source:**
   ```bash
   # Heap dump
   jmap -dump:format=b,file=heap.bin <pid>  # For Java
   gcore -o heap.dump <pid>  # For other languages
   ```

2. **Check cache size:**
   ```bash
   curl http://prod-server/debug/state-cache/stats
   ```

3. **Temporary mitigation:**
   ```bash
   # Reduce cache size
   export STATE_CACHE_SIZE=100
   
   # More aggressive cleanup
   export STATE_CACHE_TTL=300  # 5 minutes
   ```

---

## Maintenance Procedures

### Scheduled Backup Verification

**Frequency:** Daily at 2 AM

**Steps:**
1. Check latest backup:
   ```bash
   python scripts/backup_state_data.py list | head -5
   ```

2. Validate backup:
   ```bash
   python scripts/backup_state_data.py validate \
     --path /backups/state/latest.json.gz
   ```

3. Test restore (dry-run):
   ```bash
   python scripts/backup_state_data.py restore \
     --path /backups/state/latest.json.gz \
     --dry-run
   ```

### Performance Baseline Update

**Frequency:** Weekly

**Steps:**
1. Collect metrics:
   ```bash
   python scripts/collect_performance_baseline.py \
     --duration 24h \
     --output /metrics/baseline_$(date +%Y%m%d).json
   ```

2. Compare with previous:
   ```bash
   python scripts/compare_baselines.py \
     --current /metrics/baseline_$(date +%Y%m%d).json \
     --previous /metrics/baseline_$(date -d '7 days ago' +%Y%m%d).json
   ```

3. Update alert thresholds if needed

---

## Decision Trees

### Should I Disable State Persistence?

```
High Error Rate (>20%)?
├── YES → Disable immediately
└── NO → Error Rate > 5%?
    ├── YES → Can identify specific issue?
    │   ├── YES → Fix issue, monitor closely
    │   └── NO → Disable and investigate
    └── NO → Monitor and investigate
```

### Should I Page Secondary On-Call?

```
Critical Alert?
├── YES → Acknowledged?
│   ├── NO → Page after 5 minutes
│   └── YES → Making progress?
│       ├── NO → Page for help
│       └── YES → Continue solo
└── NO (Warning) → Need expertise?
    ├── YES → Page during business hours
    └── NO → Handle solo
```

---

## Post-Incident Procedures

### After Any Critical Alert:

1. **Update incident log:**
   ```bash
   echo "$(date): <incident summary>" >> /var/log/incidents/state_persistence.log
   ```

2. **Create post-mortem ticket:**
   - If customer impact > 5 minutes
   - If data loss occurred
   - If manual intervention required

3. **Update runbook:**
   - Add any new failure modes discovered
   - Update commands if they've changed
   - Add learned optimizations

### Weekly On-Call Handoff:

1. **Review week's alerts:**
   ```bash
   python scripts/generate_oncall_summary.py --week $(date +%V)
   ```

2. **Update next on-call:**
   - Any ongoing issues
   - Scheduled maintenance
   - Known problems

3. **Check monitoring:**
   - All alerts firing correctly
   - Dashboard access working
   - Scripts up to date

---

## Tools and Access

### Required Access:
- [ ] Production Kubernetes cluster
- [ ] Redis/DynamoDB admin access
- [ ] Log aggregation system
- [ ] Monitoring dashboards
- [ ] PagerDuty account
- [ ] Runbook repository

### Useful Links:
- [State Management Dashboard](http://grafana/d/state-mgmt)
- [Log Search](http://kibana/app/discover#/state-persistence)
- [Architecture Diagram](../diagrams/state-persistence-arch.png)
- [Incident History](http://wiki/state-persistence-incidents)

### Key Contacts:
- **State Persistence SME:** @state-team in Slack
- **Infrastructure:** @infra-oncall in Slack
- **Database Team:** @database-team in Slack
- **Security:** @security-team (for encryption issues)

---

## Remember:
1. **Player experience first** - Disable if needed
2. **Communicate** - Update #incidents channel
3. **Document** - Note anything unusual
4. **Ask for help** - Don't struggle alone