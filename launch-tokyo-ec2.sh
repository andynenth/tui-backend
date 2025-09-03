#!/bin/bash
# Script to launch EC2 instance in Tokyo for Liap Tui

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🗾 Launching EC2 instance in Tokyo (ap-northeast-1)...${NC}"

# Configuration
REGION="ap-northeast-1"
INSTANCE_TYPE="t3.medium"
KEY_NAME="liap-tui-tokyo-key"
SECURITY_GROUP_NAME="liap-tui-tokyo-sg"
INSTANCE_NAME="Liap-Tui-Tokyo"

# Ubuntu 22.04 LTS AMI for Tokyo region
AMI_ID="ami-0d52744d6551d851e"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found! Please install it first.${NC}"
    echo "Visit: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity --region $REGION &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured!${NC}"
    echo "Run: aws configure"
    exit 1
fi

# Create key pair if it doesn't exist
echo -e "${GREEN}🔑 Checking key pair...${NC}"
if ! aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION &> /dev/null; then
    echo "Creating new key pair..."
    aws ec2 create-key-pair --key-name $KEY_NAME --region $REGION \
        --query 'KeyMaterial' --output text > ~/.ssh/${KEY_NAME}.pem
    chmod 400 ~/.ssh/${KEY_NAME}.pem
    echo -e "${GREEN}✅ Key pair created: ~/.ssh/${KEY_NAME}.pem${NC}"
else
    echo -e "${YELLOW}Key pair already exists${NC}"
fi

# Create security group if it doesn't exist
echo -e "${GREEN}🛡️  Setting up security group...${NC}"
SG_ID=$(aws ec2 describe-security-groups --group-names $SECURITY_GROUP_NAME --region $REGION \
    --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")

if [ -z "$SG_ID" ] || [ "$SG_ID" == "None" ]; then
    echo "Creating new security group..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SECURITY_GROUP_NAME \
        --description "Security group for Liap Tui game server" \
        --region $REGION \
        --output text --query 'GroupId')
    
    # Add security group rules
    echo "Adding security rules..."
    
    # SSH (restrict to your IP)
    MY_IP=$(curl -s https://checkip.amazonaws.com)
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp --port 22 --cidr ${MY_IP}/32 \
        --region $REGION
    
    # HTTP
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp --port 80 --cidr 0.0.0.0/0 \
        --region $REGION
    
    # HTTPS
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp --port 443 --cidr 0.0.0.0/0 \
        --region $REGION
    
    # Game port (for testing)
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp --port 5050 --cidr 0.0.0.0/0 \
        --region $REGION
    
    echo -e "${GREEN}✅ Security group created: $SG_ID${NC}"
else
    echo -e "${YELLOW}Security group already exists: $SG_ID${NC}"
fi

# Launch EC2 instance
echo -e "${GREEN}🚀 Launching EC2 instance...${NC}"
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --region $REGION \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3}" \
    --output text --query 'Instances[0].InstanceId')

echo -e "${YELLOW}Instance ID: $INSTANCE_ID${NC}"

# Wait for instance to be running
echo -e "${YELLOW}⏳ Waiting for instance to start...${NC}"
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo -e "${GREEN}✅ Instance launched successfully!${NC}"
echo
echo -e "${GREEN}📋 Instance Details:${NC}"
echo "   Region: $REGION (Tokyo)"
echo "   Instance ID: $INSTANCE_ID"
echo "   Public IP: $PUBLIC_IP"
echo "   Key File: ~/.ssh/${KEY_NAME}.pem"
echo
echo -e "${GREEN}🎯 Next Steps:${NC}"
echo "1. Update deploy-ec2-ssl-tokyo-no-rebuild.sh:"
echo "   EC2_HOST=\"$PUBLIC_IP\""
echo "   KEY_PATH=\"~/.ssh/${KEY_NAME}.pem\""
echo
echo "2. Copy and run server setup:"
echo "   scp -i ~/.ssh/${KEY_NAME}.pem tokyo-server-setup.sh ubuntu@${PUBLIC_IP}:~/"
echo "   ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo "   sudo ./tokyo-server-setup.sh"
echo
echo "3. Deploy your game:"
echo "   ./deploy-ec2-ssl-tokyo-no-rebuild.sh"
echo
echo -e "${YELLOW}💡 Tip: Save this IP for your DNS update: $PUBLIC_IP${NC}"

# Save instance details to file
echo "{
  \"region\": \"$REGION\",
  \"instance_id\": \"$INSTANCE_ID\",
  \"public_ip\": \"$PUBLIC_IP\",
  \"key_path\": \"~/.ssh/${KEY_NAME}.pem\",
  \"security_group_id\": \"$SG_ID\",
  \"created_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
}" > tokyo-instance-details.json

echo
echo -e "${GREEN}✅ Instance details saved to: tokyo-instance-details.json${NC}"