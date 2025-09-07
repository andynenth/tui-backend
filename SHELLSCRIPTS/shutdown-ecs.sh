#!/bin/bash
#
# shutdown-ecs.sh - Safely shutdown AWS ECS services to avoid billing
#
# This script will:
# 1. Stop all running ECS tasks
# 2. Delete ECS service
# 3. Delete ECS cluster
# 4. Delete ECR repository (Docker images)
# 5. Check for other billable resources
#
# Usage: ./shutdown-ecs.sh
#
# Author: Liap Tui Team
# Date: September 2025

set -e  # Exit on error

# Configuration
ECS_CLUSTER="liap-tui-cluster"
ECS_SERVICE="liap-tui-service"
AWS_REGION="us-east-1"
ECR_REPO="liap-tui"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print colored messages
print_message() {
    local level=$1
    local message=$2
    local color=$3
    echo -e "${color}[$(date '+%H:%M:%S')] [${level}] ${message}${NC}"
}

# Function to check if AWS CLI is configured
check_aws_config() {
    if ! aws sts get-caller-identity &>/dev/null; then
        print_message "ERROR" "AWS CLI not configured or no valid credentials" "$RED"
        print_message "INFO" "Run: aws configure" "$BLUE"
        exit 1
    fi
}

# Function to wait for tasks to stop
wait_for_tasks_to_stop() {
    local max_wait=120  # 2 minutes
    local waited=0

    print_message "INFO" "Waiting for tasks to stop..." "$YELLOW"

    while [ $waited -lt $max_wait ]; do
        RUNNING_TASKS=$(aws ecs list-tasks --cluster $ECS_CLUSTER --region $AWS_REGION --query 'taskArns | length(@)' --output text 2>/dev/null || echo "0")

        if [ "$RUNNING_TASKS" = "0" ]; then
            print_message "SUCCESS" "All tasks stopped" "$GREEN"
            return 0
        fi

        echo -ne "\rRunning tasks: $RUNNING_TASKS - Waited ${waited}s / ${max_wait}s..."
        sleep 5
        waited=$((waited + 5))
    done

    echo ""
    print_message "WARNING" "Some tasks still running after ${max_wait}s" "$YELLOW"
    return 1
}

# Main shutdown process
main() {
    print_message "INFO" "Starting ECS Shutdown Process" "$BLUE"
    echo "================================================"

    # Check AWS CLI
    check_aws_config

    # Show current account info
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_message "INFO" "AWS Account: $ACCOUNT_ID" "$BLUE"
    print_message "INFO" "Region: $AWS_REGION" "$BLUE"
    echo ""

    # Warning
    print_message "WARNING" "This will shut down and DELETE your ECS services!" "$YELLOW"
    print_message "WARNING" "Cluster: $ECS_CLUSTER" "$YELLOW"
    print_message "WARNING" "Service: $ECS_SERVICE" "$YELLOW"
    print_message "WARNING" "ECR Repository: $ECR_REPO (ALL Docker images)" "$YELLOW"
    echo -n "Are you sure you want to continue? (yes/no): "
    read CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        print_message "INFO" "Shutdown cancelled" "$BLUE"
        exit 0
    fi

    echo ""
    print_message "INFO" "Starting shutdown..." "$BLUE"

    # Step 1: Check if service exists
    print_message "INFO" "Checking ECS service..." "$BLUE"
    if aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION &>/dev/null; then
        SERVICE_EXISTS=true

        # Get current desired count
        CURRENT_COUNT=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION --query 'services[0].desiredCount' --output text 2>/dev/null || echo "0")
        print_message "INFO" "Current running tasks: $CURRENT_COUNT" "$BLUE"

        if [ "$CURRENT_COUNT" != "0" ]; then
            # Step 2: Scale down service to 0
            print_message "INFO" "Scaling down ECS service to 0..." "$YELLOW"
            aws ecs update-service \
                --cluster $ECS_CLUSTER \
                --service $ECS_SERVICE \
                --desired-count 0 \
                --region $AWS_REGION \
                --output text >/dev/null

            print_message "SUCCESS" "Service scaled down" "$GREEN"

            # Wait for tasks to stop
            wait_for_tasks_to_stop
        fi

        # Step 3: Delete service
        print_message "INFO" "Deleting ECS service..." "$YELLOW"
        aws ecs delete-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --region $AWS_REGION \
            --output text >/dev/null

        print_message "SUCCESS" "Service deleted" "$GREEN"
    else
        print_message "INFO" "Service not found or already deleted" "$BLUE"
    fi

    # Step 4: Delete cluster
    print_message "INFO" "Checking ECS cluster..." "$BLUE"
    if aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION --query 'clusters[0].clusterName' &>/dev/null; then
        print_message "INFO" "Deleting ECS cluster..." "$YELLOW"
        aws ecs delete-cluster \
            --cluster $ECS_CLUSTER \
            --region $AWS_REGION \
            --output text >/dev/null

        print_message "SUCCESS" "Cluster deleted" "$GREEN"
    else
        print_message "INFO" "Cluster not found or already deleted" "$BLUE"
    fi

    # Step 5: Delete ECR repository
    print_message "INFO" "Checking ECR repository..." "$BLUE"
    if aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION &>/dev/null; then
        # Get number of images
        IMAGE_COUNT=$(aws ecr list-images --repository-name $ECR_REPO --region $AWS_REGION --query 'length(imageIds)' --output text 2>/dev/null || echo "0")
        print_message "INFO" "Found $IMAGE_COUNT Docker images in ECR repository" "$BLUE"

        print_message "INFO" "Deleting ECR repository and all images..." "$YELLOW"
        aws ecr delete-repository \
            --repository-name $ECR_REPO \
            --force \
            --region $AWS_REGION \
            --output text >/dev/null

        print_message "SUCCESS" "ECR repository and all Docker images deleted" "$GREEN"
    else
        print_message "INFO" "ECR repository not found or already deleted" "$BLUE"
    fi

    echo ""
    print_message "INFO" "Checking for other billable resources..." "$BLUE"

    # Check for load balancers
    print_message "INFO" "Checking for load balancers..." "$BLUE"
    LB_COUNT=$(aws elbv2 describe-load-balancers --region $AWS_REGION --query 'length(LoadBalancers[?contains(LoadBalancerName, `liap-tui`)])' --output text 2>/dev/null || echo "0")

    if [ "$LB_COUNT" != "0" ]; then
        print_message "WARNING" "Found $LB_COUNT load balancer(s) with 'liap-tui' in name" "$YELLOW"
        print_message "WARNING" "Load balancers cost ~$20-25/month even when idle!" "$YELLOW"
        print_message "INFO" "To list: aws elbv2 describe-load-balancers --region $AWS_REGION" "$BLUE"
    else
        print_message "SUCCESS" "No load balancers found" "$GREEN"
    fi

    # Check for NAT gateways
    print_message "INFO" "Checking for NAT gateways..." "$BLUE"
    NAT_COUNT=$(aws ec2 describe-nat-gateways --region $AWS_REGION --filter "Name=state,Values=available" --query 'length(NatGateways)' --output text 2>/dev/null || echo "0")

    if [ "$NAT_COUNT" != "0" ]; then
        print_message "WARNING" "Found $NAT_COUNT NAT gateway(s)" "$YELLOW"
        print_message "WARNING" "NAT gateways cost ~$45/month + data transfer!" "$YELLOW"
    else
        print_message "SUCCESS" "No NAT gateways found" "$GREEN"
    fi

    # Check for unattached Elastic IPs
    print_message "INFO" "Checking for unattached Elastic IPs..." "$BLUE"
    UNATTACHED_EIPS=$(aws ec2 describe-addresses --region $AWS_REGION --query 'length(Addresses[?AssociationId==`null`])' --output text 2>/dev/null || echo "0")

    if [ "$UNATTACHED_EIPS" != "0" ]; then
        print_message "WARNING" "Found $UNATTACHED_EIPS unattached Elastic IP(s)" "$YELLOW"
        print_message "WARNING" "Unattached Elastic IPs cost ~$3.60/month each!" "$YELLOW"
    else
        print_message "SUCCESS" "No unattached Elastic IPs found" "$GREEN"
    fi

    # Summary
    echo ""
    echo "================================================"
    print_message "SUCCESS" "ECS Shutdown Complete!" "$GREEN"
    echo "================================================"
    echo ""
    print_message "INFO" "Resources shut down:" "$BLUE"
    echo "  ✓ ECS Service: $ECS_SERVICE"
    echo "  ✓ ECS Cluster: $ECS_CLUSTER"
    echo "  ✓ ECR Repository: $ECR_REPO (with all Docker images)"
    echo ""

    # Cost-saving summary
    print_message "INFO" "Estimated monthly savings:" "$BLUE"
    echo "  - ECS Fargate tasks: Variable (based on usage)"
    echo "  - Load Balancer: ~$20-25 (if deleted)"
    echo "  - NAT Gateway: ~$45 (if deleted)"
    echo ""

    # Next steps
    print_message "INFO" "To completely remove remaining resources:" "$YELLOW"
    echo "  1. Delete load balancers if found"
    echo "  2. Delete NAT gateways if found"
    echo "  3. Release unattached Elastic IPs"
    echo ""

    print_message "SUCCESS" "Your ECS services are now stopped! 💰" "$GREEN"
}

# Run main function
main
