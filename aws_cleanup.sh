#!/bin/bash

# AWS Resource Cleanup Script - TERMINATES ALL RESOURCES
# Run this to stop all AWS charges immediately

echo "===================================="
echo "AWS RESOURCE CLEANUP SCRIPT"
echo "This will terminate ALL resources"
echo "===================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed"
    echo "Install with: brew install awscli (Mac) or apt install awscli (Linux)"
    exit 1
fi

# Test AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

echo "Starting cleanup in all regions..."
echo ""

# Get all regions
REGIONS=$(aws ec2 describe-regions --query 'Regions[].RegionName' --output text)

for REGION in $REGIONS; do
    echo "----------------------------------------"
    echo "Cleaning region: $REGION"
    echo "----------------------------------------"

    # 1. Terminate EC2 Instances
    echo "→ Terminating EC2 instances..."
    INSTANCES=$(aws ec2 describe-instances --region $REGION --query 'Reservations[].Instances[?State.Name!=`terminated`].InstanceId' --output text)
    if [ ! -z "$INSTANCES" ]; then
        aws ec2 terminate-instances --region $REGION --instance-ids $INSTANCES
        echo "  Terminated: $INSTANCES"
    else
        echo "  No running instances found"
    fi

    # 2. Delete Load Balancers (ALB/NLB)
    echo "→ Deleting Application Load Balancers..."
    ALBS=$(aws elbv2 describe-load-balancers --region $REGION --query 'LoadBalancers[].LoadBalancerArn' --output text 2>/dev/null)
    for ALB in $ALBS; do
        aws elbv2 delete-load-balancer --region $REGION --load-balancer-arn $ALB 2>/dev/null
        echo "  Deleted ALB: $ALB"
    done

    # 3. Delete Classic Load Balancers
    echo "→ Deleting Classic Load Balancers..."
    ELBS=$(aws elb describe-load-balancers --region $REGION --query 'LoadBalancerDescriptions[].LoadBalancerName' --output text 2>/dev/null)
    for ELB in $ELBS; do
        aws elb delete-load-balancer --region $REGION --load-balancer-name $ELB 2>/dev/null
        echo "  Deleted ELB: $ELB"
    done

    # 4. Stop ECS Services and Tasks
    echo "→ Stopping ECS services..."
    CLUSTERS=$(aws ecs list-clusters --region $REGION --query 'clusterArns[]' --output text 2>/dev/null)
    for CLUSTER in $CLUSTERS; do
        SERVICES=$(aws ecs list-services --region $REGION --cluster $CLUSTER --query 'serviceArns[]' --output text 2>/dev/null)
        for SERVICE in $SERVICES; do
            aws ecs update-service --region $REGION --cluster $CLUSTER --service $SERVICE --desired-count 0 2>/dev/null
            aws ecs delete-service --region $REGION --cluster $CLUSTER --service $SERVICE --force 2>/dev/null
            echo "  Deleted ECS service: $SERVICE"
        done

        # Stop all running tasks
        TASKS=$(aws ecs list-tasks --region $REGION --cluster $CLUSTER --query 'taskArns[]' --output text 2>/dev/null)
        for TASK in $TASKS; do
            aws ecs stop-task --region $REGION --cluster $CLUSTER --task $TASK 2>/dev/null
            echo "  Stopped task: $TASK"
        done
    done

    # 5. Delete NAT Gateways
    echo "→ Deleting NAT Gateways..."
    NAT_GATEWAYS=$(aws ec2 describe-nat-gateways --region $REGION --query 'NatGateways[?State!=`deleted`].NatGatewayId' --output text 2>/dev/null)
    for NAT in $NAT_GATEWAYS; do
        aws ec2 delete-nat-gateway --region $REGION --nat-gateway-id $NAT 2>/dev/null
        echo "  Deleted NAT Gateway: $NAT"
    done

    # 6. Release Elastic IPs
    echo "→ Releasing Elastic IPs..."
    EIPS=$(aws ec2 describe-addresses --region $REGION --query 'Addresses[].AllocationId' --output text 2>/dev/null)
    for EIP in $EIPS; do
        aws ec2 release-address --region $REGION --allocation-id $EIP 2>/dev/null
        echo "  Released Elastic IP: $EIP"
    done

    # 7. Delete EBS Volumes (only unattached)
    echo "→ Deleting unattached EBS volumes..."
    VOLUMES=$(aws ec2 describe-volumes --region $REGION --filters "Name=status,Values=available" --query 'Volumes[].VolumeId' --output text 2>/dev/null)
    for VOLUME in $VOLUMES; do
        aws ec2 delete-volume --region $REGION --volume-id $VOLUME 2>/dev/null
        echo "  Deleted volume: $VOLUME"
    done

    echo ""
done

echo "===================================="
echo "CLEANUP COMPLETE"
echo "===================================="
echo ""
echo "IMPORTANT NEXT STEPS:"
echo "1. Wait 5-10 minutes for instances to fully terminate"
echo "2. Run this script again to delete any remaining EBS volumes"
echo "3. Check AWS Console to verify all resources are gone"
echo "4. Set up billing alerts to prevent future surprises"
echo ""
echo "To set up billing alerts:"
echo "aws cloudwatch put-metric-alarm \\"
echo "  --alarm-name aws-billing-alarm \\"
echo "  --alarm-description 'Alert when AWS bill exceeds \$5' \\"
echo "  --metric-name EstimatedCharges \\"
echo "  --namespace AWS/Billing \\"
echo "  --statistic Maximum \\"
echo "  --period 86400 \\"
echo "  --threshold 5 \\"
echo "  --comparison-operator GreaterThanThreshold \\"
echo "  --dimensions Name=Currency,Value=USD \\"
echo "  --evaluation-periods 1 \\"
echo "  --region us-east-1"
