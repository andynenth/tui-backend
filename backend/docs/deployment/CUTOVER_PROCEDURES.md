# Blue-Green Cutover Procedures

## Overview
This document outlines the procedures for performing blue-green deployment cutover for state persistence features. These procedures ensure zero-downtime deployment with safe rollback capabilities.

## Prerequisites

### Before Starting Cutover
- [ ] All tests passing in staging environment
- [ ] Performance benchmarks meet requirements
- [ ] Rollback scripts tested and verified
- [ ] On-call team briefed and ready
- [ ] Customer support notified of deployment window
- [ ] Monitoring dashboards configured and accessible
- [ ] Load balancer configuration verified
- [ ] Both blue and green environments healthy

### Required Access
- SSH access to production servers
- Load balancer admin access
- Monitoring system access
- Feature flag management access
- Database read access for verification
- Incident management system access

## Architecture Overview

```
                    Load Balancer
                         |
                    [Traffic Split]
                    /            \
                Blue              Green
            (Current Prod)    (New Version)
                |                    |
            Database            Database
            (Shared)            (Shared)
```

## Cutover Phases

### Phase 1: Pre-Cutover Validation (T-30 minutes)

#### 1.1 Verify Green Environment
```bash
# Check green environment health
curl https://green.prod.example.com/health/detailed

# Verify feature flags
curl https://green.prod.example.com/api/feature-flags

# Run smoke tests
python scripts/smoke_test.py --env green

# Verify database connectivity
python scripts/verify_db_connection.py --env green
```

#### 1.2 Performance Validation
```bash
# Run performance comparison
python scripts/performance_test_state_persistence.py \
  --base-url https://green.prod.example.com \
  --duration 300 \
  --users 10

# Compare with blue environment
python scripts/compare_environments.py blue green
```

#### 1.3 Feature Flag Verification
```bash
# Ensure flags are at 0% in green
curl -X GET https://green.prod.example.com/api/feature-flags/use_state_persistence

# Response should show:
# {
#   "enabled": true,
#   "percentage": 0.0,
#   "strategy": "percentage"
# }
```

### Phase 2: Initial Traffic Shift (T-0)

#### 2.1 Start Gradual Shift (1% Traffic)
```bash
# Configure load balancer for 1% to green
python scripts/load_balancer_control.py \
  --action shift \
  --blue 99 \
  --green 1

# Or via API
curl -X POST https://lb.prod.example.com/api/traffic \
  -d '{
    "blue": 99.0,
    "green": 1.0,
    "strategy": "percentage"
  }'
```

#### 2.2 Monitor Initial Traffic
```bash
# Watch real-time metrics
watch -n 5 'curl -s https://green.prod.example.com/health/metrics | jq .'

# Monitor error rates
python scripts/monitor_errors.py --env green --duration 300
```

#### 2.3 Validation Checkpoints
After 5 minutes at 1%, verify:
- [ ] Error rate < 0.1%
- [ ] P99 latency < 100ms
- [ ] No circuit breakers open
- [ ] No memory leaks detected
- [ ] CPU usage stable

### Phase 3: Progressive Traffic Increase

#### 3.1 Increase to 5%
```bash
# After successful validation at 1%
python scripts/load_balancer_control.py --blue 95 --green 5

# Monitor for 10 minutes
python scripts/cutover_monitor.py --threshold 5 --duration 600
```

#### 3.2 Increase to 25%
```bash
# After successful validation at 5%
python scripts/load_balancer_control.py --blue 75 --green 25

# Extended monitoring
python scripts/cutover_monitor.py --threshold 25 --duration 900
```

#### 3.3 Increase to 50%
```bash
# Critical point - half traffic on new version
python scripts/load_balancer_control.py --blue 50 --green 50

# Intensive monitoring
python scripts/cutover_monitor.py --threshold 50 --duration 1800 --alert-team
```

**HOLD POINT**: Remain at 50% for minimum 30 minutes before proceeding.

### Phase 4: Complete Cutover

#### 4.1 Increase to 75%
```bash
python scripts/load_balancer_control.py --blue 25 --green 75

# Monitor closely
python scripts/cutover_monitor.py --threshold 75 --duration 900
```

#### 4.2 Full Cutover (100%)
```bash
# Final shift
python scripts/load_balancer_control.py --blue 0 --green 100

# Comprehensive validation
python scripts/post_cutover_validation.py
```

#### 4.3 Update DNS/Service Discovery
```bash
# Update service discovery to point to green
python scripts/update_service_discovery.py --primary green

# Verify DNS propagation
dig api.prod.example.com
```

### Phase 5: Post-Cutover Tasks

#### 5.1 Enable State Persistence Features
```bash
# Now that green is primary, enable features
python scripts/deploy_state_persistence.py production \
  --flags use_state_persistence \
  --initial-percentage 1
```

#### 5.2 Decommission Blue Environment
After 24 hours of stable operation:
```bash
# Stop blue environment
python scripts/environment_control.py --env blue --action stop

# Archive blue environment data
python scripts/archive_environment.py blue
```

## Rollback Procedures

### Immediate Rollback (Any Phase)
If issues detected at any phase:

```bash
# Immediate traffic reversal
python scripts/emergency_rollback.py --target blue

# Or manual:
python scripts/load_balancer_control.py --blue 100 --green 0

# Disable feature flags
curl -X POST https://api.prod.example.com/api/feature-flags/bulk-update \
  -d '[
    {"name": "use_state_persistence", "enabled": false},
    {"name": "enable_state_snapshots", "enabled": false}
  ]'
```

### Rollback Decision Matrix

| Issue Type | Rollback? | Action |
|------------|-----------|--------|
| Error rate > 5% | Yes | Immediate rollback |
| P99 latency > 200ms | Yes | Immediate rollback |
| Memory leak detected | Yes | Immediate rollback |
| Minor UI issues | No | Fix forward |
| Non-critical warnings | No | Monitor closely |

## Monitoring During Cutover

### Key Dashboards
1. **Traffic Distribution**: https://grafana.prod/d/traffic-split
2. **Error Rates**: https://grafana.prod/d/error-analysis
3. **Performance Metrics**: https://grafana.prod/d/performance
4. **State Persistence**: https://grafana.prod/d/state-persistence

### Critical Metrics to Watch
```bash
# Real-time metric streaming
python scripts/stream_metrics.py \
  --metrics error_rate,p99_latency,active_connections \
  --alert-threshold error_rate:0.05,p99_latency:150
```

### Alert Thresholds
- **Error Rate**: > 1% triggers warning, > 5% triggers rollback
- **P99 Latency**: > 150ms triggers warning, > 200ms triggers rollback
- **CPU Usage**: > 80% triggers warning, > 90% triggers scale-up
- **Memory Usage**: > 85% triggers warning, > 95% triggers rollback

## Communication Plan

### Pre-Cutover Announcement
```
Subject: Blue-Green Cutover Starting - State Persistence

Team,

We are beginning the blue-green cutover for state persistence at [TIME].

Timeline:
- T-0: Start 1% traffic shift
- T+30m: Increase to 25% (if stable)
- T+60m: Increase to 50% (if stable)
- T+120m: Complete cutover (if stable)

Dashboards: [Dashboard Links]
Runbook: [This Document]
On-Call: [Names and Contact]
```

### Progress Updates
Send updates at each phase:
- 1% traffic shifted
- 25% traffic shifted
- 50% traffic shifted (critical point)
- 100% cutover complete

### Issue Communication
If issues arise:
```
Subject: ISSUE - Blue-Green Cutover - [Issue Description]

Status: [Investigating/Mitigating/Resolved]
Impact: [User Impact]
Action: [Current Action]
ETA: [Resolution ETA]

[Details]
```

## Validation Scripts

### Pre-Cutover Validation
```bash
#!/bin/bash
# pre_cutover_validation.sh

echo "Running pre-cutover validation..."

# Check both environments
for env in blue green; do
  echo "Checking $env environment..."
  
  # Health check
  health=$(curl -s https://$env.prod.example.com/health)
  echo "Health: $health"
  
  # Feature flags
  flags=$(curl -s https://$env.prod.example.com/api/feature-flags)
  echo "Flags: $flags"
  
  # Database connectivity
  db_check=$(curl -s https://$env.prod.example.com/health/dependencies/database)
  echo "Database: $db_check"
done

# Compare configurations
python scripts/compare_configs.py blue green
```

### Traffic Validation
```python
# validate_traffic_split.py
import requests
import time
from collections import Counter

def validate_traffic_split(duration_seconds=60):
    """Validate actual traffic distribution."""
    
    results = Counter()
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        try:
            # Make request through load balancer
            response = requests.get(
                "https://api.prod.example.com/health",
                headers={"X-Request-ID": str(time.time())}
            )
            
            # Check which backend served the request
            backend = response.headers.get("X-Backend-Server", "unknown")
            results[backend] += 1
            
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(0.1)
    
    # Calculate percentages
    total = sum(results.values())
    for backend, count in results.items():
        percentage = (count / total) * 100
        print(f"{backend}: {count} requests ({percentage:.1f}%)")
    
    return results

if __name__ == "__main__":
    validate_traffic_split()
```

## Post-Cutover Checklist

### Immediate Tasks (First Hour)
- [ ] Verify all traffic on green environment
- [ ] Confirm error rates normal
- [ ] Check all monitoring dashboards
- [ ] Run integration test suite
- [ ] Verify state persistence working
- [ ] Update status page
- [ ] Send completion announcement

### Day 1 Tasks
- [ ] Monitor performance trends
- [ ] Review any error logs
- [ ] Gather team feedback
- [ ] Document any issues encountered
- [ ] Plan feature flag rollout
- [ ] Schedule blue environment decommission

### Week 1 Tasks
- [ ] Complete feature flag rollout
- [ ] Performance analysis report
- [ ] Update runbooks with learnings
- [ ] Plan next deployment improvements
- [ ] Archive blue environment
- [ ] Celebrate successful deployment! 🎉

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Deployment Lead | [Name] | [Phone/Slack] |
| SRE On-Call | [Name] | [Phone/Slack] |
| Database Admin | [Name] | [Phone/Slack] |
| Product Owner | [Name] | [Phone/Slack] |
| Support Lead | [Name] | [Phone/Slack] |

## Appendix: Quick Commands

```bash
# Check current traffic split
curl https://lb.prod.example.com/api/status

# Emergency rollback
./emergency_rollback.sh

# View real-time logs
tail -f /var/log/cutover.log

# Force health check
curl -X POST https://api.prod.example.com/health/force-check

# Disable all feature flags
./disable_all_flags.sh

# Scale up green environment
kubectl scale deployment green-api --replicas=10
```