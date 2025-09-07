#!/bin/bash
#
# verify-ecs-shutdown.sh - Verify ECS resources are properly shut down
#
# Usage: ./verify-ecs-shutdown.sh

# Configuration
ECS_CLUSTER="liap-tui-cluster"
ECS_SERVICE="liap-tui-service"
ECR_REPO="liap-tui"
AWS_REGION="us-east-1"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Verifying ECS Shutdown Status..."
echo "================================"

# Check ECS Cluster
echo -n "ECS Cluster: "
CLUSTER_STATUS=$(aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION --query 'clusters[0].status' --output text 2>/dev/null || echo "DELETED")
if [ "$CLUSTER_STATUS" = "ACTIVE" ]; then
    echo -e "${RED}✗ Still active${NC}"
elif [ "$CLUSTER_STATUS" = "INACTIVE" ]; then
    echo -e "${GREEN}✓ Inactive (deleted)${NC}"
else
    echo -e "${GREEN}✓ Deleted${NC}"
fi

# Check ECS Service
echo -n "ECS Service: "
SERVICE_STATUS=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION --query 'services[0].status' --output text 2>/dev/null || echo "DELETED")
if [ "$SERVICE_STATUS" = "ACTIVE" ]; then
    echo -e "${RED}✗ Still active${NC}"
elif [ "$SERVICE_STATUS" = "INACTIVE" ]; then
    echo -e "${GREEN}✓ Inactive (deleted)${NC}"
else
    echo -e "${GREEN}✓ Deleted${NC}"
fi

# Check ECR Repository
echo -n "ECR Repository: "
if aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION &>/dev/null 2>&1; then
    echo -e "${RED}✗ Still exists${NC}"
else
    echo -e "${GREEN}✓ Deleted${NC}"
fi

# Check for running tasks
echo -n "Running Tasks: "
TASK_COUNT=$(aws ecs list-tasks --cluster $ECS_CLUSTER --region $AWS_REGION --query 'length(taskArns)' --output text 2>/dev/null || echo "0")
if [ "$TASK_COUNT" = "0" ]; then
    echo -e "${GREEN}✓ None${NC}"
else
    echo -e "${RED}✗ $TASK_COUNT tasks still running${NC}"
fi

echo ""
echo "Other Resources to Check:"
echo "========================"

# Load Balancers
echo -n "Load Balancers: "
LB_COUNT=$(aws elbv2 describe-load-balancers --region $AWS_REGION --query 'length(LoadBalancers[?contains(LoadBalancerName, `liap-tui`)])' --output text 2>/dev/null || echo "0")
if [ "$LB_COUNT" = "0" ]; then
    echo -e "${GREEN}✓ None found${NC}"
else
    echo -e "${YELLOW}⚠ $LB_COUNT found (costs ~$20-25/month each)${NC}"
fi

# NAT Gateways
echo -n "NAT Gateways: "
NAT_COUNT=$(aws ec2 describe-nat-gateways --region $AWS_REGION --filter "Name=state,Values=available" --query 'length(NatGateways)' --output text 2>/dev/null || echo "0")
if [ "$NAT_COUNT" = "0" ]; then
    echo -e "${GREEN}✓ None found${NC}"
else
    echo -e "${YELLOW}⚠ $NAT_COUNT found (costs ~$45/month each)${NC}"
fi

# Elastic IPs
echo -n "Unattached EIPs: "
EIP_COUNT=$(aws ec2 describe-addresses --region $AWS_REGION --query 'length(Addresses[?AssociationId==`null`])' --output text 2>/dev/null || echo "0")
if [ "$EIP_COUNT" = "0" ]; then
    echo -e "${GREEN}✓ None found${NC}"
else
    echo -e "${YELLOW}⚠ $EIP_COUNT found (costs ~$3.60/month each)${NC}"
fi

echo ""
echo "================================"

# Summary
ALL_DELETED=true
CLUSTER_STATUS=$(aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION --query 'clusters[0].status' --output text 2>/dev/null || echo "DELETED")
if [ "$CLUSTER_STATUS" = "ACTIVE" ]; then
    ALL_DELETED=false
fi
SERVICE_STATUS=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION --query 'services[0].status' --output text 2>/dev/null || echo "DELETED")
if [ "$SERVICE_STATUS" = "ACTIVE" ]; then
    ALL_DELETED=false
fi
if aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION &>/dev/null 2>&1; then
    ALL_DELETED=false
fi

if [ "$ALL_DELETED" = true ] && [ "$LB_COUNT" = "0" ] && [ "$NAT_COUNT" = "0" ] && [ "$EIP_COUNT" = "0" ]; then
    echo -e "${GREEN}✅ All resources successfully deleted! No AWS charges.${NC}"
elif [ "$ALL_DELETED" = true ]; then
    echo -e "${YELLOW}⚠️  ECS resources deleted, but other billable resources remain.${NC}"
else
    echo -e "${RED}❌ Some ECS resources still exist. Run shutdown script again.${NC}"
fi