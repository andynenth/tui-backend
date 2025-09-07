#!/bin/bash
#
# check-old-ec2-status.sh - Check status of old EC2 server resources
#
# Usage: ./check-old-ec2-status.sh

# Configuration
INSTANCE_ID="i-031f0be2cfed1ff2f"
ELASTIC_IP="34.233.7.20"
SECURITY_GROUP_ID="sg-0e38841b4467d4545"
AWS_REGION="us-east-1"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Checking Old EC2 Server Status...${NC}"
echo "================================"

# Check EC2 Instance
echo -n "EC2 Instance: "
INSTANCE_STATE=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $AWS_REGION \
    --query 'Reservations[0].Instances[0].State.Name' \
    --output text 2>/dev/null || echo "not-found")

if [ "$INSTANCE_STATE" = "not-found" ] || [ "$INSTANCE_STATE" = "None" ]; then
    echo -e "${GREEN}✓ Not found (terminated)${NC}"
elif [ "$INSTANCE_STATE" = "terminated" ]; then
    echo -e "${GREEN}✓ Terminated${NC}"
elif [ "$INSTANCE_STATE" = "running" ]; then
    echo -e "${RED}✗ Running (costing ~$8.40/month)${NC}"
elif [ "$INSTANCE_STATE" = "stopped" ]; then
    echo -e "${YELLOW}⚠ Stopped (EBS still charged)${NC}"
else
    echo -e "${YELLOW}⚠ State: $INSTANCE_STATE${NC}"
fi

# Check Elastic IP
echo -n "Elastic IP: "
ALLOCATION_ID=$(aws ec2 describe-addresses \
    --public-ips $ELASTIC_IP \
    --region $AWS_REGION \
    --query 'Addresses[0].AllocationId' \
    --output text 2>/dev/null || echo "not-found")

if [ "$ALLOCATION_ID" = "not-found" ] || [ "$ALLOCATION_ID" = "None" ]; then
    echo -e "${GREEN}✓ Released${NC}"
else
    # Check if attached to instance
    INSTANCE_ATTACHED=$(aws ec2 describe-addresses \
        --public-ips $ELASTIC_IP \
        --region $AWS_REGION \
        --query 'Addresses[0].InstanceId' \
        --output text 2>/dev/null || echo "none")

    if [ "$INSTANCE_ATTACHED" = "None" ] || [ "$INSTANCE_ATTACHED" = "" ]; then
        echo -e "${RED}✗ Allocated but not attached (costing $3.60/month)${NC}"
    else
        echo -e "${YELLOW}⚠ Attached to instance: $INSTANCE_ATTACHED${NC}"
    fi
fi

# Check Security Group
echo -n "Security Group: "
if aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --region $AWS_REGION &>/dev/null; then
    echo -e "${YELLOW}⚠ Still exists (no cost)${NC}"
else
    echo -e "${GREEN}✓ Deleted${NC}"
fi

# Check for EBS Volumes
echo -n "EBS Volumes: "
VOLUME_COUNT=$(aws ec2 describe-volumes \
    --region $AWS_REGION \
    --filters "Name=attachment.instance-id,Values=$INSTANCE_ID" \
    --query 'length(Volumes)' \
    --output text 2>/dev/null || echo "0")

if [ "$VOLUME_COUNT" = "0" ]; then
    echo -e "${GREEN}✓ None found${NC}"
else
    TOTAL_SIZE=$(aws ec2 describe-volumes \
        --region $AWS_REGION \
        --filters "Name=attachment.instance-id,Values=$INSTANCE_ID" \
        --query 'sum(Volumes[].Size)' \
        --output text 2>/dev/null || echo "0")
    echo -e "${YELLOW}⚠ $VOLUME_COUNT volume(s), ${TOTAL_SIZE}GB total${NC}"
fi

# Summary
echo ""
echo "================================"

# Calculate costs
TOTAL_COST=0
COST_BREAKDOWN=""

if [ "$INSTANCE_STATE" = "running" ]; then
    TOTAL_COST=$(echo "$TOTAL_COST + 8.40" | bc)
    COST_BREAKDOWN="${COST_BREAKDOWN}  - EC2 Instance: \$8.40/month\n"
fi

if [ "$ALLOCATION_ID" != "not-found" ] && [ "$ALLOCATION_ID" != "None" ] && [ "$INSTANCE_ATTACHED" = "None" ]; then
    TOTAL_COST=$(echo "$TOTAL_COST + 3.60" | bc)
    COST_BREAKDOWN="${COST_BREAKDOWN}  - Elastic IP: $3.60/month\n"
fi

if [ "$VOLUME_COUNT" != "0" ] && [ "$INSTANCE_STATE" = "stopped" ]; then
    VOLUME_COST=$(echo "$TOTAL_SIZE * 0.08" | bc)
    TOTAL_COST=$(echo "$TOTAL_COST + $VOLUME_COST" | bc)
    COST_BREAKDOWN="${COST_BREAKDOWN}  - EBS Volumes: ~$${VOLUME_COST}/month\n"
fi

if (( $(echo "$TOTAL_COST > 0" | bc -l) )); then
    echo -e "${RED}💸 Estimated monthly cost: \$${TOTAL_COST}${NC}"
    echo -e "${RED}Cost breakdown:${NC}"
    echo -e "$COST_BREAKDOWN"
    echo -e "${YELLOW}Run ./shutdown-old-ec2.sh to stop these charges${NC}"
else
    echo -e "${GREEN}✅ No ongoing charges from old EC2 resources!${NC}"
fi

# Show current Tokyo server
echo ""
echo -e "${BLUE}Current Production Server:${NC}"
echo "  Tokyo: 54.250.35.226 (ap-northeast-1)"
