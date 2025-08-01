# State Persistence Capacity Planning Guide

## Overview
This guide helps plan and scale the state persistence infrastructure based on game traffic, storage requirements, and performance targets.

## Current Metrics Baseline

### Game Volume Metrics
| Metric | Current | Peak | Growth Rate |
|--------|---------|------|-------------|
| Active Games (concurrent) | 1,000 | 5,000 | +20%/month |
| Games per Day | 10,000 | 50,000 | +15%/month |
| Average Game Duration | 15 min | 45 min | Stable |
| Players per Game | 3.5 | 8 | Stable |

### Storage Metrics
| Component | Size per Game | Retention | Total Size |
|-----------|---------------|-----------|------------|
| Game State | 2-5 KB | 7 days | ~350 GB |
| Snapshots | 5-10 KB | 7 days | ~700 GB |
| Event Log | 20-50 KB | 30 days | ~15 TB |
| Total | 27-65 KB | - | ~16 TB |

### Performance Requirements
| Operation | Current p99 | Target p99 | SLA |
|-----------|-------------|------------|-----|
| State Save | 25ms | < 50ms | 99.9% |
| State Load | 15ms | < 30ms | 99.9% |
| Snapshot Create | 50ms | < 100ms | 99% |
| Recovery | 200ms | < 500ms | 99% |

## Capacity Planning Models

### Storage Capacity Formula

```
Daily Storage = (Games/Day × Avg State Size × Retention Days)

Monthly Storage Growth = Daily Storage × Growth Rate × 30

Total Storage Needed = Current Storage + (Monthly Growth × Planning Horizon Months)

With 20% buffer: Total × 1.2
```

### Example Calculation (6-month horizon):
```
Current: 16 TB
Growth Rate: 20%/month
6-month projection: 16 × (1.20)^6 = 51.5 TB
With buffer: 51.5 × 1.2 = 62 TB needed
```

### Compute Capacity Formula

```
Operations/Second = (Active Games × Operations per Game per Second)

CPU Cores Needed = Operations/Second / Operations per Core per Second

Memory Needed = (Active Games × State Size) + Cache Size + Buffer
```

### Example Calculation:
```
Peak Active Games: 5,000
Ops per Game: 2/second (save + load)
Total Ops: 10,000/second

Assuming 1,000 ops/core/second:
CPU Cores: 10,000 / 1,000 = 10 cores
With 2x headroom: 20 cores

Memory: (5,000 × 10KB) + 2GB cache + 2GB buffer = 4.5 GB
With 2x headroom: 9 GB
```

## Storage Backend Sizing

### Redis Cluster

**Current Setup:**
- 3 master nodes, 3 replicas
- 16 GB RAM per node
- Total: 48 GB usable

**6-Month Projection:**
```
Active Game States: 5,000 × 10KB = 50 MB
Snapshots (last 5): 5,000 × 5 × 10KB = 250 MB
Cache Overhead: 20%
Total RAM Needed: 300 MB × 1.2 = 360 MB (well within limits)

Recommendation: Current setup sufficient
```

**Scaling Triggers:**
- Memory usage > 70%
- CPU usage > 60%
- Network throughput > 1 Gbps

### DynamoDB

**Current Setup:**
- On-demand billing
- No preset capacity

**6-Month Projection:**
```
Write Capacity Units (WCU):
- Game saves: 10,000 games × 2 saves/min = 333 WCU
- Snapshots: 10,000 games × 0.2 snapshots/min = 33 WCU
- Total: 366 WCU

Read Capacity Units (RCU):
- Game loads: 10,000 games × 1 load/min = 167 RCU
- Recovery: 100 games/hour = 2 RCU
- Total: 169 RCU

Monthly Cost: ~$200 (on-demand pricing)
```

**Scaling Recommendations:**
- Switch to provisioned capacity if > $500/month
- Enable auto-scaling with:
  - Target utilization: 70%
  - Min capacity: 100 RCU/WCU
  - Max capacity: 1000 RCU/WCU

## Network Capacity

### Bandwidth Requirements

```
Inbound: (Saves + Updates) × Avg Size
       = 10,000 ops/sec × 5 KB = 50 MB/s = 400 Mbps

Outbound: (Loads + Snapshots) × Avg Size  
        = 5,000 ops/sec × 10 KB = 50 MB/s = 400 Mbps

Total: 800 Mbps sustained, 1.6 Gbps peak
```

### Connection Pool Sizing

```
Connections Needed = (Concurrent Requests / Requests per Connection per Second)

Example:
- Concurrent Requests: 1,000
- Requests per Connection: 100/sec
- Connections Needed: 10
- With headroom: 20 connections
```

## Scaling Strategies

### Horizontal Scaling Triggers

**Add Redis Nodes When:**
- Memory usage > 70% consistently
- CPU usage > 60% consistently  
- Network > 1 Gbps per node
- Replica lag > 1 second

**Add Application Servers When:**
- State operation queue depth > 1000
- p99 latency > 2x target
- CPU usage > 70%

### Vertical Scaling Guidelines

**Upgrade Instance Size When:**
- Horizontal scaling becomes cost-inefficient
- Single-node operations required
- Memory requirements exceed largest instance

### Caching Strategy

**Cache Sizing Formula:**
```
Cache Size = (Hot Games × State Size × Cache Copies)

Hot Games = Active Games × 0.2 (80/20 rule)
Cache Copies = 2 (primary + backup)

Example: 1,000 × 10KB × 2 = 20 MB minimum cache
Recommended: 10x minimum = 200 MB
```

## Cost Optimization

### Storage Tiering

**Hot Tier (Redis/DynamoDB):**
- Active games (< 1 hour old)
- Recent completions (< 24 hours)
- Cost: $0.10/GB/month

**Warm Tier (S3 Standard):**
- Completed games (1-7 days)
- Compressed snapshots
- Cost: $0.023/GB/month

**Cold Tier (S3 Glacier):**
- Archive (> 7 days)
- Compliance retention
- Cost: $0.004/GB/month

### Example Savings:
```
All in Hot Tier: 62 TB × $0.10 = $6,200/month
With Tiering:
- Hot: 1 TB × $0.10 = $100
- Warm: 10 TB × $0.023 = $230  
- Cold: 51 TB × $0.004 = $204
Total: $534/month (91% savings)
```

## Monitoring and Alerting Thresholds

### Capacity Alerts

| Resource | Warning | Critical | Action |
|----------|---------|----------|--------|
| Storage Usage | 70% | 85% | Add nodes |
| Memory Usage | 70% | 85% | Scale up |
| CPU Usage | 60% | 80% | Add replicas |
| Connection Pool | 70% | 90% | Increase pool |
| Network Bandwidth | 60% | 80% | Add nodes |

### Growth Tracking

**Weekly Review Metrics:**
- Game count growth rate
- Storage growth rate
- Peak concurrent games
- 95th percentile sizes

**Monthly Capacity Review:**
- Update growth projections
- Review scaling triggers
- Plan infrastructure changes
- Budget impact analysis

## Disaster Recovery Planning

### Backup Storage Requirements

```
Full Backup Size = Active Storage × Compression Ratio
                = 16 TB × 0.3 = 4.8 TB

Incremental Daily = Daily Changes × Compression
                  = 500 GB × 0.3 = 150 GB

Monthly Backup Storage = Full + (30 × Incremental)
                      = 4.8 TB + 4.5 TB = 9.3 TB
```

### Recovery Time Objectives

| Scenario | RTO | RPO | Resources Needed |
|----------|-----|-----|------------------|
| Node Failure | 30s | 0 | Automatic failover |
| Region Failure | 5m | 1m | Cross-region replica |
| Complete Loss | 1h | 1h | Restore from backup |
| Corruption | 4h | 1h | Point-in-time recovery |

## Capacity Planning Checklist

### Monthly Tasks
- [ ] Review growth metrics vs projections
- [ ] Update capacity model with actuals
- [ ] Check scaling trigger thresholds
- [ ] Review cost optimization opportunities
- [ ] Update disaster recovery requirements

### Quarterly Tasks
- [ ] Load test with projected capacity
- [ ] Review and update scaling playbooks
- [ ] Evaluate new storage technologies
- [ ] Update budget projections
- [ ] Plan infrastructure changes

### Annual Tasks
- [ ] Full capacity model review
- [ ] Technology stack evaluation
- [ ] Disaster recovery drill
- [ ] Cost optimization audit
- [ ] Multi-year growth planning

## Tooling and Automation

### Capacity Monitoring Scripts

```bash
# Check current usage
python scripts/capacity_report.py --current

# Project future needs
python scripts/capacity_projection.py --months 6

# Generate scaling recommendations
python scripts/scaling_advisor.py --threshold 70

# Cost analysis
python scripts/cost_analyzer.py --optimize
```

### Auto-Scaling Configuration

```yaml
# Redis auto-scaling
redis_autoscaling:
  enabled: true
  min_nodes: 3
  max_nodes: 10
  target_memory_usage: 70
  scale_up_cooldown: 300
  scale_down_cooldown: 900

# DynamoDB auto-scaling  
dynamodb_autoscaling:
  enabled: true
  min_rcu: 100
  max_rcu: 10000
  min_wcu: 100
  max_wcu: 10000
  target_utilization: 70
```

## Appendix: Reference Architectures

### Small Scale (< 1K concurrent games)
- Single Redis instance with replica
- Local SSD storage
- No tiering needed
- Cost: ~$200/month

### Medium Scale (1K-10K concurrent games)
- Redis cluster (3 masters, 3 replicas)
- DynamoDB with auto-scaling
- S3 for backups
- Cost: ~$2,000/month

### Large Scale (10K+ concurrent games)
- Multi-region Redis clusters
- DynamoDB global tables
- Tiered storage with lifecycle
- CDN for read caching
- Cost: ~$20,000/month

### Enterprise Scale (100K+ concurrent games)
- Custom sharding solution
- Multiple storage backends
- Global distribution
- Dedicated infrastructure team
- Cost: > $100,000/month