# Deployment Guide - AWS Production Deployment Walkthrough

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [AWS Account Setup](#aws-account-setup)
4. [Infrastructure Preparation](#infrastructure-preparation)
5. [Container Registry Setup](#container-registry-setup)
6. [Database Setup](#database-setup)
7. [ECS Deployment](#ecs-deployment)
8. [Load Balancer Configuration](#load-balancer-configuration)
9. [Domain and SSL Setup](#domain-and-ssl-setup)
10. [Monitoring Setup](#monitoring-setup)
11. [Go Live Checklist](#go-live-checklist)
12. [Post-Deployment](#post-deployment)

## Overview

This guide walks through deploying Liap Tui to AWS ECS step-by-step. By the end, you'll have a production-ready deployment capable of handling thousands of concurrent players.

### Deployment Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CloudFront │────▶│     ALB     │────▶│  ECS Tasks  │
│     CDN     │     │   (HTTPS)   │     │  (Fargate)  │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                    │
                    ┌───────▼───────┐    ┌──────▼──────┐
                    │      NLB      │    │    Redis    │
                    │  (WebSocket)  │    │(ElastiCache)│
                    └───────────────┘    └─────────────┘
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

2. **Docker installed**
   ```bash
   # Verify Docker
   docker --version
   docker-compose --version
   ```

3. **Terraform installed (optional but recommended)**
   ```bash
   # Install Terraform
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   terraform --version
   ```

### AWS Services Required

- ECS (Elastic Container Service)
- ECR (Elastic Container Registry)
- ElastiCache (Redis)
- RDS (PostgreSQL) - optional
- ALB (Application Load Balancer)
- NLB (Network Load Balancer)
- CloudWatch
- Route 53 (for domain)
- Certificate Manager

## AWS Account Setup

### Step 1: Create IAM User for Deployment

```bash
# Create deployment user
aws iam create-user --user-name liap-tui-deploy

# Attach necessary policies
aws iam attach-user-policy \
  --user-name liap-tui-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

aws iam attach-user-policy \
  --user-name liap-tui-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

aws iam attach-user-policy \
  --user-name liap-tui-deploy \
  --policy-arn arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess

# Create access key
aws iam create-access-key --user-name liap-tui-deploy
```

### Step 2: Create VPC and Subnets

```bash
# Using AWS CLI
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=liap-tui-vpc}]'

# Or use this CloudFormation template
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

## Infrastructure Preparation

### Security Groups

```yaml
# infrastructure/security-groups.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Security Groups for Liap Tui

Parameters:
  VPCId:
    Type: String
    Default: !ImportValue liap-tui-vpc-id

Resources:
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ALB
      VpcId: !Ref VPCId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: liap-tui-alb-sg

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

## Container Registry Setup

### Step 1: Create ECR Repository

```bash
# Create repository
aws ecr create-repository \
  --repository-name liap-tui \
  --image-scanning-configuration scanOnPush=true \
  --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
```

### Step 2: Build and Push Image

```bash
# Build production image
docker build -t liap-tui:latest .

# Tag for ECR
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REGISTRY=${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

docker tag liap-tui:latest ${ECR_REGISTRY}/liap-tui:latest
docker tag liap-tui:latest ${ECR_REGISTRY}/liap-tui:v1.0.0

# Push to ECR
docker push ${ECR_REGISTRY}/liap-tui:latest
docker push ${ECR_REGISTRY}/liap-tui:v1.0.0
```

### Step 3: Setup CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: liap-tui
  ECS_SERVICE: liap-tui-service
  ECS_CLUSTER: production-cluster
  TASK_DEFINITION: .aws/task-definition.json

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image
      id: build-image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT
    
    - name: Fill in the new image ID in task definition
      id: task-def
      uses: aws-actions/amazon-ecs-render-task-definition@v1
      with:
        task-definition: ${{ env.TASK_DEFINITION }}
        container-name: liap-tui-app
        image: ${{ steps.build-image.outputs.image }}
    
    - name: Deploy to ECS
      uses: aws-actions/amazon-ecs-deploy-task-definition@v1
      with:
        task-definition: ${{ steps.task-def.outputs.task-definition }}
        service: ${{ env.ECS_SERVICE }}
        cluster: ${{ env.ECS_CLUSTER }}
        wait-for-service-stability: true
```

## Database Setup

### ElastiCache Redis Setup

```yaml
# infrastructure/redis.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: ElastiCache Redis for Liap Tui

Resources:
  RedisSubnetGroup:
    Type: AWS::ElastiCache::SubnetGroup
    Properties:
      Description: Subnet group for Redis
      SubnetIds:
        - !ImportValue liap-tui-private-subnet-1
        - !ImportValue liap-tui-private-subnet-2

  RedisParameterGroup:
    Type: AWS::ElastiCache::ParameterGroup
    Properties:
      CacheParameterGroupFamily: redis7
      Description: Parameter group for Liap Tui Redis
      Properties:
        maxmemory-policy: allkeys-lru
        timeout: 300

  RedisCluster:
    Type: AWS::ElastiCache::CacheCluster
    Properties:
      CacheNodeType: cache.t3.micro  # Start small, scale as needed
      Engine: redis
      EngineVersion: 7.0
      NumCacheNodes: 1
      Port: 6379
      CacheSubnetGroupName: !Ref RedisSubnetGroup
      CacheParameterGroupName: !Ref RedisParameterGroup
      VpcSecurityGroupIds:
        - !ImportValue liap-tui-redis-sg-id
      Tags:
        - Key: Name
          Value: liap-tui-redis

Outputs:
  RedisEndpoint:
    Value: !GetAtt RedisCluster.RedisEndpoint.Address
    Export:
      Name: liap-tui-redis-endpoint
  RedisPort:
    Value: !GetAtt RedisCluster.RedisEndpoint.Port
    Export:
      Name: liap-tui-redis-port
```

Deploy Redis:
```bash
aws cloudformation create-stack \
  --stack-name liap-tui-redis \
  --template-body file://infrastructure/redis.yaml
```

### Optional: RDS PostgreSQL Setup

```yaml
# infrastructure/rds.yaml (for future persistence)
AWSTemplateFormatVersion: '2010-09-09'
Description: RDS PostgreSQL for Liap Tui (Optional)

Parameters:
  DBPassword:
    Type: String
    NoEcho: true
    Description: Database password

Resources:
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for RDS
      SubnetIds:
        - !ImportValue liap-tui-private-subnet-1
        - !ImportValue liap-tui-private-subnet-2
      Tags:
        - Key: Name
          Value: liap-tui-db-subnet-group

  DBInstance:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: liap-tui-db
      AllocatedStorage: 20
      DBInstanceClass: db.t3.micro
      Engine: postgres
      EngineVersion: '15.4'
      MasterUsername: liaptuiadmin
      MasterUserPassword: !Ref DBPassword
      DBName: liaptui
      VPCSecurityGroups:
        - !ImportValue liap-tui-rds-sg-id
      DBSubnetGroupName: !Ref DBSubnetGroup
      BackupRetentionPeriod: 7
      PreferredBackupWindow: "03:00-04:00"
      PreferredMaintenanceWindow: "mon:04:00-mon:05:00"
      Tags:
        - Key: Name
          Value: liap-tui-db

Outputs:
  DBEndpoint:
    Value: !GetAtt DBInstance.Endpoint.Address
    Export:
      Name: liap-tui-db-endpoint
```

## ECS Deployment

### Step 1: Create ECS Cluster

```bash
# Create cluster with capacity providers
aws ecs create-cluster \
  --cluster-name production-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1,base=2 \
    capacityProvider=FARGATE_SPOT,weight=2,base=0 \
  --settings name=containerInsights,value=enabled
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

## Load Balancer Configuration

### Application Load Balancer (HTTP/HTTPS)

```yaml
# infrastructure/alb.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Application Load Balancer for Liap Tui

Resources:
  ALB:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: liap-tui-alb
      Type: application
      Scheme: internet-facing
      SecurityGroups:
        - !ImportValue liap-tui-alb-sg-id
      Subnets:
        - !ImportValue liap-tui-public-subnet-1
        - !ImportValue liap-tui-public-subnet-2
      Tags:
        - Key: Name
          Value: liap-tui-alb

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

## Domain and SSL Setup

### Step 1: Request SSL Certificate

```bash
# Request certificate for your domain
aws acm request-certificate \
  --domain-name liaptui.com \
  --subject-alternative-names "*.liaptui.com" \
  --validation-method DNS \
  --region us-east-1
```

### Step 2: Create Route 53 Hosted Zone

```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name liaptui.com \
  --caller-reference $(date +%s)
```

### Step 3: Configure DNS Records

```yaml
# infrastructure/route53.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Route 53 DNS for Liap Tui

Parameters:
  HostedZoneId:
    Type: String
    Description: Route 53 Hosted Zone ID

Resources:
  WebRecord:
    Type: AWS::Route53::RecordSet
    Properties:
      HostedZoneId: !Ref HostedZoneId
      Name: liaptui.com
      Type: A
      AliasTarget:
        DNSName: !ImportValue liap-tui-alb-dns
        HostedZoneId: !GetAtt ALB.CanonicalHostedZoneID
        EvaluateTargetHealth: true

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

### CloudWatch Dashboard

```json
// infrastructure/dashboard.json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", { "stat": "Average" }],
          [".", "MemoryUtilization", { "stat": "Average" }],
          ["LiapTui", "ActiveConnections", { "stat": "Sum" }],
          [".", "GameRoomsActive", { "stat": "Average" }]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Service Metrics"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "TargetResponseTime"],
          [".", "RequestCount", { "stat": "Sum" }],
          [".", "HTTPCode_Target_4XX_Count", { "stat": "Sum" }],
          [".", "HTTPCode_Target_5XX_Count", { "stat": "Sum" }]
        ],
        "period": 300,
        "region": "us-east-1",
        "title": "ALB Metrics"
      }
    }
  ]
}
```

Create dashboard:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name liap-tui-production \
  --dashboard-body file://infrastructure/dashboard.json
```

### CloudWatch Alarms

```bash
# CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name liap-tui-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Memory alarm
aws cloudwatch put-metric-alarm \
  --alarm-name liap-tui-high-memory \
  --alarm-description "Alert when memory exceeds 80%" \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name liap-tui-high-error-rate \
  --alarm-description "Alert when 5XX errors exceed 1%" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

## Go Live Checklist

### Pre-Deployment

- [ ] **Code Review**
  - [ ] All PRs approved and merged
  - [ ] No critical security issues
  - [ ] Performance tested

- [ ] **Infrastructure**
  - [ ] VPC and subnets created
  - [ ] Security groups configured
  - [ ] Load balancers healthy
  - [ ] Redis cluster running
  - [ ] SSL certificates active

- [ ] **Container**
  - [ ] Production image built
  - [ ] Image scanned for vulnerabilities
  - [ ] Image pushed to ECR

- [ ] **Configuration**
  - [ ] Environment variables set
  - [ ] Secrets stored in Secrets Manager
  - [ ] CORS origins configured
  - [ ] Feature flags set

### Deployment Steps

1. **Deploy Infrastructure**
   ```bash
   # Deploy all CloudFormation stacks in order
   ./deploy-infrastructure.sh
   ```

2. **Deploy Application**
   ```bash
   # Update service with new task definition
   aws ecs update-service \
     --cluster production-cluster \
     --service liap-tui-service \
     --task-definition liap-tui-production:latest \
     --force-new-deployment
   ```

3. **Verify Deployment**
   ```bash
   # Check service status
   aws ecs describe-services \
     --cluster production-cluster \
     --services liap-tui-service
   
   # Check health endpoint
   curl https://liaptui.com/api/health
   ```

4. **Test WebSocket**
   ```javascript
   // Test WebSocket connection
   const ws = new WebSocket('wss://ws.liaptui.com/ws/test');
   ws.onopen = () => console.log('Connected');
   ws.onmessage = (e) => console.log('Message:', e.data);
   ```

### Post-Deployment

- [ ] **Monitoring**
  - [ ] CloudWatch dashboard showing data
  - [ ] Alarms configured and tested
  - [ ] Logs flowing correctly

- [ ] **Performance**
  - [ ] Response times acceptable
  - [ ] WebSocket latency low
  - [ ] No memory leaks

- [ ] **Security**
  - [ ] WAF rules active
  - [ ] Security groups locked down
  - [ ] Secrets rotated

- [ ] **Backup**
  - [ ] Redis snapshots enabled
  - [ ] CloudFormation templates backed up
  - [ ] Runbooks documented

## Post-Deployment

### Monitoring and Maintenance

1. **Daily Checks**
   - Review CloudWatch dashboard
   - Check error logs
   - Monitor costs

2. **Weekly Tasks**
   - Review performance metrics
   - Check for security updates
   - Update dependencies

3. **Monthly Tasks**
   - Rotate secrets
   - Review and optimize costs
   - Update documentation

### Scaling Operations

```bash
# Scale up for peak times
aws ecs update-service \
  --cluster production-cluster \
  --service liap-tui-service \
  --desired-count 10

# Scale down during quiet times
aws ecs update-service \
  --cluster production-cluster \
  --service liap-tui-service \
  --desired-count 3
```

### Troubleshooting Common Issues

1. **Container Won't Start**
   ```bash
   # Check task stopped reason
   aws ecs describe-tasks \
     --cluster production-cluster \
     --tasks $(aws ecs list-tasks --cluster production-cluster --service-name liap-tui-service --query 'taskArns[0]' --output text)
   ```

2. **WebSocket Connection Issues**
   - Check NLB target health
   - Verify security group rules
   - Check nginx timeout settings

3. **High Latency**
   - Check Redis connection
   - Review CloudWatch metrics
   - Consider scaling up

### Rollback Procedure

```bash
# Rollback to previous version
aws ecs update-service \
  --cluster production-cluster \
  --service liap-tui-service \
  --task-definition liap-tui-production:previous-version \
  --force-new-deployment

# If infrastructure issues
aws cloudformation update-stack \
  --stack-name liap-tui-infrastructure \
  --use-previous-template
```

## Summary

You've successfully deployed Liap Tui to AWS! The deployment includes:

✅ High-availability ECS Fargate cluster
✅ Auto-scaling based on load
✅ Redis for session state
✅ Dual load balancers (ALB + NLB)
✅ SSL/TLS encryption
✅ CloudWatch monitoring
✅ Automated deployments

Next steps:
1. Monitor initial performance
2. Gather user feedback
3. Optimize based on real usage
4. Plan feature updates

Congratulations on launching your multiplayer game! 🎮