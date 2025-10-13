#!/bin/bash

# AWS Instance Auto Start/Stop Management
# Save money by running instances only when needed

set -e

# Configuration
TOKYO_INSTANCE="i-00f537b8ed58a15de"
US_INSTANCE="i-0b748802dccd19026"
TOKYO_REGION="ap-northeast-1"
US_REGION="us-east-1"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

show_usage() {
    echo -e "${BLUE}AWS Instance Management${NC}"
    echo ""
    echo "Usage: $0 [command] [region]"
    echo ""
    echo "Commands:"
    echo "  start    - Start instances"
    echo "  stop     - Stop instances"
    echo "  status   - Show instance status"
    echo "  costs    - Show cost breakdown"
    echo "  schedule - Set up automatic scheduling"
    echo ""
    echo "Regions:"
    echo "  tokyo    - Tokyo instance only"
    echo "  us       - US instance only"
    echo "  all      - Both instances (default)"
    echo ""
    echo "Examples:"
    echo "  $0 start tokyo    # Start Tokyo instance"
    echo "  $0 stop all       # Stop both instances"
    echo "  $0 status         # Show all instance status"
}

get_instance_status() {
    local instance_id=$1
    local region=$2
    local name=$3

    status=$(aws ec2 describe-instances \
        --region $region \
        --instance-ids $instance_id \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text 2>/dev/null || echo "not-found")

    case $status in
        "running")
            echo -e "${GREEN}✅ $name: RUNNING${NC}"
            ;;
        "stopped")
            echo -e "${YELLOW}⏹️  $name: STOPPED${NC}"
            ;;
        "stopping")
            echo -e "${YELLOW}⏸️  $name: STOPPING...${NC}"
            ;;
        "starting")
            echo -e "${YELLOW}▶️  $name: STARTING...${NC}"
            ;;
        *)
            echo -e "${RED}❌ $name: $status${NC}"
            ;;
    esac
}

start_instance() {
    local instance_id=$1
    local region=$2
    local name=$3

    echo -e "${YELLOW}Starting $name...${NC}"
    aws ec2 start-instances --region $region --instance-ids $instance_id

    echo -e "${YELLOW}Waiting for $name to start...${NC}"
    aws ec2 wait instance-running --region $region --instance-ids $instance_id

    # Get new IP address
    new_ip=$(aws ec2 describe-instances \
        --region $region \
        --instance-ids $instance_id \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)

    echo -e "${GREEN}✅ $name started! IP: $new_ip${NC}"
}

stop_instance() {
    local instance_id=$1
    local region=$2
    local name=$3

    echo -e "${YELLOW}Stopping $name...${NC}"
    aws ec2 stop-instances --region $region --instance-ids $instance_id

    echo -e "${YELLOW}Waiting for $name to stop...${NC}"
    aws ec2 wait instance-stopped --region $region --instance-ids $instance_id

    echo -e "${GREEN}✅ $name stopped!${NC}"
}

show_costs() {
    echo -e "${BLUE}💰 Cost Breakdown (Per Hour/Month)${NC}"
    echo "=================================="
    echo -e "${YELLOW}When Running:${NC}"
    echo "  Tokyo t2.micro:  $0.0116/hour = ~$8.50/month"
    echo "  US t2.micro:     $0.0116/hour = ~$8.50/month"
    echo "  Both running:    $0.0232/hour = ~$17/month"
    echo ""
    echo -e "${GREEN}When Stopped:${NC}"
    echo "  Compute cost:    $0/hour = $0/month"
    echo "  Storage cost:    ~$1/month (EBS volumes)"
    echo ""
    echo -e "${BLUE}Usage Examples:${NC}"
    echo "  8 hours/day:     ~$4.25/month (75% savings)"
    echo "  12 hours/day:    ~$6.38/month (62% savings)"
    echo "  Weekdays only:   ~$12/month (30% savings)"
    echo "  Weekends only:   ~$5/month (70% savings)"
}

setup_scheduling() {
    echo -e "${BLUE}🕒 Auto-Scheduling Options${NC}"
    echo ""
    echo "1. Manual scripts (what we're creating now)"
    echo "2. AWS EventBridge + Lambda (advanced)"
    echo "3. Cron jobs on your local machine"
    echo ""
    echo -e "${YELLOW}Creating daily schedule scripts...${NC}"

    # Work hours start script
    cat > start_work_hours.sh << 'EOF'
#!/bin/bash
# Start instances for work hours (9 AM local time)
echo "🌅 Starting work day instances..."
./auto_start_stop.sh start all
echo "✅ Instances started for work day"
EOF

    # Work hours stop script
    cat > stop_work_hours.sh << 'EOF'
#!/bin/bash
# Stop instances after work hours (6 PM local time)
echo "🌙 Stopping instances for night..."
./auto_start_stop.sh stop all
echo "✅ Instances stopped for night - saving money!"
EOF

    chmod +x start_work_hours.sh stop_work_hours.sh

    echo -e "${GREEN}Created scheduling scripts:${NC}"
    echo "  start_work_hours.sh - Start instances"
    echo "  stop_work_hours.sh  - Stop instances"
    echo ""
    echo -e "${YELLOW}To automate with cron:${NC}"
    echo "  crontab -e"
    echo "  Add these lines:"
    echo "  0 9 * * 1-5 /path/to/start_work_hours.sh  # Start weekdays 9 AM"
    echo "  0 18 * * 1-5 /path/to/stop_work_hours.sh  # Stop weekdays 6 PM"
}

# Main script logic
case ${1:-status} in
    "start")
        case ${2:-all} in
            "tokyo")
                start_instance $TOKYO_INSTANCE $TOKYO_REGION "Tokyo"
                ;;
            "us")
                start_instance $US_INSTANCE $US_REGION "US East"
                ;;
            "all")
                start_instance $TOKYO_INSTANCE $TOKYO_REGION "Tokyo"
                start_instance $US_INSTANCE $US_REGION "US East"
                ;;
        esac
        ;;

    "stop")
        case ${2:-all} in
            "tokyo")
                stop_instance $TOKYO_INSTANCE $TOKYO_REGION "Tokyo"
                ;;
            "us")
                stop_instance $US_INSTANCE $US_REGION "US East"
                ;;
            "all")
                stop_instance $TOKYO_INSTANCE $TOKYO_REGION "Tokyo"
                stop_instance $US_INSTANCE $US_REGION "US East"
                ;;
        esac
        ;;

    "status")
        echo -e "${BLUE}📊 Instance Status${NC}"
        echo "=================="
        get_instance_status $TOKYO_INSTANCE $TOKYO_REGION "Tokyo t2.micro"
        get_instance_status $US_INSTANCE $US_REGION "US East t2.micro"
        echo ""

        # Show current costs
        tokyo_status=$(aws ec2 describe-instances --region $TOKYO_REGION --instance-ids $TOKYO_INSTANCE --query 'Reservations[0].Instances[0].State.Name' --output text)
        us_status=$(aws ec2 describe-instances --region $US_REGION --instance-ids $US_INSTANCE --query 'Reservations[0].Instances[0].State.Name' --output text)

        current_cost=0
        if [ "$tokyo_status" = "running" ]; then
            current_cost=$(echo "$current_cost + 0.0116" | bc -l)
        fi
        if [ "$us_status" = "running" ]; then
            current_cost=$(echo "$current_cost + 0.0116" | bc -l)
        fi

        monthly_cost=$(echo "$current_cost * 24 * 30" | bc -l)
        echo -e "${YELLOW}Current hourly cost: \$$(printf "%.4f" $current_cost)${NC}"
        echo -e "${YELLOW}Monthly cost if left running: \$$(printf "%.2f" $monthly_cost)${NC}"
        ;;

    "costs")
        show_costs
        ;;

    "schedule")
        setup_scheduling
        ;;

    "help"|"--help"|"-h")
        show_usage
        ;;

    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac
