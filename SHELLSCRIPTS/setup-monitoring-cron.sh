#!/bin/bash

# Setup monitoring cron job for Liap Tui EC2

echo "🕐 Setting up daily EC2 monitoring cron job..."

# Define the cron job
MONITOR_SCRIPT="/Users/nrw/python/tui-project/liap-tui/monitor-ec2.sh"
LOG_DIR="/Users/nrw/liap-tui-monitoring-logs"
CRON_JOB="0 9 * * * ${MONITOR_SCRIPT} > ${LOG_DIR}/ec2-monitor-\$(date +\\%Y\\%m\\%d).log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "monitor-ec2.sh"; then
    echo "⚠️  Monitoring cron job already exists:"
    crontab -l | grep "monitor-ec2.sh"
    echo ""
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled"
        exit 1
    fi
    # Remove existing job
    crontab -l | grep -v "monitor-ec2.sh" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "📋 Current crontab:"
crontab -l | grep "monitor-ec2.sh"
echo ""
echo "📁 Logs will be saved to: ${LOG_DIR}"
echo "⏰ Monitoring will run daily at 9:00 AM"
echo ""
echo "💡 To view logs:"
echo "   ls -la ${LOG_DIR}"
echo ""
echo "💡 To manually run monitoring now:"
echo "   ${MONITOR_SCRIPT}"
echo ""
echo "💡 To remove the cron job later:"
echo "   crontab -e  # Then delete the line with monitor-ec2.sh"