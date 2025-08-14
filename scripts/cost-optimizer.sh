#!/bin/bash
# Cost Optimization Script for Liap Tui on AWS

set -e

# Configuration
REGION="${AWS_REGION:-us-east-1}"
INSTANCE_ID="${INSTANCE_ID:-}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI not installed${NC}"
    exit 1
fi

echo -e "${BLUE}💰 AWS Cost Optimization Analysis${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Date: $(date)"
echo -e "Region: ${REGION}"
echo ""

# Track savings opportunities
TOTAL_SAVINGS=0
SAVINGS_OPPORTUNITIES=()

# 1. EC2 Instance Analysis
echo -e "${BLUE}1. EC2 Instance Analysis${NC}"

if [ ! -z "$INSTANCE_ID" ]; then
    # Get instance details
    INSTANCE_INFO=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION 2>/dev/null || echo "{}")
    INSTANCE_TYPE=$(echo $INSTANCE_INFO | jq -r '.Reservations[0].Instances[0].InstanceType' 2>/dev/null || echo "unknown")
    INSTANCE_STATE=$(echo $INSTANCE_INFO | jq -r '.Reservations[0].Instances[0].State.Name' 2>/dev/null || echo "unknown")
    
    echo -e "  Instance Type: ${INSTANCE_TYPE}"
    echo -e "  State: ${INSTANCE_STATE}"
    
    # Check if eligible for savings plans
    if [[ "$INSTANCE_TYPE" == "t2."* ]]; then
        echo -e "${YELLOW}  ⚠️  Consider t3 instances (up to 30% cheaper)${NC}"
        SAVINGS_OPPORTUNITIES+=("Switch from $INSTANCE_TYPE to t3 equivalent - Save ~30%")
        TOTAL_SAVINGS=$((TOTAL_SAVINGS + 5))  # Estimated $5/month savings
    fi
    
    # Check utilization
    echo -e "\n  Checking CPU utilization..."
    AVG_CPU=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/EC2 \
        --metric-name CPUUtilization \
        --dimensions Name=InstanceId,Value=$INSTANCE_ID \
        --statistics Average \
        --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
        --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
        --period 3600 \
        --region $REGION \
        | jq -r '.Datapoints | map(.Average) | add/length' 2>/dev/null || echo "0")
    
    echo -e "  Average CPU (7 days): ${AVG_CPU}%"
    
    if (( $(echo "$AVG_CPU < 20" | bc -l) )); then
        echo -e "${YELLOW}  ⚠️  Low CPU usage - consider smaller instance${NC}"
        SAVINGS_OPPORTUNITIES+=("Downsize instance due to low CPU usage - Save ~50%")
        TOTAL_SAVINGS=$((TOTAL_SAVINGS + 8))
    fi
else
    echo -e "${YELLOW}  ⚠️  Set INSTANCE_ID to analyze EC2 costs${NC}"
fi

# 2. Storage Analysis
echo -e "\n${BLUE}2. Storage Analysis${NC}"

# EBS Volumes
if [ ! -z "$INSTANCE_ID" ]; then
    VOLUMES=$(aws ec2 describe-volumes \
        --filters "Name=attachment.instance-id,Values=$INSTANCE_ID" \
        --region $REGION 2>/dev/null || echo "[]")
    
    TOTAL_SIZE=0
    UNATTACHED=0
    
    echo "$VOLUMES" | jq -c '.Volumes[]' 2>/dev/null | while read volume; do
        SIZE=$(echo $volume | jq -r '.Size')
        STATE=$(echo $volume | jq -r '.State')
        TYPE=$(echo $volume | jq -r '.VolumeType')
        
        TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
        
        if [ "$STATE" = "available" ]; then
            UNATTACHED=$((UNATTACHED + 1))
            echo -e "${YELLOW}  ⚠️  Unattached volume found (${SIZE}GB)${NC}"
            SAVINGS_OPPORTUNITIES+=("Delete unattached EBS volume - Save ~$${SIZE}/month")
            TOTAL_SAVINGS=$((TOTAL_SAVINGS + SIZE))
        fi
        
        if [ "$TYPE" = "gp2" ] && [ $SIZE -gt 100 ]; then
            echo -e "${YELLOW}  ⚠️  Consider gp3 for volume >100GB${NC}"
            SAVINGS_OPPORTUNITIES+=("Convert gp2 to gp3 - Save ~20%")
            TOTAL_SAVINGS=$((TOTAL_SAVINGS + 2))
        fi
    done
    
    echo -e "  Total EBS Storage: ${TOTAL_SIZE}GB"
fi

# S3 Buckets
echo -e "\n  Checking S3 usage..."
S3_BUCKETS=$(aws s3 ls --region $REGION 2>/dev/null | awk '{print $3}' | grep -E "liap|game|backup" || echo "")

if [ ! -z "$S3_BUCKETS" ]; then
    for bucket in $S3_BUCKETS; do
        # Get bucket size
        BUCKET_SIZE=$(aws s3 ls s3://$bucket --recursive --summarize 2>/dev/null | grep "Total Size" | awk '{print $3}')
        BUCKET_SIZE_GB=$((BUCKET_SIZE / 1073741824))
        
        echo -e "  Bucket: $bucket (${BUCKET_SIZE_GB}GB)"
        
        # Check for lifecycle policies
        LIFECYCLE=$(aws s3api get-bucket-lifecycle-configuration --bucket $bucket 2>/dev/null || echo "none")
        if [ "$LIFECYCLE" = "none" ]; then
            echo -e "${YELLOW}    ⚠️  No lifecycle policy - add for old backups${NC}"
            SAVINGS_OPPORTUNITIES+=("Add S3 lifecycle policy for $bucket - Save ~$5/month")
            TOTAL_SAVINGS=$((TOTAL_SAVINGS + 5))
        fi
    done
fi

# 3. Data Transfer Analysis
echo -e "\n${BLUE}3. Data Transfer Analysis${NC}"

# Check CloudFront usage
CF_DISTRIBUTIONS=$(aws cloudfront list-distributions --query 'DistributionList.Items[?Comment==`liap-tui`].Id' --output text 2>/dev/null || echo "")

if [ -z "$CF_DISTRIBUTIONS" ]; then
    echo -e "${YELLOW}  ⚠️  No CloudFront distribution found${NC}"
    echo -e "  Consider CloudFront for static assets to reduce EC2 bandwidth"
    SAVINGS_OPPORTUNITIES+=("Implement CloudFront CDN - Reduce bandwidth costs")
    TOTAL_SAVINGS=$((TOTAL_SAVINGS + 10))
else
    echo -e "${GREEN}  ✅ CloudFront configured${NC}"
fi

# 4. Idle Resource Detection
echo -e "\n${BLUE}4. Idle Resource Detection${NC}"

# Check for elastic IPs
ELASTIC_IPS=$(aws ec2 describe-addresses --region $REGION 2>/dev/null || echo "{}")
UNASSOCIATED_IPS=$(echo $ELASTIC_IPS | jq -r '.Addresses[] | select(.AssociationId == null) | .PublicIp' 2>/dev/null | wc -l)

if [ $UNASSOCIATED_IPS -gt 0 ]; then
    echo -e "${RED}  ❌ ${UNASSOCIATED_IPS} unassociated Elastic IPs (charged when not in use)${NC}"
    SAVINGS_OPPORTUNITIES+=("Release ${UNASSOCIATED_IPS} unassociated Elastic IPs - Save \$${UNASSOCIATED_IPS}.50/month")
    TOTAL_SAVINGS=$((TOTAL_SAVINGS + UNASSOCIATED_IPS))
else
    echo -e "${GREEN}  ✅ No idle Elastic IPs${NC}"
fi

# Check for old snapshots
OLD_SNAPSHOTS=$(aws ec2 describe-snapshots --owner-ids self --query "Snapshots[?StartTime<='$(date -d '30 days ago' --iso-8601)']" --region $REGION 2>/dev/null | jq -r '.[].SnapshotId' | wc -l)

if [ $OLD_SNAPSHOTS -gt 0 ]; then
    echo -e "${YELLOW}  ⚠️  ${OLD_SNAPSHOTS} snapshots older than 30 days${NC}"
    SAVINGS_OPPORTUNITIES+=("Clean up old snapshots - Save ~\$${OLD_SNAPSHOTS}/month")
    TOTAL_SAVINGS=$((TOTAL_SAVINGS + OLD_SNAPSHOTS))
fi

# 5. Reserved Instance Recommendations
echo -e "\n${BLUE}5. Reserved Instance Analysis${NC}"

if [ "$INSTANCE_TYPE" = "t2.micro" ]; then
    echo -e "  Current: t2.micro (Free tier eligible)"
    echo -e "${GREEN}  ✅ Using free tier - no RI needed${NC}"
else
    echo -e "${YELLOW}  ⚠️  Consider Reserved Instances for long-term usage${NC}"
    echo -e "  Potential savings: up to 40% with 1-year RI"
    SAVINGS_OPPORTUNITIES+=("Purchase Reserved Instance - Save ~40%")
fi

# 6. Auto-shutdown Opportunities
echo -e "\n${BLUE}6. Usage Pattern Analysis${NC}"

echo -e "  Analyzing access patterns..."
# This would require CloudWatch Logs analysis
echo -e "${YELLOW}  ⚠️  Consider auto-shutdown during low usage hours${NC}"
echo -e "  Potential savings: ~50% if shut down 12 hours/day"
SAVINGS_OPPORTUNITIES+=("Implement auto-shutdown schedule - Save ~50%")

# Generate Cost Optimization Report
echo -e "\n${BLUE}═══════════════════════════════════${NC}"
echo -e "${BLUE}💰 Total Potential Savings: \$${TOTAL_SAVINGS}/month${NC}"
echo -e "${BLUE}═══════════════════════════════════${NC}"

if [ ${#SAVINGS_OPPORTUNITIES[@]} -gt 0 ]; then
    echo -e "\n${GREEN}📋 Savings Opportunities:${NC}"
    for opportunity in "${SAVINGS_OPPORTUNITIES[@]}"; do
        echo -e "  • $opportunity"
    done
fi

# Generate implementation scripts
echo -e "\n${BLUE}🛠️  Generating optimization scripts...${NC}"

# Script for t3 migration
if [[ " ${SAVINGS_OPPORTUNITIES[@]} " =~ "t3" ]]; then
    cat > migrate_to_t3.sh << 'EOF'
#!/bin/bash
# Migrate to t3 instance type

INSTANCE_ID=$1
NEW_TYPE="t3.micro"  # or t3.small

# Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

# Change instance type
aws ec2 modify-instance-attribute --instance-id $INSTANCE_ID --instance-type "{\"Value\": \"$NEW_TYPE\"}"

# Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

echo "Migration complete!"
EOF
    chmod +x migrate_to_t3.sh
    echo -e "${GREEN}  Created: migrate_to_t3.sh${NC}"
fi

# Script for auto-shutdown
cat > auto_shutdown.sh << 'EOF'
#!/bin/bash
# Auto-shutdown script for off-hours

# Add to crontab:
# 0 20 * * * /home/ubuntu/shutdown_instance.sh  # 8 PM shutdown
# 0 8 * * * /home/ubuntu/start_instance.sh      # 8 AM start

# Shutdown
aws ec2 stop-instances --instance-ids $(ec2-metadata --instance-id | cut -d " " -f 2)

# For start, you'd need a Lambda function or external trigger
EOF
chmod +x auto_shutdown.sh
echo -e "${GREEN}  Created: auto_shutdown.sh${NC}"

# Generate detailed report
REPORT_FILE="cost_optimization_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "AWS Cost Optimization Report"
    echo "==========================="
    echo "Generated: $(date)"
    echo "Account: ${ACCOUNT_ID:-N/A}"
    echo "Region: ${REGION}"
    echo ""
    echo "Current Monthly Estimate: \$${CURRENT_COST:-Unknown}"
    echo "Potential Savings: \$${TOTAL_SAVINGS}/month"
    echo "Optimized Cost: \$${OPTIMIZED_COST:-Unknown}"
    echo ""
    echo "Recommendations:"
    for opportunity in "${SAVINGS_OPPORTUNITIES[@]}"; do
        echo "  - $opportunity"
    done
    echo ""
    echo "Free Tier Usage:"
    echo "  - EC2: 750 hours t2.micro"
    echo "  - EBS: 30GB storage"
    echo "  - S3: 5GB storage"
    echo "  - Data Transfer: 15GB out"
} > "$REPORT_FILE"

echo -e "\n${GREEN}📄 Detailed report saved to: ${REPORT_FILE}${NC}"

# Cost tracking setup
echo -e "\n${BLUE}📊 Setting up cost tracking...${NC}"

cat > track_costs.sh << 'EOF'
#!/bin/bash
# Weekly cost tracking

# Get current month costs
aws ce get-cost-and-usage \
    --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics "UnblendedCost" \
    --group-by Type=DIMENSION,Key=SERVICE \
    | jq -r '.ResultsByTime[0].Groups[] | "\(.Keys[0]): $\(.Metrics.UnblendedCost.Amount)"' \
    | sort -k2 -nr
EOF

chmod +x track_costs.sh
echo -e "${GREEN}  Created: track_costs.sh${NC}"

echo -e "\n${BLUE}💡 Next Steps:${NC}"
echo -e "  1. Review savings opportunities above"
echo -e "  2. Implement quick wins (delete unused resources)"
echo -e "  3. Plan instance type changes during maintenance"
echo -e "  4. Set up cost alerts in AWS Billing"
echo -e "  5. Run ./track_costs.sh weekly"
echo ""