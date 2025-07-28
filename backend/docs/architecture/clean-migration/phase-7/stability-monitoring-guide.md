# Stability Monitoring Guide (Phase 6 → Phase 7)

**Purpose**: Ensure production stability during the 2-week monitoring period before Phase 7  
**Period**: July 27, 2025 - August 10, 2025  
**Goal**: Validate clean architecture stability before legacy code removal

## 🎯 Monitoring Objectives

1. **Prove Stability**: Demonstrate 14+ days without incidents
2. **Validate Performance**: Ensure no degradation from Phase 6 levels
3. **Detect Issues Early**: Catch problems before Phase 7
4. **Build Confidence**: Team ready for legacy removal

## 📊 Key Metrics to Monitor

### 1. System Health Metrics
| Metric | Target | Alert Threshold | Check Frequency |
|--------|--------|-----------------|-----------------|
| Error Rate | < 0.1% | > 0.5% | Every hour |
| Response Time (avg) | < 3ms | > 5ms | Every 15 min |
| WebSocket Connections | Stable | ±20% change | Every hour |
| Memory Usage | < 1GB | > 1.5GB | Every hour |
| CPU Usage | < 60% | > 80% | Every 15 min |

### 2. Application Metrics
| Metric | Baseline | Alert Threshold | Check Frequency |
|--------|----------|-----------------|-----------------|
| Active Games | Variable | N/A | Every hour |
| Game Creation Rate | ~10/min | < 5/min | Every hour |
| Player Actions/sec | ~50/sec | < 20/sec | Every 30 min |
| Bot Response Time | < 1000ms | > 1500ms | Every hour |
| State Transitions | < 2ms | > 3ms | Every hour |

### 3. Architecture Metrics
| Metric | Expected | Alert If | Check Frequency |
|--------|----------|----------|-----------------|
| Legacy Code Calls | 0 | Any detected | Continuous |
| Adapter Routing | 100% | < 100% | Every hour |
| Clean Architecture Errors | 0 | Any detected | Continuous |
| Cross-Dependencies | 6→0 | Increases | Daily |

## 🔍 Monitoring Tools & Commands

### Real-Time Monitoring
```bash
# 1. Watch error rate (run in separate terminal)
watch -n 60 'grep -c "ERROR\|Exception" /log.txt | tail -100 | wc -l'

# 2. Monitor WebSocket connections
watch -n 300 'netstat -an | grep :5050 | grep ESTABLISHED | wc -l'

# 3. Track response times
tail -f /log.txt | grep -E "WebSocket.*[0-9]+ms" | awk '{print $NF}'

# 4. Memory usage tracking
watch -n 300 'ps aux | grep python.*backend | awk "{sum+=\$6} END {print sum/1024 \" MB\"}"'
```

### Daily Analysis Scripts
```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Daily Health Check $(date) ==="

# Error rate calculation
TOTAL_REQUESTS=$(grep -c "INFO.*WebSocket" /log.txt)
ERRORS=$(grep -c "ERROR\|Exception" /log.txt)
ERROR_RATE=$(echo "scale=2; $ERRORS * 100 / $TOTAL_REQUESTS" | bc)
echo "Error Rate: $ERROR_RATE%"

# Average response time
AVG_RESPONSE=$(grep "WebSocket.*ms" /log.txt | awk -F'ms' '{sum+=$1; count++} END {print sum/count " ms"}')
echo "Avg Response Time: $AVG_RESPONSE"

# Architecture verification
echo "Architecture Status:"
python verify_architecture_status.py | grep -E "Status|Score"

# Legacy code detection
LEGACY_CALLS=$(grep -c "shared_room_manager\|shared_bot_manager" /log.txt)
echo "Legacy Code Calls: $LEGACY_CALLS"
```

### Architecture Verification
```bash
# Check for legacy code usage
grep -i "legacy\|shared_.*_manager" /log.txt | grep -v "expected\|harmless" | tail -20

# Verify adapter routing
grep "ADAPTER-ONLY MODE\|adapter_wrapper.*INFO" /log.txt | tail -10

# Monitor cross-dependencies
cd backend && python tools/identify_architecture_type.py --directory . | grep -A5 "WARNING"
```

## 📋 Daily Monitoring Checklist

### Morning (9:00 AM)
- [ ] Check overnight error logs
- [ ] Verify no legacy code execution
- [ ] Review memory/CPU trends
- [ ] Check active game count
- [ ] Note any unusual patterns

### Midday (12:00 PM)
- [ ] Peak load performance check
- [ ] Response time analysis
- [ ] WebSocket connection stability
- [ ] Bot performance verification

### Evening (5:00 PM)
- [ ] Daily metrics summary
- [ ] Incident log review
- [ ] Architecture verification
- [ ] Team status update

### End of Day Report Template
```markdown
## Daily Monitoring Report - [DATE]

### System Health
- Error Rate: ___%
- Avg Response Time: ___ms
- Peak Connections: ___
- Memory Usage: ___MB
- CPU Usage: ___%

### Incidents
- Count: ___
- Severity: ___
- Resolution: ___

### Architecture Status
- Legacy Calls Detected: ___
- Adapter Routing: ___%
- Cross-Dependencies: ___

### Concerns/Notes
- [Any observations]

### Tomorrow's Focus
- [Specific areas to monitor]
```

## 🚨 Incident Response

### Severity Levels

#### Level 1: Critical (Immediate Action)
- Error rate > 1%
- System down/unreachable
- Data corruption detected
- Mass user disconnections

**Action**: 
1. Alert team immediately
2. Consider Phase 6 rollback
3. Stop Phase 7 planning
4. Post-mortem required

#### Level 2: High (Same Day Action)
- Error rate 0.5% - 1%
- Performance degradation > 50%
- Legacy code execution detected
- Memory leak suspected

**Action**:
1. Investigate root cause
2. Apply hotfix if needed
3. Extend monitoring period
4. Document in daily report

#### Level 3: Medium (Next Day Action)
- Error rate 0.1% - 0.5%
- Performance degradation 10-50%
- Intermittent issues
- User complaints increase

**Action**:
1. Add to investigation queue
2. Increase monitoring frequency
3. May impact Phase 7 timeline
4. Team discussion needed

#### Level 4: Low (Monitor)
- Normal fluctuations
- Known issues (documented)
- Cosmetic errors
- Expected warnings

**Action**:
1. Log in daily report
2. No immediate action
3. Track patterns
4. Address in Phase 7

## 📈 Trend Analysis

### Weekly Metrics Review
Every Monday, analyze:
1. **Error Rate Trend**: Should be stable or decreasing
2. **Performance Trend**: Should be stable or improving
3. **Resource Usage**: Should be predictable
4. **User Activity**: Should follow normal patterns

### Red Flags
- Increasing error rate (even if < 0.1%)
- Gradual performance degradation
- Memory usage trending up
- Unexplained pattern changes

### Green Flags
- Consistent low error rates
- Stable performance metrics
- Predictable resource usage
- No user complaints

## 🔧 Monitoring Tools Setup

### Grafana Dashboard (Recommended)
If available, create dashboard with:
- Error rate graph (1h, 24h, 7d views)
- Response time percentiles (p50, p95, p99)
- Active connections over time
- Memory/CPU usage trends
- Alert status panel

### Log Aggregation
Consider setting up:
- Centralized logging (ELK stack)
- Real-time alerts (PagerDuty/Slack)
- Automated reports
- Anomaly detection

### Simple Alternative
For basic monitoring:
```bash
# Create monitoring directory
mkdir -p monitoring/daily-reports

# Automated daily snapshot
crontab -e
# Add: 0 18 * * * /path/to/daily_health_check.sh > monitoring/daily-reports/$(date +%Y%m%d).txt
```

## ✅ Success Criteria for Phase 7 Go-Ahead

### Must Have (All Required)
- [ ] 14 consecutive days without Level 1 or 2 incidents
- [ ] Error rate consistently < 0.1%
- [ ] No legacy code execution detected
- [ ] Performance equal or better than July 27 baseline
- [ ] All cross-dependencies resolved
- [ ] Team consensus on stability

### Nice to Have
- [ ] Automated monitoring fully operational
- [ ] Performance improvements identified
- [ ] User satisfaction increased
- [ ] Documentation fully updated

## 📅 Monitoring Timeline

### Week 1 (July 27 - August 2)
- Focus: Establish baseline, detect early issues
- Key: Fix cross-dependencies
- Decision: Continue or extend monitoring

### Week 2 (August 3 - August 9)
- Focus: Validate stability, build confidence
- Key: Prepare Phase 7 execution plan
- Decision: Set Phase 7 start date

### Final Review (August 10)
- Comprehensive stability assessment
- Go/No-Go decision for Phase 7
- Team readiness confirmation

## 🎯 Conclusion

Successful monitoring requires:
1. **Discipline**: Check metrics consistently
2. **Documentation**: Record everything
3. **Communication**: Keep team informed
4. **Patience**: Don't rush Phase 7

Remember: The goal is to ensure Phase 7 can proceed safely without risking production stability.

---
**Document Version**: 1.0  
**Last Updated**: 2025-07-27  
**Next Review**: July 29, 2025 (Daily)  
**Owner**: Operations Team