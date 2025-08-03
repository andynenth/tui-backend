# CLAUDE.md - AI Assistant Guidelines

This file provides essential guidance to Claude Code (claude.ai/code) when working with the Liap Tui codebase.

## 📋 Project Overview

**Liap Tui** is a production-ready, real-time multiplayer board game inspired by traditional Chinese-Thai gameplay. Built with enterprise-grade architecture, WebSocket-first communication, and modern web technologies.

### Quick Stats
- **Scale**: 50+ Python modules, 55+ React components, 78+ test suites
- **Architecture**: WebSocket-only game operations, State Machine with Event Sourcing
- **Stack**: React 19.1.0 + FastAPI 0.115.12 + Docker
- **Documentation**: See `backend/docs/analysis/PROJECT_SPECIFICATIONS.md` for complete specs


## 🏗️ Key Architecture

### Backend Structure (`backend/`)
```
backend/
├── engine/                      # Core game logic
│   ├── state_machine/          # ✅ ENTERPRISE ARCHITECTURE
│   │   ├── game_state.py       # Base state with auto-broadcasting
│   │   ├── preparation_state.py
│   │   ├── declaration_state.py
│   │   ├── turn_state.py
│   │   └── scoring_state.py
│   ├── game.py                 # Main game controller
│   ├── rules.py                # Play validation
│   ├── scoring.py              # Score calculation
│   └── player.py, piece.py     # Core entities
├── api/
│   ├── routes/
│   │   └── ws.py              # WebSocket handler (22 events)
│   └── services/              # Logging, monitoring, recovery
└── tests/                     # 78+ test suites
```

### Frontend Structure (`frontend/`)
```
frontend/
├── src/
│   ├── pages/                 # StartPage, LobbyPage, RoomPage, GamePage
│   ├── components/            # 55+ React components
│   ├── services/              # NetworkService, GameStateManager
│   ├── hooks/                 # Custom React hooks
│   └── contexts/              # React contexts
├── network/                   # WebSocket management
└── esbuild.config.cjs        # Build configuration
```

### 🔌 WebSocket-Only Architecture
- **22 WebSocket Events** for ALL game operations
- **NO REST endpoints** for game actions (by design)
- **Endpoints**: `/ws/{room_id}`, `/ws/lobby`
- **Key Events**: 
  - Lobby: `create_room`, `join_room`, `request_room_list`
  - Game: `start_game`, `declare`, `play`, `request_redeal`
  - Room: `add_bot`, `remove_player`, `leave_room`

## 💻 Development Commands

### Quick Start
```bash
# Full development environment
./start.sh                      # Starts both backend and frontend

# Backend only
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend only
cd frontend
npm install
npm run dev
```

### Code Quality Checks (RUN BEFORE COMMITS)
```bash
# Backend (Python)
source venv/bin/activate
cd backend
black .                         # Format code
pylint engine/ api/ tests/      # Lint check
pytest tests/                   # Run tests

# Frontend (JavaScript/React)
cd frontend
npm run lint                    # ESLint check
npm run lint:fix               # Auto-fix issues
npm run type-check             # TypeScript validation
npm run format:fix             # Prettier formatting
npm test                       # Run tests
```

### Building & Deployment
```bash
# Production build
docker build -t liap-tui .

# Development with Docker
docker-compose -f docker-compose.dev.yml up

# Frontend production bundle
cd frontend && npm run build
```

## ⚠️ CRITICAL Development Rules for Claude

### 1. ALWAYS Check Before Modifying
```bash
# Before ANY code changes:
cd frontend && npm run lint && npm run type-check
cd backend && source venv/bin/activate && pylint [target_files]
```

### 2. Python Virtual Environment
- **ALWAYS** activate venv: `source venv/bin/activate`
- **NEVER** install packages globally
- **VERIFY** with `which python` → should show `.../venv/bin/python`

### 3. WebSocket-Only Operations
- **NEVER** create REST endpoints for game actions
- **ALWAYS** use WebSocket events in `ws.py`
- **CHECK** `backend/docs/analysis/websocket_flows.md` for event mappings

## 🚀 Enterprise Architecture Patterns (MANDATORY)

### State Machine Rules
```python
# ✅ CORRECT - Always use enterprise methods
await self.update_phase_data({
    'current_player': next_player,
    'turn_number': game.turn_number
}, f"Player {player_name} took turn")

# ❌ WRONG - Never use direct updates
self.phase_data['current_player'] = next_player  # FORBIDDEN
await broadcast(room_id, "event", data)          # FORBIDDEN
```

### Key Principles
1. **Automatic Broadcasting**: All state changes auto-broadcast
2. **Event Sourcing**: Every change is logged with timestamp
3. **Single Source of Truth**: Only `update_phase_data()` modifies state
4. **Human-Readable Logging**: Always include reason parameter

### Testing Requirements
```bash
cd backend
pytest tests/test_enterprise_architecture.py
pytest tests/test_state_machine.py
pytest tests/test_websocket.py
```

## 📊 Game Rules & Logic

### Game Flow
1. **4 Players**: Exactly 4 players (human or AI)
2. **32 Pieces**: 8 per player per round
3. **Win Condition**: First to 50 points
4. **Phases**: PREPARATION → DECLARATION → TURN → SCORING

### Key Mechanics
- **Weak Hand**: No piece > 9 points → redeal option (2x multiplier)
- **Declaration**: Players declare target piles (sum ≠ 8)
- **Valid Plays**: SINGLE, PAIR, THREE_OF_A_KIND, STRAIGHT, etc.
- **Scoring**: Actual vs declared piles (+5 for exact, negative for miss)

### Implementation Status
✅ **All 4 phases fully implemented with enterprise architecture**
✅ **22 WebSocket events handling all operations**
✅ **AI bots with strategic decision-making**
✅ **Complete scoring system with multipliers**
✅ **Event sourcing for game replay**

## 📁 Important File Locations

### Core Files
- **Game Engine**: `backend/engine/game.py`
- **State Machine**: `backend/engine/state_machine/`
- **WebSocket Handler**: `backend/api/routes/ws.py`
- **Frontend Entry**: `frontend/main.js`
- **Game Rules**: `RULES.md`
- **Project Specs**: `backend/docs/analysis/PROJECT_SPECIFICATIONS.md`

### Documentation
- **Analysis**: `backend/docs/analysis/`
  - `complete_dataflow_analysis.md` - Architecture diagrams
  - `PROJECT_SPECIFICATIONS.md` - Full specifications
  - `run_analysis.sh` - Regenerate documentation
- **API Docs**: `docs/WEBSOCKET_API.md`
- **Architecture**: `docs/ENTERPRISE_ARCHITECTURE.md`

## 🔧 Troubleshooting Guide

### Common Issues
1. **Import Errors**: Check virtual environment is activated
2. **WebSocket Connection Failed**: Ensure port 5050 is free
3. **Frontend Build Errors**: Update Node to v22, run `npm install`
4. **Test Failures**: Run `npm run lint:fix` and `black .`

### Debug Commands
```bash
# Check system status
curl http://localhost:5050/api/health/detailed

# View WebSocket events
cd backend/docs/analysis
python3 websocket_flow_analyzer.py

# Regenerate documentation
./run_analysis.sh
```

## 📝 Claude-Specific Instructions

### When Asked to Implement Features
1. **First**: Check existing WebSocket events in `ws.py`
2. **Then**: Look for similar patterns in state machine
3. **Always**: Use enterprise architecture methods
4. **Never**: Create new REST endpoints for game logic

### When Debugging
1. Check `backend/docs/analysis/websocket_flows.md` for event flow
2. Review `complete_dataflow_analysis.md` for architecture
3. Use `pytest -v` for detailed test output
4. Enable debug logging in `backend/api/services/logging_service.py`

### When Documenting
1. Update `PROJECT_SPECIFICATIONS.md` for requirement changes
2. Run `final_dataflow_analyzer.py` after major changes
3. Keep CLAUDE.md current with new patterns
4. Document WebSocket events in `websocket_flows.md`

## ✅ Quick Checklist for Claude

Before making changes:
- [ ] Virtual environment activated? (`source venv/bin/activate`)
- [ ] Linting passed? (`npm run lint`, `pylint`)
- [ ] Tests passing? (`npm test`, `pytest`)
- [ ] Using WebSocket for game operations? (not REST)
- [ ] Following enterprise architecture patterns?
- [ ] Documentation updated if needed?

---
*Last Updated: December 2024*
*Version: 2.0 - Comprehensive revision with current architecture*