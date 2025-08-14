# Deployment Guide - AWS EC2 Production Deployment Walkthrough

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [AWS Account Setup](#aws-account-setup)
4. [EC2 Instance Setup](#ec2-instance-setup)
5. [Software Installation](#software-installation)
6. [Application Deployment](#application-deployment)
7. [Database Setup](#database-setup)
8. [Domain and SSL Setup](#domain-and-ssl-setup)
9. [Monitoring Setup](#monitoring-setup)
10. [Go Live Checklist](#go-live-checklist)
11. [Post-Deployment](#post-deployment)
12. [Cost Optimization](#cost-optimization)

## Overview

This guide walks through deploying Liap Tui to AWS EC2 step-by-step. By the end, you'll have a production-ready deployment capable of handling hundreds of concurrent players on a single EC2 instance.

### Deployment Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CloudFront │────▶│   EC2 with  │────▶│   SQLite    │
│     CDN     │     │   Docker    │     │   Database  │
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                    ┌───────▼───────┐
                    │     Nginx     │
                    │  (SSL/Proxy)  │
                    └───────────────┘
```

## Prerequisites

### Local Requirements

1. **AWS CLI installed and configured**
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   
   # Configure credentials
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Enter default region (e.g., us-east-1)
   # Enter default output format (json)
   ```

2. **SSH Key Pair**
   ```bash
   # Create key pair if you don't have one
   aws ec2 create-key-pair --key-name liap-tui-key --query 'KeyMaterial' --output text > liap-tui-key.pem
   chmod 400 liap-tui-key.pem
   ```

3. **Git for deployment**
   ```bash
   # Ensure git is installed
   git --version
   ```

### AWS Services Required

- EC2 (Elastic Compute Cloud)
- VPC (Virtual Private Cloud)
- Security Groups
- Elastic IP
- CloudWatch
- S3 (for backups)
- Route 53 (for domain)
- Certificate Manager (optional)

## AWS Account Setup

### Step 1: Check Free Tier Eligibility

```bash
# Check if your account is eligible for free tier
# t2.micro instance is free for 750 hours/month for 12 months
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UsageQuantity" \
  --group-by Type=DIMENSION,Key=USAGE_TYPE
```

### Step 2: Create Security Group

```bash
# Create security group
aws ec2 create-security-group \
  --group-name liap-tui-sg \
  --description "Security group for Liap Tui game server"

# Get your IP address
MY_IP=$(curl -s http://checkip.amazonaws.com)

# Add inbound rules
# SSH (restricted to your IP)
aws ec2 authorize-security-group-ingress \
  --group-name liap-tui-sg \
  --protocol tcp \
  --port 22 \
  --cidr $MY_IP/32

# HTTP
aws ec2 authorize-security-group-ingress \
  --group-name liap-tui-sg \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# HTTPS
aws ec2 authorize-security-group-ingress \
  --group-name liap-tui-sg \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# WebSocket (if using separate port)
aws ec2 authorize-security-group-ingress \
  --group-name liap-tui-sg \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

```yaml
# infrastructure/vpc.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: VPC for Liap Tui

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: liap-tui-vpc

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: liap-tui-public-1

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: liap-tui-public-2

  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.11.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      Tags:
        - Key: Name
          Value: liap-tui-private-1

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.12.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      Tags:
        - Key: Name
          Value: liap-tui-private-2

  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: liap-tui-igw

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  NATGateway:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt EIPForNAT.AllocationId
      SubnetId: !Ref PublicSubnet1

  EIPForNAT:
    Type: AWS::EC2::EIP
    Properties:
      Domain: vpc

  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: liap-tui-public-rt

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PrivateRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: liap-tui-private-rt

  PrivateRoute:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NATGateway

Outputs:
  VPCId:
    Value: !Ref VPC
    Export:
      Name: liap-tui-vpc-id
  PublicSubnet1Id:
    Value: !Ref PublicSubnet1
    Export:
      Name: liap-tui-public-subnet-1
  PublicSubnet2Id:
    Value: !Ref PublicSubnet2
    Export:
      Name: liap-tui-public-subnet-2
  PrivateSubnet1Id:
    Value: !Ref PrivateSubnet1
    Export:
      Name: liap-tui-private-subnet-1
  PrivateSubnet2Id:
    Value: !Ref PrivateSubnet2
    Export:
      Name: liap-tui-private-subnet-2
```

Deploy VPC:
```bash
aws cloudformation create-stack \
  --stack-name liap-tui-vpc \
  --template-body file://infrastructure/vpc.yaml
```

## EC2 Instance Setup

### Step 1: Launch EC2 Instance

```bash
# Launch t2.micro instance (free tier eligible)
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t2.micro \
  --key-name liap-tui-key \
  --security-groups liap-tui-sg \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=liap-tui-production}]' \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --user-data file://user-data.sh
```

### Step 2: Create User Data Script

```bash
# user-data.sh
#!/bin/bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo yum install git -y

# Install CloudWatch Agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Create app directory
mkdir -p /home/ec2-user/liap-tui
chown ec2-user:ec2-user /home/ec2-user/liap-tui
```

  NLBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for NLB (WebSocket)
      VpcId: !Ref VPCId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8000
          ToPort: 8000
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: liap-tui-nlb-sg

  ECSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ECS tasks
      VpcId: !Ref VPCId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          SourceSecurityGroupId: !Ref ALBSecurityGroup
        - IpProtocol: tcp
          FromPort: 8000
          ToPort: 8000
          SourceSecurityGroupId: !Ref NLBSecurityGroup
      Tags:
        - Key: Name
          Value: liap-tui-ecs-sg

  RedisSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Redis
      VpcId: !Ref VPCId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 6379
          ToPort: 6379
          SourceSecurityGroupId: !Ref ECSSecurityGroup
      Tags:
        - Key: Name
          Value: liap-tui-redis-sg

Outputs:
  ALBSecurityGroupId:
    Value: !Ref ALBSecurityGroup
    Export:
      Name: liap-tui-alb-sg-id
  ECSSecurityGroupId:
    Value: !Ref ECSSecurityGroup
    Export:
      Name: liap-tui-ecs-sg-id
  RedisSecurityGroupId:
    Value: !Ref RedisSecurityGroup
    Export:
      Name: liap-tui-redis-sg-id
```

Deploy security groups:
```bash
aws cloudformation create-stack \
  --stack-name liap-tui-security-groups \
  --template-body file://infrastructure/security-groups.yaml
```

### Step 3: Allocate Elastic IP

```bash
# Allocate Elastic IP
EIP_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
echo "Elastic IP Allocation ID: $EIP_ALLOC"

# Get instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=liap-tui-production" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

# Associate Elastic IP with instance
aws ec2 associate-address \
  --instance-id $INSTANCE_ID \
  --allocation-id $EIP_ALLOC

# Get the public IP
PUBLIC_IP=$(aws ec2 describe-addresses \
  --allocation-ids $EIP_ALLOC \
  --query 'Addresses[0].PublicIp' \
  --output text)

echo "Your server IP: $PUBLIC_IP"
```

### Step 4: Connect to Instance

```bash
# SSH into the instance
ssh -i liap-tui-key.pem ec2-user@$PUBLIC_IP

# Once connected, verify Docker is installed
docker --version
docker-compose --version
```

## Software Installation

### Step 1: Install Application Dependencies

```bash
# SSH into your EC2 instance
ssh -i liap-tui-key.pem ec2-user@$PUBLIC_IP

# Clone your repository
cd /home/ec2-user
git clone https://github.com/yourusername/liap-tui.git
cd liap-tui

# Create necessary directories
mkdir -p logs backups

# Set permissions
chown -R ec2-user:ec2-user /home/ec2-user/liap-tui
```

### Step 2: Configure Environment

```bash
# Create production environment file
cat > .env.production << EOF
ENV=production
DATABASE_PATH=/home/ec2-user/liap-tui/game_events.db
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=info
WORKERS=4
MAX_CONNECTIONS=1000
JWT_SECRET=$(openssl rand -base64 32)
EOF

# Secure the file
chmod 600 .env.production
```

### Step 3: Setup Automated Deployment Script

```bash
# deploy.sh
#!/bin/bash
set -e

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Build and restart containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check health
sleep 10
curl -f http://localhost/api/health || exit 1

echo "Deployment complete!"
```

## Application Deployment

### Step 1: Initial Docker Setup

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    build: .
    container_name: liap-tui
    ports:
      - "80:80"
      - "443:443"
    environment:
      - ENV=production
      - DATABASE_PATH=/app/data/game_events.db
    volumes:
      - ./game_events.db:/app/data/game_events.db
      - ./logs:/app/logs
      - ./backups:/app/backups
      - /etc/letsencrypt:/etc/letsencrypt:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF
```

### Step 2: Build and Run

```bash
# Build the application
docker-compose build

# Start the application
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify it's running
curl http://localhost/api/health
```

Deploy Redis:
```bash
aws cloudformation create-stack \
  --stack-name liap-tui-redis \
  --template-body file://infrastructure/redis.yaml
```

## Database Setup

### SQLite Configuration

```bash
# The database is automatically created by the application
# Ensure proper permissions
touch /home/ec2-user/liap-tui/game_events.db
chown ec2-user:ec2-user /home/ec2-user/liap-tui/game_events.db
chmod 644 /home/ec2-user/liap-tui/game_events.db

# Setup automated backups
cat > /home/ec2-user/liap-tui/backup.sh << 'EOF'
#!/bin/bash
# Daily backup script

DB_PATH="/home/ec2-user/liap-tui/game_events.db"
BACKUP_DIR="/home/ec2-user/liap-tui/backups"
S3_BUCKET="liap-tui-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create local backup
sqlite3 $DB_PATH ".backup $BACKUP_DIR/game_events_$DATE.db"
gzip $BACKUP_DIR/game_events_$DATE.db

# Upload to S3 (if configured)
if command -v aws &> /dev/null; then
    aws s3 cp $BACKUP_DIR/game_events_$DATE.db.gz s3://$S3_BUCKET/daily/
fi

# Keep only last 7 days of local backups
find $BACKUP_DIR -name "*.db.gz" -mtime +7 -delete
EOF

chmod +x /home/ec2-user/liap-tui/backup.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ec2-user/liap-tui/backup.sh") | crontab -
```

### S3 Backup Bucket (Optional)

```bash
# Create S3 bucket for backups
aws s3 mb s3://liap-tui-backups-$(date +%s)

# Set lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket liap-tui-backups-$(date +%s) \
  --lifecycle-configuration file://s3-lifecycle.json
```

### S3 Lifecycle Configuration

```json
// s3-lifecycle.json
{
  "Rules": [{
    "Id": "ArchiveOldBackups",
    "Status": "Enabled",
    "Transitions": [{
      "Days": 30,
      "StorageClass": "STANDARD_IA"
    }, {
      "Days": 90,
      "StorageClass": "GLACIER"
    }],
    "Expiration": {
      "Days": 365
    }
  }]
}
```

### Step 2: Create Task Definition

```json
// .aws/task-definition.json
{
  "family": "liap-tui-production",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/liap-tui-task-role",
  "containerDefinitions": [
    {
      "name": "liap-tui-app",
      "image": "${ECR_REGISTRY}/liap-tui:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        },
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENV",
          "value": "production"
        },
        {
          "name": "CORS_ORIGINS",
          "value": "https://liaptui.com,https://www.liaptui.com"
        }
      ],
      "secrets": [
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:${AWS_ACCOUNT_ID}:secret:liap-tui/redis-url"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/liap-tui",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register task definition:
```bash
# Create log group
aws logs create-log-group --log-group-name /ecs/liap-tui

# Register task definition
aws ecs register-task-definition --cli-input-json file://.aws/task-definition.json
```

### Step 3: Create ECS Service

```yaml
# infrastructure/ecs-service.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: ECS Service for Liap Tui

Parameters:
  ClusterName:
    Type: String
    Default: production-cluster
  TaskDefinition:
    Type: String
    Default: liap-tui-production:latest

Resources:
  ECSService:
    Type: AWS::ECS::Service
    DependsOn: 
      - ALBListener
      - NLBListener
    Properties:
      ServiceName: liap-tui-service
      Cluster: !Ref ClusterName
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 3
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          Subnets:
            - !ImportValue liap-tui-private-subnet-1
            - !ImportValue liap-tui-private-subnet-2
          SecurityGroups:
            - !ImportValue liap-tui-ecs-sg-id
          AssignPublicIp: DISABLED
      LoadBalancers:
        - ContainerName: liap-tui-app
          ContainerPort: 80
          TargetGroupArn: !Ref ALBTargetGroup
        - ContainerName: liap-tui-app
          ContainerPort: 8000
          TargetGroupArn: !Ref NLBTargetGroup
      DeploymentConfiguration:
        MaximumPercent: 200
        MinimumHealthyPercent: 100
        DeploymentCircuitBreaker:
          Enable: true
          Rollback: true
      PlacementStrategies:
        - Type: spread
          Field: attribute:ecs.availability-zone
      Tags:
        - Key: Name
          Value: liap-tui-service
```

## Domain and SSL Setup

### Step 1: Install Certbot

```bash
# Install Certbot for Let's Encrypt
sudo yum install -y certbot

# Stop the application temporarily
cd /home/ec2-user/liap-tui
docker-compose down

# Get SSL certificate
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive

# Start the application again
docker-compose up -d
```

### Step 2: Configure Nginx for SSL

```nginx
# nginx.conf (updated for SSL)
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rest of configuration...
}
```

  ALBTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: liap-tui-alb-tg
      Port: 80
      Protocol: HTTP
      VpcId: !ImportValue liap-tui-vpc-id
      TargetType: ip
      HealthCheckEnabled: true
      HealthCheckPath: /api/health
      HealthCheckProtocol: HTTP
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 10
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      Matcher:
        HttpCode: 200
      TargetGroupAttributes:
        - Key: deregistration_delay.timeout_seconds
          Value: 30
        - Key: stickiness.enabled
          Value: true
        - Key: stickiness.type
          Value: lb_cookie
        - Key: stickiness.lb_cookie.duration_seconds
          Value: 3600

  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref ALB
      Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: redirect
          RedirectConfig:
            Protocol: HTTPS
            Port: 443
            StatusCode: HTTP_301

  ALBListenerHTTPS:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref ALB
      Port: 443
      Protocol: HTTPS
      Certificates:
        - CertificateArn: !Ref Certificate
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ALBTargetGroup

Outputs:
  ALBDNSName:
    Value: !GetAtt ALB.DNSName
    Export:
      Name: liap-tui-alb-dns
```

### Network Load Balancer (WebSocket)

```yaml
# infrastructure/nlb.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Network Load Balancer for WebSocket

Resources:
  NLB:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: liap-tui-nlb
      Type: network
      Scheme: internet-facing
      Subnets:
        - !ImportValue liap-tui-public-subnet-1
        - !ImportValue liap-tui-public-subnet-2
      Tags:
        - Key: Name
          Value: liap-tui-nlb

  NLBTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: liap-tui-nlb-tg
      Port: 8000
      Protocol: TCP
      VpcId: !ImportValue liap-tui-vpc-id
      TargetType: ip
      HealthCheckEnabled: true
      HealthCheckProtocol: HTTP
      HealthCheckPath: /api/health
      HealthCheckPort: 80
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 10
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      TargetGroupAttributes:
        - Key: deregistration_delay.timeout_seconds
          Value: 60
        - Key: preserve_client_ip.enabled
          Value: true

  NLBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref NLB
      Port: 8000
      Protocol: TCP
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref NLBTargetGroup

Outputs:
  NLBDNSName:
    Value: !GetAtt NLB.DNSName
    Export:
      Name: liap-tui-nlb-dns
```

### Step 3: Setup Auto-Renewal

```bash
# Add renewal cron job
echo "0 0,12 * * * root certbot renew --quiet --post-hook 'docker restart liap-tui'" | sudo tee /etc/cron.d/certbot
```

### Step 4: Configure Route 53

```bash
# Create A record pointing to your Elastic IP
HOSTED_ZONE_ID="Z123456789ABC" # Your hosted zone ID

aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "yourdomain.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$PUBLIC_IP'"}]
      }
    }, {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "www.yourdomain.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$PUBLIC_IP'"}]
      }
    }]
  }'
```

  WWWRecord:
    Type: AWS::Route53::RecordSet
    Properties:
      HostedZoneId: !Ref HostedZoneId
      Name: www.liaptui.com
      Type: A
      AliasTarget:
        DNSName: !ImportValue liap-tui-alb-dns
        HostedZoneId: !GetAtt ALB.CanonicalHostedZoneID
        EvaluateTargetHealth: true

  WebSocketRecord:
    Type: AWS::Route53::RecordSet
    Properties:
      HostedZoneId: !Ref HostedZoneId
      Name: ws.liaptui.com
      Type: A
      AliasTarget:
        DNSName: !ImportValue liap-tui-nlb-dns
        HostedZoneId: !GetAtt NLB.CanonicalHostedZoneID
        EvaluateTargetHealth: true
```

## Monitoring Setup

### Step 1: Configure CloudWatch Agent

```bash
# Create CloudWatch configuration
sudo cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "metrics": {
    "namespace": "LiapTui",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {"name": "cpu_usage_idle", "rename": "CPU_USAGE_IDLE", "unit": "Percent"},
          "cpu_usage_active"
        ],
        "metrics_collection_interval": 60,
        "totalcpu": false
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/home/ec2-user/liap-tui/logs/app.log",
            "log_group_name": "/aws/ec2/liap-tui",
            "log_stream_name": "{instance_id}/app.log"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch Agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

### Step 2: Create CloudWatch Dashboard

```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name liap-tui-ec2 \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/EC2", "CPUUtilization", {"stat": "Average"}],
            [".", "NetworkIn", {"stat": "Sum"}],
            [".", "NetworkOut", {"stat": "Sum"}],
            ["LiapTui", "CPU_USAGE_IDLE", {"stat": "Average"}],
            [".", "mem_used_percent", {"stat": "Average"}]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "EC2 Instance Metrics"
        }
      }
    ]
  }'
```

Create dashboard:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name liap-tui-production \
  --dashboard-body file://infrastructure/dashboard.json
```

### Step 3: Setup Alarms

```bash
# CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name liap-tui-ec2-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID

# Disk space alarm
aws cloudwatch put-metric-alarm \
  --alarm-name liap-tui-ec2-high-disk \
  --alarm-description "Alert when disk usage exceeds 80%" \
  --metric-name disk_used_percent \
  --namespace LiapTui \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1

# Setup SNS for notifications (optional)
aws sns create-topic --name liap-tui-alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:liap-tui-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

## Go Live Checklist

### Pre-Deployment

- [ ] **Server Setup**
  - [ ] EC2 instance running
  - [ ] Security group configured
  - [ ] Elastic IP assigned
  - [ ] SSH access working

- [ ] **Software Installation**
  - [ ] Docker installed
  - [ ] Docker Compose installed
  - [ ] Git repository cloned
  - [ ] Environment variables set

- [ ] **Application**
  - [ ] Docker image builds successfully
  - [ ] Health check passing
  - [ ] Database file created
  - [ ] Logs directory created

- [ ] **SSL/Domain**
  - [ ] Domain pointing to Elastic IP
  - [ ] SSL certificate obtained
  - [ ] HTTPS working
  - [ ] Auto-renewal configured

### Deployment Steps

1. **Initial Deployment**
   ```bash
   # SSH into server
   ssh -i liap-tui-key.pem ec2-user@$PUBLIC_IP
   
   # Navigate to application
   cd /home/ec2-user/liap-tui
   
   # Start application
   docker-compose up -d
   
   # Check logs
   docker-compose logs -f
   ```

2. **Verify Deployment**
   ```bash
   # Check health endpoint
   curl https://yourdomain.com/api/health
   
   # Check Docker status
   docker ps
   
   # Check resource usage
   docker stats liap-tui
   ```

3. **Test WebSocket**
   ```javascript
   // Test WebSocket connection
   const ws = new WebSocket('wss://yourdomain.com/ws/lobby');
   ws.onopen = () => console.log('Connected');
   ws.onmessage = (e) => console.log('Message:', e.data);
   ```

4. **Update Deployment**
   ```bash
   # For updates
   cd /home/ec2-user/liap-tui
   git pull origin main
   docker-compose build
   docker-compose up -d
   ```

### Post-Deployment

- [ ] **Monitoring**
  - [ ] CloudWatch dashboard showing data
  - [ ] Alarms working
  - [ ] Logs visible in CloudWatch

- [ ] **Performance**
  - [ ] Page load time < 3s
  - [ ] WebSocket latency < 100ms
  - [ ] CPU usage < 50%
  - [ ] Memory usage < 70%

- [ ] **Security**
  - [ ] SSH restricted to your IP
  - [ ] HTTPS enforced
  - [ ] Firewall rules verified
  - [ ] fail2ban active

- [ ] **Backup**
  - [ ] Database backup script working
  - [ ] S3 backups configured (optional)
  - [ ] Can restore from backup

## Post-Deployment

### Monitoring and Maintenance

1. **Daily Checks**
   ```bash
   # Check application health
   curl https://yourdomain.com/api/health
   
   # Check disk space
   df -h
   
   # Check Docker logs
   docker-compose logs --tail=100
   ```

2. **Weekly Tasks**
   ```bash
   # Update system packages
   sudo yum update -y
   
   # Check for Docker updates
   docker version
   
   # Review backup files
   ls -la /home/ec2-user/liap-tui/backups/
   ```

3. **Monthly Tasks**
   ```bash
   # Rotate logs
   docker-compose logs > logs/archive-$(date +%Y%m).log
   docker-compose logs --tail=0 -f > logs/current.log &
   
   # Update SSL certificate (auto-renews)
   sudo certbot renew --dry-run
   
   # Review costs in AWS console
   ```

### Scaling Considerations

When you need to scale:

1. **Vertical Scaling** (Recommended first)
   ```bash
   # Stop instance
   aws ec2 stop-instances --instance-ids $INSTANCE_ID
   
   # Change instance type
   aws ec2 modify-instance-attribute \
     --instance-id $INSTANCE_ID \
     --instance-type t2.small
   
   # Start instance
   aws ec2 start-instances --instance-ids $INSTANCE_ID
   ```

2. **Add CloudFront CDN**
   - Reduces load on server
   - Improves global performance
   - Caches static assets

### Troubleshooting Common Issues

1. **Container Won't Start**
   ```bash
   # Check container logs
   docker-compose logs app
   
   # Check container status
   docker ps -a
   
   # Rebuild if needed
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **WebSocket Connection Issues**
   ```bash
   # Check if port is open
   sudo netstat -tlnp | grep 8000
   
   # Check nginx config
   docker exec liap-tui cat /etc/nginx/nginx.conf
   
   # Test WebSocket locally
   wscat -c ws://localhost:8000/ws/test
   ```

3. **High CPU/Memory Usage**
   ```bash
   # Check resource usage
   docker stats
   
   # Check process inside container
   docker exec liap-tui top
   
   # Restart if needed
   docker-compose restart
   ```

### Backup and Recovery

1. **Create Manual Backup**
   ```bash
   # Backup database
   sqlite3 game_events.db ".backup game_events_backup_$(date +%Y%m%d).db"
   
   # Backup entire application
   tar -czf liap-tui-backup-$(date +%Y%m%d).tar.gz \
     game_events.db docker-compose.yml .env.production
   ```

2. **Restore from Backup**
   ```bash
   # Stop application
   docker-compose down
   
   # Restore database
   cp game_events_backup_20240115.db game_events.db
   
   # Start application
   docker-compose up -d
   ```

## Cost Optimization

### Free Tier Usage
- **EC2**: 750 hours/month of t2.micro (12 months)
- **EBS**: 30GB storage included
- **Data Transfer**: 15GB/month out
- **CloudWatch**: Basic monitoring free
- **Total Cost**: $0/month within limits

### After Free Tier
- **t2.micro**: ~$8.50/month
- **30GB EBS**: ~$3/month  
- **Elastic IP**: Free when attached
- **Data Transfer**: $0.09/GB after 15GB
- **Estimated Total**: ~$15-20/month

### Cost Saving Tips
1. Use CloudFront for static assets
2. Enable gzip compression
3. Implement caching headers
4. Monitor data transfer
5. Use S3 for backups (cheaper than EBS)

## Summary

You've successfully deployed Liap Tui to AWS EC2! The deployment includes:

✅ EC2 t2.micro instance (free tier eligible)
✅ Docker containerization
✅ SQLite database with backups
✅ SSL/TLS encryption with Let's Encrypt
✅ CloudWatch monitoring
✅ Automated backup system
✅ Simple deployment process

Next steps:
1. Monitor initial performance
2. Set up CloudFront CDN if needed
3. Implement additional monitoring
4. Plan for scaling when needed

Congratulations on launching your multiplayer game! 🎮

Total deployment time: ~30 minutes
Monthly cost: $0 (free tier) or ~$15-20