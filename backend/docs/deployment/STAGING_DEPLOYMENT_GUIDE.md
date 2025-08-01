# State Persistence Staging Deployment Guide

## Overview
This guide covers enabling state persistence in the staging environment after successful development validation.

## Prerequisites
- ✅ Development environment validation complete
- ✅ All integration tests passing
- ✅ Metrics collection verified
- ✅ In-memory stores tested

## Staging Deployment Steps

### 1. Environment Configuration
Set the following environment variables in your staging environment:

```bash
# Enable state persistence
export FF_USE_STATE_PERSISTENCE=true
export FF_ENABLE_STATE_SNAPSHOTS=true

# Optional: Enable recovery for fault tolerance
export FF_ENABLE_STATE_RECOVERY=true
```

### 2. Verify Configuration
Run the verification script in staging:

```bash
python scripts/enable_state_persistence.py
```

Expected output:
- ✅ State persistence enabled successfully
- ✅ All integration tests passed
- ✅ Metrics collector operational
- ✅ State adapter created and enabled

### 3. Monitoring Checklist

#### First 24 Hours
Monitor these key metrics:
- [ ] No increase in error rates
- [ ] Game flow continues normally
- [ ] State transitions are logged
- [ ] Memory usage remains stable
- [ ] No performance degradation

#### Metrics to Track
```python
# Key metrics to monitor
- state_transitions_total
- state_snapshots_created
- state_persistence_errors
- state_operation_duration_ms
- circuit_breaker_status
```

### 4. Rollback Plan
If issues arise, disable state persistence immediately:

```bash
# Disable state persistence
export FF_USE_STATE_PERSISTENCE=false
export FF_ENABLE_STATE_SNAPSHOTS=false
```

No code changes or deployments needed - just restart the application.

### 5. Success Criteria
After 24-48 hours, validate:
- ✅ No state-related errors in logs
- ✅ Game sessions complete successfully
- ✅ Metrics show healthy operation
- ✅ No player-reported issues

## Production Readiness Checklist

Before enabling in production:
1. [ ] Replace in-memory stores with persistent storage (Redis/DynamoDB)
2. [ ] Configure appropriate retention policies
3. [ ] Set up monitoring alerts
4. [ ] Document recovery procedures
5. [ ] Performance test under load

## Troubleshooting

### Common Issues

1. **"State persistence enabled but no manager available"**
   - Ensure both USE_STATE_PERSISTENCE and ENABLE_STATE_SNAPSHOTS are true
   - Check application logs for initialization errors

2. **Performance degradation**
   - Monitor state_operation_duration_ms metric
   - Consider adjusting batch_size in PersistenceConfig
   - Enable caching if not already enabled

3. **Memory growth**
   - Check for state accumulation in in-memory stores
   - Implement cleanup policies for old states
   - Monitor memory_usage metrics

### Debug Commands

```bash
# Check feature flag status
python -c "from infrastructure.feature_flags import FeatureFlags; f = FeatureFlags(); print(f.get_all_flags())"

# Test state adapter creation
python scripts/test_state_persistence_live.py

# Check metrics
curl http://staging-server/metrics | grep state_
```

## Next Steps
Once staging validation is complete:
1. Review Phase 4 deployment tasks
2. Plan production rollout strategy
3. Prepare persistent storage infrastructure
4. Update runbooks and documentation