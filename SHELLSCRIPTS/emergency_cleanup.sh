#!/bin/bash
# emergency_cleanup.sh - When disk space is critical

echo "Running emergency cleanup..."
echo "Current disk usage:"
df -h .

# 1. Keep only 24 hours in main database
echo "Cleaning up database events older than 24 hours..."
curl -X POST http://localhost:5050/api/event-store/cleanup \
  -H "Content-Type: application/json" \
  -d '{"hours": 24}'

# 2. Delete all archives except last 7 days
echo "Removing old archives..."
find archives/ -name "*.gz" -mtime +7 -delete 2>/dev/null || echo "No old archives found"

# 3. Vacuum database
echo "Vacuuming database..."
sqlite3 game_events.db "VACUUM;" 2>/dev/null || echo "Database vacuum failed"

# 4. Show new disk usage
echo "New disk usage:"
df -h .

# 5. Show maintenance status
echo "Checking maintenance status..."
curl -s http://localhost:5050/api/maintenance/status | python3 -m json.tool

echo "Emergency cleanup complete"
