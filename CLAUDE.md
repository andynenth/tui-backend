# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Liap Tui is a real-time multiplayer board game inspired by traditional Chinese-Thai gameplay. The project uses a Python FastAPI backend with a JavaScript/PixiJS frontend, packaged in a single Docker container.

**Current Status**: Week 3 - Integration Phase  
**Week 2 Complete**: Full state machine architecture implemented and tested (78+ tests passing)  
**Current Focus**: Integrating state machine with existing routes, bots, and WebSocket handlers

## Key Architecture

### Backend Structure
- **FastAPI** with WebSocket support for real-time gameplay
- **State Machine Pattern** (`backend/engine/state_machine/`) **COMPLETE** - manages game flow through phases:
  - `PREPARATION`: Deal cards, handle weak hands and redeals ✅ PRODUCTION READY
  - `DECLARATION`: Players declare target pile counts ✅ PRODUCTION READY  
  - `TURN`: Turn-based piece playing ✅ PRODUCTION READY
  - `SCORING`: Calculate scores and check win conditions ✅ PRODUCTION READY
- **Game Engine** (`backend/engine/`) contains core game logic:
  - `game.py`: Main Game class with round management
  - `rules.py`: Play validation and game rules
  - `scoring.py`: Score calculation
  - `player.py`, `piece.py`: Core game entities
- **API Layer** (`backend/api/`) provides REST and WebSocket endpoints **[WEEK 3 INTEGRATION TARGET]**

### Frontend Structure
- **React 19.1.0** with React Router DOM for modern UI architecture
- **ESBuild** for bundling and hot reload during development
- **Component Architecture** (`frontend/src/components/`) with reusable UI components
- **Page Components** (`frontend/src/pages/`) handle different application states
- **React Game Phases** (`frontend/src/phases/`) mirror backend state machine
- **Network Layer** (`frontend/network/`) manages WebSocket communication
- **React Hooks** (`frontend/src/hooks/`) bridge existing game managers

## Development Commands

### Local Development
```bash
# Start both backend and frontend with hot reload
./start.sh

# Backend only (in Docker)
docker-compose -f docker-compose.dev.yml up backend

# Frontend development server
cd frontend && npm run dev
```

### Testing (Week 2 Complete - All Passing)
```bash
# State machine verification (integration test)
cd backend && python test_full_game_flow.py

# Run all backend tests (78+ tests)
cd backend && python -m pytest tests/ -v

# Individual state tests
cd backend && python -m pytest tests/test_preparation_state.py -v
cd backend && python -m pytest tests/test_turn_state.py -v  
cd backend && python -m pytest tests/test_scoring_state.py -v

# Quick state machine test
cd backend && python run_tests.py

# Frontend tests
cd frontend && npm test
```

### Building
```bash
# Frontend bundle
cd frontend && npm run build

# Docker production build
docker build -t liap-tui .
```

### Code Quality
```bash
# Python formatting (Poetry dev dependency)
cd backend && black .

# Frontend linting via npm scripts in package.json
cd frontend && npm run lint  # (if available)
```

## Game State Management ✅ PRODUCTION READY

The game uses a sophisticated state machine (`GameStateMachine`) **FULLY IMPLEMENTED** that:  
- Processes actions asynchronously through an action queue ✅ TESTED
- Validates actions based on current game phase ✅ TESTED  
- Manages player turns and game flow transitions ✅ TESTED
- Handles disconnections and reconnections ✅ TESTED

Key classes **ALL WORKING**:
- `GameAction`: Represents player/system actions with payloads
- `GamePhase`: Enum defining the four main game phases  
- `ActionType`: All possible action types in the game

**Week 3 Focus**: Integration with existing routes (`backend/api/routes/routes.py`) and bot system (`backend/engine/bot_manager.py`)

## Game Rules Summary

- 4 players, 8 pieces each per round
- **Weak Hand Rule**: Players with no piece > 9 points can request redeal
- **Declaration Phase**: Players declare target pile count (total ≠ 8)
- **Turn Phase**: Play 1-6 pieces in sets, winner takes all pieces
- **Scoring**: Compare actual vs declared piles, apply multipliers
- **Win Condition**: First to 50 points or highest after 20 rounds

## Development Notes

- The project uses both `requirements.txt` and `pyproject.toml` (Poetry) for Python dependencies
- Frontend uses ESBuild for fast compilation and bundling  
- **State machine is COMPLETE** - 78+ tests passing, full integration test working
- **Week 3 Integration Targets**: Replace `if phase ==` checks in routes with state machine validation
- WebSocket communication follows a specific protocol defined in the API layer **[INTEGRATION TARGET]**
- The `start.sh` script sets up the full development environment automatically

## Week 3 Integration Strategy

**Current Phase**: Integrating complete state machine with existing systems
**Priority**: 
1. `backend/api/routes/routes.py` - Replace manual phase checks
2. `backend/engine/bot_manager.py` - Bot decision making integration  
3. WebSocket handlers - Real-time state synchronization
4. Performance testing - Multi-game concurrent testing

**Key Patterns Applied**:
- State Pattern: Each phase = separate state class ✅ PROVEN
- Action Queue: Sequential processing prevents race conditions ✅ PROVEN  
- Single Responsibility: Each state handles only its phase logic ✅ PROVEN

## File Locations

- Main game engine: `backend/engine/game.py`
- State machine: `backend/engine/state_machine/game_state_machine.py`
- API routes: `backend/api/routes/`
- Frontend entry: `frontend/main.js`
- Game rules documentation: `RULES.md`