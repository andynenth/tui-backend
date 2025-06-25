# 🀄 Liap Tui Online Board Game

[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async--ready-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PixiJS](https://img.shields.io/badge/PixiJS-8.x-ff69b4?logo=pixiv)](https://pixijs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A real-time online multiplayer board game inspired by *Liap Tui*, a traditional Chinese-Thai game.  
> Built with **FastAPI** for the backend and **PixiJS + ESBuild** for the frontend.  
> Supports real-time interaction via **WebSocket**, and packaged in a single Docker container.

---

## 🚀 Features

### Core Game Features
- 🎮 **Turn-based multiplayer gameplay** (up to 4 players)
- 📡 **Real-time updates** via WebSocket with automatic reconnection
- 🧠 **Intelligent AI bots** with strategic decision-making
- 🎯 **Complete game flow** with all 4 phases: Preparation, Declaration, Turn, Scoring
- 🔄 **Weak hand redeal system** with player voting
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

## 📁 Project Structure

```
frontend/                    → React 19 + TypeScript frontend
├── src/
│   ├── components/         → Pure UI components (Button, Modal, GamePiece, etc.)
│   ├── contexts/           → React contexts (GameContext, AppContext)
│   ├── hooks/              → Custom hooks (useGameState, useGameActions, useConnectionStatus)
│   ├── pages/              → Page components (GamePage, LobbyPage, RoomPage)
│   ├── services/           → TypeScript services (GameService, NetworkService, RecoveryService)
│   └── styles/             → CSS and styling
├── network/                → WebSocket management and message queuing
└── game/                   → Legacy PixiJS game components

backend/                     → FastAPI + Python backend
├── api/
│   ├── routes/             → REST API and WebSocket endpoints
│   └── services/           → Enterprise services (logging, health monitoring, recovery)
├── engine/                 → Core game engine
│   ├── state_machine/      → Robust state management system
│   └── *.py                → Game logic, rules, scoring, AI
├── tests/                  → Comprehensive test suite (78+ tests)
└── *.py                    → Shared instances, socket management

Dockerfile                  → Multi-stage Docker build (Node + Python)
docker-compose.dev.yml      → Development environment setup
```

---

## 📦 Installation

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

## 📊 Production Monitoring

The application includes enterprise-grade monitoring and observability:

### Health Check Endpoints
```bash
# Basic health check (for load balancers)
curl http://localhost:5050/api/health

# Detailed health information
curl http://localhost:5050/api/health/detailed

# Prometheus-compatible metrics
curl http://localhost:5050/api/health/metrics
```

### System Statistics
```bash
# Complete system overview
curl http://localhost:5050/api/system/stats

# Recovery system status
curl http://localhost:5050/api/recovery/status

# Room and game statistics
curl http://localhost:5050/api/debug/room-stats
```

### Event Store & Recovery
```bash
# View game events for analysis
curl http://localhost:5050/api/rooms/{room_id}/events

# Get reconstructed game state
curl http://localhost:5050/api/rooms/{room_id}/state

# Event store statistics
curl http://localhost:5050/api/event-store/stats
```

### Logging
All system events are logged in structured JSON format with correlation IDs:
- Game events (phases, player actions, scoring)
- WebSocket activity (connections, message delivery)
- Performance metrics (operation timing, resource usage)
- Security events (authentication, suspicious activity)
- Error tracking with full context

---

## 🧠 Liap Tui – Game Rules

> [See `/docs`]  
Includes: Piece types, Turn flow, Declaration, Redeal logic, Scoring system, and more.

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

## 📄 License

MIT © [Andy Nenthong](https://github.com/andynenth/tui-backend).  
See [LICENSE](LICENSE) for details.