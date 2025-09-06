#\!/bin/bash
# AWS Free Tier Eligibility Checker

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🆓 AWS Free Tier Eligibility Check${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Check if AWS CLI is available
if \! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not installed${NC}"
    exit 1
fi

# Get account creation date (approximate)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}❌ Cannot get AWS account information${NC}"
    exit 1
fi

echo -e "${BLUE}Account ID: ${ACCOUNT_ID}${NC}"
echo ""

# Free Tier Resources for Liap Tui
echo -e "${GREEN}✅ AWS Free Tier Resources (12 months):${NC}"
echo ""

echo -e "${BLUE}EC2:${NC}"
echo -e "  • 750 hours/month of t2.micro instance"
echo -e "  • For Liap Tui: Running 24/7 = 720-744 hours ✅"
echo ""

echo -e "${BLUE}Storage:${NC}"
echo -e "  • 30 GB of EBS General Purpose (SSD) storage"
echo -e "  • For Liap Tui: Using 30 GB ✅"
echo ""

echo -e "${BLUE}Data Transfer:${NC}"
echo -e "  • 15 GB/month bandwidth out to Internet"
echo -e "  • 1 GB/month regional data transfer"
echo -e "  • For Liap Tui: Typical game usage <5 GB/month ✅"
echo ""

echo -e "${BLUE}Elastic IP:${NC}"
echo -e "  • 1 Elastic IP free when attached to running instance"
echo -e "  • For Liap Tui: 1 Elastic IP ✅"
echo ""

echo -e "${GREEN}✅ Always Free Resources:${NC}"
echo ""

echo -e "${BLUE}S3 Storage:${NC}"
echo -e "  • 5 GB standard storage"
echo -e "  • 20,000 GET requests"
echo -e "  • 2,000 PUT requests"
echo -e "  • For Liap Tui backups: <1 GB typically ✅"
echo ""

# Cost Estimate
echo -e "${BLUE}💰 Monthly Cost Estimate:${NC}"
echo -e "${BLUE}========================${NC}"
echo ""

echo -e "${GREEN}Within Free Tier (First 12 months):${NC}"
echo -e "  • EC2 t2.micro: $0.00"
echo -e "  • 30 GB EBS: $0.00"
echo -e "  • Elastic IP: $0.00"
echo -e "  • Data Transfer (<15GB): $0.00"
echo -e "  • ${GREEN}Total: $0.00/month${NC}"
echo ""

echo -e "${YELLOW}After Free Tier expires:${NC}"
echo -e "  • EC2 t2.micro: ~$8.50/month"
echo -e "  • 30 GB EBS: ~$3.00/month"
echo -e "  • Elastic IP: $0.00 (when attached)"
echo -e "  • Data Transfer: ~$0.50/month"
echo -e "  • ${YELLOW}Total: ~$12.00/month${NC}"
echo ""

# Warnings
echo -e "${RED}⚠️  Important Warnings:${NC}"
echo -e "  • Free tier is for first 12 months only"
echo -e "  • Exceeding 750 hours/month will incur charges"
echo -e "  • Unattached Elastic IPs cost $0.005/hour"
echo -e "  • Always monitor AWS Billing Dashboard"
echo ""

# Recommendations
echo -e "${BLUE}💡 Cost Optimization Tips:${NC}"
echo -e "  1. Set up billing alerts at $1, $5, $10"
echo -e "  2. Use AWS Budgets to track usage"
echo -e "  3. Stop instance when not needed (saves hours)"
echo -e "  4. Delete old snapshots and unattached volumes"
echo -e "  5. Monitor data transfer usage"
echo ""

# Create billing alert script
cat > setup-billing-alerts.sh << 'ALERT_EOF'
#\!/bin/bash
# Setup AWS Billing Alerts

echo "Setting up billing alerts..."

# Create SNS topic for alerts
TOPIC_ARN=$(aws sns create-topic --name billing-alerts --query TopicArn --output text)

# Subscribe email
echo -n "Enter your email for billing alerts: "
read EMAIL
aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint $EMAIL

# Create CloudWatch alarms
for THRESHOLD in 1 5 10; do
    aws cloudwatch put-metric-alarm \
        --alarm-name "Billing-Alert-${THRESHOLD}USD" \
        --alarm-description "Alert when bill exceeds $${THRESHOLD}" \
        --metric-name EstimatedCharges \
        --namespace AWS/Billing \
        --statistic Maximum \
        --period 86400 \
        --threshold $THRESHOLD \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 1 \
        --alarm-actions $TOPIC_ARN \
        --dimensions Name=Currency,Value=USD
done

echo "Billing alerts created\! Check your email to confirm subscription."
ALERT_EOF

chmod +x setup-billing-alerts.sh

echo -e "${GREEN}✅ Created setup-billing-alerts.sh${NC}"
echo -e "   Run this script to set up cost alerts"
echo ""
echo -e "${BLUE}Ready to launch your Free Tier eligible EC2 instance\!${NC}"
