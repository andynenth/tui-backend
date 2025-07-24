# Adapter System Deployment Runbook

## Pre-Deployment Checklist

- [ ] All contract tests passing locally
- [ ] Shadow mode tested in development
- [ ] Monitoring scripts ready
- [ ] Rollback plan documented
- [ ] Team notified of deployment

## Deployment Phases

### Phase 1: Shadow Mode Testing (Day 1-2)

#### 1.1 Enable Shadow Mode (1%)
```bash
# Set environment variables
export ADAPTER_ENABLED=false
export SHADOW_MODE_ENABLED=true
export SHADOW_MODE_PERCENTAGE=1

# Restart application
```

#### 1.2 Monitor Shadow Mode
```bash
# Run monitoring script
python3 monitor_shadow_mode.py

# Check logs for mismatches
grep "Shadow mode comparison" logs/app.log | grep MISMATCH
```

#### 1.3 Increase Shadow Percentage
If no critical issues after 2 hours:
```bash
export SHADOW_MODE_PERCENTAGE=10
# Restart application
```

### Phase 2: Initial Live Rollout (Day 3-4)

#### 2.1 Enable Adapters at 1%
```bash
export ADAPTER_ENABLED=true
export ADAPTER_ROLLOUT_PERCENTAGE=1
export SHADOW_MODE_ENABLED=false

# Restart application
```

#### 2.2 Monitor Metrics
```bash
# Check adapter status
curl http://localhost:8000/api/ws/adapter-status

# Monitor error rates
grep "Adapter error" logs/app.log | wc -l

# Check performance
grep "Adapter overhead" logs/app.log | awk '{print $NF}' | sort -n
```

#### 2.3 Gradual Increase
After each increase, wait at least 2 hours before proceeding:

```bash
# 5% rollout
export ADAPTER_ROLLOUT_PERCENTAGE=5

# 10% rollout
export ADAPTER_ROLLOUT_PERCENTAGE=10

# 25% rollout
export ADAPTER_ROLLOUT_PERCENTAGE=25

# 50% rollout
export ADAPTER_ROLLOUT_PERCENTAGE=50
```

### Phase 3: Full Rollout (Day 5)

#### 3.1 Complete Migration
```bash
export ADAPTER_ROLLOUT_PERCENTAGE=100
# Restart application
```

#### 3.2 Final Verification
- [ ] All WebSocket events working
- [ ] Performance metrics acceptable
- [ ] No increase in error rates
- [ ] User complaints addressed

## Monitoring Commands

### Real-time Monitoring
```bash
# Watch adapter status
watch -n 5 'curl -s http://localhost:8000/api/ws/adapter-status | jq .'

# Monitor error rate
tail -f logs/app.log | grep -E "(Adapter error|Shadow mode)"

# Performance tracking
tail -f logs/app.log | grep "Adapter overhead" | awk '{sum+=$NF; count++} END {print "Avg:", sum/count, "ms"}'
```

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/api/health

# Detailed health check
curl http://localhost:8000/api/health/detailed

# WebSocket test
python3 test_adapter_integration_live.py
```

## Rollback Procedures

### Immediate Rollback (< 1 minute)
```bash
# Option 1: Disable adapters completely
export ADAPTER_ENABLED=false
# Restart application

# Option 2: Reduce percentage
export ADAPTER_ROLLOUT_PERCENTAGE=0
# Restart application
```

### Partial Rollback
```bash
# Reduce to previous stable percentage
export ADAPTER_ROLLOUT_PERCENTAGE=10  # or last known good value
# Restart application
```

## Troubleshooting Guide

### Issue: High Error Rate
1. Check specific adapter errors:
   ```bash
   grep "Adapter error" logs/app.log | tail -20
   ```
2. Identify problematic event types
3. Rollback if needed
4. Fix adapter implementation
5. Re-test in shadow mode

### Issue: Performance Degradation
1. Check adapter overhead:
   ```bash
   grep "Adapter overhead" logs/app.log | sort -k5 -n | tail -20
   ```
2. Identify slow adapters
3. Consider optimization or rollback

### Issue: Mismatched Responses
1. Enable shadow mode to capture details
2. Review mismatch logs
3. Update adapter to match legacy behavior
4. Re-test before proceeding

## Success Criteria

### Shadow Mode Success
- [ ] < 1% mismatch rate
- [ ] No critical mismatches
- [ ] Performance overhead < 2ms average

### Rollout Success
- [ ] Error rate unchanged from baseline
- [ ] Response times within 5% of baseline
- [ ] No user-reported issues
- [ ] All contract tests passing

## Post-Deployment

### After Successful Rollout
1. Document any issues encountered
2. Update golden masters if needed
3. Remove legacy code (Phase 2)
4. Celebrate! 🎉

### Metrics to Track
- WebSocket connection success rate
- Average response time by event type
- Error rate by adapter
- User engagement metrics

## Emergency Contacts

- On-call Engineer: [PHONE]
- Tech Lead: [EMAIL]
- Escalation: [PROCESS]

## Appendix: Quick Commands

```bash
# Enable adapters (dev)
export ADAPTER_ENABLED=true ADAPTER_ROLLOUT_PERCENTAGE=100

# Shadow mode
export ADAPTER_ENABLED=false SHADOW_MODE_ENABLED=true SHADOW_MODE_PERCENTAGE=1

# Production rollout
export ADAPTER_ENABLED=true ADAPTER_ROLLOUT_PERCENTAGE=1

# Emergency disable
export ADAPTER_ENABLED=false
```