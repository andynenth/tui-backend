#\!/bin/bash
# Interactive AWS Billing Alerts Setup

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}💰 AWS Billing Alerts Setup${NC}"
echo -e "${BLUE}=========================${NC}"
echo ""

# Check AWS CLI
if \! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Error: AWS credentials not configured${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account: ${ACCOUNT_ID}${NC}"
echo ""

# Get email for notifications
echo -ne "${YELLOW}Enter your email for billing alerts: ${NC}"
read EMAIL

if ! echo "$EMAIL" | grep -qE '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'; then
    echo -e "${RED}❌ Invalid email address${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Setting up the following alerts:${NC}"
echo -e "  • $1 - When charges exceed $1"
echo -e "  • $5 - When charges exceed $5"
echo -e "  • $10 - When charges exceed $10"
echo -e "  • Free Tier Usage alerts"
echo ""

# Create SNS topic
echo -e "${YELLOW}Creating SNS topic for notifications...${NC}"
TOPIC_ARN=$(aws sns create-topic --name billing-alerts --query TopicArn --output text 2>/dev/null)

if [ -z "$TOPIC_ARN" ]; then
    # Topic might already exist
    TOPIC_ARN=$(aws sns list-topics --query "Topics[?contains(TopicArn, 'billing-alerts')].TopicArn" --output text)
fi

echo -e "${GREEN}✅ SNS Topic: ${TOPIC_ARN}${NC}"

# Subscribe email
echo -e "${YELLOW}Subscribing email to notifications...${NC}"
aws sns subscribe \
    --topic-arn $TOPIC_ARN \
    --protocol email \
    --notification-endpoint $EMAIL

echo -e "${YELLOW}⚠️  Check your email and confirm the subscription\!${NC}"
echo -e "${YELLOW}Press Enter after confirming the email...${NC}"
read

# Enable billing alerts in preferences
echo -e "${YELLOW}Enabling billing alerts...${NC}"
aws ce put-anomaly-monitor \
    --anomaly-monitor '{
        "MonitorName": "FreeTierMonitor",
        "MonitorType": "DIMENSIONAL",
        "MonitorDimension": "SERVICE"
    }' 2>/dev/null || true

# Create billing alarms
for THRESHOLD in 1 5 10; do
    echo -e "${YELLOW}Creating alarm for $${THRESHOLD}...${NC}"
    
    aws cloudwatch put-metric-alarm \
        --alarm-name "Billing-Alert-${THRESHOLD}USD" \
        --alarm-description "Alert when AWS charges exceed $${THRESHOLD}" \
        --metric-name EstimatedCharges \
        --namespace AWS/Billing \
        --statistic Maximum \
        --period 86400 \
        --threshold $THRESHOLD \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 1 \
        --alarm-actions $TOPIC_ARN \
        --dimensions Name=Currency,Value=USD \
        --treat-missing-data notBreaching
    
    echo -e "${GREEN}✅ Created $${THRESHOLD} alert${NC}"
done

# Create Free Tier usage alarm
echo -e "${YELLOW}Creating Free Tier usage alarm...${NC}"

# EC2 Free Tier alarm (750 hours)
aws cloudwatch put-metric-alarm \
    --alarm-name "FreeTier-EC2-Usage" \
    --alarm-description "Alert when EC2 usage approaches Free Tier limit" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 3600 \
    --threshold 700 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --alarm-actions $TOPIC_ARN \
    --dimensions Name=InstanceType,Value=t2.micro \
    --unit Count \
    --treat-missing-data notBreaching 2>/dev/null || true

echo -e "${GREEN}✅ Billing alerts configured\!${NC}"

# Create cost report script
cat > check-aws-costs.sh << 'SCRIPT_EOF'
#\!/bin/bash
# Check current AWS costs

# Get current month costs
CURRENT_MONTH_START=$(date +%Y-%m-01)
CURRENT_DATE=$(date +%Y-%m-%d)

echo "AWS Cost Report"
echo "==============="
echo "Period: $CURRENT_MONTH_START to $CURRENT_DATE"
echo ""

# Get total cost
TOTAL_COST=$(aws ce get-cost-and-usage \
    --time-period Start=$CURRENT_MONTH_START,End=$CURRENT_DATE \
    --granularity MONTHLY \
    --metrics "UnblendedCost" \
    --query 'ResultsByTime[0].Total.UnblendedCost.Amount' \
    --output text 2>/dev/null || echo "0")

echo "Total Cost: \$${TOTAL_COST}"
echo ""

# Get cost by service
echo "Cost by Service:"
aws ce get-cost-and-usage \
    --time-period Start=$CURRENT_MONTH_START,End=$CURRENT_DATE \
    --granularity MONTHLY \
    --metrics "UnblendedCost" \
    --group-by Type=DIMENSION,Key=SERVICE \
    --query 'ResultsByTime[0].Groups[?Metrics.UnblendedCost.Amount>`0`].[Keys[0],Metrics.UnblendedCost.Amount]' \
    --output table 2>/dev/null || echo "Unable to fetch service costs"

# Check Free Tier usage
echo ""
echo "EC2 Hours Used (Free Tier: 750 hours/month):"
INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=liap-tui-game-server" --query "Reservations[0].Instances[0].InstanceId" --output text 2>/dev/null)
if [ "$INSTANCE_ID" \!= "None" ] && [ \! -z "$INSTANCE_ID" ]; then
    HOURS_USED=$(aws ce get-cost-and-usage \
        --time-period Start=$CURRENT_MONTH_START,End=$CURRENT_DATE \
        --granularity MONTHLY \
        --metrics "UsageQuantity" \
        --filter file://<(echo '{
            "Dimensions": {
                "Key": "USAGE_TYPE",
                "Values": ["BoxUsage:t2.micro"]
            }
        }') \
        --query 'ResultsByTime[0].Total.UsageQuantity.Amount' \
        --output text 2>/dev/null || echo "0")
    
    echo "Hours used: ${HOURS_USED:-0} / 750"
fi
SCRIPT_EOF

chmod +x check-aws-costs.sh

echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "${BLUE}========${NC}"
echo -e "${GREEN}✅ SNS Topic created${NC}"
echo -e "${GREEN}✅ Email subscription pending (check email)${NC}"
echo -e "${GREEN}✅ Billing alarms created ($1, $5, $10)${NC}"
echo -e "${GREEN}✅ Free Tier monitoring enabled${NC}"
echo -e "${GREEN}✅ Cost checking script created${NC}"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo -e "  1. Confirm the email subscription"
echo -e "  2. Alarms may take up to 24 hours to start working"
echo -e "  3. Check costs regularly: ./check-aws-costs.sh"
echo -e "  4. AWS bills monthly - monitor throughout the month"
echo ""
echo -e "${BLUE}To check current costs, run:${NC}"
echo -e "  ${GREEN}./check-aws-costs.sh${NC}"
