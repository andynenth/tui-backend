# Feature Flag Rollout Guide

## Overview
This guide documents the recommended rollout percentages and strategies for state persistence feature flags to ensure safe and controlled deployment.

## Feature Flag Inventory

### Core State Persistence Flags

| Flag Name | Description | Rollout Strategy | Dependencies |
|-----------|-------------|------------------|--------------|
| `use_state_persistence` | Master switch for state persistence | Percentage | None |
| `enable_state_snapshots` | Enable periodic snapshots | Percentage | use_state_persistence |
| `enable_state_recovery` | Enable automatic recovery | Percentage | enable_state_snapshots |

### Use-Case Specific Flags

| Flag Name | Description | Rollout Strategy | Dependencies |
|-----------|-------------|------------------|--------------|
| `use_state_persistence_startgame` | Enable for StartGameUseCase | Ring | use_state_persistence |
| `use_state_persistence_playturn` | Enable for PlayTurnUseCase | Ring | use_state_persistence |
| `use_state_persistence_declare` | Enable for DeclareUseCase | Ring | use_state_persistence |
| `use_state_persistence_scoring` | Enable for ScoringUseCase | Ring | use_state_persistence |

## Rollout Strategies

### 1. Percentage-Based Rollout

Used for core infrastructure flags that affect all users equally.

**Recommended Progression:**
```
0% → 1% → 5% → 10% → 25% → 50% → 75% → 100%
```

**Timing:**
- **Staging**: 30 minutes between increments
- **Production**: 1-2 hours between increments
- **Hold at 50%**: Monitor for 4-6 hours before proceeding

**Example Timeline (Production):**
```
Day 1:
  09:00 - Deploy at 0%
  09:30 - Increase to 1%
  11:00 - Increase to 5%
  13:00 - Increase to 10%
  15:00 - Increase to 25%

Day 2:
  09:00 - Increase to 50%
  15:00 - Increase to 75%

Day 3:
  09:00 - Increase to 100%
```

### 2. Ring-Based Rollout

Used for feature-specific flags where we want to test with specific user groups.

**Ring Definitions:**
- **Internal**: Company employees and QA team (100-200 users)
- **Beta**: Opted-in beta testers (1,000-2,000 users)
- **GA**: General availability (all users)

**Recommended Progression:**
```json
{
  "rings": {
    "internal": 100,  // Week 1
    "beta": 100,      // Week 2
    "ga": 0           // Week 3+
  }
}
```

### 3. Canary Deployment

Used for testing on specific servers/regions before full rollout.

**Canary Servers:**
- Start with 1 server (2-5% of traffic)
- Expand to 1 full region (10-20% of traffic)
- Then follow percentage rollout

## Rollout Procedures

### Pre-Rollout Checklist

- [ ] All tests passing in staging
- [ ] Rollback script tested
- [ ] Monitoring dashboards ready
- [ ] Alert thresholds configured
- [ ] On-call team briefed
- [ ] Customer support notified

### Staging Rollout

```bash
# Day 1: Basic functionality
python scripts/deploy_state_persistence.py staging --flags use_state_persistence

# Day 2: Add snapshots
python scripts/deploy_state_persistence.py staging --flags enable_state_snapshots

# Day 3: Add recovery
python scripts/deploy_state_persistence.py staging --flags enable_state_recovery

# Day 4: Full system test
python scripts/performance_test_state_persistence.py --compare
```

### Production Rollout

#### Week 1: Core Infrastructure

**Monday:**
```bash
# Enable at 1% for monitoring
curl -X PUT https://api.prod/feature-flags/use_state_persistence \
  -d '{"enabled": true, "percentage": 1}'

# Monitor for 2 hours, then increase
curl -X POST https://api.prod/feature-flags/rollout/use_state_persistence/increase \
  -d '{"increase_by": 4}'  # To 5%
```

**Tuesday-Wednesday:**
```bash
# Gradual increase
# 5% → 10% → 25% → 50%
python scripts/deploy_state_persistence.py production \
  --flags use_state_persistence \
  --initial-percentage 5
```

**Thursday:**
```bash
# Complete rollout if metrics good
curl -X PUT https://api.prod/feature-flags/use_state_persistence \
  -d '{"enabled": true, "percentage": 100}'
```

#### Week 2: Additional Features

**Enable Snapshots:**
```bash
# Start with internal ring
curl -X PUT https://api.prod/feature-flags/enable_state_snapshots \
  -d '{
    "enabled": true,
    "strategy": "ring",
    "rings": {"internal": 100, "beta": 0, "ga": 0}
  }'
```

**Enable Recovery:**
```bash
# After snapshots stable
curl -X PUT https://api.prod/feature-flags/enable_state_recovery \
  -d '{"enabled": true, "percentage": 50}'
```

#### Week 3: Use-Case Rollout

**Per Use-Case Enablement:**
```bash
# Start with low-risk use case
curl -X PUT https://api.prod/feature-flags/use_state_persistence_startgame \
  -d '{
    "enabled": true,
    "strategy": "ring",
    "rings": {"internal": 100, "beta": 50, "ga": 0}
  }'

# Gradually enable others
for use_case in playturn declare scoring; do
  curl -X PUT https://api.prod/feature-flags/use_state_persistence_${use_case} \
    -d '{"enabled": true, "percentage": 10}'
done
```

## Monitoring During Rollout

### Key Metrics to Watch

| Metric | Threshold | Action if Exceeded |
|--------|-----------|-------------------|
| Error Rate | > 5% | Pause rollout |
| P99 Latency | > 100ms | Investigate, possibly pause |
| Recovery Failures | > 1% | Rollback recovery feature |
| Memory Usage | > 80% | Scale infrastructure |

### Dashboard URLs

- **Overall Health**: https://grafana.prod/d/state-health
- **Performance Impact**: https://grafana.prod/d/state-performance
- **Error Analysis**: https://grafana.prod/d/state-errors

### Alert Response

**If error rate > 5%:**
```bash
# Freeze current percentage
curl -X POST https://api.prod/feature-flags/freeze/use_state_persistence

# Investigate errors
grep "ERROR.*state_persistence" /var/log/app.log | tail -100

# If critical, rollback
python scripts/rollback_state_persistence.py
```

## Rollback Procedures

### Partial Rollback

To rollback to a previous percentage:
```bash
# Rollback to 25%
curl -X PUT https://api.prod/feature-flags/use_state_persistence \
  -d '{"enabled": true, "percentage": 25}'
```

### Complete Rollback

For emergency situations:
```bash
# Disable all state persistence
python scripts/rollback_state_persistence.py

# Or via API
curl -X POST https://api.prod/feature-flags/bulk-update \
  -d '[
    {"name": "use_state_persistence", "enabled": false},
    {"name": "enable_state_snapshots", "enabled": false},
    {"name": "enable_state_recovery", "enabled": false}
  ]'
```

## A/B Testing Configuration

### Performance Impact Test

```json
{
  "experiment": "state_persistence_performance",
  "variants": {
    "control": 50,      // No state persistence
    "treatment": 50     // With state persistence
  },
  "metrics": [
    "game_latency_p99",
    "error_rate",
    "user_satisfaction"
  ],
  "min_sample_size": 10000
}
```

### Feature Adoption Test

```json
{
  "experiment": "recovery_feature_value",
  "variants": {
    "no_recovery": 33.33,
    "auto_recovery": 33.33,
    "manual_recovery": 33.34
  },
  "metrics": [
    "games_recovered",
    "user_retention",
    "support_tickets"
  ]
}
```

## Best Practices

### DO:
- ✅ Monitor continuously during rollout
- ✅ Have rollback plan ready
- ✅ Communicate with team during rollout
- ✅ Document any issues encountered
- ✅ Wait for metrics to stabilize before increasing
- ✅ Test rollback procedures before starting

### DON'T:
- ❌ Skip percentage steps
- ❌ Rollout during peak hours
- ❌ Ignore warning signs in metrics
- ❌ Rollout multiple flags simultaneously
- ❌ Proceed without monitoring access

## Rollout Communication Template

### Pre-Rollout Announcement
```
Subject: State Persistence Rollout Starting [Date]

Team,

We will begin rolling out state persistence on [Date] at [Time].

Rollout Plan:
- Initial: 1% of traffic
- Target: 100% by [End Date]
- Rollback ready if needed

Monitor: [Dashboard Link]
Runbook: [Runbook Link]

Contact [On-Call] with questions.
```

### Progress Update
```
State Persistence Rollout Update

Current: [X]% enabled
Status: [Green/Yellow/Red]
Metrics: Error rate [X]%, P99 [X]ms
Next: Increase to [X]% at [Time]

Issues: [None/Description]
```

### Completion Announcement
```
State Persistence Rollout Complete ✅

Final Status:
- 100% of traffic enabled
- Error rate: [X]% (within threshold)
- Performance impact: [X]ms P99
- [X] games with state persistence

Thank you for your support during rollout!
```

## Appendix: Quick Commands

```bash
# Check current rollout percentage
curl https://api.prod/feature-flags/use_state_persistence

# Increase by 10%
curl -X POST https://api.prod/feature-flags/rollout/use_state_persistence/increase

# Set specific percentage
curl -X PUT https://api.prod/feature-flags/use_state_persistence \
  -d '{"percentage": 50}'

# Emergency disable
curl -X POST https://api.prod/feature-flags/toggle \
  -d '{"flag": "use_state_persistence", "enabled": false}'

# Get rollout report
curl https://api.prod/feature-flags/evaluate \
  -d '{"context": {"user_id": "test-user"}}'
```