# Production Operations Guide

This guide covers production monitoring, maintenance, and operational procedures for Liap Tui.

## Table of Contents
1. [Health Monitoring](#health-monitoring)
2. [System Statistics](#system-statistics)
3. [Event Store & Recovery](#event-store--recovery)
4. [Logging](#logging)
5. [Performance Monitoring](#performance-monitoring)
6. [Troubleshooting Production Issues](#troubleshooting-production-issues)

## Health Monitoring

The application includes enterprise-grade monitoring and observability features.

### Health Check Endpoints

#### Basic Health Check
Used by load balancers to verify service availability:
```bash
curl http://localhost:5050/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Detailed Health Information
Provides comprehensive system health metrics:
```bash
curl http://localhost:5050/api/health/detailed
```

Response includes:
- Service uptime
- Resource usage (CPU, memory)
- Active connections
- Recent error rates
- Component health status

#### Prometheus-Compatible Metrics
For integration with monitoring systems:
```bash
curl http://localhost:5050/api/health/metrics
```

Returns metrics in Prometheus format:
```
# HELP active_connections Number of active WebSocket connections
# TYPE active_connections gauge
active_connections 42

# HELP game_rooms_active Number of active game rooms
# TYPE game_rooms_active gauge
game_rooms_active 12
```

## System Statistics

### Complete System Overview
```bash
curl http://localhost:5050/api/system/stats
```

Provides:
- Server resource usage
- Connection statistics
- Game room metrics
- Performance indicators
- Error summaries

### Recovery System Status
```bash
curl http://localhost:5050/api/recovery/status
```

Shows:
- Auto-recovery configuration
- Recent recovery actions
- Failed recovery attempts
- System stability score

### Room and Game Statistics
```bash
curl http://localhost:5050/api/debug/room-stats
```

Detailed room information:
- Active rooms and their states
- Player counts and bot status
- Game phase distribution
- Average game duration

## Event Store & Recovery

### View Game Events
Analyze game history for debugging or auditing:
```bash
curl http://localhost:5050/api/rooms/{room_id}/events
```

Returns chronological event list:
- Player actions
- State transitions
- System events
- Error occurrences

### Reconstructed Game State
Get current game state from event history:
```bash
curl http://localhost:5050/api/rooms/{room_id}/state
```

Useful for:
- Debugging state inconsistencies
- Recovering from crashes
- Analyzing game progression

### Event Store Statistics
```bash
curl http://localhost:5050/api/event-store/stats
```

Metrics include:
- Total events stored
- Events per game type
- Storage usage
- Compression ratios

## Logging

### Log Structure
All system events are logged in structured JSON format with correlation IDs.

#### Log Categories

**Game Events**
- Phase transitions
- Player actions (declare, play, redeal decisions)
- Scoring calculations
- Win conditions

**WebSocket Activity**
- Connection establishment/termination
- Message delivery confirmations
- Reconnection attempts
- Protocol errors

**Performance Metrics**
- Operation timing
- Resource usage spikes
- Queue depths
- Latency measurements

**Security Events**
- Authentication attempts
- Rate limit violations
- Suspicious patterns
- Access denials

**Error Tracking**
- Full stack traces
- Request context
- User session info
- Recovery attempts

### Log Format Example
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "correlation_id": "abc123-def456",
  "category": "game_event",
  "event": "phase_change",
  "room_id": "ROOM_XYZ",
  "details": {
    "from_phase": "DECLARATION",
    "to_phase": "TURN",
    "player_count": 4,
    "duration_ms": 150
  }
}
```

### Log Aggregation
Logs can be aggregated using standard tools:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- CloudWatch Logs (AWS)
- Splunk
- Datadog

## Performance Monitoring

### Key Metrics to Monitor

**Response Times**
- WebSocket message round-trip time
- API endpoint latency
- Database query duration

**Throughput**
- Messages per second
- Concurrent games
- Active connections

**Resource Usage**
- CPU utilization
- Memory consumption
- Network bandwidth
- Disk I/O

**Game Metrics**
- Average game duration
- Actions per minute
- Bot vs human player ratio
- Popular game times

### Performance Thresholds

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| WebSocket Latency | <50ms | 50-200ms | >200ms |
| CPU Usage | <60% | 60-80% | >80% |
| Memory Usage | <70% | 70-85% | >85% |
| Error Rate | <0.1% | 0.1-1% | >1% |

## Troubleshooting Production Issues

### Common Issues and Solutions

#### High Memory Usage
**Symptoms**: Increasing memory consumption over time

**Diagnosis**:
1. Check for memory leaks in game state
2. Review connection cleanup
3. Analyze event store size

**Solutions**:
- Implement connection limits
- Add memory-based auto-scaling
- Configure event store pruning

#### WebSocket Connection Drops
**Symptoms**: Frequent disconnections, reconnection storms

**Diagnosis**:
1. Check network infrastructure
2. Review proxy/load balancer timeouts
3. Analyze client-side errors

**Solutions**:
- Adjust keepalive intervals
- Implement connection pooling
- Add retry backoff logic

#### Slow Game Performance
**Symptoms**: High latency, delayed responses

**Diagnosis**:
1. Profile hot code paths
2. Check database query performance
3. Review broadcast efficiency

**Solutions**:
- Optimize state machine transitions
- Implement caching layer
- Batch message broadcasts

### Emergency Procedures

#### Service Degradation
1. Enable rate limiting
2. Disable non-essential features
3. Scale horizontally
4. Monitor recovery

#### Data Corruption
1. Stop write operations
2. Backup current state
3. Restore from event store
4. Validate data integrity

#### Complete Outage
1. Check infrastructure health
2. Review recent deployments
3. Rollback if necessary
4. Communicate with users

### Monitoring Dashboards

Recommended dashboard panels:
1. **System Overview**: Health, uptime, active games
2. **Performance**: Latency, throughput, errors
3. **Resources**: CPU, memory, network, disk
4. **Game Analytics**: Popular times, game duration, win rates
5. **Alerts**: Critical issues, anomalies, trends

### Alerting Rules

Configure alerts for:
- Health check failures (>3 consecutive)
- Error rate spike (>1% for 5 minutes)
- Resource exhaustion (>90% for 10 minutes)
- Connection limit reached
- Recovery system activation

## Maintenance Tasks

### Regular Maintenance

**Daily**
- Review error logs
- Check resource trends
- Verify backup completion

**Weekly**
- Analyze performance metrics
- Review security events
- Update monitoring thresholds

**Monthly**
- Prune old event data
- Optimize database indices
- Review capacity planning
- Update documentation

### Deployment Procedures

**Pre-deployment**
1. Run full test suite
2. Check resource availability
3. Notify users of maintenance
4. Prepare rollback plan

**Deployment**
1. Deploy to staging
2. Run smoke tests
3. Deploy to production (rolling)
4. Monitor error rates

**Post-deployment**
1. Verify all services healthy
2. Check performance metrics
3. Monitor user feedback
4. Document any issues

## Security Monitoring

### Security Metrics
- Failed authentication attempts
- Rate limit violations
- Unusual traffic patterns
- Geographic anomalies

### Security Response
1. **Detection**: Automated alerts on suspicious activity
2. **Investigation**: Review logs and patterns
3. **Mitigation**: Block IPs, adjust rate limits
4. **Prevention**: Update rules and monitoring

## Capacity Planning

### Scaling Triggers
- CPU sustained >70%
- Memory usage >80%
- Queue depth >1000
- Response time >200ms

### Scaling Strategy
1. **Horizontal**: Add more containers
2. **Vertical**: Increase container resources
3. **Geographic**: Deploy to multiple regions
4. **Caching**: Add Redis/CDN layers

## Compliance and Auditing

### Audit Requirements
- Game fairness verification
- User action logging
- System access tracking
- Data retention policies

### Compliance Checks
- Regular security scans
- Dependency updates
- License compliance
- Privacy regulations

---

For development and testing procedures, see the main [README](README.md).
For debugging specific issues, consult the [Debugging Guide](docs/06-tutorials/DEBUGGING_GUIDE.md).