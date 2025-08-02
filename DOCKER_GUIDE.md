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

### 4. **docker-compose**
- A tool for defining multi-container applications
- Uses YAML files to configure services
- Makes it easy to manage complex setups

## Understanding Liap Tui's Docker Setup

### The Dockerfile
```dockerfile
FROM python:3.11-slim          # Start with Python 3.11
WORKDIR /app                   # Set working directory
COPY backend/ ./backend        # Copy backend code
COPY shared/ ./shared          # Copy shared code
COPY requirements.txt ./       # Copy dependencies list
RUN pip install -r requirements.txt  # Install dependencies
ENV PYTHONPATH=/app/backend    # Set Python path
EXPOSE 5050                    # Open port 5050
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "5050"]
```

### How It Works
1. **Backend runs in Docker**: The Python/FastAPI server runs inside the container
2. **Frontend is pre-built**: JavaScript is compiled into static files (bundle.js, bundle.css)
3. **FastAPI serves both**: The backend serves API endpoints AND the static frontend files
4. **Single container**: Everything runs in one container on port 5050

## Essential Docker Commands

### Building and Running

```bash
# Build the image (run this after code changes)
docker build -t liap-tui .

# Run the container
docker run -p 5050:5050 liap-tui

# Run with a custom name
docker run -p 5050:5050 --name my-game liap-tui

# Run in background (detached)
docker run -d -p 5050:5050 liap-tui
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
# For production build
docker build -t liap-tui .
docker run -p 5050:5050 liap-tui

# For development (with hot reload)
docker-compose -f docker-compose.dev.yml up
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
# Build production image
docker build -t liap-tui:v1.0 .

# Run production container
docker run -d \
  --name liap-tui-prod \
  --restart unless-stopped \
  -p 5050:5050 \
  liap-tui:v1.0
```

## Tips and Best Practices

1. **Always use `.dockerignore`** to exclude unnecessary files
2. **Tag your images** with versions: `liap-tui:v1.0`
3. **Use docker-compose** for development - it's easier
4. **Check logs first** when debugging issues
5. **Clean up regularly** to save disk space
6. **One process per container** - Docker philosophy

## Next Steps

1. Try building and running the container
2. Make a small code change and see it reflected
3. Practice viewing logs and debugging
4. Experiment with docker-compose commands

Remember: Docker ensures your app runs the same everywhere - from your laptop to production servers!