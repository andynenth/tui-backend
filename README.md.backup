# 🀄 Liap Tui Online Board Game

[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async--ready-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1-61dafb?logo=react)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A real-time online multiplayer board game inspired by *Liap Tui*, a traditional Chinese-Thai game.  
> Built with **FastAPI** for the backend and **React 19 + ESBuild** for the frontend.  
> Uses **WebSocket-first architecture** for all game operations, packaged in a single Docker container.

## Table of Contents
- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Development](#-development-local-with-hot-reload)
- [Testing](#-testing)
- [Game Mechanics](#-game-mechanics)
- [API Architecture](#-api-architecture)
- [Documentation](#-comprehensive-documentation)
- [Contributing](#-contributing)
- [Architecture Evolution](#-architecture-evolution)
- [Troubleshooting](#-troubleshooting)
- [Support](#-support)
- [License](#-license)

---

## 🚀 Features

### Core Game Features
- 🎮 **Turn-based multiplayer gameplay** (up to 4 players)
- 📡 **Real-time updates** via WebSocket with automatic reconnection
- 🧠 **Intelligent AI bots** with strategic decision-making
- 🎯 **Complete game flow** with all 4 phases: Preparation, Declaration, Turn, Scoring
- 🔄 **Simultaneous weak hand redeal system** with dynamic starter determination
- 🏆 **Advanced scoring system** with multipliers and win conditions

### Enterprise Architecture (Phase 1-4 Enhancements)
- ⚡ **State Machine Architecture** - Robust game state management with action queues
- 🔐 **Event Sourcing System** - Complete game history with replay capabilities
- 📨 **Reliable Message Delivery** - Guaranteed message delivery with acknowledgments
- 🏥 **Health Monitoring** - Real-time system resource and performance monitoring
- 🔧 **Automatic Recovery** - Self-healing procedures for common failure scenarios
- 📊 **Centralized Logging** - Structured JSON logging with correlation IDs

### Frontend Modernization
- ⚛️ **React 19** with modern hooks and component architecture
- 🔌 **Smart WebSocket Management** - Connection monitoring and auto-reconnection
- 🎨 **Pure UI Components** - Separation of concerns with container/presentation pattern
- 🚀 **TypeScript Services** - Type-safe game state management and network handling
- 📱 **Responsive Design** - Mobile-friendly interface with error boundaries

### Production Ready
- 🐳 **Single-container Docker deployment**
- 📈 **Prometheus metrics** endpoint for monitoring
- 🔍 **Health check endpoints** for load balancers
- 🔄 **Client recovery** from network interruptions
- 📋 **Comprehensive testing** with 78+ test suites

---

## 💻 System Requirements

- **Python** 3.11 or higher
- **Node.js** 16 or higher
- **Docker** (optional, for containerized deployment)
- **Git** for version control

### Minimum Hardware
- 2GB RAM
- 1 CPU core
- 1GB free disk space

---

## 📦 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/andynenth/tui-backend.git
cd liap-tui
```

### 2. Build the Docker image

```bash
docker build -t liap-tui .
```

### 3. Run the container

```bash
docker run -p 5050:5050 liap-tui
```

Then open your browser:  
👉 `http://localhost:5050`

> The frontend is served from FastAPI’s static files.  
> WebSocket and API routes are available under `/ws/` and `/api`.

---

## 📁 Project Structure

```
liap-tui/
├── frontend/                    → React 19 + TypeScript frontend
│   ├── src/
│   │   ├── components/         → Pure UI components
│   │   ├── contexts/           → React contexts (Game, App)
│   │   ├── hooks/              → Custom React hooks
│   │   ├── pages/              → Page components
│   │   ├── services/           → TypeScript services
│   │   └── styles/             → CSS and styling
│   └── network/                → WebSocket management
│
├── backend/                     → FastAPI + Python backend
│   ├── api/                    → API endpoints
│   ├── engine/                 → Core game engine
│   │   └── state_machine/      → State management
│   └── tests/                  → Test suite (78+ tests)
│
├── docs/                       → Comprehensive documentation (27 docs)
│   ├── 01-overview/           → Architecture overview
│   ├── 02-flow-traces/        → Application flows
│   ├── 03-*-deep-dives/       → Component details
│   ├── 04-data-structures/    → Data formats
│   ├── 05-patterns-practices/ → Best practices
│   └── 06-tutorials/          → Step-by-step guides
│
├── Dockerfile                  → Production container
├── docker-compose.dev.yml      → Development setup
├── requirements.txt            → Python dependencies
├── .env.example               → Configuration template
└── start.sh                   → Quick start script
```

---

## ⚙️ Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and adjust as needed:

### Core Settings
- `API_HOST` - Backend host (default: 0.0.0.0)
- `API_PORT` - Backend port (default: 5050)
- `DEBUG` - Debug mode (default: true)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING)

### Game Settings
- `MAX_SCORE` - Winning score (default: 50)
- `MAX_ROUNDS` - Maximum rounds (default: 20)
- `BOT_ENABLED` - Enable AI bots (default: true)

### Rate Limiting
- `RATE_LIMIT_ENABLED` - Enable rate limiting (default: true)
- `RATE_LIMIT_GLOBAL_RPM` - Global requests per minute (default: 100)
- Various endpoint-specific limits (see `.env.example`)

For complete configuration options, see [`.env.example`](.env.example).

---

## 🏗️ API Architecture

This project uses a **WebSocket-first architecture**:

- **WebSocket (`/ws/`)**: All game operations including room management, game actions, and real-time updates
- **REST API (`/api/`)**: Limited to health checks, monitoring, and administrative functions

### Why WebSocket-Only for Game Operations?
- **Real-time Updates**: Instant state synchronization across all clients
- **Bidirectional Communication**: Server can push updates without polling
- **Simplified Architecture**: Single communication channel for all game logic
- **Better Performance**: Persistent connections reduce overhead

For detailed WebSocket API documentation, see [docs/WEBSOCKET_API.md](docs/WEBSOCKET_API.md).

---

## 🧪 Testing

The project includes comprehensive testing across all components:

### Backend Tests (78+ test suites)
```bash
# Run all backend tests
cd backend && source venv/bin/activate
python -m pytest tests/ -v

# Test specific components
python test_full_game_flow.py          # Complete game integration
python test_reliable_messaging.py      # Message delivery system
python test_error_recovery.py          # Health monitoring & recovery
python test_event_sourcing.py          # Event store system

# Quick state machine validation
python run_tests.py
```

### Frontend Tests
```bash
cd frontend
npm test                    # Run all frontend tests
npm run type-check         # TypeScript validation
npm run lint               # Code quality checks
```

### Quality Assurance
```bash
# Python (run in venv)
cd backend && source venv/bin/activate
black .                    # Code formatting
pylint engine/ api/ tests/ # Code analysis

# Frontend
cd frontend
npm run lint:fix           # Auto-fix linting issues
```

---

## ⚙️ Development (Local with Hot Reload)

### Option 1: With `./start.sh`

```bash
./start.sh
```

This launches:
- `uvicorn` backend server with hot reload
- `esbuild` frontend watch mode
- Auto-copies `index.html` into `static/`

---

### Option 2: Manually (Local Dev)

#### Backend (Docker)

```bash
docker-compose -f docker-compose.dev.yml up backend
```

#### Frontend Development (Live Build)

```bash
npm run dev
```

> This ensures backend runs in Docker, while frontend is live-rebuilt by host.

---

## 🚢 Deployment Options

### Option 1: AWS EC2 with Docker Compose (Recommended for Free Tier)

Perfect for AWS Free Tier users who want simple deployment with database persistence.

**Features:**
- ✅ Database persistence with Docker volumes
- ✅ Automated daily backups
- ✅ Health monitoring and auto-recovery
- ✅ Simple deployment with one command
- ✅ Free tier friendly (t2.micro + 30GB storage)

**Quick Deploy:**
```bash
# 1. Update deployment script with your EC2 details
# Edit deploy-ec2.sh: EC2_HOST and KEY_PATH

# 2. Deploy to EC2
./deploy-ec2.sh

# 3. Access your game
http://your-ec2-ip
```

**Full Guide:** See [EC2_DEPLOYMENT_GUIDE.md](EC2_DEPLOYMENT_GUIDE.md)

### Option 2: AWS ECS (Original Method)

For users who need auto-scaling and managed container orchestration.

```bash
# Deploy to ECS
./deploy-to-aws.sh
```

**Note:** ECS may incur costs beyond free tier (ALB, data transfer, etc.)

### Option 3: Local Docker

For testing or private network deployment.

```bash
# Production build
docker build -t liap-tui -f Dockerfile.prod .
docker run -p 80:5050 liap-tui

# With persistence
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🎯 Game Mechanics

Liap Tui is a strategic 4-player board game with unique piece-playing and scoring mechanics.

### Quick Overview
- **Players**: 4 (human or AI bots)
- **Pieces**: 8 pieces per player per round
- **Game Flow**: 4 phases - Preparation → Declaration → Turn → Scoring
- **Winning**: First to 50 points or highest after 20 rounds

### Key Features
- **Declaration Phase**: Players declare how many piles they'll win (must total ≠ 8)
- **Turn-Based Play**: Play 1-6 pieces per turn, winner takes all pieces
- **Redeal System**: Players with weak hands can request new pieces
- **Scoring**: Points based on declaration accuracy with multipliers

> **📖 Complete Rules**: See [RULES.md](RULES.md) for detailed game mechanics, piece types, scoring system, and strategic tips.

---

## 📚 Comprehensive Documentation

The project includes extensive teaching materials organized into 7 categories:

#### 1. **Overview Documents** (3 docs)
- Project architecture and system design
- Technology stack decisions and rationale
- Core design principles and patterns

#### 2. **Flow Traces** (4 docs)
- Application startup sequence
- Complete user journey from login to game end
- WebSocket message patterns and lifecycle
- Game state machine transitions

#### 3. **Component Deep Dives** (8 docs)
- **Backend**: State machine, room manager, game engine, WebSocket handler
- **Frontend**: React architecture, context system, network service, UI flow

#### 4. **Data Structures** (4 docs)
- Message format specifications
- Game state shapes at each phase
- Database schema design (future)
- API contracts and type definitions

#### 5. **Patterns & Practices** (4 docs)
- Enterprise architecture implementation
- Error handling and recovery strategies
- Comprehensive testing approach
- AWS ECS deployment patterns

#### 6. **Tutorials** (4 docs)
- Local development setup guide
- Step-by-step feature addition tutorial
- Debugging guide with common issues
- Production deployment walkthrough

> **📖 All Documentation**: See [`/docs`](docs/) for complete teaching materials (27 documents total).

---

## 🤝 Contributing

We welcome contributions to Liap Tui! Here's how you can help:

### Getting Started
1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/tui-backend.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Make your changes
5. Run tests and quality checks (see below)
6. Commit with clear messages: `git commit -m "Add amazing feature"`
7. Push to your fork: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Development Guidelines
- Follow existing code style and patterns
- Add tests for new features
- Update documentation as needed
- Keep commits focused and atomic

### Quality Checks Before Submitting

**Python (Backend)**:
```bash
# Activate virtual environment
source venv/bin/activate

# Format code
cd backend && black .

# Run linting
pylint engine/ api/ tests/

# Run tests
python -m pytest tests/ -v
```

**JavaScript (Frontend)**:
```bash
cd frontend

# Type checking
npm run type-check

# Linting
npm run lint

# Fix linting issues
npm run lint:fix
```

### Areas for Contribution
- 🐛 Bug fixes and issue resolution
- ✨ New features and enhancements
- 📝 Documentation improvements
- 🧪 Test coverage expansion
- 🎨 UI/UX improvements
- 🌐 Internationalization

For detailed contribution guidelines, see [docs/CONTRIBUTING_GUIDE.md](docs/CONTRIBUTING_GUIDE.md).

---

## 🏗️ Architecture Evolution

This project evolved through 4 major development phases:

### Phase 1: Foundation
- ✅ State machine architecture implementation
- ✅ Complete game flow with all phases (Preparation, Declaration, Turn, Scoring)
- ✅ Robust action queue system for sequential processing
- ✅ AI bot integration with state machine
- ✅ Comprehensive testing suite (78+ tests)

### Phase 2: Frontend Modernization
- ✅ Migration from PixiJS to React 19
- ✅ Clean separation with custom hooks (`useGameState`, `useGameActions`, `useConnectionStatus`)
- ✅ Pure UI components with container/presentation pattern
- ✅ TypeScript integration for type safety
- ✅ Modern component architecture with error boundaries

### Phase 3: System Integration
- ✅ Smart WebSocket management with auto-reconnection
- ✅ Message queuing and delivery tracking
- ✅ Client-side recovery from network interruptions
- ✅ Performance optimization and connection monitoring
- ✅ Seamless backend-frontend integration

### Phase 4: Enterprise Robustness
- ✅ Event sourcing system with complete game history
- ✅ Reliable message delivery with acknowledgments and retries
- ✅ Health monitoring with real-time system metrics
- ✅ Automatic recovery procedures for common failures
- ✅ Centralized structured logging with correlation IDs
- ✅ Production-ready monitoring and observability

### Key Architectural Principles
- **Single Responsibility**: Each component has a clear, focused purpose
- **Event-Driven**: Asynchronous communication with proper error handling
- **Testable**: Comprehensive test coverage across all layers
- **Observable**: Full logging and monitoring for production environments
- **Resilient**: Automatic recovery and graceful degradation
- **Scalable**: Modular design that supports future enhancements

---

## 🔧 Troubleshooting

### Common Issues

#### WebSocket Connection Failed
```
Error: WebSocket connection to 'ws://localhost:5050/ws/lobby' failed
```
**Solutions:**
- Ensure backend is running: `docker ps` or check `localhost:5050/api/health`
- Check firewall/proxy settings aren't blocking WebSocket
- Try different browser or incognito mode

#### Player Cannot Reconnect
**Symptoms:** "Room is full" error or name not recognized
**Solutions:**
- Use exact same player name (case-sensitive)
- Clear browser cache and localStorage
- Check if room still exists: `/api/debug/room-stats`

#### Frontend Build Errors
```
Error: Cannot find module 'react'
```
**Solution:** Install dependencies:
```bash
cd frontend && npm install
```

#### Python Import Errors
```
ImportError: No module named 'fastapi'
```
**Solution:** Activate virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### High Memory Usage
**Solutions:**
- Check for zombie rooms: `/api/system/stats`
- Restart container: `docker restart liap-tui`
- Enable event store pruning in production

#### Database Persistence Issues
**Symptoms:** Data lost after container restart
**Solutions:**
- Ensure using docker-compose with volumes (not plain docker run)
- Check volume mapping in docker-compose.yml
- Verify DATABASE_PATH environment variable is set
- For EC2: Check `/home/ubuntu/liap-tui-data/` permissions

#### Migration from ECS to EC2
**Resources:**
- [Migration Checklist](MIGRATION_CHECKLIST.md) - Step-by-step guide
- [EC2 Deployment Guide](EC2_DEPLOYMENT_GUIDE.md) - Complete EC2 setup
- Test persistence locally: `./test-persistence.sh`

### Getting Help

For more detailed troubleshooting:
- See [docs/troubleshooting.md](docs/troubleshooting.md) for comprehensive guide
- Check [OPERATIONS.md](OPERATIONS.md) for production issues
- Review logs: `docker logs liap-tui`

---

## 📞 Support

### Resources
- **Documentation**: [/docs](docs/) - Comprehensive guides and tutorials
- **Issues**: [GitHub Issues](https://github.com/andynenth/tui-backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/andynenth/tui-backend/discussions)

### Before Reporting Issues
1. Check existing issues for duplicates
2. Try troubleshooting steps above
3. Gather relevant information:
   - Browser console logs
   - Backend logs (`docker logs`)
   - Steps to reproduce
   - Environment details

### Security Issues
For security vulnerabilities, please email directly instead of creating public issues.

---

## 📄 License

MIT © [Andy Nenthong](https://github.com/andynenth/tui-backend).  
See [LICENSE](LICENSE) for details.