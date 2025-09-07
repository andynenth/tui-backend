#\!/bin/bash
# AWS EC2 Instance Launch Helper Script for Liap Tui

set -e

# Configuration
REGION="${AWS_REGION:-us-east-1}"
AMI_ID="${AMI_ID:-}"  # Will be populated based on region
INSTANCE_TYPE="${INSTANCE_TYPE:-t2.micro}"
KEY_NAME="${KEY_NAME:-}"
SECURITY_GROUP_NAME="${SECURITY_GROUP_NAME:-liap-tui-sg}"
INSTANCE_NAME="${INSTANCE_NAME:-liap-tui-game-server}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Liap Tui EC2 Instance Launcher${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Check AWS CLI
if \! command -v aws &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI not installed${NC}"
    echo "Install instructions: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
if \! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

# Function to get Ubuntu 22.04 AMI ID for the region
get_ubuntu_ami() {
    echo -e "${YELLOW}🔍 Finding Ubuntu 22.04 LTS AMI for ${REGION}...${NC}"

    AMI_ID=$(aws ec2 describe-images \
        --region $REGION \
        --owners 099720109477 \
        --filters \
            "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
            "Name=state,Values=available" \
        --query 'Images[0].ImageId' \
        --output text)

    if [ "$AMI_ID" = "None" ] || [ -z "$AMI_ID" ]; then
        echo -e "${RED}❌ Error: Could not find Ubuntu 22.04 AMI${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Found AMI: ${AMI_ID}${NC}"
}

# Step 1: Get AMI ID
get_ubuntu_ami

# Step 2: Check/Create Key Pair
echo -e "\n${YELLOW}🔑 Checking SSH Key Pair...${NC}"

if [ -z "$KEY_NAME" ]; then
    echo -e "${YELLOW}Enter your SSH key pair name (or press Enter to create new):${NC}"
    read -r KEY_INPUT

    if [ -z "$KEY_INPUT" ]; then
        KEY_NAME="liap-tui-key-$(date +%s)"
        echo -e "${YELLOW}Creating new key pair: ${KEY_NAME}${NC}"

        aws ec2 create-key-pair \
            --key-name $KEY_NAME \
            --query 'KeyMaterial' \
            --output text \
            --region $REGION > "${KEY_NAME}.pem"

        chmod 400 "${KEY_NAME}.pem"
        echo -e "${GREEN}✅ Key pair created and saved to: ${KEY_NAME}.pem${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Keep this file safe\! You'll need it to connect to your instance.${NC}"
    else
        KEY_NAME="$KEY_INPUT"
        echo -e "${GREEN}✅ Using existing key pair: ${KEY_NAME}${NC}"
    fi
fi

# Step 3: Create Security Group
echo -e "\n${YELLOW}🔒 Creating Security Group...${NC}"

# Check if security group exists
SG_ID=$(aws ec2 describe-security-groups \
    --group-names $SECURITY_GROUP_NAME \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ -z "$SG_ID" ] || [ "$SG_ID" = "None" ]; then
    echo -e "${YELLOW}Creating new security group...${NC}"

    SG_ID=$(aws ec2 create-security-group \
        --group-name $SECURITY_GROUP_NAME \
        --description "Security group for Liap Tui game server" \
        --region $REGION \
        --query 'GroupId' \
        --output text)

    # Add SSH rule (your IP only)
    MY_IP=$(curl -s https://checkip.amazonaws.com)
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 22 \
        --cidr ${MY_IP}/32 \
        --region $REGION

    # Add HTTP rule (open to all)
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region $REGION

    # Add HTTPS rule for future use
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region $REGION

    echo -e "${GREEN}✅ Security group created: ${SG_ID}${NC}"
else
    echo -e "${GREEN}✅ Using existing security group: ${SG_ID}${NC}"
fi

# Step 4: Launch Instance
echo -e "\n${YELLOW}🚀 Launching EC2 Instance...${NC}"

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --region $REGION \
    --query 'Instances[0].InstanceId' \
    --output text)

echo -e "${GREEN}✅ Instance launched: ${INSTANCE_ID}${NC}"

# Step 5: Wait for instance to be running
echo -e "\n${YELLOW}⏳ Waiting for instance to start...${NC}"
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Step 6: Allocate and Associate Elastic IP
echo -e "\n${YELLOW}🌐 Allocating Elastic IP...${NC}"

ALLOCATION_ID=$(aws ec2 allocate-address \
    --domain vpc \
    --region $REGION \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=liap-tui-eip}]" \
    --query 'AllocationId' \
    --output text)

ELASTIC_IP=$(aws ec2 describe-addresses \
    --allocation-ids $ALLOCATION_ID \
    --region $REGION \
    --query 'Addresses[0].PublicIp' \
    --output text)

echo -e "${GREEN}✅ Elastic IP allocated: ${ELASTIC_IP}${NC}"

# Associate Elastic IP with instance
aws ec2 associate-address \
    --instance-id $INSTANCE_ID \
    --allocation-id $ALLOCATION_ID \
    --region $REGION

echo -e "${GREEN}✅ Elastic IP associated with instance${NC}"

# Step 7: Get instance details
echo -e "\n${BLUE}📋 Instance Details:${NC}"
echo -e "${BLUE}===================${NC}"
echo -e "Instance ID: ${INSTANCE_ID}"
echo -e "Instance Type: ${INSTANCE_TYPE}"
echo -e "Elastic IP: ${ELASTIC_IP}"
echo -e "Key Pair: ${KEY_NAME}"
echo -e "Security Group: ${SG_ID}"
echo -e "Region: ${REGION}"

# Step 8: Wait for SSH to be ready
echo -e "\n${YELLOW}⏳ Waiting for SSH to be ready (this may take 1-2 minutes)...${NC}"
sleep 30

while \! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i "${KEY_NAME}.pem" ubuntu@${ELASTIC_IP} "echo 'SSH is ready'" 2>/dev/null; do
    echo -n "."
    sleep 10
done
echo ""
echo -e "${GREEN}✅ SSH is ready\!${NC}"

# Step 9: Generate connection script
cat > connect-to-ec2.sh << SCRIPT_EOF
#\!/bin/bash
# Connect to Liap Tui EC2 instance

ssh -i "${KEY_NAME}.pem" ubuntu@${ELASTIC_IP}
SCRIPT_EOF

chmod +x connect-to-ec2.sh

# Step 10: Update deployment script
sed -i.bak "s/EC2_HOST=\"your-ec2-ip-here\"/EC2_HOST=\"${ELASTIC_IP}\"/" deploy-ec2.sh
sed -i.bak "s < /dev/null | KEY_PATH=\"~/.ssh/your-key.pem\"|KEY_PATH=\"${PWD}/${KEY_NAME}.pem\"|" deploy-ec2.sh

# Step 11: Save instance details
cat > ec2-instance-details.txt << DETAILS_EOF
Liap Tui EC2 Instance Details
============================
Created: $(date)

Instance ID: ${INSTANCE_ID}
Instance Type: ${INSTANCE_TYPE}
Elastic IP: ${ELASTIC_IP}
SSH Key: ${KEY_NAME}.pem
Security Group: ${SG_ID}
Region: ${REGION}

Connection Command:
  ssh -i ${KEY_NAME}.pem ubuntu@${ELASTIC_IP}

Or use:
  ./connect-to-ec2.sh

Deployment:
  EC2_HOST has been updated in deploy-ec2.sh
  KEY_PATH has been updated in deploy-ec2.sh
DETAILS_EOF

echo -e "\n${GREEN}🎉 EC2 instance successfully launched\!${NC}"
echo -e "\n${BLUE}📝 Next Steps:${NC}"
echo -e "1. Connect to your instance:"
echo -e "   ${GREEN}./connect-to-ec2.sh${NC}"
echo -e ""
echo -e "2. Run the setup script on EC2:"
echo -e "   ${GREEN}scp -i ${KEY_NAME}.pem ec2-setup.sh ubuntu@${ELASTIC_IP}:~/${NC}"
echo -e "   ${GREEN}ssh -i ${KEY_NAME}.pem ubuntu@${ELASTIC_IP} 'chmod +x ec2-setup.sh && ./ec2-setup.sh'${NC}"
echo -e ""
echo -e "3. Deploy your application:"
echo -e "   ${GREEN}./deploy-ec2.sh${NC}"
echo -e ""
echo -e "${YELLOW}⚠️  Important files created:${NC}"
echo -e "  - ${KEY_NAME}.pem (SSH private key - keep this safe\!)"
echo -e "  - connect-to-ec2.sh (Quick connection script)"
echo -e "  - ec2-instance-details.txt (Instance information)"
echo -e ""
echo -e "${GREEN}Instance details saved to: ec2-instance-details.txt${NC}"
