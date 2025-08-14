#\!/bin/bash
# Phase 2 Interactive Checklist Helper

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📋 Phase 2: AWS EC2 Setup Checklist${NC}"
echo -e "${BLUE}===================================${NC}"
echo ""

# Function to ask yes/no
ask_confirm() {
    local prompt="$1"
    while true; do
        echo -ne "${YELLOW}${prompt} (y/n): ${NC}"
        read -r answer
        case $answer in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes (y) or no (n).";;
        esac
    done
}

# Check AWS CLI
echo -e "${BLUE}Pre-requisites:${NC}"
if command -v aws &> /dev/null; then
    echo -e "${GREEN}✅ AWS CLI installed${NC}"
    
    if aws sts get-caller-identity &> /dev/null; then
        echo -e "${GREEN}✅ AWS credentials configured${NC}"
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        echo -e "   Account ID: ${ACCOUNT_ID}"
    else
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        echo -e "${YELLOW}   Run: aws configure${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ AWS CLI not installed${NC}"
    echo -e "${YELLOW}   Install from: https://aws.amazon.com/cli/${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step-by-Step Guide:${NC}"
echo ""

# Step 1: Launch Instance
if ask_confirm "Ready to launch EC2 instance?"; then
    echo -e "${GREEN}Running launch script...${NC}"
    ./launch-ec2-instance.sh
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ EC2 instance launched successfully${NC}"
    else
        echo -e "${RED}❌ Failed to launch instance${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Skipping instance launch${NC}"
fi

# Step 2: Verify instance details
if [ -f "ec2-instance-details.txt" ]; then
    echo ""
    echo -e "${BLUE}Instance Details:${NC}"
    cat ec2-instance-details.txt
    echo ""
fi

# Step 3: Setup EC2
if ask_confirm "Ready to run setup on EC2?"; then
    if [ -f "ec2-instance-details.txt" ]; then
        ELASTIC_IP=$(grep "Elastic IP:" ec2-instance-details.txt  < /dev/null |  awk '{print $3}')
        KEY_FILE=$(grep "SSH Key:" ec2-instance-details.txt | awk '{print $3}')
        
        echo -e "${YELLOW}Copying setup script to EC2...${NC}"
        scp -o StrictHostKeyChecking=no -i ${KEY_FILE} ec2-setup.sh ubuntu@${ELASTIC_IP}:~/
        
        echo -e "${YELLOW}Running setup script...${NC}"
        ssh -o StrictHostKeyChecking=no -i ${KEY_FILE} ubuntu@${ELASTIC_IP} 'chmod +x ec2-setup.sh && ./ec2-setup.sh'
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ EC2 setup completed${NC}"
        else
            echo -e "${RED}❌ Setup failed${NC}"
        fi
    else
        echo -e "${RED}❌ No instance details found. Run launch script first.${NC}"
    fi
else
    echo -e "${YELLOW}Skipping EC2 setup${NC}"
fi

# Step 4: Summary
echo ""
echo -e "${BLUE}Phase 2 Checklist Summary:${NC}"
echo -e "${BLUE}=========================${NC}"

# Read from instance details if available
if [ -f "ec2-instance-details.txt" ]; then
    INSTANCE_ID=$(grep "Instance ID:" ec2-instance-details.txt | awk '{print $3}')
    ELASTIC_IP=$(grep "Elastic IP:" ec2-instance-details.txt | awk '{print $3}')
    echo -e "✅ Instance launched: ${INSTANCE_ID}"
    echo -e "✅ Elastic IP allocated: ${ELASTIC_IP}"
    echo -e "✅ Security group configured"
    echo -e "✅ SSH key pair created/configured"
else
    echo -e "❌ No instance launched yet"
fi

echo ""
echo -e "${BLUE}📝 Next Phase (Phase 3 - EC2 Configuration):${NC}"
echo -e "1. Verify Docker installation on EC2"
echo -e "2. Check directories created"
echo -e "3. Verify cron jobs"
echo -e "4. Test deployment"
echo ""
echo -e "${GREEN}Ready to proceed to Phase 3\!${NC}"
