# Event Store Maintenance Guide

## Overview
The game stores all events in a SQLite database (`game_events.db`) for debugging, recovery, and analysis. While this doesn't impact memory usage, the database grows continuously and requires periodic maintenance.

## Current Status
- **Storage**: SQLite database (not in-memory)
- **Growth Rate**: Varies by usage (typical: 10-50MB per day with active games)
- **Cleanup**: Manual only - no automatic cleanup scheduled

## Maintenance Tasks

### Check Database Size
```bash
# Check current database size
ls -lh game_events.db

# Check event count
sqlite3 game_events.db "SELECT COUNT(*) FROM game_events;"

# Check oldest events
sqlite3 game_events.db "SELECT MIN(created_at), MAX(created_at) FROM game_events;"
```

### Manual Cleanup
Remove events older than 24 hours (default):
```bash
curl -X POST http://localhost:5050/api/event-store/cleanup
```

Remove events older than specific hours:
```bash
curl -X POST http://localhost:5050/api/event-store/cleanup \
  -H "Content-Type: application/json" \
  -d '{"hours": 168}'  # Keep last 7 days
```

### Recommended Cleanup Schedule
- **Development**: Daily cleanup (24 hours retention)
- **Production**: Weekly cleanup (7 days retention)
- **High-volume**: Daily cleanup with 3 days retention

## Monitoring Recommendations

### Set Up Alerts
Monitor these metrics:
- Database file size > 1GB
- Disk space < 10%
- Event count > 1 million

### Add to Cron
Example cron job for daily cleanup:
```bash
# Add to crontab
0 3 * * * curl -X POST http://localhost:5050/api/event-store/cleanup
```

## Future Improvements
Consider implementing:
1. Automatic background cleanup task
2. Configurable retention policy
3. Event archival to compressed files
4. Separate database for events vs game state

## Performance Notes
- SQLite handles millions of events efficiently with proper indexes
- Current indexes: room_id, sequence, timestamp, created_at
- Query performance remains good even with large datasets
- No memory impact - events stored on disk only
