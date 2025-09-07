# Simple Log Maintenance Plan (No Cloud Required)

## Overview

A straightforward, local-only log maintenance strategy that requires zero external services and costs nothing.

## Strategy: Keep It Simple

### Storage Tiers (All Local)

#### Active Database (0-3 days)
- **File**: `game_events.db`
- **Size**: ~500MB maximum
- **Purpose**: Recent games, active debugging

#### Compressed Archives (3-30 days)
- **Location**: `archives/` directory
- **Format**: `game_events_2024_01_15.db.gz`
- **Size**: ~10-20MB per day compressed
- **Total**: ~300-600MB for a month

#### Old Archives (30+ days)
- **Action**: Delete automatically
- **Rationale**: Older than 30 days rarely needed

## Implementation

### 1. Simple Cleanup Script

```python
# backend/api/services/simple_maintenance.py
import os
import gzip
import shutil
import sqlite3
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class SimpleMaintenanceScheduler:
    def __init__(self, event_store):
        self.event_store = event_store
        self.scheduler = AsyncIOScheduler()

    def start(self):
        # Daily cleanup at 3 AM
        self.scheduler.add_job(
            self.daily_cleanup,
            'cron',
            hour=3,
            minute=0,
            id='daily_cleanup'
        )
        self.scheduler.start()

    async def daily_cleanup(self):
        """Simple daily maintenance"""
        try:
            # 1. Archive yesterday's events
            yesterday = datetime.now() - timedelta(days=1)
            await self.archive_day(yesterday)

            # 2. Remove events older than 3 days from main DB
            await self.event_store.cleanup_old_events(hours=72)

            # 3. Vacuum database to reclaim space
            conn = sqlite3.connect('game_events.db')
            conn.execute('VACUUM')
            conn.close()

            # 4. Delete archives older than 30 days
            self.cleanup_old_archives(days=30)

            # 5. Log summary
            self.log_maintenance_summary()

        except Exception as e:
            logger.error(f"Maintenance failed: {e}")

    async def archive_day(self, date):
        """Archive a single day's events"""
        date_str = date.strftime('%Y_%m_%d')
        temp_db = f"temp_{date_str}.db"
        archive_path = f"archives/game_events_{date_str}.db.gz"

        # Skip if already archived
        if os.path.exists(archive_path):
            return

        # Export day's events to temporary database
        conn_main = sqlite3.connect('game_events.db')
        conn_temp = sqlite3.connect(temp_db)

        # Copy schema
        conn_main.backup(conn_temp, pages=0)

        # Copy only that day's events
        query = """
        INSERT INTO game_events
        SELECT * FROM main.game_events
        WHERE date(created_at) = date(?)
        """
        conn_temp.execute(query, (date.isoformat(),))
        conn_temp.commit()

        # Close connections
        conn_main.close()
        conn_temp.close()

        # Compress
        with open(temp_db, 'rb') as f_in:
            with gzip.open(archive_path, 'wb', compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Cleanup
        os.remove(temp_db)

    def cleanup_old_archives(self, days):
        """Delete archives older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)

        for filename in os.listdir('archives'):
            if filename.startswith('game_events_') and filename.endswith('.db.gz'):
                # Parse date from filename
                date_str = filename[12:22]  # Extract YYYY_MM_DD
                try:
                    file_date = datetime.strptime(date_str, '%Y_%m_%d')
                    if file_date < cutoff:
                        os.remove(f"archives/{filename}")
                        logger.info(f"Deleted old archive: {filename}")
                except ValueError:
                    continue
```

### 2. Manual Backup (Optional)

```bash
#!/bin/bash
# backup_archives.sh - Run monthly or as needed

BACKUP_DIR="/path/to/backup/drive"
DATE=$(date +%Y%m)

# Create monthly backup
tar -czf "$BACKUP_DIR/liap_tui_archives_$DATE.tar.gz" archives/

# Or use rsync to another machine
# rsync -av archives/ user@backup-server:/backups/liap-tui/
```

### 3. Simple Monitoring

```python
# backend/api/routes/maintenance.py
@router.get("/api/maintenance/status")
async def maintenance_status():
    """Simple maintenance status endpoint"""

    # Calculate sizes
    db_size = os.path.getsize('game_events.db') / 1024 / 1024  # MB
    archive_count = len(glob.glob('archives/*.gz'))
    archive_size = sum(os.path.getsize(f) for f in glob.glob('archives/*.gz')) / 1024 / 1024

    # Get date range
    oldest_archive = min(glob.glob('archives/*.gz'), default=None)

    return {
        "database": {
            "size_mb": round(db_size, 2),
            "days_retained": 3
        },
        "archives": {
            "count": archive_count,
            "size_mb": round(archive_size, 2),
            "oldest": oldest_archive,
            "days_retained": 30
        },
        "total_size_mb": round(db_size + archive_size, 2),
        "last_cleanup": get_last_cleanup_time(),
        "next_cleanup": "Daily at 3:00 AM"
    }
```

### 4. Configuration

```bash
# .env - Simple configuration
LOG_RETENTION_ACTIVE_DAYS=3     # Days in main database
LOG_RETENTION_ARCHIVE_DAYS=30   # Days to keep archives
LOG_CLEANUP_ENABLED=true        # Enable automatic cleanup
LOG_CLEANUP_TIME="03:00"        # When to run cleanup
```

### 5. Emergency Cleanup

```bash
#!/bin/bash
# emergency_cleanup.sh - When disk space is critical

echo "Running emergency cleanup..."

# 1. Keep only 24 hours in main database
curl -X POST http://localhost:5050/api/event-store/cleanup \
  -d '{"hours": 24}'

# 2. Delete all archives except last 7 days
find archives/ -name "*.gz" -mtime +7 -delete

# 3. Vacuum database
sqlite3 game_events.db "VACUUM;"

echo "Emergency cleanup complete"
```

## Benefits of This Approach

### Pros
- **Zero Cost**: No cloud services needed
- **Simple**: Easy to understand and maintain
- **Reliable**: No network dependencies
- **Fast**: All operations are local
- **Sufficient**: 30 days of history is plenty

### Cons
- **No Offsite Backup**: Risk if server fails
- **Manual Disaster Recovery**: Need to backup manually
- **Limited History**: Only 30 days retained

## Storage Estimates

- **Active DB**: ~500MB (3 days)
- **Archives**: ~600MB (30 days)
- **Total**: ~1.1GB maximum
- **Growth**: Self-limiting due to rotation

## Getting Started

1. Create the archives directory:
   ```bash
   mkdir -p archives
   ```

2. Add the maintenance scheduler to your app startup:
   ```python
   # In your FastAPI startup
   maintenance = SimpleMaintenanceScheduler(event_store)
   maintenance.start()
   ```

3. Monitor the status:
   ```bash
   curl http://localhost:5050/api/maintenance/status
   ```

## Conclusion

This simple plan provides automated log maintenance without any external dependencies. It keeps your logs under control, maintains useful history, and costs nothing to operate. Perfect for a personal project or small deployment.
