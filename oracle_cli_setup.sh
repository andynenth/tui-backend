#!/bin/bash

# Oracle Cloud Infrastructure CLI Setup and Deployment Script
# Creates ARM instance in Tokyo region for liap-tui game

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGION="ap-northeast-1"  # Tokyo
COMPARTMENT_NAME="liap-tui"
VCN_NAME="liap-tui-vcn"
SUBNET_NAME="public-subnet"
INSTANCE_NAME="liap-tui-tokyo-arm"

echo -e "${BLUE}🏗️  Oracle Cloud CLI Setup & Deployment${NC}"
echo ""

# Step 1: Install OCI CLI
echo -e "${YELLOW}Step 1: Installing OCI CLI...${NC}"

if ! command -v oci &> /dev/null; then
    echo "Installing OCI CLI..."

    # Install via pip (works on macOS/Linux)
    if command -v pip3 &> /dev/null; then
        pip3 install oci-cli
    else
        echo "Installing via curl..."
        bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
    fi
else
    echo "OCI CLI already installed"
fi

# Verify installation
oci --version

echo ""
echo -e "${YELLOW}Step 2: Configure OCI CLI Authentication...${NC}"

# Check if already configured
if [ ! -f ~/.oci/config ]; then
    echo "OCI CLI not configured. Setting up..."
    echo ""
    echo -e "${BLUE}Please run the following command and follow the prompts:${NC}"
    echo -e "${GREEN}oci setup config${NC}"
    echo ""
    echo "You'll need:"
    echo "1. User OCID (from Oracle Cloud Console > Profile > User Settings)"
    echo "2. Tenancy OCID (from Console > Administration > Tenancy Details)"
    echo "3. Region: ap-northeast-1 (Tokyo)"
    echo "4. Generate new API key pair (Y/y)"
    echo ""
    echo -e "${YELLOW}After setup, add the public key to your Oracle Cloud user:${NC}"
    echo "Console > Profile > User Settings > API Keys > Add API Key"
    echo ""
    read -p "Press Enter after completing OCI CLI setup..."
else
    echo "OCI CLI already configured"
fi

# Test authentication
echo ""
echo -e "${YELLOW}Step 3: Testing OCI CLI authentication...${NC}"

if ! oci iam user get --user-id $(oci iam user list --query 'data[0].id' --raw-output) &> /dev/null; then
    echo -e "${RED}❌ OCI CLI authentication failed!${NC}"
    echo "Please check your configuration and API key setup"
    exit 1
fi

echo -e "${GREEN}✅ OCI CLI authentication successful${NC}"

# Get compartment OCID (using root compartment by default)
echo ""
echo -e "${YELLOW}Step 4: Getting compartment information...${NC}"

TENANCY_OCID=$(oci iam compartment list --query 'data[?name==`root`].id | [0]' --raw-output)
COMPARTMENT_OCID=$TENANCY_OCID

echo "Using root compartment: $COMPARTMENT_OCID"

# Check ARM quota
echo ""
echo -e "${YELLOW}Step 5: Checking ARM instance availability...${NC}"

ARM_QUOTA=$(oci limits resource-availability get \
    --compartment-id $COMPARTMENT_OCID \
    --limit-name "standard-a1-cores" \
    --service-name compute \
    --availability-domain $(oci iam availability-domain list --query 'data[0].name' --raw-output) \
    --query 'data.available' --raw-output 2>/dev/null || echo "0")

echo "Available ARM cores: $ARM_QUOTA"

if [ "$ARM_QUOTA" = "0" ] || [ "$ARM_QUOTA" = "null" ]; then
    echo -e "${RED}⚠️  No ARM cores available in Tokyo region${NC}"
    echo -e "${YELLOW}Options:${NC}"
    echo "1. Try again later (ARM instances are released periodically)"
    echo "2. Use x86 free tier instance instead"
    echo "3. Try different availability domain"
    echo ""
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
fi

# Create SSH key pair
echo ""
echo -e "${YELLOW}Step 6: Creating SSH key pair...${NC}"

if [ ! -f ~/.ssh/oracle-tokyo-key ]; then
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle-tokyo-key -N ""
    chmod 600 ~/.ssh/oracle-tokyo-key
    echo "SSH key pair created: ~/.ssh/oracle-tokyo-key"
else
    echo "SSH key pair already exists"
fi

SSH_PUBLIC_KEY=$(cat ~/.ssh/oracle-tokyo-key.pub)

# Create VCN
echo ""
echo -e "${YELLOW}Step 7: Creating Virtual Cloud Network...${NC}"

VCN_OCID=$(oci network vcn list \
    --compartment-id $COMPARTMENT_OCID \
    --display-name $VCN_NAME \
    --query 'data[0].id' --raw-output 2>/dev/null)

if [ "$VCN_OCID" = "null" ] || [ -z "$VCN_OCID" ]; then
    echo "Creating VCN: $VCN_NAME"

    VCN_OCID=$(oci network vcn create \
        --compartment-id $COMPARTMENT_OCID \
        --display-name $VCN_NAME \
        --cidr-block "10.0.0.0/16" \
        --dns-label "liaptui" \
        --query 'data.id' --raw-output)

    echo "VCN created: $VCN_OCID"

    # Wait for VCN to be available
    oci network vcn get --vcn-id $VCN_OCID --wait-for-state AVAILABLE
else
    echo "VCN already exists: $VCN_OCID"
fi

# Get Internet Gateway
echo ""
echo -e "${YELLOW}Step 8: Setting up Internet Gateway...${NC}"

IGW_OCID=$(oci network internet-gateway list \
    --compartment-id $COMPARTMENT_OCID \
    --vcn-id $VCN_OCID \
    --query 'data[0].id' --raw-output 2>/dev/null)

if [ "$IGW_OCID" = "null" ] || [ -z "$IGW_OCID" ]; then
    echo "Creating Internet Gateway"

    IGW_OCID=$(oci network internet-gateway create \
        --compartment-id $COMPARTMENT_OCID \
        --vcn-id $VCN_OCID \
        --display-name "${VCN_NAME}-igw" \
        --is-enabled true \
        --query 'data.id' --raw-output)

    echo "Internet Gateway created: $IGW_OCID"
else
    echo "Internet Gateway already exists: $IGW_OCID"
fi

# Update default route table
echo ""
echo -e "${YELLOW}Step 9: Configuring routing...${NC}"

DEFAULT_RT_OCID=$(oci network vcn get \
    --vcn-id $VCN_OCID \
    --query 'data."default-route-table-id"' --raw-output)

# Check if route already exists
EXISTING_ROUTES=$(oci network route-table get \
    --rt-id $DEFAULT_RT_OCID \
    --query 'data."route-rules"[?destination==`0.0.0.0/0`]' --raw-output)

if [ "$EXISTING_ROUTES" = "[]" ]; then
    echo "Adding internet route to default route table"

    oci network route-table update \
        --rt-id $DEFAULT_RT_OCID \
        --route-rules '[{
            "destination": "0.0.0.0/0",
            "destinationType": "CIDR_BLOCK",
            "networkEntityId": "'$IGW_OCID'"
        }]' \
        --force
else
    echo "Internet route already exists"
fi

# Update default security list
echo ""
echo -e "${YELLOW}Step 10: Configuring security rules...${NC}"

DEFAULT_SL_OCID=$(oci network vcn get \
    --vcn-id $VCN_OCID \
    --query 'data."default-security-list-id"' --raw-output)

echo "Updating default security list with required ports"

oci network security-list update \
    --security-list-id $DEFAULT_SL_OCID \
    --ingress-security-rules '[
        {
            "source": "0.0.0.0/0",
            "protocol": "6",
            "isStateless": false,
            "tcpOptions": {
                "destinationPortRange": {
                    "min": 22,
                    "max": 22
                }
            }
        },
        {
            "source": "0.0.0.0/0",
            "protocol": "6",
            "isStateless": false,
            "tcpOptions": {
                "destinationPortRange": {
                    "min": 80,
                    "max": 80
                }
            }
        },
        {
            "source": "0.0.0.0/0",
            "protocol": "6",
            "isStateless": false,
            "tcpOptions": {
                "destinationPortRange": {
                    "min": 443,
                    "max": 443
                }
            }
        },
        {
            "source": "0.0.0.0/0",
            "protocol": "6",
            "isStateless": false,
            "tcpOptions": {
                "destinationPortRange": {
                    "min": 8080,
                    "max": 8080
                }
            }
        }
    ]' \
    --force

# Create subnet
echo ""
echo -e "${YELLOW}Step 11: Creating public subnet...${NC}"

# Get first availability domain
AD_NAME=$(oci iam availability-domain list --query 'data[0].name' --raw-output)

SUBNET_OCID=$(oci network subnet list \
    --compartment-id $COMPARTMENT_OCID \
    --vcn-id $VCN_OCID \
    --display-name $SUBNET_NAME \
    --query 'data[0].id' --raw-output 2>/dev/null)

if [ "$SUBNET_OCID" = "null" ] || [ -z "$SUBNET_OCID" ]; then
    echo "Creating subnet: $SUBNET_NAME"

    SUBNET_OCID=$(oci network subnet create \
        --compartment-id $COMPARTMENT_OCID \
        --vcn-id $VCN_OCID \
        --display-name $SUBNET_NAME \
        --cidr-block "10.0.1.0/24" \
        --availability-domain $AD_NAME \
        --route-table-id $DEFAULT_RT_OCID \
        --security-list-ids '["'$DEFAULT_SL_OCID'"]' \
        --query 'data.id' --raw-output)

    echo "Subnet created: $SUBNET_OCID"

    # Wait for subnet to be available
    oci network subnet get --subnet-id $SUBNET_OCID --wait-for-state AVAILABLE
else
    echo "Subnet already exists: $SUBNET_OCID"
fi

# Get Oracle Linux 8 ARM image
echo ""
echo -e "${YELLOW}Step 12: Finding Oracle Linux ARM image...${NC}"

ARM_IMAGE_OCID=$(oci compute image list \
    --compartment-id $COMPARTMENT_OCID \
    --operating-system "Oracle Linux" \
    --operating-system-version "8" \
    --shape "VM.Standard.A1.Flex" \
    --sort-by TIMECREATED \
    --sort-order DESC \
    --query 'data[0].id' --raw-output)

if [ "$ARM_IMAGE_OCID" = "null" ] || [ -z "$ARM_IMAGE_OCID" ]; then
    echo -e "${RED}❌ No Oracle Linux ARM image found${NC}"
    echo "Trying generic ARM image..."

    ARM_IMAGE_OCID=$(oci compute image list \
        --compartment-id $COMPARTMENT_OCID \
        --shape "VM.Standard.A1.Flex" \
        --sort-by TIMECREATED \
        --sort-order DESC \
        --limit 1 \
        --query 'data[0].id' --raw-output)
fi

echo "Using image: $ARM_IMAGE_OCID"

# Create compute instance
echo ""
echo -e "${YELLOW}Step 13: Creating ARM compute instance...${NC}"

INSTANCE_OCID=$(oci compute instance list \
    --compartment-id $COMPARTMENT_OCID \
    --display-name $INSTANCE_NAME \
    --query 'data[0].id' --raw-output 2>/dev/null)

if [ "$INSTANCE_OCID" = "null" ] || [ -z "$INSTANCE_OCID" ]; then
    echo "Creating instance: $INSTANCE_NAME"
    echo "This may take 2-3 minutes..."

    INSTANCE_OCID=$(oci compute instance launch \
        --compartment-id $COMPARTMENT_OCID \
        --availability-domain $AD_NAME \
        --display-name $INSTANCE_NAME \
        --image-id $ARM_IMAGE_OCID \
        --subnet-id $SUBNET_OCID \
        --shape "VM.Standard.A1.Flex" \
        --shape-config '{"ocpus": 4, "memoryInGBs": 24}' \
        --ssh-authorized-keys-file ~/.ssh/oracle-tokyo-key.pub \
        --assign-public-ip true \
        --query 'data.id' --raw-output)

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Instance creation initiated: $INSTANCE_OCID${NC}"

        # Wait for instance to be running
        echo "Waiting for instance to reach RUNNING state..."
        oci compute instance get --instance-id $INSTANCE_OCID --wait-for-state RUNNING

        echo -e "${GREEN}✅ Instance is now running!${NC}"
    else
        echo -e "${RED}❌ Failed to create ARM instance${NC}"
        echo -e "${YELLOW}This usually means ARM capacity is not available${NC}"
        echo -e "${YELLOW}You can try again later or use x86 instance instead${NC}"
        exit 1
    fi
else
    echo "Instance already exists: $INSTANCE_OCID"
fi

# Get public IP
echo ""
echo -e "${YELLOW}Step 14: Getting instance details...${NC}"

PUBLIC_IP=$(oci compute instance list-vnics \
    --instance-id $INSTANCE_OCID \
    --query 'data[0]."public-ip"' --raw-output)

PRIVATE_IP=$(oci compute instance list-vnics \
    --instance-id $INSTANCE_OCID \
    --query 'data[0]."private-ip"' --raw-output)

echo ""
echo -e "${GREEN}🎉 Oracle Cloud Instance Created Successfully!${NC}"
echo "========================================"
echo -e "${BLUE}Instance Details:${NC}"
echo "Instance OCID: $INSTANCE_OCID"
echo "Public IP: $PUBLIC_IP"
echo "Private IP: $PRIVATE_IP"
echo "SSH Key: ~/.ssh/oracle-tokyo-key"
echo "Region: Tokyo (ap-northeast-1)"
echo "Shape: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)"
echo ""
echo -e "${YELLOW}Connect via SSH:${NC}"
echo "ssh -i ~/.ssh/oracle-tokyo-key opc@$PUBLIC_IP"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test SSH connection"
echo "2. Update system and install dependencies"
echo "3. Deploy your liap-tui application"
echo "4. Configure nginx and SSL"
echo "5. Update DNS to point to $PUBLIC_IP"
echo ""

# Save instance details
cat > oracle_instance_details.txt << EOF
Oracle Cloud Instance Details
============================
Instance OCID: $INSTANCE_OCID
Public IP: $PUBLIC_IP
Private IP: $PRIVATE_IP
SSH Command: ssh -i ~/.ssh/oracle-tokyo-key opc@$PUBLIC_IP
Region: ap-northeast-1 (Tokyo)
Shape: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)
Created: $(date)
EOF

echo -e "${GREEN}Instance details saved to: oracle_instance_details.txt${NC}"

# Test SSH connection
echo ""
echo -e "${YELLOW}Testing SSH connection...${NC}"
sleep 10  # Give the instance a moment to fully initialize

if ssh -i ~/.ssh/oracle-tokyo-key -o ConnectTimeout=10 -o StrictHostKeyChecking=no opc@$PUBLIC_IP "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection test successful!${NC}"
else
    echo -e "${YELLOW}⚠️  SSH connection not ready yet. Try again in a few minutes.${NC}"
fi

echo ""
echo -e "${GREEN}🏗️  Infrastructure setup complete!${NC}"
echo -e "${BLUE}Ready for application deployment.${NC}"
