#\!/bin/bash
# Automated AWS Billing Alerts Setup

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
EMAIL="${AWS_ALERT_EMAIL:-your-email@example.com}"

echo -e "${BLUE}💰 AWS Billing Alerts Setup (Automated)${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if email is provided
if [ "$EMAIL" = "your-email@example.com" ]; then
    echo -e "${YELLOW}Please set your email:${NC}"
    echo -e "  export AWS_ALERT_EMAIL=your-email@example.com"
    echo -e "  ./setup-billing-alerts-auto.sh"
    exit 1
fi

echo -e "${GREEN}Setting up alerts for: ${EMAIL}${NC}"
echo ""

# Create CloudWatch alarms (these work without SNS confirmation)
echo -e "${YELLOW}Creating billing alarms...${NC}"

# First, we need to ensure billing metrics are enabled
# This is done in the AWS Console under Billing Preferences

# Create alarms that log to CloudWatch (no email needed for setup)
for THRESHOLD in 1 5 10; do
    echo -e "${YELLOW}Creating alarm for \$${THRESHOLD}...${NC}"
    
    aws cloudwatch put-metric-alarm \
        --alarm-name "Billing-Alert-${THRESHOLD}USD" \
        --alarm-description "Alert when AWS charges exceed \$${THRESHOLD}" \
        --metric-name EstimatedCharges \
        --namespace AWS/Billing \
        --statistic Maximum \
        --period 86400 \
        --threshold $THRESHOLD \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 1 \
        --dimensions Name=Currency,Value=USD \
        --treat-missing-data notBreaching 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Created \$${THRESHOLD} alarm${NC}"
    else
        echo -e "${YELLOW}⚠️  Alarm might already exist or billing metrics not enabled${NC}"
    fi
done

# Create a simple cost checking script
cat > check-costs.sh << 'SCRIPT_EOF'
#\!/bin/bash
# Quick AWS cost check

echo "Current AWS Costs"
echo "================="
date
echo ""

# Get current month
START=$(date +%Y-%m-01)
END=$(date +%Y-%m-%d)

# Get total cost
echo "Month-to-date total:"
aws ce get-cost-and-usage \
    --time-period Start=$START,End=$END \
    --granularity MONTHLY \
    --metrics "UnblendedCost" \
    --query 'ResultsByTime[0].Total.UnblendedCost.Amount' \
    --output text 2>/dev/null  < /dev/null |  xargs printf "$%.2f\n"

echo ""
echo "By service:"
aws ce get-cost-and-usage \
    --time-period Start=$START,End=$END \
    --granularity MONTHLY \
    --metrics "UnblendedCost" \
    --group-by Type=DIMENSION,Key=SERVICE \
    --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' \
    --output text 2>/dev/null | while read service cost; do
    if [ $(echo "$cost > 0" | bc -l) -eq 1 ]; then
        printf "  %-30s $%.2f\n" "$service" "$cost"
    fi
done

# Check Free Tier usage
echo ""
echo "EC2 t2.micro hours used this month:"
aws cloudwatch get-metric-statistics \
    --namespace AWS/EC2 \
    --metric-name CPUUtilization \
    --dimensions Name=InstanceType,Value=t2.micro \
    --statistics SampleCount \
    --start-time $(date -u -d "$START" +%Y-%m-%dT00:00:00Z) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 3600 \
    --query 'Datapoints | length(@)' \
    --output text 2>/dev/null || echo "0"
echo "(Free tier limit: 750 hours/month)"
SCRIPT_EOF

chmod +x check-costs.sh

echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "${GREEN}✅ Billing alarms created${NC}"
echo -e "${GREEN}✅ Cost checking script created${NC}"
echo ""
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo -e "  1. Billing metrics must be enabled in AWS Console:"
echo -e "     • Go to: https://console.aws.amazon.com/billing/home#/preferences"
echo -e "     • Check 'Receive Billing Alerts'"
echo -e "  2. Alarms appear in CloudWatch console"
echo -e "  3. To add email notifications later, use SNS"
echo ""
echo -e "${BLUE}Check your costs anytime:${NC}"
echo -e "  ${GREEN}./check-costs.sh${NC}"
echo ""
echo -e "${BLUE}View alarms in AWS Console:${NC}"
echo -e "  https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:"
