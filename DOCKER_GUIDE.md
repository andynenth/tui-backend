# Docker Guide for Liap Tui

## What is Docker?

Docker is a platform that packages your application and all its dependencies into a "container" - think of it as a lightweight, portable box that contains everything needed to run your app. This ensures your app runs the same way on any computer.

## Key Concepts

### 1. **Image**
- A blueprint for creating containers
- Like a recipe that describes what goes in the container
- Built from a Dockerfile
- Example: Your `liap-tui` image contains Python, FastAPI, and your game code

### 2. **Container**
- A running instance of an image
- Like a running application created from the blueprint
- Can start, stop, and delete containers without affecting the image

### 3. **Dockerfile**
- A text file with instructions to build an image
- Each line is a step in building your application environment
- **Two types**: `Dockerfile` (development) and `Dockerfile.prod` (production)

### 4. **docker-compose**
- A tool for defining multi-container applications
- Uses YAML files to configure services
- Makes it easy to manage complex setups

## Understanding Liap Tui's Docker Setup

### 🔧 Development vs Production Dockerfiles

**Why Two Dockerfiles?**
- **Dockerfile**: Optimized for development (fast builds, hot reload)
- **Dockerfile.prod**: Optimized for production (security, performance, size)

### The Development Dockerfile
```dockerfile
FROM python:3.11-slim          # Start with Python 3.11
WORKDIR /app                   # Set working directory
COPY backend/ ./backend        # Copy backend code
COPY shared/ ./shared          # Copy shared code
COPY requirements.txt ./       # Copy dependencies list
RUN pip install -r requirements.txt  # Install dependencies
ENV PYTHONPATH=/app            # Set Python path
EXPOSE 5050                    # Open port 5050
CMD ["uvicorn", "backend.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "5050"]
```

### The Production Dockerfile.prod
```dockerfile
# Frontend build stage
FROM node:18-alpine as frontend-builder
WORKDIR /app
RUN apk add --no-cache python3 make g++ libc6-compat
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Python production stage  
FROM python:3.11-slim
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend/ ./backend
COPY shared/ ./shared
COPY backend/shared_instances.py ./

# Copy built frontend files
COPY --from=frontend-builder /app/bundle.* ./backend/static/
COPY --from=frontend-builder /app/index.html ./backend/static/

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Health check for AWS
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5050/api/health || exit 1

ENV PYTHONPATH=/app
ENV DEBUG=false
EXPOSE 5050

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "5050", "--workers", "1"]
```

### 📊 Key Differences

| Feature | Development | Production |
|---------|-------------|------------|
| **Build Time** | Fast (~2 min) | Slower (~5-8 min) |
| **Image Size** | ~300MB | ~256MB |
| **Hot Reload** | ✅ `--reload` | ❌ Static |
| **Frontend** | Served separately | Built into container |
| **Security** | Root user | Non-root user |
| **Health Checks** | None | AWS-compatible |
| **Multi-stage** | Single stage | Multi-stage (optimized) |
| **Debug Mode** | Enabled | Disabled |

### How It Works
1. **Development**: Fast iteration with hot reload
2. **Production**: Optimized, secure, single container with frontend built-in
3. **CI/CD**: Automatically uses Dockerfile.prod for AWS deployment
4. **Single container**: Everything runs in one container on port 5050

## Essential Docker Commands

### Building and Running

```bash
# Development: Build and run (fast iteration)
docker build -t liap-tui:dev .
docker run -p 5050:5050 --name liap-dev liap-tui:dev

# Production: Build and run (optimized)
docker build -f Dockerfile.prod -t liap-tui:prod .
docker run -p 5050:5050 --name liap-prod liap-tui:prod

# Run with environment variables
docker run -p 5050:5050 -e DEBUG=false -e ALLOWED_ORIGINS="https://yourdomain.com" liap-tui:prod

# Run in background (detached)
docker run -d -p 5050:5050 --name liap-game liap-tui:prod
```

### Managing Containers

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop a container
docker stop <container-id or name>

# Start a stopped container
docker start <container-id or name>

# Remove a container
docker rm <container-id or name>

# View container logs
docker logs <container-id or name>

# Follow logs in real-time
docker logs -f <container-id or name>
```

### Managing Images

```bash
# List images
docker images

# Remove an image
docker rmi liap-tui

# Remove unused images
docker image prune
```

## Development with Docker Compose

### Using docker-compose.dev.yml

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Run in background
docker-compose -f docker-compose.dev.yml up -d

# Stop services
docker-compose -f docker-compose.dev.yml down

# Rebuild and start
docker-compose -f docker-compose.dev.yml up --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Key Features of Dev Setup
- **Hot reload**: Code changes are reflected immediately
- **Volume mounting**: Your local files are synced with the container
- **Environment variables**: Loaded from `.env` file

## Common Scenarios

### 1. Making Code Changes

```bash
# Development workflow (recommended)
./start.sh                              # Uses docker-compose with hot reload

# Manual development build
docker build -t liap-tui:dev .
docker run -p 5050:5050 liap-tui:dev

# Production build (for deployment testing)
docker build -f Dockerfile.prod -t liap-tui:prod .
docker run -p 5050:5050 -e DEBUG=false liap-tui:prod
```

### 2. Debugging Issues

```bash
# Check if container is running
docker ps

# View error logs
docker logs <container-name>

# Access container shell
docker exec -it <container-name> /bin/bash

# Inside container, you can:
ls -la                    # List files
python --version          # Check Python version
pip list                  # List installed packages
```

### 3. Clean Up

```bash
# Stop all containers
docker stop $(docker ps -q)

# Remove all stopped containers
docker container prune

# Remove all images
docker image prune -a

# Full cleanup (containers, images, networks, volumes)
docker system prune -a
```

## Port Mapping Explained

When you run:
```bash
docker run -p 5050:5050 liap-tui
```

- First `5050`: Port on your computer (host)
- Second `5050`: Port inside the container
- `-p 5050:5050` maps host:container ports

You can change the host port:
```bash
docker run -p 8080:5050 liap-tui  # Access on localhost:8080
```

## Environment Variables

### Using .env file
The `.env` file contains configuration:
```bash
API_PORT=5050
DEBUG=true
BOT_ENABLED=true
```

### Override at runtime
```bash
docker run -p 5050:5050 -e DEBUG=false liap-tui
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs <container-name>

# Common issues:
# - Port already in use
# - Missing dependencies
# - Syntax errors in code
```

### Can't access the app
```bash
# Verify container is running
docker ps

# Check port mapping
docker port <container-name>

# Test connectivity
curl http://localhost:5050/api/health
```

### Changes not reflected
```bash
# For production: rebuild image
docker build -t liap-tui .

# For development: ensure volumes are mounted
# Check docker-compose.dev.yml has:
volumes:
  - ./backend:/app/backend
```

## Quick Reference

### Daily Workflow
```bash
# Morning: Start development
cd liap-tui
docker-compose -f docker-compose.dev.yml up

# Make changes to code...
# Changes auto-reload in dev mode

# Evening: Stop development
docker-compose -f docker-compose.dev.yml down
```

### Deployment
```bash
# Build production image (with version tag)
docker build -f Dockerfile.prod -t liap-tui:v1.0 .

# Run production container
docker run -d \
  --name liap-tui-prod \
  --restart unless-stopped \
  -p 5050:5050 \
  -e DEBUG=false \
  -e ALLOWED_ORIGINS="https://yourdomain.com" \
  liap-tui:v1.0

# Test health endpoint
curl http://localhost:5050/api/health
```

## Tips and Best Practices

1. **Use the right Dockerfile** for the right purpose:
   - Development: `Dockerfile` (fast builds, hot reload)
   - Production: `Dockerfile.prod` (optimized, secure)
2. **Always use `.dockerignore`** to exclude unnecessary files
3. **Tag your images** with versions: `liap-tui:v1.0`
4. **Use docker-compose** for development - it's easier
5. **Test production builds locally** before deploying
6. **Check logs first** when debugging issues
7. **Clean up regularly** to save disk space
8. **Use environment variables** for configuration
9. **Non-root users** in production for security

## Next Steps

1. **Development**: Use `./start.sh` for daily development
2. **Test production build**: `docker build -f Dockerfile.prod -t liap-tui:prod .`
3. **Practice debugging**: View logs and inspect containers
4. **CI/CD**: Push to GitHub and watch automatic deployment
5. **AWS deployment**: Use production Docker image in ECS

## 🚀 CI/CD Integration

**Automatic Deployment**: 
- GitHub Actions uses `Dockerfile.prod` for AWS deployment
- You develop with `./start.sh`, CI/CD handles production builds
- No manual Docker commands needed for deployment!

**Your Workflow**:
```bash
./start.sh          # Development
git push            # Automatic production deployment
```

Remember: Docker ensures your app runs the same everywhere - from your laptop to AWS production!