#!/bin/bash
#
# audit-aws-resources.sh - Comprehensive AWS resource audit for us-east-1
#
# This script checks for all potentially billable AWS resources
#
# Usage: ./audit-aws-resources.sh

# Configuration
AWS_REGION="us-east-1"
PROJECT_NAME="liap-tui"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}AWS Resource Audit - Region: $AWS_REGION${NC}"
echo "============================================"
echo "Checking for all resources that might cost money..."
echo ""

# Function to check if command succeeded
check_resource() {
    local resource_name=$1
    local count=$2

    if [ "$count" = "0" ] || [ -z "$count" ]; then
        echo -e "${GREEN}✓ No ${resource_name} found${NC}"
    else
        echo -e "${RED}✗ Found ${count} ${resource_name}${NC}"
    fi
}

# 1. EC2 Instances
echo -e "${BLUE}1. EC2 Instances:${NC}"
INSTANCE_COUNT=$(aws ec2 describe-instances \
    --region $AWS_REGION \
    --filters "Name=instance-state-name,Values=running,stopped" \
    --query 'length(Reservations[].Instances[])' \
    --output text 2>/dev/null || echo "0")

if [ "$INSTANCE_COUNT" != "0" ]; then
    echo -e "${RED}✗ Found ${INSTANCE_COUNT} EC2 instance(s)${NC}"
    aws ec2 describe-instances \
        --region $AWS_REGION \
        --filters "Name=instance-state-name,Values=running,stopped" \
        --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' \
        --output table
else
    echo -e "${GREEN}✓ No EC2 instances found${NC}"
fi
echo ""

# 2. Elastic IPs
echo -e "${BLUE}2. Elastic IPs:${NC}"
ELASTIC_IPS=$(aws ec2 describe-addresses \
    --region $AWS_REGION \
    --query 'Addresses[].[PublicIp,AllocationId,InstanceId,AssociationId]' \
    --output text 2>/dev/null || echo "")

if [ -n "$ELASTIC_IPS" ]; then
    echo -e "${RED}✗ Found Elastic IP(s):${NC}"
    echo "$ELASTIC_IPS" | while IFS=$'\t' read -r ip allocation instance association; do
        if [ -z "$instance" ] || [ "$instance" = "None" ]; then
            echo -e "  ${RED}$ip - UNATTACHED (costs \$3.60/month)${NC}"
        else
            echo -e "  ${YELLOW}$ip - Attached to $instance${NC}"
        fi
    done
else
    echo -e "${GREEN}✓ No Elastic IPs found${NC}"
fi
echo ""

# 3. EBS Volumes
echo -e "${BLUE}3. EBS Volumes:${NC}"
VOLUME_COUNT=$(aws ec2 describe-volumes \
    --region $AWS_REGION \
    --query 'length(Volumes)' \
    --output text 2>/dev/null || echo "0")

if [ "$VOLUME_COUNT" != "0" ]; then
    echo -e "${RED}✗ Found ${VOLUME_COUNT} EBS volume(s):${NC}"
    aws ec2 describe-volumes \
        --region $AWS_REGION \
        --query 'Volumes[].[VolumeId,Size,State,Attachments[0].InstanceId]' \
        --output table

    # Calculate total size
    TOTAL_SIZE=$(aws ec2 describe-volumes \
        --region $AWS_REGION \
        --query 'sum(Volumes[].Size)' \
        --output text 2>/dev/null || echo "0")
    VOLUME_COST=$(echo "$TOTAL_SIZE * 0.08" | bc)
    echo -e "${YELLOW}  Total: ${TOTAL_SIZE}GB (~\$${VOLUME_COST}/month)${NC}"
else
    echo -e "${GREEN}✓ No EBS volumes found${NC}"
fi
echo ""

# 4. EBS Snapshots
echo -e "${BLUE}4. EBS Snapshots:${NC}"
SNAPSHOT_COUNT=$(aws ec2 describe-snapshots \
    --owner-ids self \
    --region $AWS_REGION \
    --query 'length(Snapshots)' \
    --output text 2>/dev/null || echo "0")

if [ "$SNAPSHOT_COUNT" != "0" ]; then
    echo -e "${YELLOW}⚠ Found ${SNAPSHOT_COUNT} snapshot(s)${NC}"
    SNAPSHOT_SIZE=$(aws ec2 describe-snapshots \
        --owner-ids self \
        --region $AWS_REGION \
        --query 'sum(Snapshots[].VolumeSize)' \
        --output text 2>/dev/null || echo "0")
    SNAPSHOT_COST=$(echo "$SNAPSHOT_SIZE * 0.05" | bc)
    echo -e "${YELLOW}  Total: ${SNAPSHOT_SIZE}GB (~\$${SNAPSHOT_COST}/month)${NC}"
else
    echo -e "${GREEN}✓ No snapshots found${NC}"
fi
echo ""

# 5. Load Balancers (ALB/NLB)
echo -e "${BLUE}5. Load Balancers:${NC}"
LB_COUNT=$(aws elbv2 describe-load-balancers \
    --region $AWS_REGION \
    --query 'length(LoadBalancers)' \
    --output text 2>/dev/null || echo "0")

if [ "$LB_COUNT" != "0" ]; then
    echo -e "${RED}✗ Found ${LB_COUNT} load balancer(s) (each costs ~\$20-25/month):${NC}"
    aws elbv2 describe-load-balancers \
        --region $AWS_REGION \
        --query 'LoadBalancers[].[LoadBalancerName,Type,State.Code,DNSName]' \
        --output table
else
    echo -e "${GREEN}✓ No load balancers found${NC}"
fi
echo ""

# 6. RDS Databases
echo -e "${BLUE}6. RDS Databases:${NC}"
RDS_COUNT=$(aws rds describe-db-instances \
    --region $AWS_REGION \
    --query 'length(DBInstances)' \
    --output text 2>/dev/null || echo "0")

if [ "$RDS_COUNT" != "0" ]; then
    echo -e "${RED}✗ Found ${RDS_COUNT} RDS instance(s):${NC}"
    aws rds describe-db-instances \
        --region $AWS_REGION \
        --query 'DBInstances[].[DBInstanceIdentifier,DBInstanceClass,Engine,DBInstanceStatus]' \
        --output table
else
    echo -e "${GREEN}✓ No RDS instances found${NC}"
fi
echo ""

# 7. NAT Gateways
echo -e "${BLUE}7. NAT Gateways:${NC}"
NAT_COUNT=$(aws ec2 describe-nat-gateways \
    --region $AWS_REGION \
    --filter "Name=state,Values=available,pending" \
    --query 'length(NatGateways)' \
    --output text 2>/dev/null || echo "0")

if [ "$NAT_COUNT" != "0" ]; then
    echo -e "${RED}✗ Found ${NAT_COUNT} NAT Gateway(s) (each costs ~\$45/month):${NC}"
    aws ec2 describe-nat-gateways \
        --region $AWS_REGION \
        --filter "Name=state,Values=available,pending" \
        --query 'NatGateways[].[NatGatewayId,State,PublicIp,PrivateIp]' \
        --output table
else
    echo -e "${GREEN}✓ No NAT gateways found${NC}"
fi
echo ""

# 8. VPC Endpoints (some cost money)
echo -e "${BLUE}8. VPC Endpoints:${NC}"
ENDPOINT_COUNT=$(aws ec2 describe-vpc-endpoints \
    --region $AWS_REGION \
    --query 'length(VpcEndpoints[?VpcEndpointType==`Interface`])' \
    --output text 2>/dev/null || echo "0")

if [ "$ENDPOINT_COUNT" != "0" ]; then
    echo -e "${YELLOW}⚠ Found ${ENDPOINT_COUNT} Interface endpoint(s) (may cost ~\$7.20/month each)${NC}"
else
    echo -e "${GREEN}✓ No interface endpoints found${NC}"
fi
echo ""

# 9. S3 Buckets (in us-east-1)
echo -e "${BLUE}9. S3 Buckets:${NC}"
S3_BUCKETS=$(aws s3api list-buckets \
    --query 'Buckets[].Name' \
    --output text 2>/dev/null || echo "")

if [ -n "$S3_BUCKETS" ]; then
    echo -e "${YELLOW}⚠ Checking S3 buckets for content:${NC}"
    for bucket in $S3_BUCKETS; do
        # Get bucket location
        BUCKET_REGION=$(aws s3api get-bucket-location \
            --bucket $bucket \
            --query 'LocationConstraint' \
            --output text 2>/dev/null || echo "unknown")

        # us-east-1 returns null for location
        if [ "$BUCKET_REGION" = "None" ] || [ "$BUCKET_REGION" = "" ]; then
            BUCKET_REGION="us-east-1"
        fi

        if [ "$BUCKET_REGION" = "us-east-1" ]; then
            # Get bucket size
            BUCKET_SIZE=$(aws s3 ls s3://$bucket --recursive --summarize 2>/dev/null | grep "Total Size" | awk '{print $3}' || echo "0")
            if [ -n "$BUCKET_SIZE" ] && [ "$BUCKET_SIZE" != "0" ]; then
                SIZE_MB=$(echo "$BUCKET_SIZE / 1024 / 1024" | bc)
                echo -e "  ${YELLOW}$bucket - ${SIZE_MB}MB${NC}"
            else
                echo -e "  ${GREEN}$bucket - empty${NC}"
            fi
        fi
    done
else
    echo -e "${GREEN}✓ No S3 buckets found${NC}"
fi
echo ""

# 10. CloudFront Distributions
echo -e "${BLUE}10. CloudFront Distributions:${NC}"
CF_COUNT=$(aws cloudfront list-distributions \
    --query 'DistributionList.Quantity' \
    --output text 2>/dev/null || echo "0")

if [ "$CF_COUNT" != "0" ]; then
    echo -e "${YELLOW}⚠ Found ${CF_COUNT} CloudFront distribution(s)${NC}"
    aws cloudfront list-distributions \
        --query 'DistributionList.Items[].[Id,DomainName,Enabled]' \
        --output table
else
    echo -e "${GREEN}✓ No CloudFront distributions found${NC}"
fi
echo ""

# 11. Route53 Hosted Zones
echo -e "${BLUE}11. Route53 Hosted Zones:${NC}"
ZONE_COUNT=$(aws route53 list-hosted-zones \
    --query 'length(HostedZones)' \
    --output text 2>/dev/null || echo "0")

if [ "$ZONE_COUNT" != "0" ]; then
    echo -e "${YELLOW}⚠ Found ${ZONE_COUNT} hosted zone(s) (each costs \$0.50/month)${NC}"
    aws route53 list-hosted-zones \
        --query 'HostedZones[].[Name,Config.PrivateZone]' \
        --output table
else
    echo -e "${GREEN}✓ No Route53 hosted zones found${NC}"
fi
echo ""

# 12. Lambda Functions
echo -e "${BLUE}12. Lambda Functions:${NC}"
LAMBDA_COUNT=$(aws lambda list-functions \
    --region $AWS_REGION \
    --query 'length(Functions)' \
    --output text 2>/dev/null || echo "0")

if [ "$LAMBDA_COUNT" != "0" ]; then
    echo -e "${YELLOW}⚠ Found ${LAMBDA_COUNT} Lambda function(s)${NC}"
    echo "(Lambda charges based on invocations)"
else
    echo -e "${GREEN}✓ No Lambda functions found${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}SUMMARY - Potential Monthly Costs:${NC}"
echo -e "${BLUE}============================================${NC}"

TOTAL_MONTHLY_COST=0
COST_ITEMS=""

# Add up potential costs
if [ "$INSTANCE_COUNT" != "0" ]; then
    # Rough estimate for t2.micro
    INSTANCE_COST=$(echo "$INSTANCE_COUNT * 8.40" | bc)
    TOTAL_MONTHLY_COST=$(echo "$TOTAL_MONTHLY_COST + $INSTANCE_COST" | bc)
    COST_ITEMS="${COST_ITEMS}EC2 Instances: ~\$${INSTANCE_COST}/month\n"
fi

if [ -n "$ELASTIC_IPS" ]; then
    UNATTACHED_COUNT=$(echo "$ELASTIC_IPS" | grep -c "UNATTACHED" || echo "0")
    if [ "$UNATTACHED_COUNT" != "0" ]; then
        EIP_COST=$(echo "$UNATTACHED_COUNT * 3.60" | bc)
        TOTAL_MONTHLY_COST=$(echo "$TOTAL_MONTHLY_COST + $EIP_COST" | bc)
        COST_ITEMS="${COST_ITEMS}Unattached Elastic IPs: ~\$${EIP_COST}/month\n"
    fi
fi

if [ "$VOLUME_COUNT" != "0" ]; then
    TOTAL_MONTHLY_COST=$(echo "$TOTAL_MONTHLY_COST + $VOLUME_COST" | bc)
    COST_ITEMS="${COST_ITEMS}EBS Volumes: ~\$${VOLUME_COST}/month\n"
fi

if [ "$LB_COUNT" != "0" ]; then
    LB_COST=$(echo "$LB_COUNT * 22.50" | bc)
    TOTAL_MONTHLY_COST=$(echo "$TOTAL_MONTHLY_COST + $LB_COST" | bc)
    COST_ITEMS="${COST_ITEMS}Load Balancers: ~\$${LB_COST}/month\n"
fi

if [ "$NAT_COUNT" != "0" ]; then
    NAT_COST=$(echo "$NAT_COUNT * 45" | bc)
    TOTAL_MONTHLY_COST=$(echo "$TOTAL_MONTHLY_COST + $NAT_COST" | bc)
    COST_ITEMS="${COST_ITEMS}NAT Gateways: ~\$${NAT_COST}/month\n"
fi

if [ $(echo "$TOTAL_MONTHLY_COST > 0" | bc -l) -eq 1 ]; then
    echo -e "${RED}💸 Estimated total monthly cost: \$${TOTAL_MONTHLY_COST}${NC}"
    echo -e "${RED}Breakdown:${NC}"
    echo -e "$COST_ITEMS"
else
    echo -e "${GREEN}✅ No significant ongoing charges detected!${NC}"
fi

echo ""
echo -e "${YELLOW}Note: This audit covers major services in $AWS_REGION.${NC}"
echo -e "${YELLOW}Check your AWS Cost Explorer for complete billing details.${NC}"
