# Log Maintenance Plan - AWS Free Tier Edition

## Executive Summary

This plan provides a cost-effective log maintenance strategy that stays within AWS Free Tier limits while preventing database growth issues.

## AWS Free Tier Constraints

### Relevant Limits
- **S3 Storage**: 5GB free for 12 months
- **S3 Requests**: 20,000 GET / 2,000 PUT per month
- **EC2**: 750 hours t2.micro (if using)
- **CloudWatch**: 10 custom metrics, 5GB logs
- **Lambda**: 1M requests, 400,000 GB-seconds (if needed)

### Strategy: Maximize Free Resources
- Use S3 sparingly for critical archives only
- Compress aggressively before uploading
- Local rotation for most logs
- Minimal CloudWatch usage

## Revised Maintenance Strategy

### 1. Local-First Storage Tiers

#### Active Database (0-3 days)
- **Storage**: SQLite `game_events.db`
- **Location**: Local disk
- **Size Target**: <500MB
- **Rationale**: Reduced from 7 days to minimize size

#### Local Archives (3-14 days)
- **Storage**: Compressed SQLite on local disk
- **Format**: `archives/game_events_YYYY_MM_DD.db.gz`
- **Compression**: gzip -9 (best compression)
- **Size**: ~10-20MB per day compressed
- **Total**: ~200MB for 2 weeks

#### S3 Monthly Backups (14+ days)
- **Storage**: S3 Standard (within 5GB free tier)
- **Format**: Monthly tar.gz archives
- **Example**: `game_events_2024_01.tar.gz`
- **Size**: ~300-500MB per month
- **Retention**: 6 months (fitting in 5GB)

### 2. Automated Cleanup System

```python
# backend/api/services/free_tier_maintenance.py
import asyncio
import gzip
import shutil
from datetime import datetime, timedelta
import boto3
from botocore.config import Config

class FreeTierMaintenanceScheduler:
    def __init__(self, event_store):
        self.event_store = event_store
        self.scheduler = AsyncIOScheduler()
        # Use minimal S3 configuration
        self.s3_client = boto3.client(
            's3',
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 2}  # Minimize requests
            )
        )
        
    def start(self):
        # Daily cleanup at 3 AM
        self.scheduler.add_job(
            self.daily_maintenance,
            'cron',
            hour=3,
            minute=0
        )
        
        # Monthly S3 backup on the 1st at 4 AM
        self.scheduler.add_job(
            self.monthly_s3_backup,
            'cron',
            day=1,
            hour=4,
            minute=0
        )
        
        self.scheduler.start()
    
    async def daily_maintenance(self):
        """Daily local maintenance within free tier"""
        try:
            # 1. Archive events older than 3 days locally
            await self.archive_to_local(days_old=3)
            
            # 2. Delete from main DB
            await self.event_store.cleanup_old_events(hours=72)
            
            # 3. Vacuum database
            await self.vacuum_database()
            
            # 4. Clean up local archives older than 14 days
            self.cleanup_local_archives(days=14)
            
            # 5. Log metrics (locally, not CloudWatch)
            self.log_local_metrics()
            
        except Exception as e:
            # Log error locally, avoid CloudWatch costs
            logger.error(f"Maintenance failed: {e}")
    
    async def archive_to_local(self, days_old):
        """Archive to compressed local files"""
        date = datetime.now() - timedelta(days=days_old)
        archive_name = f"archives/game_events_{date.strftime('%Y_%m_%d')}.db"
        
        # Export day's events to separate SQLite file
        await self.export_events_by_date(date, archive_name)
        
        # Compress with maximum compression
        with open(archive_name, 'rb') as f_in:
            with gzip.open(f"{archive_name}.gz", 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        os.remove(archive_name)
    
    async def monthly_s3_backup(self):
        """Monthly backup to S3 (within free tier)"""
        last_month = datetime.now() - timedelta(days=30)
        month_str = last_month.strftime('%Y_%m')
        
        # Create monthly archive from local files
        archive_path = f"/tmp/game_events_{month_str}.tar.gz"
        self.create_monthly_archive(last_month, archive_path)
        
        # Upload to S3 (minimize PUT requests)
        try:
            file_size = os.path.getsize(archive_path)
            if file_size > 500_000_000:  # 500MB limit per archive
                logger.warning(f"Archive too large: {file_size}")
                return
                
            self.s3_client.upload_file(
                archive_path,
                'liap-tui-archives',  # Your bucket name
                f"monthly/game_events_{month_str}.tar.gz",
                ExtraArgs={
                    'StorageClass': 'STANDARD',  # Free tier
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            # Clean up old S3 files (keep only 6 months)
            await self.cleanup_old_s3_files(months=6)
            
        finally:
            os.remove(archive_path)
```

### 3. Local Monitoring (No CloudWatch Costs)

```python
# backend/api/services/local_monitoring.py
class LocalMetricsCollector:
    """Collect metrics locally without CloudWatch costs"""
    
    def __init__(self):
        self.metrics_file = "logs/maintenance_metrics.json"
    
    def record_metrics(self):
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "database_size_mb": self.get_database_size_mb(),
            "archive_count": len(glob.glob("archives/*.gz")),
            "total_archive_size_mb": self.get_archive_size_mb(),
            "oldest_event_days": self.get_oldest_event_age_days()
        }
        
        # Append to local metrics file
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')
        
        # Check thresholds
        self.check_alerts(metrics)
    
    def check_alerts(self, metrics):
        # Simple local alerting
        if metrics["database_size_mb"] > 500:
            self.create_alert("Database size exceeds 500MB")
        
        if metrics["total_archive_size_mb"] > 2000:
            self.create_alert("Local archives exceed 2GB")
```

### 4. Free Tier Monitoring Dashboard

```python
@router.get("/api/monitoring/free-tier-status")
async def free_tier_status():
    """Monitor usage within free tier limits"""
    return {
        "local_storage": {
            "database_size_mb": get_database_size_mb(),
            "archive_size_mb": get_local_archive_size_mb(),
            "total_used_mb": get_total_local_storage_mb(),
            "days_retained_active": 3,
            "days_retained_local": 14
        },
        "s3_usage": {
            "estimated_monthly_size_mb": estimate_monthly_archive_size(),
            "months_stored": 6,
            "total_s3_usage_gb": get_s3_usage_gb(),
            "free_tier_remaining_gb": max(0, 5 - get_s3_usage_gb()),
            "put_requests_this_month": 1,  # Only monthly uploads
            "get_requests_this_month": get_s3_get_count()
        },
        "cost_estimate": {
            "current_month": "$0.00",
            "projected_annual": "$0.00"
        }
    }
```

### 5. Emergency Procedures (Free Tier Safe)

```bash
#!/bin/bash
# free_tier_emergency_cleanup.sh

# 1. Aggressive local cleanup (keep only 24 hours)
echo "Emergency cleanup - preserving free tier limits"

# 2. Delete all local archives
rm -f archives/*.gz

# 3. Cleanup main database
curl -X POST http://localhost:5050/api/event-store/cleanup \
  -d '{"hours": 24}'

# 4. Vacuum immediately
sqlite3 game_events.db "VACUUM;"

# 5. DO NOT upload to S3 (save requests)
echo "Skipping S3 upload to preserve free tier"

# 6. Create local alert
echo "$(date): Emergency cleanup performed" >> logs/alerts.log
```

### 6. Configuration for Free Tier

```bash
# .env configuration
EVENT_RETENTION_DAYS=3           # Reduced from 7
LOCAL_ARCHIVE_DAYS=14           # Keep 2 weeks locally
S3_BACKUP_ENABLED=true          # Monthly only
S3_RETENTION_MONTHS=6           # Keep 6 months in S3
S3_BUCKET_NAME=liap-tui-archives
MAX_ARCHIVE_SIZE_MB=500         # Per monthly archive
CLOUDWATCH_ENABLED=false        # Avoid costs
LOCAL_MONITORING_ENABLED=true   # Use local metrics
```

### 7. Storage Calculations

#### Monthly Storage Estimate
- **Active DB**: ~500MB (3 days)
- **Local Archives**: ~200MB (14 days compressed)
- **S3 Monthly**: ~400MB per month
- **S3 Total**: ~2.4GB (6 months)
- **Total S3 Usage**: Well within 5GB free tier

#### Request Calculations
- **S3 PUT**: 1 per month (monthly backup)
- **S3 GET**: ~10 per month (occasional recovery)
- **Total**: Well within 2,000 PUT / 20,000 GET limits

### 8. Cost Optimization Tips

1. **Compress Everything**: Use gzip -9 for maximum compression
2. **Batch Operations**: One monthly S3 upload instead of daily
3. **Local First**: Keep recent data local, S3 for disaster recovery
4. **No CloudWatch**: Use local monitoring and alerts
5. **Lifecycle Rules**: Set S3 lifecycle to auto-delete after 6 months

### 9. Implementation Priority

#### Week 1: Local Automation
- [ ] Implement 3-day retention
- [ ] Add local archival with compression
- [ ] Create local monitoring

#### Week 2: S3 Integration
- [ ] Set up S3 bucket with lifecycle rules
- [ ] Implement monthly backup job
- [ ] Test restore procedures

#### Week 3: Monitoring
- [ ] Create free tier usage dashboard
- [ ] Add local alerting system
- [ ] Document procedures

### 10. Limitations & Trade-offs

#### What We Sacrifice
- Shorter active retention (3 vs 7 days)
- No real-time CloudWatch monitoring
- Limited S3 backup frequency
- Manual monitoring checks

#### What We Gain
- **$0 monthly cost**
- Automated maintenance
- 6 months of backup history
- Protection against data loss

## Conclusion

This plan provides robust log maintenance while staying completely within AWS Free Tier limits. The key is aggressive local management with S3 used only for disaster recovery backups.