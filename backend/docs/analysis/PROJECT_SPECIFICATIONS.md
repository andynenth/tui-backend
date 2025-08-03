# 🎮 Liap Tui - Complete Project Specifications

## 📋 Executive Summary

**Liap Tui** is a real-time multiplayer online board game inspired by a traditional Chinese-Thai game. It's a turn-based strategy game for exactly 4 players, built with modern web technologies and enterprise-grade architecture.

---

## 🎯 Game Specifications

### Core Gameplay
- **Players**: Exactly 4 players per game (human or AI)
- **Pieces**: 32 total pieces (8 per player per round)
- **Objective**: First to reach 50 points wins
- **Duration**: Multiple rounds until winner emerges

### Game Pieces
- **Total**: 32 unique pieces
- **Types**: GENERAL, ELEPHANT, HORSE, CHARIOT, CANNON, SOLDIER
- **Colors**: RED and BLACK
- **Points**: Range from 1 (SOLDIER_BLACK) to 14 (GENERAL_RED)

### Game Phases (Per Round)
1. **PREPARATION**: Deal cards, check for weak hands, handle redeals
2. **DECLARATION**: Players declare target pile counts (0-8)
3. **TURN**: Players play pieces in sets, winner takes all
4. **SCORING**: Calculate scores based on actual vs declared piles

### Special Rules
- **Weak Hand**: No piece > 9 points triggers redeal option
- **Redeal Multiplier**: 2x, 3x, 4x... for successive redeals
- **Declaration Constraint**: Total declarations ≠ 8
- **Zero Declaration**: Can't declare 0 for 3 consecutive rounds

### Valid Play Types
- SINGLE (1 piece)
- PAIR (2 identical)
- THREE_OF_A_KIND (3 soldiers)
- STRAIGHT (3 sequential)
- FOUR_OF_A_KIND (4 soldiers)
- EXTENDED_STRAIGHT (4-5 pieces)
- FIVE_OF_A_KIND (5 soldiers)
- DOUBLE_STRAIGHT (6 pieces)

### Scoring System
| Scenario | Points |
|----------|---------|
| Declared 0, captured 0 | +3 |
| Declared 0, captured X | -X |
| Declared X, captured X | X+5 |
| Declared X, captured Y | -\|X-Y\| |

---

## 🏗️ Technical Architecture

### System Design
- **Architecture Pattern**: WebSocket-first, Event-driven
- **Communication**: Real-time bidirectional WebSocket
- **State Management**: Enterprise State Machine with Event Sourcing
- **Deployment**: Single Docker container
- **Scalability**: Horizontal scaling ready with room-based isolation

### Technology Stack

#### Backend (Python)
- **Framework**: FastAPI 0.115.12
- **Server**: Uvicorn 0.34.2 with async support
- **WebSocket**: websockets 15.0.1
- **Python Version**: 3.10+ (3.11 recommended)
- **Key Libraries**:
  - aiohttp 3.11.11 (async HTTP)
  - psutil 5.9.8 (system monitoring)
  - python-dotenv 1.1.0 (environment config)
  - PyYAML 6.0.2 (configuration)

#### Frontend (JavaScript/TypeScript)
- **Framework**: React 19.1.0
- **Router**: React Router DOM 7.6.2
- **Bundler**: ESBuild 0.25.5
- **UI Library**: Custom components + Tailwind CSS 4.1.10
- **Testing**: Jest 29.7.0 + React Testing Library 16.3.0
- **Linting**: ESLint 8.57.0 + Prettier 3.6.2
- **Type Checking**: TypeScript 5.3.3

#### Infrastructure
- **Container**: Docker with multi-stage build
- **Database**: SQLite (event store) - game_events.db
- **Monitoring**: Prometheus metrics endpoint
- **Health Checks**: Multiple health endpoints
- **Logging**: Structured JSON with correlation IDs

---

## 📡 API Specifications

### WebSocket Protocol
**Primary Endpoint**: `/ws/{room_id}` or `/ws/lobby`

#### Lobby Events (22 total)
- `request_room_list` → `room_list_update`
- `create_room` → `room_created`
- `join_room` → `room_joined`
- `ping` → `pong`

#### Room Management Events
- `client_ready` → `room_state_update`
- `add_bot` → `room_update`
- `remove_player` → `room_update`
- `leave_room` → `player_left`

#### Game Events
- `start_game` → `game_started`
- `declare` → `declaration_made`
- `play` → `play_made`
- `request_redeal` → `redeal_requested`
- `accept_redeal` → `redeal_accepted`
- `decline_redeal` → `redeal_declined`

### REST API (Debug/Health Only)
- **NO game operations via REST** - all game actions use WebSocket
- `/api/health` - Basic health check
- `/api/health/detailed` - Detailed system status
- `/api/health/metrics` - Prometheus metrics
- `/api/debug/*` - Debug endpoints (dev only)

---

## 🚀 Enterprise Features

### Reliability
- **Message Queue**: Guaranteed delivery with acknowledgments
- **Reconnection**: Automatic client reconnection with state recovery
- **Event Sourcing**: Complete game history for replay/recovery
- **Error Boundaries**: Graceful error handling in UI

### Performance
- **Async Architecture**: Non-blocking I/O throughout
- **Connection Pooling**: Efficient resource management
- **State Caching**: In-memory game state cache
- **Optimized Bundling**: ESBuild for fast builds

### Monitoring & Operations
- **Health Monitoring**: CPU, memory, connection tracking
- **Structured Logging**: JSON logs with correlation IDs
- **Metrics Export**: Prometheus-compatible metrics
- **Debug Tools**: Event replay, state inspection

### Security
- **Input Validation**: Schema validation on all inputs
- **Rate Limiting**: Connection and message rate limits
- **Room Isolation**: Games isolated by room ID
- **No Direct DB Access**: All through controlled interfaces

---

## 📦 Deployment Specifications

### Docker Configuration
```dockerfile
# Multi-stage build
FROM node:22-alpine (frontend build)
FROM python:3.11-slim (runtime)
EXPOSE 5050
```

### Resource Requirements
- **Memory**: 512MB minimum, 1GB recommended
- **CPU**: 1 core minimum, 2 cores recommended
- **Storage**: 100MB for application + logs
- **Network**: WebSocket support required

### Environment Variables
- `PORT`: Server port (default: 5050)
- `LOG_LEVEL`: Logging verbosity
- `MAX_ROOMS`: Maximum concurrent rooms
- `MAX_PLAYERS_PER_ROOM`: Player limit (default: 4)

---

## 📊 Project Statistics

### Codebase Size
- **Backend**: 50+ Python modules
- **Frontend**: 55+ React components
- **Tests**: 78+ test suites
- **Documentation**: 30+ markdown files

### Complexity Metrics
- **WebSocket Events**: 22 distinct types
- **Game States**: 4 major phases
- **Play Types**: 8 valid combinations
- **Error Types**: 15+ handled scenarios

### Quality Metrics
- **Test Coverage**: Target 80%+
- **Linting**: ESLint + Prettier enforced
- **Type Safety**: TypeScript for services
- **Code Review**: GitHub Actions CI/CD

---

## 🔄 Development Workflow

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

### Testing
```bash
# Backend tests
pytest tests/

# Frontend tests
npm test
npm run lint
npm run type-check
```

### Building
```bash
# Docker build
docker build -t liap-tui .

# Frontend production build
npm run build
```

---

## 📚 Key Design Decisions

1. **WebSocket-Only Game Operations**: Ensures real-time sync, no REST for gameplay
2. **State Machine Architecture**: Predictable state transitions, easier debugging
3. **Event Sourcing**: Complete audit trail, replay capability
4. **Single Container Deploy**: Simplified operations, reduced complexity
5. **React 19 + ESBuild**: Modern, fast development experience
6. **Enterprise Patterns**: Production-ready from day one

---

## 🎮 Game Flow Sequence

```
1. Player creates/joins room (lobby)
2. Host adds bots or waits for players
3. Host starts game → PREPARATION phase
4. Cards dealt, weak hands checked
5. Players declare targets → DECLARATION phase
6. Players take turns playing pieces → TURN phase
7. Round scoring → SCORING phase
8. Check win condition (50 points)
9. Next round or game over
```

---

## 📈 Performance Targets

- **Latency**: < 100ms for local actions
- **Throughput**: 100+ concurrent games
- **Availability**: 99.9% uptime target
- **Recovery**: < 5s reconnection time
- **Scale**: 1000+ concurrent players

---

*Last Updated: August 2025*
*Version: 1.0.0*