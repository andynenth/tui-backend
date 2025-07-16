# Docker Development Guide

## Overview

This guide explains how Docker is used in the Liap Tui project and helps you choose the right approach for your development needs.

### Key Concepts
- **Single Container Architecture**: One FastAPI process serves both API and frontend
- **Pre-built Frontend**: Frontend must be built to `backend/static/` before Docker build
- **Multiple Workflows**: Different approaches for different development scenarios

## Quick Start - Which Approach Should I Use?

```
┌─────────────────────────────────┐
│  What are you trying to do?     │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼───┐        ┌───▼───┐
│Testing│        │Active │
│Prod?  │        │Dev?   │
└───┬───┘        └───┬───┘
    │                │
    ▼                ▼
Use Simple      Check Below
Docker
```

### Quick Commands by Scenario

| Scenario | Commands |
|----------|----------|
| **Quick Test Everything** | `./start.sh` |
| **Test Production Build** | `cd frontend && npm run build:docker`<br>`docker build -t liap-tui .`<br>`docker run -p 5050:5050 liap-tui` |
| **Backend Development** | `cd frontend && npm run build`<br>`docker-compose -f docker-compose.dev.yml up` |
| **Full Hot Reload** | `./start.sh` |
| **Frontend Only** | Terminal 1: `docker-compose up backend`<br>Terminal 2: `cd frontend && npm run dev` |

## Detailed Workflows

### Workflow A: Simple Docker (Production-like)

**When to use**: Testing production builds, demonstrations, EC2 deployment, or when you don't need hot reload

```bash
# Step 1: Build frontend assets with CSS processing (matches ./start.sh rendering)
cd frontend && npm run build:docker

# Step 2: Build Docker image
docker build -t liap-tui .

# Step 3: Run container
docker run -p 5050:5050 liap-tui

# To stop: Press Ctrl+C
```

**Important**: Use `npm run build:docker` to ensure:
- Tailwind CSS is processed correctly (content centered, not top-left)
- Same minification as `./start.sh`
- Identical rendering between development and production

**What happens**:
1. Frontend compiles to `backend/static/` (bundle.js, bundle.css)
2. The build script also copies index.html to `backend/static/`
3. Docker copies everything including the built frontend
4. FastAPI serves both API and static files on port 5050

### Workflow B: Docker Compose (Backend Development)

**When to use**: Developing backend features with hot reload

```bash
# First time setup
cd frontend && npm run build
docker-compose -f docker-compose.dev.yml build

# Start development
docker-compose -f docker-compose.dev.yml up

# To stop: Press Ctrl+C or run:
docker-compose -f docker-compose.dev.yml down
```

**Features**:
- Backend hot reload (file changes auto-restart)
- Volume mounting for backend code
- Environment variables from `.env`
- No frontend hot reload

### Workflow C: Full Hot Reload (Recommended for Active Development)

**When to use**: Developing both frontend and backend features

```bash
# Just run the start script
./start.sh

# This starts:
# - Backend with uvicorn hot reload
# - Frontend with esbuild watch mode
# - Automatic file syncing

# To stop: Press Ctrl+C
```

**Features**:
- Both frontend and backend hot reload
- Instant feedback on changes
- Best developer experience

### Workflow D: Frontend-Only Development

**When to use**: Working exclusively on UI/React components

```bash
# Terminal 1: Start backend
docker-compose -f docker-compose.dev.yml up backend

# Terminal 2: Start frontend dev server
cd frontend && npm run dev

# Frontend runs on http://localhost:3050
# API calls proxy to backend on :5050
```

## Understanding the Build Process

### Frontend Build Flow

```
frontend/main.js
       │
       ▼ (npm run build)
   esbuild bundles
       │
       ▼
backend/static/
├── bundle.js      # All JavaScript
├── bundle.css     # All styles  
├── index.html     # Entry point
└── *.map          # Source maps
       │
       ▼ (docker build)
   Copied into image
       │
       ▼ (docker run)
   FastAPI serves files
```

### Why Frontend Must Be Built First

The Dockerfile contains:
```dockerfile
COPY backend/ ./backend
```

This copies whatever is in `backend/static/` at build time. If empty, your Docker image has no frontend!

## Docker Commands Reference

### Building Images

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `docker build -t liap-tui .` | Basic build | Standard builds |
| `docker build --no-cache -t liap-tui .` | Fresh build | Dependencies changed |
| `docker build --progress=plain -t liap-tui .` | Verbose output | Debugging builds |
| `docker-compose build` | Build compose services | First time setup |
| `docker-compose build --no-cache` | Fresh compose build | After major changes |

### Running Containers

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `docker run -p 5050:5050 liap-tui` | Run in foreground | Testing/debugging |
| `docker run -d -p 5050:5050 liap-tui` | Run in background | Long-running tests |
| `docker run --rm -p 5050:5050 liap-tui` | Auto-remove after stop | Clean testing |
| `docker-compose up` | Start all services | Development |
| `docker-compose up --build` | Rebuild and start | After code changes |

### Managing Containers

| Command | Purpose |
|---------|---------|
| `docker ps` | List running containers |
| `docker ps -a` | List all containers |
| `docker stop <container-id>` | Gracefully stop container |
| `docker rm <container-id>` | Remove stopped container |
| `docker-compose down` | Stop and remove compose containers |
| `docker-compose down -v` | Also remove volumes |

### Cleanup Commands

| Command | Purpose | Reclaims |
|---------|---------|----------|
| `docker container prune` | Remove stopped containers | Variable |
| `docker image prune` | Remove dangling images | Often GBs |
| `docker system prune` | Remove all unused data | Most space |
| `docker builder prune` | Clear build cache | Build layers |

## Common Issues and Solutions

### Issue: "Module not found" errors
**Solution**: Rebuild frontend before Docker build
```bash
cd frontend && npm run build
docker build -t liap-tui .
```

### Issue: Port 5050 already in use
**Solution**: Find and stop the process
```bash
# Find process using port
lsof -i :5050

# Or just use a different port
docker run -p 8080:5050 liap-tui
```

### Issue: Changes not reflected in Docker
**Solution**: Rebuild with no cache
```bash
docker build --no-cache -t liap-tui .
```

### Issue: Docker using too much disk space
**Solution**: Clean up unused resources
```bash
docker system prune -a
docker builder prune
```

### Issue: Frontend files missing in Docker
**Solution**: Check if frontend was built
```bash
ls backend/static/
# Should show: bundle.js, bundle.css, index.html

# If empty, build frontend:
cd frontend && npm run build
```

## Best Practices

### 1. Development vs Production

**Development**:
- Use docker-compose for easy environment management
- Enable hot reload for faster iteration
- Mount volumes for code changes

**Production**:
- Use simple docker with pre-built frontend
- No volume mounts (everything in image)
- Use specific version tags

### 2. When to Rebuild

**Rebuild Docker image when**:
- Python dependencies change (requirements.txt)
- Dockerfile is modified
- System packages are added

**Rebuild frontend when**:
- JavaScript/React code changes (for Docker deployment)
- CSS changes
- Static assets updated

### 3. Managing Resources

```bash
# Regular cleanup (safe)
docker system prune

# Check disk usage
docker system df

# Remove old images
docker images | grep liap-tui
docker rmi <old-image-id>
```

### 4. Environment Variables

Always use `.env` file for configuration:
```bash
# Check current settings
cat .env

# Key variables:
API_PORT=5050
API_HOST=0.0.0.0
DEBUG=True
```

## Architecture Notes

### How FastAPI Serves Everything

In `backend/api/main.py`:
```python
# Serves static files from backend/static/
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
```

This means:
- `/` → serves `index.html`
- `/bundle.js` → serves JavaScript
- `/api/*` → handles API routes
- `/ws/*` → handles WebSocket

### File Structure
```
liap-tui/
├── frontend/           # React source code
│   └── (builds to) →  
├── backend/
│   ├── static/        # Built frontend files
│   │   ├── bundle.js
│   │   ├── bundle.css
│   │   └── index.html
│   └── api/           # FastAPI application
└── Dockerfile         # Copies everything
```

## EC2 Deployment

To ensure EC2 renders exactly like `./start.sh`:

```bash
# 1. Build with CSS processing and minification (IMPORTANT!)
cd frontend && npm run build:docker

# 2. Build Docker image
docker build -t liap-tui .

# 3. Tag for your registry (example)
docker tag liap-tui:latest your-registry/liap-tui:latest

# 4. Push to registry
docker push your-registry/liap-tui:latest
```

**Why `build:docker`?**
- Uses the same CSS processing as `./start.sh` (Tailwind works properly)
- Includes minification (698KB bundle)
- Ensures content is centered, not stuck in top-left corner
- Identical rendering between local development and EC2

## Summary

1. **Frontend must be built** before Docker build (`npm run build:docker` for production)
2. **Choose the right workflow** for your task
3. **Use ./start.sh** for the best development experience
4. **Use build:docker** for EC2/Docker to match local rendering
5. **Clean up regularly** to save disk space
6. **One container serves everything** - no nginx needed!

For more help, see:
- [Developer Onboarding Guide](./DEVELOPER_ONBOARDING_GUIDE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING_AND_DEBUGGING_GUIDE.md)
- [Technical Architecture](./TECHNICAL_ARCHITECTURE_DEEP_DIVE.md)