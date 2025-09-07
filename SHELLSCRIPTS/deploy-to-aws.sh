#!/bin/bash
# deploy-to-aws.sh - Deploy Liap Tui to AWS ECS

set -e  # Exit on any error

# Configuration
ECR_REPO_URI="300079938592.dkr.ecr.us-east-1.amazonaws.com/liap-tui"
ECS_CLUSTER="liap-tui-cluster"
ECS_SERVICE="liap-tui-service"
ECS_TASK_FAMILY="liap-tui"
AWS_REGION="us-east-1"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting deployment process...${NC}"

# Get version from package.json
VERSION=$(cat frontend/package.json | grep '"version"' | cut -d '"' -f 4)
echo -e "${YELLOW}📦 Deploying version: ${VERSION}${NC}"

# Step 1: Build Docker image
echo -e "${GREEN}🏗️  Building Docker image...${NC}"
docker build -t liap-tui:v${VERSION} -f Dockerfile.prod .
docker tag liap-tui:v${VERSION} liap-tui:latest

# Step 2: Tag for ECR
echo -e "${GREEN}🏷️  Tagging image for ECR...${NC}"
docker tag liap-tui:v${VERSION} ${ECR_REPO_URI}:v${VERSION}
docker tag liap-tui:v${VERSION} ${ECR_REPO_URI}:latest

# Step 3: Login to ECR
echo -e "${GREEN}🔐 Logging into ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URI}

# Step 4: Push to ECR
echo -e "${GREEN}📤 Pushing image to ECR...${NC}"
docker push ${ECR_REPO_URI}:v${VERSION}
docker push ${ECR_REPO_URI}:latest

# Step 5: Update ECS task definition
echo -e "${GREEN}📝 Creating new task definition...${NC}"

# Get current task definition
aws ecs describe-task-definition --task-definition ${ECS_TASK_FAMILY} --query 'taskDefinition' > current-task-def.json

# Update image in task definition
cat current-task-def.json | jq --arg IMAGE "${ECR_REPO_URI}:v${VERSION}" 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy, .deregisteredAt) | .containerDefinitions[0].image = $IMAGE' > new-task-def.json

# Register new task definition
TASK_REVISION=$(aws ecs register-task-definition --cli-input-json file://new-task-def.json --query 'taskDefinition.revision' --output text)
echo -e "${YELLOW}📋 Created task definition revision: ${TASK_REVISION}${NC}"

# Step 6: Update ECS service
echo -e "${GREEN}🔄 Updating ECS service...${NC}"
aws ecs update-service \
  --cluster ${ECS_CLUSTER} \
  --service ${ECS_SERVICE} \
  --task-definition ${ECS_TASK_FAMILY}:${TASK_REVISION} \
  --force-new-deployment

# Step 7: Wait for deployment to stabilize
echo -e "${GREEN}⏳ Waiting for deployment to complete...${NC}"
aws ecs wait services-stable --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE}

# Step 8: Verify deployment
echo -e "${GREEN}✅ Verifying deployment...${NC}"
ALB_DNS=$(aws elbv2 describe-load-balancers --names liap-tui-alb --query 'LoadBalancers[0].DNSName' --output text)
HEALTH_CHECK=$(curl -s http://${ALB_DNS}/api/health | jq -r '.status')

if [ "$HEALTH_CHECK" == "healthy" ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo -e "${GREEN}🌐 Application URL: http://${ALB_DNS}/${NC}"
    echo -e "${GREEN}📊 Version ${VERSION} is now live!${NC}"

    # Optional: Check maintenance endpoint if v1.1.0 or later
    if curl -s http://${ALB_DNS}/api/maintenance/status > /dev/null 2>&1; then
        echo -e "${GREEN}🧹 Log maintenance system is active${NC}"
    fi
else
    echo -e "${RED}❌ Health check failed. Please check the deployment.${NC}"
    exit 1
fi

# Cleanup
rm -f current-task-def.json new-task-def.json

echo -e "${GREEN}🎉 Deployment complete!${NC}"
