#!/bin/bash
# Clear telemetry data on EC2 server

echo "🧹 Clearing telemetry data on EC2..."

# SSH into EC2 and clear the database
ssh -i ~/.ssh/liap-tui-key-1755152170.pem ubuntu@34.233.7.20 << 'EOF'
  echo "📦 Using direct SQLite access (container doesn't have SQLite installed)"

  echo "📊 Current telemetry data:"
  sqlite3 liap-tui-data/telemetry_data.db "SELECT 'Events:', COUNT(*) FROM telemetry_events UNION SELECT 'Sessions:', COUNT(*) FROM telemetry_sessions;"

  echo -e "\n🗑️  Clearing telemetry data..."
  sqlite3 liap-tui-data/telemetry_data.db "DELETE FROM telemetry_events; DELETE FROM telemetry_sessions; DELETE FROM telemetry_stats;"

  echo -e "\n✅ Verification - should all be 0:"
  sqlite3 liap-tui-data/telemetry_data.db "SELECT 'Events:', COUNT(*) FROM telemetry_events UNION SELECT 'Sessions:', COUNT(*) FROM telemetry_sessions UNION SELECT 'Stats:', COUNT(*) FROM telemetry_stats;"

  echo -e "\n📁 Database file info:"
  ls -la /home/ubuntu/liap-tui-data/telemetry_data.db
EOF

echo -e "\n✨ Done! Telemetry data cleared on EC2."
