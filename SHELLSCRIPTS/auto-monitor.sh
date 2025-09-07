#\!/bin/bash
# Automated monitoring with alerts

EC2_HOST="34.233.7.20"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=90
ALERT_THRESHOLD_DISK=85

check_health() {
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${EC2_HOST}/api/health)
    if [ "$STATUS" \!= "200" ]; then
        echo "$(date): ALERT - Game health check failed (HTTP $STATUS)"
        return 1
    fi
    return 0
}

check_resources() {
    # This would SSH and check resources
    # For now, just check if we can reach the server
    curl -s -m 5 http://${EC2_HOST} > /dev/null
    return $?
}

# Create log file
LOG_FILE="monitoring_$(date +%Y%m%d).log"

echo "Starting automated monitoring of ${EC2_HOST}"  < /dev/null |  tee -a $LOG_FILE
echo "Alerts will be logged to: $LOG_FILE"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    echo -n "$(date '+%H:%M:%S') - "

    if check_health; then
        echo -n "Health: OK | "
    else
        echo -n "Health: FAIL | "
    fi

    if check_resources; then
        echo "Server: OK"
    else
        echo "Server: UNREACHABLE"
    fi

    sleep 60  # Check every minute
done
