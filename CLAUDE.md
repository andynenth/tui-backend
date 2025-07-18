# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Liap Tui is a real-time multiplayer board game inspired by traditional Chinese-Thai gameplay. The project uses a Python FastAPI backend with a JavaScript/PixiJS frontend, packaged in a single Docker container.


## Key Architecture

### Backend Structure
- **FastAPI** with WebSocket support for real-time gameplay
- **🚀 ENTERPRISE ARCHITECTURE** (`backend/engine/state_machine/`) **FULLY IMPLEMENTED** - production-ready enterprise patterns:
  - **Automatic Broadcasting System**: All state changes trigger automatic phase_change broadcasts
  - **Centralized State Management**: `update_phase_data()` ensures consistent state updates
  - **Event Sourcing**: Complete change history with sequence numbers and timestamps
  - **JSON-Safe Serialization**: Automatic conversion of game objects for WebSocket broadcasting
  - **Single Source of Truth**: No manual broadcast calls - all automatic and guaranteed
- **State Machine Phases** - All using enterprise architecture:
  - `PREPARATION`: Deal cards, handle weak hands ✅ ENTERPRISE ARCHITECTURE
  - `DECLARATION`: Players declare target pile counts ✅ ENTERPRISE ARCHITECTURE  
  - `TURN`: Turn-based piece playing ✅ ENTERPRISE ARCHITECTURE
  - `SCORING`: Calculate scores and check win conditions ✅ ENTERPRISE ARCHITECTURE
- **Game Engine** (`backend/engine/`) contains core game logic:
  - `game.py`: Main Game class with round management
  - `rules.py`: Play validation and game rules
  - `scoring.py`: Score calculation
  - `player.py`, `piece.py`: Core game entities
- **API Layer** (`backend/api/`) provides REST and WebSocket endpoints

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


### Building
```bash
# Frontend bundle
cd frontend && npm run build

# Docker production build
docker build -t liap-tui .
```

### Code Quality
```bash
# Python formatting and linting (ALWAYS in venv)
source venv/bin/activate && cd backend && black .
source venv/bin/activate && cd backend && pylint engine/ api/ tests/

# Frontend TypeScript checking and linting  
cd frontend && npm run type-check
cd frontend && npm run lint
cd frontend && npm run lint:fix  # Auto-fix issues
```

## Development Best Practices

- **CRITICAL**: Always run Python commands in venv: `source venv/bin/activate`
- **CRITICAL FOR CLAUDE**: Before making code changes, run quality checks:
  - `cd frontend && npm run lint` to catch constructor.name and type issues
  - `source venv/bin/activate && cd backend && pylint [files]` to catch import/attribute errors
  - `cd frontend && npm run type-check` for TypeScript validation

### **🚀 Enterprise Architecture Guidelines (MANDATORY)**

**For State Machine Development:**
- **✅ ALWAYS USE**: `await self.update_phase_data()` for state changes
- **❌ NEVER USE**: Direct `self.phase_data.update()` or `self.phase_data[key] = value`
- **✅ ALWAYS USE**: `await self.broadcast_custom_event()` for game events  
- **❌ NEVER USE**: Manual `broadcast()` function calls
- **✅ ALWAYS INCLUDE**: Human-readable reason parameter for debugging

**Enterprise Pattern Examples:**
```python
# ✅ CORRECT - Enterprise pattern
await self.update_phase_data({
    'current_player': next_player,
    'required_piece_count': count
}, f"Player {player_name} played {count} pieces")

# ❌ WRONG - Manual pattern (causes sync bugs)
self.phase_data['current_player'] = next_player
self.phase_data['required_piece_count'] = count
await broadcast(room_id, "play", data)  # This will cause sync issues!
```

**Testing Enterprise Architecture:**
- Run `python test_enterprise_architecture.py` to validate enterprise features
- Run `python test_turn_number_sync.py` to verify sync bug prevention
- All state changes must go through enterprise methods (no exceptions)

## 🚀 Enterprise Architecture Implementation ✅ PRODUCTION READY

### **Automatic Broadcasting System**
The backend now implements a **guaranteed automatic broadcasting system** that eliminates sync bugs:

```python
# 🚀 ENTERPRISE PATTERN - All state changes use this:
await self.update_phase_data({
    'current_player': next_player,
    'turn_number': game.turn_number,
    'phase_data': updated_data
}, "Human-readable reason for change")
# ↑ Automatically broadcasts phase_change event to all clients
```

### **Key Enterprise Features IMPLEMENTED:**
- **✅ Automatic Broadcasting**: No manual `broadcast()` calls needed - all automatic
- **✅ Event Sourcing**: Complete change history with sequence numbers and timestamps  
- **✅ JSON-Safe Serialization**: Game objects automatically converted for WebSocket transmission
- **✅ Centralized State Management**: Single `update_phase_data()` method for all state changes
- **✅ Custom Event Broadcasting**: `broadcast_custom_event()` for game-specific events
- **✅ Change History Tracking**: `get_change_history()` for debugging and audit trails

### **Enterprise Architecture Benefits DELIVERED:**
1. **🔒 Sync Bug Prevention**: Impossible to forget broadcasting - it's automatic
2. **🔍 Complete Debugging**: Every state change logged with reason and sequence
3. **⚡ Performance**: JSON serialization optimized for WebSocket transmission
4. **🏗️ Maintainability**: Single source of truth for all state management
5. **🧪 Testability**: Predictable state changes with full history tracking

### **Backend State Machine ✅ ENTERPRISE READY**
All phases now use enterprise architecture:
- **`PreparationState`**: ✅ Enterprise automatic broadcasting
- **`DeclarationState`**: ✅ Enterprise automatic broadcasting  
- **`TurnState`**: ✅ Enterprise automatic broadcasting
- **`ScoringState`**: ✅ Enterprise automatic broadcasting

Key classes **ALL ENTERPRISE**:
- `GameAction`: Represents player/system actions with payloads
- `GamePhase`: Enum defining the four main game phases  
- `ActionType`: All possible action types in the game
- `GameState`: Base class with enterprise `update_phase_data()` and `broadcast_custom_event()`

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
- WebSocket communication follows a specific protocol defined in the API layer **[INTEGRATION TARGET]**
- The `start.sh` script sets up the full development environment automatically

## File Locations

- Main game engine: `backend/engine/game.py`
- State machine: `backend/engine/state_machine/game_state_machine.py`
- API routes: `backend/api/routes/`
- Frontend entry: `frontend/main.js`
- Game rules documentation: `RULES.md`