#!/bin/bash

# Downgrade Tokyo instance from t3.medium to t2.micro
# This will save ~$39/month in costs

set -e

# Configuration
REGION="ap-northeast-1"  # Tokyo
CURRENT_IP="54.250.35.226"
INSTANCE_TYPE="t2.micro"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🗾 Tokyo Instance Downgrade to t2.micro${NC}"
echo -e "${GREEN}💰 This will save ~$39/month${NC}"
echo ""

# Find the current instance by IP
echo -e "${YELLOW}Finding current Tokyo instance...${NC}"
CURRENT_INSTANCE=$(aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=ip-address,Values=$CURRENT_IP" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

if [ "$CURRENT_INSTANCE" == "None" ] || [ -z "$CURRENT_INSTANCE" ]; then
    echo -e "${RED}❌ Could not find running instance with IP $CURRENT_IP${NC}"
    exit 1
fi

echo -e "${GREEN}Found instance: $CURRENT_INSTANCE${NC}"

# Get current instance details
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $CURRENT_INSTANCE \
    --query 'Reservations[0].Instances[0]')

CURRENT_TYPE=$(echo $INSTANCE_INFO | jq -r '.InstanceType')
SUBNET_ID=$(echo $INSTANCE_INFO | jq -r '.SubnetId')
SECURITY_GROUPS=$(echo $INSTANCE_INFO | jq -r '.SecurityGroups[].GroupId' | tr '\n' ' ')
KEY_NAME=$(echo $INSTANCE_INFO | jq -r '.KeyName')
INSTANCE_NAME=$(echo $INSTANCE_INFO | jq -r '.Tags[]? | select(.Key=="Name") | .Value // "tokyo-server"')

echo -e "${YELLOW}Current type: $CURRENT_TYPE${NC}"
echo -e "${YELLOW}Target type: $INSTANCE_TYPE${NC}"

if [ "$CURRENT_TYPE" == "$INSTANCE_TYPE" ]; then
    echo -e "${GREEN}✅ Instance is already $INSTANCE_TYPE!${NC}"
    echo -e "${GREEN}No downgrade needed - you're already on the cheapest option${NC}"
    exit 0
fi

# Get Elastic IP allocation ID
echo -e "${YELLOW}Finding Elastic IP...${NC}"
EIP_ALLOC=$(aws ec2 describe-addresses \
    --region $REGION \
    --filters "Name=instance-id,Values=$CURRENT_INSTANCE" \
    --query 'Addresses[0].AllocationId' \
    --output text)

if [ "$EIP_ALLOC" == "None" ] || [ -z "$EIP_ALLOC" ]; then
    echo -e "${RED}❌ No Elastic IP found attached to instance${NC}"
    echo -e "${YELLOW}We'll need to use the auto-assigned public IP${NC}"
    EIP_ALLOC=""
fi

echo ""
echo -e "${YELLOW}💾 Step 1: Creating AMI snapshot...${NC}"
AMI_NAME="tokyo-downgrade-$(date +%Y%m%d-%H%M%S)"

AMI_ID=$(aws ec2 create-image \
    --region $REGION \
    --instance-id $CURRENT_INSTANCE \
    --name "$AMI_NAME" \
    --description "Pre-downgrade snapshot of $INSTANCE_NAME" \
    --no-reboot \
    --query 'ImageId' \
    --output text)

echo -e "${GREEN}Created AMI: $AMI_ID${NC}"
echo -e "${YELLOW}Waiting for AMI to be available (5-10 minutes)...${NC}"

aws ec2 wait image-available \
    --region $REGION \
    --image-ids $AMI_ID

echo -e "${GREEN}✅ AMI snapshot complete!${NC}"

echo ""
echo -e "${YELLOW}🚀 Step 2: Launching new t2.micro instance...${NC}"

# Launch new t2.micro instance
NEW_INSTANCE=$(aws ec2 run-instances \
    --region $REGION \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --subnet-id $SUBNET_ID \
    --security-group-ids $SECURITY_GROUPS \
    --key-name $KEY_NAME \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME-t2micro}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo -e "${GREEN}Launched new instance: $NEW_INSTANCE${NC}"

echo -e "${YELLOW}Waiting for instance to be running...${NC}"
aws ec2 wait instance-running \
    --region $REGION \
    --instance-ids $NEW_INSTANCE

echo ""
echo -e "${YELLOW}🔄 Step 3: Stopping old instance...${NC}"
aws ec2 stop-instances \
    --region $REGION \
    --instance-ids $CURRENT_INSTANCE

echo -e "${YELLOW}Waiting for instance to stop...${NC}"
aws ec2 wait instance-stopped \
    --region $REGION \
    --instance-ids $CURRENT_INSTANCE

# Transfer Elastic IP if it exists
if [ ! -z "$EIP_ALLOC" ]; then
    echo ""
    echo -e "${YELLOW}🔗 Step 4: Transferring Elastic IP...${NC}"

    # Disassociate from old instance
    aws ec2 disassociate-address \
        --region $REGION \
        --allocation-id $EIP_ALLOC || true

    # Associate with new instance
    aws ec2 associate-address \
        --region $REGION \
        --instance-id $NEW_INSTANCE \
        --allocation-id $EIP_ALLOC

    echo -e "${GREEN}✅ Elastic IP transferred to new instance${NC}"
    NEW_IP=$CURRENT_IP
else
    # Get new public IP
    NEW_IP=$(aws ec2 describe-instances \
        --region $REGION \
        --instance-ids $NEW_INSTANCE \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    echo -e "${YELLOW}⚠️  New public IP: $NEW_IP${NC}"
fi

echo ""
echo -e "${GREEN}✅ Downgrade Complete!${NC}"
echo "================================"
echo -e "${GREEN}New t2.micro instance: $NEW_INSTANCE${NC}"
echo -e "${GREEN}Public IP: $NEW_IP${NC}"
echo -e "${GREEN}Monthly savings: ~$39${NC}"
echo "================================"

echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo ""

if [ "$NEW_IP" != "$CURRENT_IP" ]; then
    echo -e "${YELLOW}1. Update deploy script IP address:${NC}"
    echo "   Change EC2_HOST from $CURRENT_IP to $NEW_IP"
    echo ""
    echo -e "${YELLOW}2. Update DNS if using domain:${NC}"
    echo "   Point castellan.andynenth.dev to $NEW_IP"
    echo ""
fi

echo -e "${YELLOW}3. Test the new instance:${NC}"
echo "   ssh -i ~/.ssh/liap-tui-tokyo-key.pem ubuntu@$NEW_IP"
echo ""

echo -e "${YELLOW}4. Deploy your application:${NC}"
echo "   Run your deploy script to verify everything works"
echo ""

echo -e "${YELLOW}5. Once verified, terminate the old instance:${NC}"
echo -e "${RED}   aws ec2 terminate-instances --region $REGION --instance-ids $CURRENT_INSTANCE${NC}"
echo ""

# Create cleanup script
cat > cleanup_old_instance.sh << EOF
#!/bin/bash
# Run this AFTER confirming new t2.micro instance works

echo "This will TERMINATE the old t3.medium instance. Are you sure? (yes/no)"
read CONFIRM
if [ "\$CONFIRM" != "yes" ]; then
    echo "Cancelled"
    exit 1
fi

echo "Terminating old instance $CURRENT_INSTANCE..."
aws ec2 terminate-instances --region $REGION --instance-ids $CURRENT_INSTANCE

echo "✅ Old instance terminated - you'll save ~\$39/month!"
EOF

chmod +x cleanup_old_instance.sh

echo -e "${GREEN}💡 Created cleanup_old_instance.sh for when you're ready${NC}"

# Update deploy script if needed
if [ "$NEW_IP" != "$CURRENT_IP" ]; then
    echo ""
    echo -e "${YELLOW}🔧 Updating deploy script...${NC}"

    if [ -f "deploy-ec2-ssl-tokyo-no-rebuild.sh" ]; then
        cp deploy-ec2-ssl-tokyo-no-rebuild.sh deploy-ec2-ssl-tokyo-no-rebuild.sh.bak
        sed -i.tmp "s/$CURRENT_IP/$NEW_IP/g" deploy-ec2-ssl-tokyo-no-rebuild.sh
        rm deploy-ec2-ssl-tokyo-no-rebuild.sh.tmp
        echo -e "${GREEN}✅ Updated deploy script with new IP${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎉 Downgrade successful!${NC}"
echo -e "${GREEN}Your Tokyo server is now on t2.micro (much cheaper!)${NC}"
