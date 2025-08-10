# Log Maintenance Plan

## Executive Summary

This plan addresses the critical need for automated log maintenance to prevent:
- Unbounded database growth (currently 12MB and growing)
- Disk space exhaustion
- Performance degradation
- Manual maintenance burden

## Current State Analysis

### Problems
1. **No Automatic Cleanup**: Event store grows indefinitely
2. **Manual Process**: Requires admin to run cleanup endpoint
3. **No Monitoring**: No alerts for database size or growth rate
4. **No Retention Policy**: All events kept forever
5. **Single Database**: No archival or partitioning strategy

### Risk Assessment
- **High Risk**: Disk space exhaustion within 6-12 months
- **Medium Risk**: Query performance degradation at >1GB
- **Low Risk**: Current performance impact (well-indexed)

## Proposed Maintenance Strategy

### 1. Automated Cleanup System

#### Implementation Plan
```python
# backend/api/services/maintenance_scheduler.py
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class MaintenanceScheduler:
    def __init__(self, event_store):
        self.event_store = event_store
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        # Daily cleanup at 3 AM
        self.scheduler.add_job(
            self.cleanup_old_events,
            'cron',
            hour=3,
            minute=0,
            id='daily_cleanup'
        )
        
        # Hourly stats collection
        self.scheduler.add_job(
            self.collect_stats,
            'interval',
            hours=1,
            id='hourly_stats'
        )
        
        self.scheduler.start()
    
    async def cleanup_old_events(self):
        """Remove events older than retention period"""
        retention_days = int(os.getenv('EVENT_RETENTION_DAYS', '7'))
        await self.event_store.cleanup_old_events(
            hours=retention_days * 24
        )
```

#### Configuration
```bash
# Environment variables
EVENT_RETENTION_DAYS=7        # Keep last 7 days
EVENT_CLEANUP_ENABLED=true    # Enable automatic cleanup
EVENT_ARCHIVE_ENABLED=true    # Archive before deletion
EVENT_SIZE_LIMIT_GB=5         # Alert if DB exceeds this size
```

### 2. Tiered Storage Strategy

#### Active Database (0-7 days)
- **Storage**: SQLite `game_events.db`
- **Purpose**: Recent games, active debugging
- **Access**: Full query capabilities
- **Size Target**: <1GB

#### Archive Storage (7-30 days)
- **Storage**: Compressed SQLite files by week
- **Format**: `archive/game_events_2024_week_01.db.gz`
- **Purpose**: Historical analysis, dispute resolution
- **Access**: Restore to query

#### Cold Storage (30+ days)
- **Storage**: S3/Cloud storage
- **Format**: Parquet files for efficient analytics
- **Purpose**: Long-term analytics, compliance
- **Access**: Analytics tools only

### 3. Monitoring & Alerting

#### Database Metrics
```python
# backend/api/routes/monitoring.py
@router.get("/api/monitoring/database/metrics")
async def get_database_metrics():
    return {
        "size_mb": get_file_size_mb("game_events.db"),
        "event_count": await event_store.get_event_count(),
        "oldest_event": await event_store.get_oldest_event_date(),
        "growth_rate_mb_per_day": calculate_growth_rate(),
        "estimated_full_date": estimate_disk_full_date()
    }
```

#### Alert Thresholds
| Metric | Warning | Critical | Action |
|--------|---------|----------|---------|
| DB Size | >1GB | >5GB | Trigger cleanup |
| Growth Rate | >100MB/day | >500MB/day | Reduce retention |
| Disk Space | <20% | <10% | Emergency cleanup |
| Cleanup Failures | 1 | 3 | Manual intervention |

### 4. Implementation Phases

#### Phase 1: Basic Automation (Week 1-2)
- [ ] Add scheduled cleanup job
- [ ] Implement basic monitoring endpoint
- [ ] Add size-based alerts
- [ ] Test cleanup process

#### Phase 2: Archival System (Week 3-4)
- [ ] Implement archive before delete
- [ ] Add compressed storage format
- [ ] Create restoration utilities
- [ ] Document recovery procedures

#### Phase 3: Advanced Features (Week 5-6)
- [ ] Add Parquet export for analytics
- [ ] Implement partitioned tables by date
- [ ] Create analytics dashboard
- [ ] Add self-tuning retention

### 5. Operational Procedures

#### Daily Tasks (Automated)
```yaml
03:00: Run cleanup job
  - Archive events older than 7 days
  - Delete events older than 30 days
  - Vacuum database
  - Update statistics

Every Hour:
  - Collect database metrics
  - Check alert thresholds
  - Update monitoring dashboard
```

#### Weekly Tasks (Automated)
```yaml
Sunday 04:00: Deep maintenance
  - Rebuild indexes
  - Analyze query performance
  - Generate storage report
  - Compress weekly archives
```

#### Monthly Tasks (Manual Review)
- Review retention policy effectiveness
- Analyze storage costs
- Plan capacity upgrades
- Update documentation

### 6. Emergency Procedures

#### Disk Space Critical (<5%)
```bash
#!/bin/bash
# emergency_cleanup.sh

# 1. Stop non-critical services
systemctl stop game-analytics

# 2. Aggressive cleanup (keep only 24 hours)
curl -X POST http://localhost:5050/api/event-store/cleanup \
  -d '{"hours": 24}'

# 3. Vacuum database immediately
sqlite3 game_events.db "VACUUM;"

# 4. Archive to external storage
tar -czf /backup/emergency_archive_$(date +%Y%m%d).tar.gz game_events.db

# 5. Alert administrators
send_alert "Emergency cleanup performed - review storage plan"
```

### 7. Performance Optimization

#### Database Optimizations
```sql
-- Add partitioning by date (future migration)
CREATE TABLE game_events_2024_01 PARTITION OF game_events
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Optimize indexes for cleanup queries
CREATE INDEX idx_events_created_at ON game_events(created_at);
CREATE INDEX idx_events_room_date ON game_events(room_id, created_at);
```

#### Query Optimization
- Use date-based queries with index
- Implement query result caching
- Add read replicas for analytics

### 8. Cost-Benefit Analysis

#### Current Costs
- Manual maintenance time: ~2 hours/month
- Risk of outage: High
- Storage waste: ~90% (keeping all data)

#### Projected Benefits
- Automated maintenance: 0 hours/month
- Predictable storage: <5GB active
- Improved performance: 50% faster queries
- Reduced risk: Near-zero downtime

### 9. Success Metrics

#### KPIs to Track
1. **Database Size Stability**: Stay within 1-5GB range
2. **Cleanup Success Rate**: >99% successful runs
3. **Query Performance**: <50ms for recent events
4. **Storage Costs**: <$10/month for archives
5. **Incident Reduction**: Zero storage-related outages

### 10. Rollback Plan

If automated maintenance causes issues:
1. Disable cleanup job immediately
2. Restore from pre-cleanup backup
3. Revert to manual process
4. Investigate and fix issues
5. Re-enable with corrections

## Appendix: Implementation Code

### A. Cleanup Job
```python
async def automated_cleanup():
    try:
        # 1. Check current size
        size_mb = get_database_size_mb()
        logger.info(f"Database size: {size_mb}MB")
        
        # 2. Archive old events
        if ARCHIVE_ENABLED:
            await archive_old_events()
        
        # 3. Delete old events
        deleted = await event_store.cleanup_old_events(
            hours=RETENTION_DAYS * 24
        )
        logger.info(f"Deleted {deleted} events")
        
        # 4. Vacuum database
        await vacuum_database()
        
        # 5. Report success
        await send_maintenance_report(size_mb, deleted)
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        await send_alert("Cleanup job failed", str(e))
```

### B. Monitoring Dashboard
```python
@router.get("/api/monitoring/dashboard")
async def monitoring_dashboard():
    return {
        "database": {
            "size_mb": get_database_size_mb(),
            "growth_rate": calculate_growth_rate(),
            "health": assess_database_health()
        },
        "cleanup": {
            "last_run": get_last_cleanup_time(),
            "next_run": get_next_cleanup_time(),
            "success_rate": calculate_cleanup_success_rate()
        },
        "alerts": get_active_alerts()
    }
```

## Conclusion

This maintenance plan transforms log management from a manual, risky process to an automated, reliable system. Implementation should begin immediately with Phase 1 to prevent storage issues.