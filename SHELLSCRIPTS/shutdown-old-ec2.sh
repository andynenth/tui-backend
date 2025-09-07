#!/bin/bash
#
# shutdown-old-ec2.sh - Safely shutdown old EC2 server in US-East-1
#
# This script will:
# 1. Check and stop EC2 instance
# 2. Terminate EC2 instance
# 3. Release Elastic IP
# 4. Check for orphaned resources
# 5. Attempt to delete security group
#
# Usage: ./shutdown-old-ec2.sh
#
# Author: Liap Tui Team
# Date: September 2025

set -e  # Exit on error

# Configuration from ec2-instance-details.txt
INSTANCE_ID="i-031f0be2cfed1ff2f"
ELASTIC_IP="34.233.7.20"
SECURITY_GROUP_ID="sg-0e38841b4467d4545"
AWS_REGION="us-east-1"

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

# Main shutdown process
main() {
    print_message "INFO" "Starting Old EC2 Shutdown Process" "$BLUE"
    echo "================================================"
    
    # Check AWS CLI
    check_aws_config
    
    # Show current account info
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_message "INFO" "AWS Account: $ACCOUNT_ID" "$BLUE"
    print_message "INFO" "Region: $AWS_REGION" "$BLUE"
    echo ""
    
    # Warning
    print_message "WARNING" "This will shut down your OLD EC2 server!" "$YELLOW"
    print_message "WARNING" "Instance ID: $INSTANCE_ID" "$YELLOW"
    print_message "WARNING" "Elastic IP: $ELASTIC_IP" "$YELLOW"
    print_message "WARNING" "Security Group: $SECURITY_GROUP_ID" "$YELLOW"
    echo ""
    print_message "INFO" "Make sure you've migrated everything to Tokyo (54.250.35.226)" "$BLUE"
    echo -n "Are you sure you want to continue? (yes/no): "
    read CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        print_message "INFO" "Shutdown cancelled" "$BLUE"
        exit 0
    fi
    
    echo ""
    print_message "INFO" "Starting shutdown..." "$BLUE"
    
    # Step 1: Check instance status
    print_message "INFO" "Checking EC2 instance status..." "$BLUE"
    INSTANCE_STATE=$(aws ec2 describe-instances \
        --instance-ids $INSTANCE_ID \
        --region $AWS_REGION \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text 2>/dev/null || echo "not-found")
    
    if [ "$INSTANCE_STATE" = "not-found" ] || [ "$INSTANCE_STATE" = "None" ]; then
        print_message "INFO" "Instance not found or already terminated" "$BLUE"
    else
        print_message "INFO" "Instance state: $INSTANCE_STATE" "$BLUE"
        
        # Stop instance if running
        if [ "$INSTANCE_STATE" = "running" ]; then
            print_message "INFO" "Stopping EC2 instance..." "$YELLOW"
            aws ec2 stop-instances \
                --instance-ids $INSTANCE_ID \
                --region $AWS_REGION \
                --output text >/dev/null
            
            # Wait for instance to stop
            print_message "INFO" "Waiting for instance to stop..." "$YELLOW"
            aws ec2 wait instance-stopped \
                --instance-ids $INSTANCE_ID \
                --region $AWS_REGION
            
            print_message "SUCCESS" "Instance stopped" "$GREEN"
        fi
        
        # Terminate instance
        if [ "$INSTANCE_STATE" != "terminated" ]; then
            print_message "INFO" "Terminating EC2 instance..." "$YELLOW"
            aws ec2 terminate-instances \
                --instance-ids $INSTANCE_ID \
                --region $AWS_REGION \
                --output text >/dev/null
            
            # Wait for termination
            print_message "INFO" "Waiting for instance termination..." "$YELLOW"
            aws ec2 wait instance-terminated \
                --instance-ids $INSTANCE_ID \
                --region $AWS_REGION
            
            print_message "SUCCESS" "Instance terminated" "$GREEN"
        fi
    fi
    
    # Step 2: Release Elastic IP
    print_message "INFO" "Checking Elastic IP..." "$BLUE"
    ALLOCATION_ID=$(aws ec2 describe-addresses \
        --public-ips $ELASTIC_IP \
        --region $AWS_REGION \
        --query 'Addresses[0].AllocationId' \
        --output text 2>/dev/null || echo "not-found")
    
    if [ "$ALLOCATION_ID" != "not-found" ] && [ "$ALLOCATION_ID" != "None" ]; then
        print_message "INFO" "Releasing Elastic IP..." "$YELLOW"
        aws ec2 release-address \
            --allocation-id $ALLOCATION_ID \
            --region $AWS_REGION
        
        print_message "SUCCESS" "Elastic IP released" "$GREEN"
    else
        print_message "INFO" "Elastic IP not found or already released" "$BLUE"
    fi
    
    # Step 3: Check for orphaned EBS volumes
    print_message "INFO" "Checking for orphaned EBS volumes..." "$BLUE"
    ORPHANED_VOLUMES=$(aws ec2 describe-volumes \
        --region $AWS_REGION \
        --filters "Name=status,Values=available" \
        --query 'Volumes[?Tags[?Key==`Name` && contains(Value, `liap-tui`)]].[VolumeId,Size,State]' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$ORPHANED_VOLUMES" ]; then
        print_message "WARNING" "Found orphaned volumes:" "$YELLOW"
        echo "$ORPHANED_VOLUMES"
        print_message "INFO" "To delete: aws ec2 delete-volume --volume-id <volume-id> --region $AWS_REGION" "$BLUE"
    else
        print_message "SUCCESS" "No orphaned volumes found" "$GREEN"
    fi
    
    # Step 4: Check for snapshots
    print_message "INFO" "Checking for snapshots..." "$BLUE"
    SNAPSHOT_COUNT=$(aws ec2 describe-snapshots \
        --owner-ids self \
        --region $AWS_REGION \
        --query 'length(Snapshots[?Description && contains(Description, `liap-tui`)])' \
        --output text 2>/dev/null || echo "0")
    
    if [ "$SNAPSHOT_COUNT" != "0" ]; then
        print_message "WARNING" "Found $SNAPSHOT_COUNT snapshot(s) related to liap-tui" "$YELLOW"
        print_message "INFO" "Review with: aws ec2 describe-snapshots --owner-ids self --region $AWS_REGION" "$BLUE"
    else
        print_message "SUCCESS" "No related snapshots found" "$GREEN"
    fi
    
    # Step 5: Try to delete security group
    print_message "INFO" "Checking security group..." "$BLUE"
    
    # Wait a bit for AWS to update dependencies
    sleep 5
    
    if aws ec2 delete-security-group \
        --group-id $SECURITY_GROUP_ID \
        --region $AWS_REGION 2>/dev/null; then
        print_message "SUCCESS" "Security group deleted" "$GREEN"
    else
        print_message "INFO" "Security group could not be deleted (may still be in use or default)" "$BLUE"
    fi
    
    # Summary
    echo ""
    echo "================================================"
    print_message "SUCCESS" "Old EC2 Shutdown Complete!" "$GREEN"
    echo "================================================"
    echo ""
    print_message "INFO" "Resources shut down:" "$BLUE"
    echo "  ✓ EC2 Instance: $INSTANCE_ID"
    echo "  ✓ Elastic IP: $ELASTIC_IP"
    echo ""
    
    # Cost savings
    print_message "INFO" "Estimated monthly savings:" "$BLUE"
    echo "  - EC2 t2.micro: ~$8.40"
    echo "  - Elastic IP: ~$3.60"
    echo "  - Total: ~$12.00/month"
    echo ""
    
    # Next steps
    print_message "INFO" "Your application is now only running on:" "$BLUE"
    echo "  Tokyo server: 54.250.35.226"
    echo ""
    
    # Check for any remaining resources
    print_message "INFO" "To verify all resources are cleaned up:" "$YELLOW"
    echo "  aws ec2 describe-instances --region $AWS_REGION"
    echo "  aws ec2 describe-addresses --region $AWS_REGION"
    echo "  aws ec2 describe-volumes --region $AWS_REGION"
    echo "  aws ec2 describe-security-groups --region $AWS_REGION"
    echo ""
    
    print_message "SUCCESS" "Old infrastructure successfully removed! 💰" "$GREEN"
}

# Run main function
main