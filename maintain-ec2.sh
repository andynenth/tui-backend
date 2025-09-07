#!/bin/bash
# EC2 Maintenance Script - Common maintenance operations for Liap Tui

set -e

# Configuration
EC2_HOST="${EC2_HOST:-54.250.35.226}"
EC2_USER="${EC2_USER:-ubuntu}"
KEY_PATH="${KEY_PATH:-~/.ssh/liap-tui-tokyo-key.pem}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if EC2_HOST is configured
if [ "$EC2_HOST" = "your-ec2-ip-here" ]; then
    echo -e "${RED}❌ Error: Please set EC2_HOST environment variable or edit this script${NC}"
    echo "Example: EC2_HOST=54.123.45.67 ./maintain-ec2.sh"
    exit 1
fi

# Function to run remote command
run_remote() {
    ssh -o ConnectTimeout=5 -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST} "$1"
}

# Function to show menu
show_menu() {
    echo -e "\n${BLUE}🔧 Liap Tui EC2 Maintenance Menu${NC}"
    echo -e "${BLUE}================================${NC}"
    echo -e "Host: ${EC2_HOST}"
    echo ""
    echo "1) View container status"
    echo "2) Restart game container"
    echo "3) View recent logs (last 50 lines)"
    echo "4) Create manual backup"
    echo "5) Download latest backup"
    echo "6) Clean up old backups (keep last 7)"
    echo "7) Update container to latest image"
    echo "8) View database statistics"
    echo "9) Check disk usage"
    echo "10) Restart Docker service"
    echo "11) View active game rooms"
    echo "12) Clean up completed games (>30 days)"
    echo "13) Export game statistics"
    echo "14) View system resources"
    echo "15) Emergency container rebuild"
    echo "0) Exit"
    echo ""
}

# Function to pause
pause() {
    echo -e "\n${YELLOW}Press Enter to continue...${NC}"
    read
}

# Main loop
while true; do
    show_menu
    read -p "Select an option: " choice

    case $choice in
        1) # View container status
            echo -e "\n${BLUE}📊 Container Status${NC}"
            run_remote "docker ps -a --filter name=liap-tui"
            echo -e "\n${BLUE}Container Stats:${NC}"
            run_remote "docker stats --no-stream liap-tui-game" || echo "Container not running"
            pause
            ;;

        2) # Restart container
            echo -e "\n${YELLOW}🔄 Restarting game container...${NC}"
            run_remote "cd /home/ubuntu && docker-compose restart"
            echo -e "${GREEN}✅ Container restarted${NC}"

            # Wait for health check
            echo -e "${YELLOW}Waiting for health check...${NC}"
            sleep 5
            if curl -f http://${EC2_HOST}/api/health > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Health check passed${NC}"
            else
                echo -e "${RED}❌ Health check failed - check logs${NC}"
            fi
            pause
            ;;

        3) # View logs
            echo -e "\n${BLUE}📋 Recent Container Logs${NC}"
            run_remote "docker logs --tail 50 liap-tui-game"
            pause
            ;;

        4) # Create backup
            echo -e "\n${YELLOW}💾 Creating manual backup...${NC}"
            run_remote "/home/ubuntu/backup-game.sh"
            echo -e "${GREEN}✅ Backup created${NC}"

            # Show backup info
            LATEST=$(run_remote "ls -t /home/ubuntu/backups/game_backup_*.tar.gz | head -1")
            if [ ! -z "$LATEST" ]; then
                SIZE=$(run_remote "ls -lh $LATEST | awk '{print \$5}'")
                echo -e "Latest backup: $(basename $LATEST) (${SIZE})"
            fi
            pause
            ;;

        5) # Download backup
            echo -e "\n${YELLOW}📥 Downloading latest backup...${NC}"

            # Get latest backup
            LATEST=$(run_remote "ls -t /home/ubuntu/backups/game_backup_*.tar.gz 2>/dev/null | head -1")
            if [ -z "$LATEST" ]; then
                echo -e "${RED}❌ No backups found${NC}"
            else
                FILENAME=$(basename "$LATEST")
                mkdir -p ./backups
                scp -i ${KEY_PATH} ${EC2_USER}@${EC2_HOST}:${LATEST} ./backups/
                echo -e "${GREEN}✅ Downloaded: ./backups/${FILENAME}${NC}"
                ls -lh ./backups/${FILENAME}
            fi
            pause
            ;;

        6) # Clean up old backups
            echo -e "\n${YELLOW}🧹 Cleaning up old backups...${NC}"

            # Show current backups
            echo -e "\nCurrent backups:"
            run_remote "ls -lh /home/ubuntu/backups/game_backup_*.tar.gz 2>/dev/null | awk '{print \$9, \$5}'" || echo "No backups found"

            # Clean up
            run_remote "cd /home/ubuntu/backups && ls -t game_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -v"

            echo -e "\n${GREEN}✅ Cleanup complete${NC}"
            echo -e "\nRemaining backups:"
            run_remote "ls -lh /home/ubuntu/backups/game_backup_*.tar.gz 2>/dev/null | awk '{print \$9, \$5}'" || echo "No backups found"
            pause
            ;;

        7) # Update container
            echo -e "\n${YELLOW}🔄 Updating container to latest image...${NC}"
            echo -e "${RED}⚠️  This will restart the game server!${NC}"
            read -p "Continue? (y/N): " confirm

            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                # Create backup first
                echo -e "${YELLOW}Creating backup before update...${NC}"
                run_remote "/home/ubuntu/backup-game.sh"

                # Pull latest image and restart
                echo -e "${YELLOW}Pulling latest image...${NC}"
                run_remote "cd /home/ubuntu && docker-compose pull"

                echo -e "${YELLOW}Restarting with new image...${NC}"
                run_remote "cd /home/ubuntu && docker-compose down && docker-compose up -d"

                echo -e "${GREEN}✅ Update complete${NC}"
            else
                echo -e "${YELLOW}Update cancelled${NC}"
            fi
            pause
            ;;

        8) # Database statistics
            echo -e "\n${BLUE}📊 Database Statistics${NC}"

            # Database file info
            run_remote "ls -lh /home/ubuntu/liap-tui-data/game_events.db 2>/dev/null" || echo "Database not found"

            # Query statistics
            echo -e "\n${BLUE}Game Statistics:${NC}"
            run_remote "docker exec liap-tui-game sqlite3 /app/data/game_events.db \"
                SELECT 'Total Games:', COUNT(*) FROM game_summaries;
                SELECT 'Active Games:', COUNT(*) FROM game_summaries WHERE completed_at IS NULL;
                SELECT 'Completed Games:', COUNT(*) FROM game_summaries WHERE completed_at IS NOT NULL;
                SELECT 'Games Today:', COUNT(*) FROM game_summaries WHERE datetime(started_at, 'unixepoch') > datetime('now', '-1 day');
                SELECT 'Total Rounds:', COUNT(*) FROM round_snapshots;
            \" 2>/dev/null" || echo "Could not query database"
            pause
            ;;

        9) # Disk usage
            echo -e "\n${BLUE}💾 Disk Usage${NC}"
            run_remote "df -h"
            echo -e "\n${BLUE}Directory Sizes:${NC}"
            run_remote "du -sh /home/ubuntu/liap-tui-data /home/ubuntu/backups /home/ubuntu/logs 2>/dev/null"

            # Docker cleanup suggestion
            DOCKER_USAGE=$(run_remote "docker system df --format 'table {{.Type}}\t{{.Size}}\t{{.Reclaimable}}'" 2>/dev/null || echo "")
            if [ ! -z "$DOCKER_USAGE" ]; then
                echo -e "\n${BLUE}Docker Disk Usage:${NC}"
                echo "$DOCKER_USAGE"

                echo -e "\n${YELLOW}💡 To free up space, you can run:${NC}"
                echo "   docker system prune -a"
            fi
            pause
            ;;

        10) # Restart Docker
            echo -e "\n${RED}⚠️  This will restart Docker and all containers!${NC}"
            read -p "Continue? (y/N): " confirm

            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                echo -e "${YELLOW}Restarting Docker service...${NC}"
                run_remote "sudo systemctl restart docker"
                sleep 5

                echo -e "${YELLOW}Starting game container...${NC}"
                run_remote "cd /home/ubuntu && docker-compose up -d"

                echo -e "${GREEN}✅ Docker restarted${NC}"
            else
                echo -e "${YELLOW}Restart cancelled${NC}"
            fi
            pause
            ;;

        11) # View active rooms
            echo -e "\n${BLUE}🎮 Active Game Rooms${NC}"
            run_remote "docker exec liap-tui-game sqlite3 -header -column /app/data/game_events.db \"
                SELECT
                    room_id,
                    json_extract(player_names, '$') as players,
                    current_round,
                    datetime(started_at, 'unixepoch') as started,
                    CASE
                        WHEN completed_at IS NULL THEN 'Active'
                        ELSE 'Completed'
                    END as status
                FROM game_summaries
                WHERE completed_at IS NULL
                ORDER BY started_at DESC
                LIMIT 10;
            \" 2>/dev/null" || echo "Could not query database"
            pause
            ;;

        12) # Clean up old games
            echo -e "\n${YELLOW}🧹 Cleaning up old completed games (>30 days)...${NC}"

            # Show count before cleanup
            OLD_COUNT=$(run_remote "docker exec liap-tui-game sqlite3 /app/data/game_events.db \"
                SELECT COUNT(*) FROM game_summaries
                WHERE completed_at IS NOT NULL
                AND datetime(completed_at, 'unixepoch') < datetime('now', '-30 days');
            \" 2>/dev/null" || echo "0")

            echo -e "Games to clean up: ${OLD_COUNT}"

            if [ "$OLD_COUNT" != "0" ] && [ "$OLD_COUNT" -gt 0 ]; then
                read -p "Continue with cleanup? (y/N): " confirm

                if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                    # TODO: Implement cleanup via API endpoint when available
                    echo -e "${YELLOW}Note: Cleanup requires API endpoint implementation${NC}"
                    echo -e "${YELLOW}For now, old games are kept for historical data${NC}"
                fi
            else
                echo -e "${GREEN}No old games to clean up${NC}"
            fi
            pause
            ;;

        13) # Export statistics
            echo -e "\n${BLUE}📊 Exporting Game Statistics...${NC}"

            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            EXPORT_FILE="liap_tui_stats_${TIMESTAMP}.txt"

            # Create statistics report
            {
                echo "Liap Tui Game Statistics Report"
                echo "Generated: $(date)"
                echo "Server: ${EC2_HOST}"
                echo "==============================="
                echo ""

                # Get stats from remote
                run_remote "docker exec liap-tui-game sqlite3 /app/data/game_events.db \"
                    SELECT '=== Overall Statistics ===' as '';
                    SELECT 'Total Games Played:', COUNT(*) FROM game_summaries;
                    SELECT 'Total Rounds Played:', COUNT(*) FROM round_snapshots;
                    SELECT 'Active Games:', COUNT(*) FROM game_summaries WHERE completed_at IS NULL;
                    SELECT '';
                    SELECT '=== Player Statistics ===' as '';
                    SELECT 'Unique Players:', COUNT(DISTINCT json_extract(value, '$.name'))
                        FROM game_summaries, json_each(player_names);
                    SELECT '';
                    SELECT '=== Top Winners ===' as '';
                    SELECT winner as Player, COUNT(*) as Wins
                        FROM game_summaries
                        WHERE winner IS NOT NULL
                        GROUP BY winner
                        ORDER BY Wins DESC
                        LIMIT 10;
                    SELECT '';
                    SELECT '=== Recent Games ===' as '';
                    SELECT room_id as 'Room ID',
                           datetime(started_at, 'unixepoch') as Started,
                           total_rounds as Rounds,
                           winner as Winner
                        FROM game_summaries
                        ORDER BY started_at DESC
                        LIMIT 10;
                \" 2>/dev/null" || echo "Could not generate statistics"
            } > "$EXPORT_FILE"

            echo -e "${GREEN}✅ Statistics exported to: ${EXPORT_FILE}${NC}"
            pause
            ;;

        14) # System resources
            echo -e "\n${BLUE}💻 System Resources${NC}"
            run_remote "top -bn1 | head -20"
            echo -e "\n${BLUE}Memory Usage:${NC}"
            run_remote "free -h"
            echo -e "\n${BLUE}CPU Info:${NC}"
            run_remote "lscpu | grep -E 'Model name|CPU\(s\)|Thread|Core'"
            pause
            ;;

        15) # Emergency rebuild
            echo -e "\n${RED}🚨 Emergency Container Rebuild${NC}"
            echo -e "${RED}This will completely rebuild the container!${NC}"
            echo -e "${RED}Use only if the container is corrupted.${NC}"
            read -p "Are you sure? Type 'REBUILD' to confirm: " confirm

            if [ "$confirm" = "REBUILD" ]; then
                echo -e "${YELLOW}Creating emergency backup...${NC}"
                run_remote "/home/ubuntu/backup-game.sh"

                echo -e "${YELLOW}Stopping and removing container...${NC}"
                run_remote "cd /home/ubuntu && docker-compose down"

                echo -e "${YELLOW}Removing container and image...${NC}"
                run_remote "docker rm -f liap-tui-game 2>/dev/null || true"
                run_remote "docker rmi liap-tui:latest 2>/dev/null || true"

                echo -e "${YELLOW}Rebuilding container...${NC}"
                run_remote "cd /home/ubuntu && docker-compose build --no-cache"

                echo -e "${YELLOW}Starting new container...${NC}"
                run_remote "cd /home/ubuntu && docker-compose up -d"

                echo -e "${GREEN}✅ Container rebuilt${NC}"
            else
                echo -e "${YELLOW}Rebuild cancelled${NC}"
            fi
            pause
            ;;

        0) # Exit
            echo -e "\n${GREEN}Goodbye!${NC}"
            exit 0
            ;;

        *)
            echo -e "${RED}Invalid option${NC}"
            pause
            ;;
    esac
done