# AWS Deployment Journey: From Setup to Production Bug Fixes

## Table of Contents
1. [Overview](#overview)
2. [Initial AWS Setup](#initial-aws-setup)
3. [First Deployment Issues](#first-deployment-issues)
4. [WebSocket URL Hardcoding Bug](#websocket-url-hardcoding-bug)
5. [Connection Stability Bug](#connection-stability-bug)
6. [Key Learnings](#key-learnings)
7. [Best Practices Discovered](#best-practices-discovered)

## Overview

This document chronicles the complete journey of deploying a real-time multiplayer game (Liap Tui) to AWS, including all the challenges encountered and solutions implemented. The application uses:
- **Frontend**: React 19.1.0 with ESBuild bundler
- **Backend**: Python FastAPI with WebSocket support
- **Infrastructure**: AWS ECS Fargate with Application Load Balancer
- **Container**: Single Docker container serving both frontend and backend

## Initial AWS Setup

### Infrastructure Components Created

1. **ECR Repository**
   ```bash
   aws ecr create-repository --repository-name liap-tui --region us-east-1
   ```

2. **ECS Cluster**
   ```bash
   aws ecs create-cluster --cluster-name liap-tui-cluster --region us-east-1
   ```

3. **Application Load Balancer**
   - Created ALB with health checks on `/api/health`
   - Configured for WebSocket support (sticky sessions)
   - Public-facing with HTTP listener on port 80

4. **ECS Service**
   - Fargate launch type
   - Single task running
   - Connected to ALB target group

### Initial Deployment Process

1. Built production Docker image using multi-stage build
2. Pushed to ECR
3. Created ECS task definition
4. Deployed service with ALB integration

## First Deployment Issues

### Issue 1: 502 Bad Gateway Errors

**Symptom**: ALB returned 502 errors when accessing the application

**Root Cause**: Health check configuration mismatch
- ALB expected health check at `/health`
- Application served it at `/api/health`

**Solution**: Updated target group health check path to `/api/health`

### Issue 2: Static Files Not Loading

**Symptom**: Frontend assets returned 404 errors

**Root Cause**: FastAPI static file mounting issue
- Static files were built into `/app/backend/static/`
- But the path wasn't properly configured in production

**Solution**: Already properly configured in `main.py`:
```python
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
```

## WebSocket URL Hardcoding Bug

### The Problem

**Symptom**: WebSocket connections tried to connect to `ws://localhost:5050/ws` in production

**Discovery Process**:
1. Used Playwright to inspect the deployed application
2. Found hardcoded localhost URL in bundle.js
3. Traced back to `frontend/src/constants.ts`

### Root Cause Analysis

The WebSocket URL was defined as a getter in `constants.ts`:
```typescript
export const NETWORK = {
  get WEBSOCKET_BASE_URL(): string {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      return `${protocol}//${host}/ws`;
    }
    return 'ws://localhost:5050/ws';
  },
}
```

**The Issue**: ESBuild's minification process evaluated the getter at build time:
- Build environment (Node.js) has no `window` object
- Getter returned the fallback `'ws://localhost:5050/ws'`
- ESBuild optimized this to a constant value

### The Solution

Converted the getter to a regular function to prevent build-time evaluation:
```typescript
export const NETWORK = {
  WEBSOCKET_BASE_URL: function(): string {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      return `${protocol}//${host}/ws`;
    }
    return 'ws://localhost:5050/ws';
  },
}
```

And updated the NetworkService to call it as a function:
```typescript
const baseUrl = NETWORK.WEBSOCKET_BASE_URL();
```

## Connection Stability Bug

### The Problem

**Symptom**: "Create Room" button stuck on "Creating..." in production

**Discovery Process**:
1. Observed WebSocket connect/disconnect loops in browser console
2. Messages being queued instead of sent
3. Only happened on AWS, not local Docker

### Root Cause Analysis

The issue was in `LobbyPage.jsx`'s useEffect dependencies:
```javascript
useEffect(() => {
  // WebSocket connection and event listener setup
  // ...
}, [isConnected, isCreatingRoom, app, navigate, isJoiningRoom]);
```

**The Problem Flow**:
1. User clicks "Create Room" → `setIsCreatingRoom(true)`
2. State change triggers useEffect to re-run
3. Cleanup function disconnects WebSocket
4. Setup function reconnects WebSocket
5. `create_room` message queued during reconnection
6. Room creation never completes

### Why It Only Happened on AWS

**Local Docker Environment**:
- Near-zero latency (localhost)
- WebSocket reconnection happens instantly
- Message gets through before disconnect completes

**AWS Environment**:
- Network latency (Client → ALB → ECS)
- Reconnection takes longer
- Timing window allows message to be queued
- Classic "Heisenbug" - timing-dependent issue

### The Solution

Restructured the React hooks to prevent reconnection on state changes:

1. **Separated connection from event listeners**:
```javascript
// Connection effect - runs once
useEffect(() => {
  const initializeLobby = async () => {
    await networkService.connectToRoom('lobby');
    setIsConnected(true);
  };
  initializeLobby();
  return () => networkService.disconnectFromRoom('lobby');
}, []);

// Event listeners effect - runs when connection changes
useEffect(() => {
  // Setup all event listeners
  // ...
  return () => unsubscribers.forEach(unsub => unsub());
}, [isConnected]);
```

2. **Removed component state from event handlers** to avoid stale closures

## Key Learnings

### 1. Build-Time vs Runtime Evaluation
- Modern bundlers (ESBuild, Webpack) aggressively optimize code
- Getters can be evaluated at build time if deemed "pure"
- Use functions instead of getters for runtime-dependent values

### 2. Environment Differences Matter
- Timing issues may only manifest in production
- Network latency exposes race conditions
- Always test in production-like environments

### 3. React useEffect Dependencies
- Be extremely careful with dependency arrays
- State in dependencies can cause unwanted re-runs
- Separate concerns: connection vs event handling

### 4. WebSocket Connection Management
- Rapid connect/disconnect cycles cause issues
- Message queuing is essential for reliability
- Load balancers add complexity to WebSocket handling

### 5. Debugging Production Issues
- Browser DevTools are invaluable for production debugging
- Playwright/Puppeteer can automate investigation
- Check the actual bundle output, not just source code

### 6. ECS Task Definition Management
- Task definitions store specific image tags, not tag references
- Pushing `:latest` doesn't automatically update running services
- Must create new task definition revision with updated image tag
- Always verify which image tag the service is actually using

## Best Practices Discovered

### 1. WebSocket URL Configuration
```typescript
// ❌ Bad: Getter that can be optimized away
get WEBSOCKET_URL() { return window?.location ? dynamic : fallback; }

// ✅ Good: Function that must be called at runtime
WEBSOCKET_URL() { return window?.location ? dynamic : fallback; }
```

### 2. React WebSocket Integration
```javascript
// ❌ Bad: State in useEffect dependencies
useEffect(() => {
  // WebSocket setup
}, [isConnected, isCreating, otherState]);

// ✅ Good: Minimal dependencies
useEffect(() => {
  // Connection only
}, []);

useEffect(() => {
  // Event handlers
}, [isConnected]);
```

### 3. Docker Multi-Stage Builds
```dockerfile
# Frontend build stage
FROM node:18-alpine as frontend-builder
# Build frontend with production optimizations

# Backend stage  
FROM python:3.11-slim
# Copy built frontend from previous stage
COPY --from=frontend-builder /app/bundle.* ./backend/static/
```

### 4. AWS Deployment Commands
```bash
# Build and tag
docker build -t app:tag -f Dockerfile.prod .
docker tag app:tag $ECR_URI:tag

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker push $ECR_URI:tag

# Update ECS
aws ecs register-task-definition --cli-input-json file://task-def.json
aws ecs update-service --cluster cluster-name --service service-name --task-definition task:revision
```

### 6. ECS Task Definition Tag Management

**Issue Discovered**: ECS task definitions can be configured with specific image tags instead of `latest`, causing deployments to use outdated images.

**Symptom**: After pushing new image with `latest` tag, the application still runs old version.

**Solution**: Update task definition to use the correct tag:
```bash
# Check current task definition
aws ecs describe-services --cluster cluster-name --service service-name --query 'services[0].taskDefinition'

# Get image being used
aws ecs describe-task-definition --task-definition task:revision --query 'taskDefinition.containerDefinitions[0].image'

# Create new task definition with updated image
aws ecs describe-task-definition --task-definition task:revision | \
  jq '.taskDefinition | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy) | .containerDefinitions[0].image = "ECR_URI:latest"' > new-task-def.json

# Register new task definition
aws ecs register-task-definition --cli-input-json file://new-task-def.json

# Update service with new task definition
aws ecs update-service --cluster cluster-name --service service-name --task-definition task:new-revision --force-new-deployment
```

### 5. Health Check Configuration
- Always verify health check paths match your application
- Use proper health check intervals (30s is reasonable)
- Implement comprehensive health endpoints

## Conclusion

This deployment journey highlighted several critical aspects of modern web application deployment:

1. **Build tools can introduce subtle bugs** through optimization
2. **Timing-dependent bugs** may only appear in production
3. **React hooks require careful design** for WebSocket integration
4. **AWS infrastructure adds complexity** but provides scalability
5. **Thorough testing in production-like environments** is essential

The combination of these issues created a perfect storm that only manifested in the AWS environment, teaching valuable lessons about full-stack deployment challenges and solutions.