# Liap Tui Hybrid Migration Checklist
## ECS Fargate + Lambda Implementation Guide

### Pre-Migration Requirements
- [ ] AWS Account with appropriate permissions
- [ ] Docker installed locally for testing
- [ ] Terraform or AWS CDK for infrastructure as code
- [ ] Redis installed locally for development
- [ ] AWS CLI configured with credentials

---

## Phase 1: State Externalization (Week 1-2)

### 1.1 Redis Adapter Implementation
- [ ] **Create Redis adapter** (`backend/adapters/redis_adapter.py`)
  - [ ] Implement connection pooling
  - [ ] Add save/get methods for room state
  - [ ] Add save/get methods for game state
  - [ ] Implement pub/sub for event broadcasting
  - [ ] Add connection retry logic
  - [ ] Create TTL management for rooms

- [ ] **Update Room Manager** (`backend/room_manager.py`)
  - [ ] Inject Redis adapter dependency
  - [ ] Implement local cache with Redis fallback
  - [ ] Add state synchronization methods
  - [ ] Update create_room to persist to Redis
  - [ ] Update get_room to check Redis
  - [ ] Add cache invalidation logic

- [ ] **Update Game State Machine** (`backend/engine/state_machine/`)
  - [ ] Add serialization methods to game state
  - [ ] Implement state persistence after each transition
  - [ ] Update event sourcing to use Redis
  - [ ] Add state recovery from Redis
  - [ ] Test state machine with external storage

### 1.2 WebSocket Manager Updates
- [ ] **Modify Socket Manager** (`backend/socket_manager.py`)
  - [ ] Add Redis pub/sub for cross-instance messaging
  - [ ] Implement connection registry in Redis
  - [ ] Update broadcast to use Redis pub/sub
  - [ ] Add connection recovery logic
  - [ ] Handle multi-instance scenarios

### 1.3 Local Testing
- [ ] **Docker Compose Setup**
  - [ ] Add Redis service to docker-compose.dev.yml
  - [ ] Configure Redis persistence
  - [ ] Test with multiple backend instances
  - [ ] Verify state synchronization
  - [ ] Load test with shared state

---

## Phase 2: Lambda Function Development (Week 3)

### 2.1 Project Structure
- [ ] **Create Lambda directory structure**
  ```
  lambda/
  ├── src/
  │   ├── handlers/
  │   │   ├── health.py
  │   │   ├── stats.py
  │   │   ├── events.py
  │   │   └── admin.py
  │   ├── utils/
  │   │   ├── redis_client.py
  │   │   └── response.py
  │   └── requirements.txt
  ├── tests/
  ├── serverless.yml
  └── package.json
  ```

### 2.2 Lambda Functions
- [ ] **Health Check Endpoints**
  - [ ] Basic health check handler
  - [ ] Detailed health with Redis connectivity
  - [ ] Metrics endpoint for Prometheus
  - [ ] Add CORS headers
  - [ ] Implement error handling

- [ ] **Statistics Endpoints**
  - [ ] System stats handler
  - [ ] Room statistics from Redis
  - [ ] Player count aggregation
  - [ ] Game metrics calculation
  - [ ] Performance monitoring data

- [ ] **Event Store Endpoints**
  - [ ] Get events by room ID
  - [ ] Event filtering and pagination
  - [ ] State reconstruction endpoint
  - [ ] Event store statistics
  - [ ] Add caching headers

- [ ] **Admin Endpoints**
  - [ ] Force room cleanup
  - [ ] Reset stuck games
  - [ ] View/modify game state
  - [ ] Player management
  - [ ] System maintenance functions

### 2.3 Serverless Configuration
- [ ] **Serverless Framework Setup**
  - [ ] Install Serverless Framework
  - [ ] Configure serverless.yml
  - [ ] Set up environment variables
  - [ ] Configure VPC settings for Redis access
  - [ ] Add Lambda Layers for dependencies

- [ ] **API Gateway Configuration**
  - [ ] Define REST endpoints
  - [ ] Configure CORS settings
  - [ ] Set up request/response models
  - [ ] Add request validation
  - [ ] Configure throttling

### 2.4 Local Lambda Testing
- [ ] **SAM Local Testing**
  - [ ] Install AWS SAM CLI
  - [ ] Create SAM template
  - [ ] Test functions locally
  - [ ] Mock Redis responses
  - [ ] Verify API Gateway events

---

## Phase 3: WebSocket Service Containerization (Week 4)

### 3.1 Fargate-Optimized Container
- [ ] **Create Fargate Dockerfile**
  - [ ] Multi-stage build for size optimization
  - [ ] Include only WebSocket dependencies
  - [ ] Remove unnecessary files
  - [ ] Add health check endpoint
  - [ ] Configure for horizontal scaling

- [ ] **WebSocket-Only Application**
  - [ ] Create `websocket_app.py`
  - [ ] Remove REST endpoints
  - [ ] Configure Redis connection
  - [ ] Add graceful shutdown
  - [ ] Implement connection draining

### 3.2 Container Configuration
- [ ] **Environment Variables**
  - [ ] REDIS_URL configuration
  - [ ] WebSocket settings
  - [ ] Logging configuration
  - [ ] Performance tuning
  - [ ] Security settings

- [ ] **Health Checks**
  - [ ] HTTP health endpoint
  - [ ] WebSocket health check
  - [ ] Redis connectivity check
  - [ ] Memory usage monitoring
  - [ ] Connection count limits

### 3.3 Local Container Testing
- [ ] **Docker Testing**
  - [ ] Build Fargate container
  - [ ] Test with local Redis
  - [ ] Verify WebSocket connections
  - [ ] Test horizontal scaling
  - [ ] Measure resource usage

---

## Phase 4: Infrastructure Deployment (Week 5)

### 4.1 Network Infrastructure
- [ ] **VPC Configuration**
  - [ ] Create VPC with public/private subnets
  - [ ] Configure NAT gateways
  - [ ] Set up security groups
  - [ ] Configure VPC endpoints
  - [ ] Plan IP addressing

### 4.2 ElastiCache Redis
- [ ] **Redis Cluster Setup**
  - [ ] Create ElastiCache subnet group
  - [ ] Deploy Redis cluster (multi-AZ)
  - [ ] Configure parameter groups
  - [ ] Set up automatic backups
  - [ ] Configure security groups

- [ ] **Redis Configuration**
  - [ ] Enable Redis AUTH
  - [ ] Configure maxmemory policy
  - [ ] Set up Redis persistence
  - [ ] Configure replication
  - [ ] Test failover scenarios

### 4.3 ECS Fargate Setup
- [ ] **ECS Cluster**
  - [ ] Create ECS cluster
  - [ ] Configure cluster capacity providers
  - [ ] Set up CloudWatch Container Insights
  - [ ] Configure cluster auto-scaling
  - [ ] Add cluster monitoring

- [ ] **Task Definition**
  - [ ] Create Fargate task definition
  - [ ] Configure CPU/memory settings
  - [ ] Set environment variables
  - [ ] Configure logging to CloudWatch
  - [ ] Add task IAM roles

- [ ] **ECS Service**
  - [ ] Create ECS service
  - [ ] Configure desired count (start with 2)
  - [ ] Set up service auto-scaling
  - [ ] Configure deployment settings
  - [ ] Add circuit breaker

### 4.4 Load Balancer Configuration
- [ ] **Application Load Balancer**
  - [ ] Create ALB with WebSocket support
  - [ ] Configure target groups
  - [ ] Set up health checks
  - [ ] Configure sticky sessions for WebSocket
  - [ ] Add SSL/TLS certificates

- [ ] **Path-Based Routing**
  - [ ] Route /ws/* to Fargate targets
  - [ ] Route /api/* to Lambda functions
  - [ ] Configure WebSocket upgrade headers
  - [ ] Set up request routing rules
  - [ ] Test routing configuration

### 4.5 Lambda Deployment
- [ ] **Deploy Lambda Functions**
  - [ ] Package Lambda functions
  - [ ] Deploy using Serverless Framework
  - [ ] Configure VPC access
  - [ ] Set up environment variables
  - [ ] Test Lambda endpoints

- [ ] **API Gateway Integration**
  - [ ] Create API Gateway
  - [ ] Configure Lambda integrations
  - [ ] Set up custom domain
  - [ ] Configure API keys (if needed)
  - [ ] Deploy to stages

### 4.6 Monitoring Setup
- [ ] **CloudWatch Configuration**
  - [ ] Create dashboards for ECS metrics
  - [ ] Add Lambda function metrics
  - [ ] Monitor Redis metrics
  - [ ] Set up ALB metrics
  - [ ] Create custom metrics

- [ ] **Alarms and Notifications**
  - [ ] ECS task count alarms
  - [ ] Lambda error rate alarms
  - [ ] Redis memory/CPU alarms
  - [ ] ALB target health alarms
  - [ ] Create SNS topics for alerts

---

## Phase 5: Testing & Migration (Week 6)

### 5.1 Integration Testing
- [ ] **End-to-End Testing**
  - [ ] Test game creation flow
  - [ ] Verify WebSocket connections
  - [ ] Test real-time updates
  - [ ] Verify state persistence
  - [ ] Test failover scenarios

### 5.2 Performance Testing
- [ ] **Load Testing**
  - [ ] Create load test scripts
  - [ ] Test with 100 concurrent games
  - [ ] Measure WebSocket latency
  - [ ] Test API response times
  - [ ] Monitor resource usage

- [ ] **Stress Testing**
  - [ ] Test auto-scaling triggers
  - [ ] Simulate connection spikes
  - [ ] Test Redis failover
  - [ ] Verify graceful degradation
  - [ ] Document performance limits

### 5.3 Security Validation
- [ ] **Security Checks**
  - [ ] Verify VPC isolation
  - [ ] Test security group rules
  - [ ] Validate IAM permissions
  - [ ] Check Redis AUTH
  - [ ] Scan for vulnerabilities

### 5.4 Migration Execution
- [ ] **DNS Preparation**
  - [ ] Set up Route 53 hosted zone
  - [ ] Create weighted routing policies
  - [ ] Configure health checks
  - [ ] Plan DNS cutover
  - [ ] Document rollback procedure

- [ ] **Traffic Migration**
  - [ ] Start with 5% traffic to new infrastructure
  - [ ] Monitor error rates and latency
  - [ ] Increase to 25% after 2 hours
  - [ ] Move to 50% after 24 hours
  - [ ] Complete migration to 100%

- [ ] **Monitoring During Migration**
  - [ ] Watch CloudWatch dashboards
  - [ ] Monitor application logs
  - [ ] Track user complaints
  - [ ] Check game completion rates
  - [ ] Verify state consistency

### 5.5 Post-Migration
- [ ] **Cleanup**
  - [ ] Document new architecture
  - [ ] Update runbooks
  - [ ] Remove old infrastructure
  - [ ] Update CI/CD pipelines
  - [ ] Archive old code

- [ ] **Optimization**
  - [ ] Analyze cost metrics
  - [ ] Right-size Fargate tasks
  - [ ] Optimize Lambda memory
  - [ ] Review Redis usage
  - [ ] Implement cost controls

---

## Rollback Plan

### Immediate Rollback Triggers
- [ ] Error rate > 5%
- [ ] WebSocket connection failures > 10%
- [ ] Game state corruption detected
- [ ] Redis connectivity issues
- [ ] User complaints spike

### Rollback Steps
1. [ ] Update Route 53 weights to 0% new infrastructure
2. [ ] Verify traffic returns to old infrastructure
3. [ ] Assess and fix issues
4. [ ] Plan remediation
5. [ ] Retry migration with fixes

---

## Success Criteria

### Technical Metrics
- [ ] WebSocket latency < 100ms (p99)
- [ ] API response time < 200ms (p95)
- [ ] Zero game state loss
- [ ] 99.9% uptime during migration
- [ ] Auto-scaling working correctly

### Business Metrics
- [ ] No increase in user complaints
- [ ] Game completion rate unchanged
- [ ] Player retention stable
- [ ] Cost within 10% of estimate
- [ ] Support ticket volume normal

---

## Long-Term Maintenance

### Weekly Tasks
- [ ] Review CloudWatch metrics
- [ ] Check Redis memory usage
- [ ] Analyze Lambda cold starts
- [ ] Review auto-scaling events
- [ ] Update documentation

### Monthly Tasks
- [ ] Cost optimization review
- [ ] Security patches
- [ ] Performance analysis
- [ ] Capacity planning
- [ ] Disaster recovery testing

---

## Documentation Deliverables

### Required Documentation
- [ ] Architecture diagram
- [ ] API documentation updates
- [ ] Operational runbooks
- [ ] Troubleshooting guide
- [ ] Performance benchmarks
- [ ] Cost analysis report
- [ ] Security assessment
- [ ] Disaster recovery plan

---

## Team Training

### Knowledge Transfer
- [ ] Architecture overview session
- [ ] Fargate operations training
- [ ] Lambda debugging workshop
- [ ] Redis management basics
- [ ] Monitoring and alerting guide
- [ ] Incident response procedures

---

This checklist ensures a systematic approach to migrating Liap Tui to a hybrid architecture while maintaining game performance and reliability.