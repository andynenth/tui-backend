#!/bin/bash

# Enable IPv6 to eliminate IPv4 public IP costs
# WARNING: IPv6 is not universally supported - test thoroughly

set -e

REGION="ap-northeast-1"  # Tokyo
INSTANCE_ID="i-00f537b8ed58a15de"  # Your current instance

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}⚠️  WARNING: IPv6 MIGRATION RISK${NC}"
echo -e "${RED}This will make your server IPv6-only${NC}"
echo -e "${RED}Some users may not be able to access it${NC}"
echo ""
echo -e "${YELLOW}IPv6 Support:${NC}"
echo "✅ Modern browsers (Chrome, Firefox, Safari)"
echo "✅ Most ISPs in developed countries"
echo "❌ Some older networks/routers"
echo "❌ Some corporate firewalls"
echo ""
echo "Continue? (yes/no)"
read CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled"
    exit 1
fi

echo -e "${GREEN}🌐 Starting IPv6 Migration${NC}"

# Get instance details
echo -e "${YELLOW}Getting instance details...${NC}"
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0]')

VPC_ID=$(echo $INSTANCE_INFO | jq -r '.VpcId')
SUBNET_ID=$(echo $INSTANCE_INFO | jq -r '.SubnetId')
SECURITY_GROUPS=$(echo $INSTANCE_INFO | jq -r '.SecurityGroups[].GroupId' | tr '\n' ' ')

echo "VPC: $VPC_ID"
echo "Subnet: $SUBNET_ID"
echo "Security Groups: $SECURITY_GROUPS"

# Step 1: Enable IPv6 on VPC
echo -e "${YELLOW}Step 1: Enabling IPv6 on VPC...${NC}"

# Check if IPv6 is already enabled
IPV6_CIDRS=$(aws ec2 describe-vpcs \
    --region $REGION \
    --vpc-ids $VPC_ID \
    --query 'Vpcs[0].Ipv6CidrBlockAssociationSet[?Ipv6CidrBlockState.State==`associated`].Ipv6CidrBlock' \
    --output text)

if [ -z "$IPV6_CIDRS" ] || [ "$IPV6_CIDRS" == "None" ]; then
    echo "Associating IPv6 CIDR block with VPC..."
    aws ec2 associate-vpc-cidr-block \
        --region $REGION \
        --vpc-id $VPC_ID \
        --amazon-provided-ipv6-cidr-block

    echo "Waiting for IPv6 CIDR association..."
    sleep 30

    IPV6_CIDRS=$(aws ec2 describe-vpcs \
        --region $REGION \
        --vpc-ids $VPC_ID \
        --query 'Vpcs[0].Ipv6CidrBlockAssociationSet[?Ipv6CidrBlockState.State==`associated`].Ipv6CidrBlock' \
        --output text)
else
    echo "IPv6 already enabled on VPC"
fi

echo "VPC IPv6 CIDR: $IPV6_CIDRS"

# Step 2: Enable IPv6 on subnet
echo -e "${YELLOW}Step 2: Enabling IPv6 on subnet...${NC}"

# Get the first /64 from VPC CIDR for subnet
IPV6_SUBNET_CIDR=$(echo $IPV6_CIDRS | sed 's|/56|01::/64|')

# Check if subnet already has IPv6
SUBNET_IPV6=$(aws ec2 describe-subnets \
    --region $REGION \
    --subnet-ids $SUBNET_ID \
    --query 'Subnets[0].Ipv6CidrBlockAssociationSet[?Ipv6CidrBlockState.State==`associated`].Ipv6CidrBlock' \
    --output text)

if [ -z "$SUBNET_IPV6" ] || [ "$SUBNET_IPV6" == "None" ]; then
    echo "Associating IPv6 CIDR with subnet..."
    aws ec2 associate-subnet-cidr-block \
        --region $REGION \
        --subnet-id $SUBNET_ID \
        --ipv6-cidr-block $IPV6_SUBNET_CIDR

    echo "Waiting for subnet IPv6 association..."
    sleep 20
else
    echo "IPv6 already enabled on subnet"
    IPV6_SUBNET_CIDR=$SUBNET_IPV6
fi

echo "Subnet IPv6 CIDR: $IPV6_SUBNET_CIDR"

# Step 3: Enable auto-assign IPv6
echo -e "${YELLOW}Step 3: Enabling auto-assign IPv6...${NC}"
aws ec2 modify-subnet-attribute \
    --region $REGION \
    --subnet-id $SUBNET_ID \
    --assign-ipv6-address-on-creation

# Step 4: Update security groups for IPv6
echo -e "${YELLOW}Step 4: Updating security groups for IPv6...${NC}"
for SG in $SECURITY_GROUPS; do
    echo "Updating security group: $SG"

    # Add IPv6 HTTP rule
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG \
        --protocol tcp \
        --port 80 \
        --ipv6-cidr ::/0 2>/dev/null || echo "IPv6 HTTP rule already exists"

    # Add IPv6 HTTPS rule
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG \
        --protocol tcp \
        --port 443 \
        --ipv6-cidr ::/0 2>/dev/null || echo "IPv6 HTTPS rule already exists"

    # Add IPv6 SSH rule
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG \
        --protocol tcp \
        --port 22 \
        --ipv6-cidr ::/0 2>/dev/null || echo "IPv6 SSH rule already exists"
done

# Step 5: Update route table for IPv6
echo -e "${YELLOW}Step 5: Updating route table for IPv6...${NC}"
ROUTE_TABLE=$(aws ec2 describe-route-tables \
    --region $REGION \
    --filters "Name=association.subnet-id,Values=$SUBNET_ID" \
    --query 'RouteTables[0].RouteTableId' \
    --output text)

IGW_ID=$(aws ec2 describe-internet-gateways \
    --region $REGION \
    --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
    --query 'InternetGateways[0].InternetGatewayId' \
    --output text)

# Add IPv6 route to internet gateway
aws ec2 create-route \
    --region $REGION \
    --route-table-id $ROUTE_TABLE \
    --destination-ipv6-cidr-block ::/0 \
    --gateway-id $IGW_ID 2>/dev/null || echo "IPv6 route already exists"

# Step 6: Assign IPv6 to instance
echo -e "${YELLOW}Step 6: Assigning IPv6 to instance...${NC}"

# Get network interface ID
ENI_ID=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].NetworkInterfaces[0].NetworkInterfaceId' \
    --output text)

# Assign IPv6 address
aws ec2 assign-ipv6-addresses \
    --region $REGION \
    --network-interface-id $ENI_ID \
    --ipv6-address-count 1 2>/dev/null || echo "IPv6 already assigned"

# Get the assigned IPv6 address
sleep 10
IPV6_ADDRESS=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].NetworkInterfaces[0].Ipv6Addresses[0].Ipv6Address' \
    --output text)

echo -e "${GREEN}✅ IPv6 Configuration Complete!${NC}"
echo "================================"
echo "IPv6 Address: $IPV6_ADDRESS"
echo "Test URL: http://[$IPV6_ADDRESS]"
echo "================================"

echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo ""
echo -e "${YELLOW}1. Test IPv6 connectivity:${NC}"
echo "   ping6 $IPV6_ADDRESS"
echo "   curl -6 http://[$IPV6_ADDRESS]"
echo ""
echo -e "${YELLOW}2. Update your domain DNS:${NC}"
echo "   Add AAAA record: castellan.andynenth.dev → $IPV6_ADDRESS"
echo ""
echo -e "${YELLOW}3. Test from different networks:${NC}"
echo "   - Your home internet"
echo "   - Mobile data"
echo "   - Different countries"
echo ""
echo -e "${YELLOW}4. Configure server for IPv6:${NC}"
echo "   SSH into server and ensure nginx binds to IPv6"
echo ""

# Create IPv6 test script
cat > test_ipv6.sh << EOF
#!/bin/bash
# Test IPv6 connectivity

echo "Testing IPv6 connectivity to $IPV6_ADDRESS..."

# Test ping
echo "1. Ping test:"
ping6 -c 3 $IPV6_ADDRESS || echo "❌ IPv6 ping failed"

# Test HTTP
echo "2. HTTP test:"
curl -6 -I http://[$IPV6_ADDRESS] || echo "❌ IPv6 HTTP failed"

# Test from different tools
echo "3. Online IPv6 test:"
echo "   Visit: https://ipv6-test.com/"
echo "   Test your domain: http://[$IPV6_ADDRESS]"

echo ""
echo "If tests pass, you can remove IPv4 public IP to save $3.60/month"
EOF

chmod +x test_ipv6.sh

echo -e "${GREEN}💡 Created test_ipv6.sh for testing${NC}"

echo ""
echo -e "${RED}⚠️  IMPORTANT WARNINGS:${NC}"
echo "1. Some users won't be able to access IPv6-only sites"
echo "2. Test thoroughly before removing IPv4"
echo "3. Keep IPv4 as backup initially"
echo "4. Monitor access logs for IPv6 adoption"

echo ""
echo -e "${YELLOW}💰 Potential Savings:${NC}"
echo "Remove IPv4 public IP: Save $3.60/month per instance"
echo "Total current savings from t3.medium→t2.micro: ~$39/month"
echo "Additional IPv6 savings: $3.60/month"
echo "Combined savings: ~$42.60/month"
