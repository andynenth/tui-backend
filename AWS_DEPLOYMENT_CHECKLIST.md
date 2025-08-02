# AWS Deployment Checklist for Liap Tui

## 🚨 Critical Tasks (Do First)

### 1. Remove Sensitive Data from Git
```bash
# Remove .env from git history
git rm --cached .env
git commit -m "Remove .env from tracking"

# Add to .gitignore
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .env to gitignore"
```

### 2. Create Environment Configuration
```bash
# Create example file
cp .env .env.example
# Edit .env.example to remove actual values
```

### 3. Create Production Dockerfile
Create `Dockerfile.prod` with multi-stage build:
```dockerfile
# Build stage
FROM node:18-alpine as frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Python stage
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend
COPY shared/ ./shared
COPY --from=frontend-builder /app/dist ./backend/static

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:5050/api/health')"

ENV PYTHONPATH=/app
EXPOSE 5050

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "5050"]
```

## 📋 Pre-Deployment Tasks

### Configuration Updates

1. **Update CORS for production**
   ```python
   # backend/api/main.py
   ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
   # Set in AWS: "https://yourdomain.com,https://www.yourdomain.com"
   ```

2. **Disable debug mode**
   ```python
   DEBUG = os.getenv("DEBUG", "false").lower() == "true"
   ```

3. **Configure logging for CloudWatch**
   ```python
   # JSON format for CloudWatch
   logging.basicConfig(
       format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
       level=logging.INFO if not DEBUG else logging.DEBUG
   )
   ```

### AWS-Specific Files

1. **Create `buildspec.yml`** for CodeBuild:
   ```yaml
   version: 0.2
   phases:
     pre_build:
       commands:
         - echo Logging in to Amazon ECR...
         - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
     build:
       commands:
         - echo Build started on `date`
         - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG -f Dockerfile.prod .
         - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
     post_build:
       commands:
         - echo Build completed on `date`
         - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
   ```

2. **Create ECS Task Definition** `task-definition.json`:
   ```json
   {
     "family": "liap-tui",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "containerDefinitions": [
       {
         "name": "liap-tui",
         "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/liap-tui:latest",
         "portMappings": [
           {
             "containerPort": 5050,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {"name": "API_HOST", "value": "0.0.0.0"},
           {"name": "API_PORT", "value": "5050"},
           {"name": "DEBUG", "value": "false"}
         ],
         "secrets": [
           {
             "name": "ALLOWED_ORIGINS",
             "valueFrom": "arn:aws:secretsmanager:region:account:secret:liap-tui/allowed-origins"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/liap-tui",
             "awslogs-region": "${AWS_REGION}",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

## 🚀 Deployment Options

### Option 1: ECS Fargate (Recommended)
- Serverless containers
- Auto-scaling
- No server management
- Good for WebSocket apps

### Option 2: Elastic Beanstalk
- Easier setup
- Less control
- May have issues with WebSocket

### Option 3: EC2 with Docker
- Full control
- More management overhead
- Need to handle scaling

## 🔧 Additional Considerations

### WebSocket on AWS
- Use Application Load Balancer (ALB) with sticky sessions
- Enable WebSocket support on target group
- Set idle timeout to 3600 seconds (1 hour)

### Static Assets
- Upload frontend build to S3
- Use CloudFront for CDN
- Update FastAPI to redirect static requests

### Database
- Currently uses in-memory storage
- Need to add:
  - RDS for persistent data
  - ElastiCache for rate limiting
  - DynamoDB for session storage

### Monitoring
- CloudWatch Logs for application logs
- CloudWatch Metrics for custom metrics
- X-Ray for distributed tracing
- CloudWatch Alarms for alerts

## 📊 Cost Estimation

### Minimal Setup (Dev/Test)
- ECS Fargate: ~$20-30/month
- ALB: ~$20/month
- CloudWatch: ~$5/month
- **Total: ~$45-55/month**

### Production Setup
- ECS Fargate (2 tasks): ~$40-60/month
- ALB: ~$20/month
- RDS (db.t3.micro): ~$15/month
- ElastiCache: ~$15/month
- CloudFront: ~$10/month
- **Total: ~$100-120/month**

## 🎯 Next Steps

1. Fix security issues (remove .env from git)
2. Create production Dockerfile
3. Set up AWS account and ECR repository
4. Create ECS cluster and task definition
5. Set up ALB with WebSocket support
6. Configure CloudWatch logging
7. Deploy and test
8. Set up monitoring and alarms

## 🔗 Useful AWS Resources

- [ECS with Fargate Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/getting-started-fargate.html)
- [ALB WebSocket Support](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html#listener-configuration)
- [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)