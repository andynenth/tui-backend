#!/bin/bash

# AWS Migration to Free Tier Script
# Migrates existing instance to t2.micro free tier

echo "===================================="
echo "AWS FREE TIER MIGRATION SCRIPT"
echo "===================================="
echo ""

# Configuration
SOURCE_REGION="ap-northeast-1"  # Tokyo
TARGET_REGION="us-east-1"       # N. Virginia (better free tier)
INSTANCE_TYPE="t2.micro"        # Free tier eligible

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not installed${NC}"
    echo "Install with: brew install awscli"
    exit 1
fi

echo -e "${GREEN}Step 1: Finding running instances...${NC}"
INSTANCE_ID=$(aws ec2 describe-instances \
    --region $SOURCE_REGION \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

if [ "$INSTANCE_ID" == "None" ] || [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}No running instances found in $SOURCE_REGION${NC}"
    echo "Checking US East region..."
    SOURCE_REGION="us-east-1"
    INSTANCE_ID=$(aws ec2 describe-instances \
        --region $SOURCE_REGION \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[0].Instances[0].InstanceId' \
        --output text)
fi

if [ "$INSTANCE_ID" == "None" ] || [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}No running instances found${NC}"
    exit 1
fi

echo -e "${GREEN}Found instance: $INSTANCE_ID in $SOURCE_REGION${NC}"

# Get instance details
INSTANCE_NAME=$(aws ec2 describe-instances \
    --region $SOURCE_REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].Tags[?Key==`Name`].Value' \
    --output text)

echo ""
echo -e "${GREEN}Step 2: Creating AMI snapshot...${NC}"
AMI_NAME="migration-snapshot-$(date +%Y%m%d-%H%M%S)"

AMI_ID=$(aws ec2 create-image \
    --region $SOURCE_REGION \
    --instance-id $INSTANCE_ID \
    --name "$AMI_NAME" \
    --description "Migration snapshot for free tier" \
    --no-reboot \
    --query 'ImageId' \
    --output text)

echo "Created AMI: $AMI_ID"
echo "Waiting for AMI to be available (this may take 5-10 minutes)..."

aws ec2 wait image-available \
    --region $SOURCE_REGION \
    --image-ids $AMI_ID

echo -e "${GREEN}AMI is ready!${NC}"

echo ""
echo -e "${GREEN}Step 3: Launching FREE TIER t2.micro instance...${NC}"

# Get the default VPC
VPC_ID=$(aws ec2 describe-vpcs \
    --region $TARGET_REGION \
    --filters "Name=is-default,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text)

# Get subnet in the VPC
SUBNET_ID=$(aws ec2 describe-subnets \
    --region $TARGET_REGION \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[0].SubnetId' \
    --output text)

# Create or update security group
SG_NAME="free-tier-web-sg"
SG_ID=$(aws ec2 describe-security-groups \
    --region $TARGET_REGION \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null)

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
    echo "Creating security group..."
    SG_ID=$(aws ec2 create-security-group \
        --region $TARGET_REGION \
        --group-name $SG_NAME \
        --description "Free tier web server security group" \
        --vpc-id $VPC_ID \
        --query 'GroupId' \
        --output text)

    # Add SSH rule
    aws ec2 authorize-security-group-ingress \
        --region $TARGET_REGION \
        --group-id $SG_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0

    # Add HTTP rule
    aws ec2 authorize-security-group-ingress \
        --region $TARGET_REGION \
        --group-id $SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0

    # Add HTTPS rule
    aws ec2 authorize-security-group-ingress \
        --region $TARGET_REGION \
        --group-id $SG_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0
fi

# Find the latest Amazon Linux 2 AMI (free tier eligible)
FREE_AMI=$(aws ec2 describe-images \
    --region $TARGET_REGION \
    --owners amazon \
    --filters \
        "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
        "Name=state,Values=available" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text)

echo "Using Amazon Linux 2 AMI: $FREE_AMI"

# Launch the instance
NEW_INSTANCE=$(aws ec2 run-instances \
    --region $TARGET_REGION \
    --image-id $FREE_AMI \
    --instance-type $INSTANCE_TYPE \
    --security-group-ids $SG_ID \
    --subnet-id $SUBNET_ID \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=free-tier-${INSTANCE_NAME:-server}}]" \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":8,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo -e "${GREEN}Launched new FREE TIER instance: $NEW_INSTANCE${NC}"

echo "Waiting for instance to be running..."
aws ec2 wait instance-running \
    --region $TARGET_REGION \
    --instance-ids $NEW_INSTANCE

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --region $TARGET_REGION \
    --instance-ids $NEW_INSTANCE \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo -e "${GREEN}Step 4: Instance Details${NC}"
echo "================================"
echo "Instance ID: $NEW_INSTANCE"
echo "Region: $TARGET_REGION"
echo "Type: $INSTANCE_TYPE (FREE TIER)"
echo "Public IP: $PUBLIC_IP"
echo "================================"

echo ""
echo -e "${YELLOW}Step 5: Data Migration Options${NC}"
echo "Choose your migration method:"
echo ""
echo "Option A: Manual data copy (recommended for simple apps)"
echo "  ssh ec2-user@$PUBLIC_IP"
echo "  # Then copy your application files"
echo ""
echo "Option B: Create AMI in target region (for exact clone)"
echo "  # Copy AMI to target region:"
echo "  aws ec2 copy-image --source-region $SOURCE_REGION --source-image-id $AMI_ID --region $TARGET_REGION --name '$AMI_NAME-copy'"
echo ""

echo -e "${GREEN}Step 6: IMPORTANT - Cost Saving Actions${NC}"
echo "After verifying the new instance works:"
echo ""
echo "1. TERMINATE the old instance:"
echo -e "${RED}  aws ec2 terminate-instances --region $SOURCE_REGION --instance-ids $INSTANCE_ID${NC}"
echo ""
echo "2. Delete the old EBS volumes:"
echo "  aws ec2 describe-volumes --region $SOURCE_REGION --filters Name=status,Values=available"
echo "  aws ec2 delete-volume --region $SOURCE_REGION --volume-id <volume-id>"
echo ""
echo "3. Release Elastic IPs:"
echo "  aws ec2 release-address --region $SOURCE_REGION --allocation-id <allocation-id>"
echo ""

# Create a cleanup script
cat > cleanup_old_resources.sh << 'EOF'
#!/bin/bash
# Run this AFTER confirming new instance works

echo "This will DELETE your old resources. Are you sure? (yes/no)"
read CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled"
    exit 1
fi

SOURCE_REGION="ap-northeast-1"

# Terminate old instance
aws ec2 terminate-instances --region $SOURCE_REGION --instance-ids $(aws ec2 describe-instances --region $SOURCE_REGION --filters "Name=instance-state-name,Values=running,stopped" --query 'Reservations[].Instances[].InstanceId' --output text)

# Wait for termination
sleep 30

# Delete volumes
aws ec2 describe-volumes --region $SOURCE_REGION --filters Name=status,Values=available --query 'Volumes[].VolumeId' --output text | xargs -I {} aws ec2 delete-volume --region $SOURCE_REGION --volume-id {}

# Release IPs
aws ec2 describe-addresses --region $SOURCE_REGION --query 'Addresses[].AllocationId' --output text | xargs -I {} aws ec2 release-address --region $SOURCE_REGION --allocation-id {}

echo "Cleanup complete!"
EOF

chmod +x cleanup_old_resources.sh

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo "Created cleanup_old_resources.sh - run this after testing"
echo ""
echo -e "${YELLOW}FREE TIER LIMITS:${NC}"
echo "✓ 750 hours/month t2.micro (covers 24/7 for one instance)"
echo "✓ 30 GB EBS storage (we used 8 GB)"
echo "✓ 15 GB bandwidth"
echo "✓ Valid for 12 months from AWS account creation"
