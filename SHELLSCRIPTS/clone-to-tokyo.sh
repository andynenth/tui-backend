#!/bin/bash
# Clone current EC2 to Tokyo region

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔄 Cloning US-East EC2 to Tokyo...${NC}"

# Configuration
SOURCE_INSTANCE_ID=""  # We'll find this
SOURCE_REGION="us-east-1"
TARGET_REGION="ap-northeast-1"
TARGET_INSTANCE_IP="54.250.35.226"  # Your new Tokyo instance

# Find the source instance ID by IP
echo -e "${YELLOW}Finding source instance ID...${NC}"
SOURCE_INSTANCE_ID=$(aws ec2 describe-instances \
    --filters "Name=ip-address,Values=34.233.7.20" \
    --region $SOURCE_REGION \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

if [ -z "$SOURCE_INSTANCE_ID" ] || [ "$SOURCE_INSTANCE_ID" == "None" ]; then
    echo -e "${RED}❌ Could not find instance with IP 34.233.7.20${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found source instance: $SOURCE_INSTANCE_ID${NC}"

# Step 1: Create AMI from source instance
AMI_NAME="liap-tui-backup-$(date +%Y%m%d-%H%M%S)"
echo -e "${YELLOW}📸 Creating AMI from source instance...${NC}"
echo "This may take 5-10 minutes..."

AMI_ID=$(aws ec2 create-image \
    --instance-id $SOURCE_INSTANCE_ID \
    --name "$AMI_NAME" \
    --description "Backup of Liap Tui server for Tokyo migration" \
    --region $SOURCE_REGION \
    --output text)

echo -e "${GREEN}✅ AMI creation started: $AMI_ID${NC}"

# Wait for AMI to be available
echo -e "${YELLOW}⏳ Waiting for AMI to be ready...${NC}"
aws ec2 wait image-available --image-ids $AMI_ID --region $SOURCE_REGION
echo -e "${GREEN}✅ AMI is ready!${NC}"

# Step 2: Copy AMI to Tokyo region
echo -e "${YELLOW}📋 Copying AMI to Tokyo region...${NC}"
TOKYO_AMI_ID=$(aws ec2 copy-image \
    --source-image-id $AMI_ID \
    --source-region $SOURCE_REGION \
    --region $TARGET_REGION \
    --name "$AMI_NAME-tokyo" \
    --description "Tokyo copy of Liap Tui server" \
    --output text)

echo -e "${GREEN}✅ AMI copy started: $TOKYO_AMI_ID${NC}"

# Wait for Tokyo AMI to be available
echo -e "${YELLOW}⏳ Waiting for Tokyo AMI to be ready...${NC}"
echo "This may take 10-20 minutes..."
aws ec2 wait image-available --image-ids $TOKYO_AMI_ID --region $TARGET_REGION
echo -e "${GREEN}✅ Tokyo AMI is ready!${NC}"

# Save AMI information
echo "{
  \"source_ami_id\": \"$AMI_ID\",
  \"tokyo_ami_id\": \"$TOKYO_AMI_ID\",
  \"created_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
}" > tokyo-ami-details.json

echo -e "${GREEN}✅ AMI details saved to: tokyo-ami-details.json${NC}"
echo
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. You now have an exact copy of your server as an AMI in Tokyo"
echo "2. You can launch a new instance from this AMI: $TOKYO_AMI_ID"
echo "3. Or restore your existing Tokyo instance from this AMI"
echo
echo -e "${YELLOW}💡 To launch from this AMI:${NC}"
echo "aws ec2 run-instances \\"
echo "    --image-id $TOKYO_AMI_ID \\"
echo "    --instance-type t3.medium \\"
echo "    --key-name liap-tui-tokyo-key \\"
echo "    --security-group-ids sg-021680f0aafc22cf8 \\"
echo "    --region ap-northeast-1"
