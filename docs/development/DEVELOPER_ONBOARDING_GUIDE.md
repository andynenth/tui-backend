# Developer Onboarding Guide

## Welcome to Liap Tui! 🎮

This guide will help you understand the project architecture, set up your development environment, and start contributing effectively.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Local Development Setup](#local-development-setup)
4. [Code Organization](#code-organization)
5. [Key Concepts](#key-concepts)
6. [Common Development Tasks](#common-development-tasks)
7. [Troubleshooting](#troubleshooting)
8. [Next Steps](#next-steps)

---

## Project Overview

**Liap Tui** is a real-time multiplayer board game inspired by traditional Chinese-Thai gameplay. The project features:

- **4-player multiplayer** with bot support
- **Real-time gameplay** via WebSockets
- **Enterprise architecture** with automatic state synchronization
- **React frontend** with modern UI components
- **FastAPI backend** with state machine game logic

### Game Flow Summary
```
WAITING → PREPARATION → DECLARATION → TURN ↔ TURN_RESULTS → SCORING → GAME_OVER
```

Players progress through 7 distinct phases, from room setup to final scoring, with automatic state management and real-time updates.

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   React Frontend │ ←------------→ │  FastAPI Backend │
│                 │                 │                 │
│ • UI Components │                 │ • State Machine │
│ • GameService   │                 │ • Room Manager  │
│ • NetworkService│                 │ • Bot Manager   │
└─────────────────┘                 └─────────────────┘
```

### Key Technologies

#### Frontend Stack
- **React 19.1.0** - Modern UI framework
- **ESBuild** - Fast bundling and hot reload
- **CSS Modules** - Scoped styling
- **TypeScript** - Type safety for services

#### Backend Stack
- **FastAPI** - High-performance Python web framework
- **WebSockets** - Real-time bidirectional communication
- **State Machine** - Enterprise architecture for game logic
- **Bot Manager** - AI player management

### Enterprise Architecture Pattern

The backend uses an **Enterprise Architecture** pattern with:

- **Automatic Broadcasting**: All state changes trigger automatic WebSocket broadcasts
- **Event Sourcing**: Complete change history with sequence numbers
- **JSON-Safe Serialization**: Game objects automatically converted for transmission
- **Single Source of Truth**: No manual broadcast calls needed
- **Centralized State Management**: `update_phase_data()` ensures consistency

---

## Local Development Setup

### Prerequisites

- **Python 3.9+** 
- **Node.js 16+**
- **Docker** (optional, for containerized development)

### Quick Start

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd liap-tui
   ```

2. **Start Development Environment**
   ```bash
   ./start.sh
   ```
   This script:
   - Sets up Python virtual environment
   - Installs backend dependencies
   - Installs frontend dependencies
   - Starts both backend and frontend with hot reload

3. **Access the Application**
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

### Manual Setup (Alternative)

#### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Start backend
python -m api.main
```

#### Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

### Docker Setup (Alternative)
```bash
# Start backend only
docker-compose -f docker-compose.dev.yml up backend

# For production build
docker build -t liap-tui .
```

---

## Code Organization

### Project Structure

```
liap-tui/
├── backend/              # FastAPI backend
│   ├── api/             # API routes and WebSocket handlers
│   │   ├── routes/      
│   │   │   ├── routes.py    # HTTP endpoints
│   │   │   └── ws.py        # WebSocket handlers
│   │   └── main.py      # FastAPI application
│   ├── engine/          # Core game logic
│   │   ├── game.py      # Main Game class
│   │   ├── player.py    # Player entities
│   │   ├── piece.py     # Game pieces
│   │   ├── room.py      # Room management
│   │   ├── rules.py     # Game rules and validation
│   │   ├── scoring.py   # Score calculation
│   │   └── state_machine/   # Enterprise architecture
│   │       ├── core.py      # State machine definitions
│   │       ├── game_state_machine.py  # Main state machine
│   │       └── states/      # Individual phase handlers
│   └── tests/           # Backend tests
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   │   └── game/    # Game-specific components
│   │   ├── pages/       # Route components
│   │   ├── services/    # Business logic and API integration
│   │   ├── contexts/    # React context providers
│   │   ├── hooks/       # Custom React hooks
│   │   └── styles/      # CSS modules and themes
│   ├── package.json     # Frontend dependencies
│   └── esbuild.config.cjs  # Build configuration
├── docs/               # Project documentation
├── CLAUDE.md          # AI assistant instructions
└── start.sh           # Development startup script
```

### Key Directories

#### Backend Key Files
- **`backend/api/routes/ws.py`** - WebSocket event handlers
- **`backend/engine/state_machine/`** - Core game logic
- **`backend/engine/game.py`** - Main game class
- **`backend/engine/room.py`** - Room management

#### Frontend Key Files
- **`frontend/src/services/GameService.ts`** - Game state management
- **`frontend/src/services/NetworkService.ts`** - WebSocket communication
- **`frontend/src/components/game/`** - Phase-specific UI components
- **`frontend/src/pages/GamePage.jsx`** - Main game interface

---

## Key Concepts

### 1. Enterprise Architecture (Backend)

The backend uses a sophisticated enterprise pattern:

```python
# ✅ CORRECT - Enterprise pattern
await self.update_phase_data({
    'current_player': next_player,
    'turn_number': game.turn_number
}, "Player completed their turn")
# ↑ Automatically broadcasts to all clients

# ❌ WRONG - Manual pattern (causes sync bugs)
self.phase_data['current_player'] = next_player
await broadcast(room_id, "update", data)  # Manual, error-prone
```

**Key Benefits:**
- **🔒 Sync Bug Prevention**: Impossible to forget broadcasting
- **🔍 Complete Debugging**: Every change logged with reason
- **⚡ Performance**: Optimized JSON serialization
- **🏗️ Maintainability**: Single source of truth

### 2. Game State Machine

The game progresses through 7 phases managed by a state machine:

```python
class GamePhase(Enum):
    WAITING = "waiting"           # Room setup
    PREPARATION = "preparation"   # Deal cards, handle weak hands
    DECLARATION = "declaration"   # Players declare targets
    TURN = "turn"                # Players play pieces
    TURN_RESULTS = "turn_results" # Show turn results
    SCORING = "scoring"          # Calculate scores
    GAME_OVER = "game_over"      # Final results
```

Each phase has:
- **State handler class** (`/backend/engine/state_machine/states/`)
- **Allowed actions** (what players can do)
- **Transition conditions** (when to move to next phase)
- **Frontend UI component** (`/frontend/src/components/game/`)

### 3. WebSocket Communication

Real-time communication uses a structured protocol:

**Message Format:**
```json
{
  "event": "event_name",
  "data": {
    "timestamp": 1234567890.123,
    "room_id": "room_123",
    "sequence": 42
  }
}
```

**Common Events:**
- `phase_change` - Game phase transitions (automatic)
- `room_update` - Room state changes
- `play` - Player actions
- `error` - Error notifications

### 4. Frontend State Management

The frontend uses a service-oriented architecture:

```
ServiceIntegration (orchestrator)
    ↓
GameService (state management)
    ↓
NetworkService (WebSocket communication)
```

**GameService** manages:
- Current game phase
- Player data and game state
- Action validation
- State synchronization

### 5. Component Architecture

React components follow a clear hierarchy:

```
GameContainer (orchestrator)
    ↓
Phase-specific UI (TurnUI, DeclarationUI, etc.)
    ↓
Reusable components (Button, GamePiece, etc.)
```

---

## Common Development Tasks

### Adding a New Game Phase

1. **Create Backend State Handler**
   ```python
   # /backend/engine/state_machine/states/my_new_state.py
   class MyNewState(GameState):
       async def _setup_phase(self):
           await self.update_phase_data({
               'my_data': 'initial_value'
           }, "Phase initialized")
   ```

2. **Add to State Machine**
   ```python
   # /backend/engine/state_machine/core.py
   class GamePhase(Enum):
       MY_NEW_PHASE = "my_new_phase"
   ```

3. **Create Frontend Component**
   ```jsx
   // /frontend/src/components/game/MyNewUI.jsx
   export const MyNewUI = ({ gameState, gameActions }) => {
       return <div>My new phase UI</div>;
   };
   ```

4. **Register in GameContainer**
   ```jsx
   // Add to GameContainer.jsx switch statement
   case 'my_new_phase':
       return <MyNewUI {...myNewProps} />;
   ```

### Adding a New WebSocket Event

1. **Backend Handler**
   ```python
   # /backend/api/routes/ws.py
   elif event == "my_new_event":
       # Handle the event
       data = message.get("data", {})
       # Process and respond
   ```

2. **Frontend Sender**
   ```javascript
   // /frontend/src/services/NetworkService.ts
   sendMyNewEvent(data) {
       this.send(this.currentRoomId, 'my_new_event', data);
   }
   ```

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests  
cd frontend
npm test

# Specific test file
python -m pytest tests/test_state_machine.py -v
```

### Code Quality Checks

```bash
# Python formatting and linting (ALWAYS in venv)
source venv/bin/activate
cd backend
black .
pylint engine/ api/ tests/

# Frontend TypeScript checking and linting
cd frontend
npm run type-check
npm run lint
npm run lint:fix  # Auto-fix issues
```

### Debugging WebSocket Issues

1. **Check Browser Network Tab** - See WebSocket messages
2. **Backend Logs** - Look for error messages in console
3. **Use Network Service Debug** - Add console.log in NetworkService
4. **State Machine Logs** - Enterprise architecture logs all changes

### Adding New UI Components

1. **Create Component**
   ```jsx
   // /frontend/src/components/MyComponent.jsx
   export const MyComponent = ({ prop1, prop2 }) => {
       return <div className="my-component">...</div>;
   };
   ```

2. **Add Styles** (if needed)
   ```css
   /* /frontend/src/styles/components/mycomponent.css */
   .my-component {
       /* styles using CSS variables from theme.css */
   }
   ```

3. **Export from Index**
   ```javascript
   // /frontend/src/components/index.js
   export { MyComponent } from './MyComponent';
   ```

---

## Troubleshooting

### Common Issues

#### Frontend Build Errors
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check
```

#### Backend Import Errors
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### WebSocket Connection Issues
- Check if backend is running on port 8000
- Verify no CORS issues in browser console
- Check network tab for WebSocket connection status

#### State Sync Issues
- Enterprise architecture should prevent these
- Check backend logs for state machine errors
- Use browser developer tools to inspect WebSocket messages

### Development Environment

#### Hot Reload Not Working
- Frontend: Check if ESBuild is watching files
- Backend: FastAPI should auto-reload on file changes
- Try restarting both servers

#### Port Conflicts
- Backend: Change port in `/backend/api/main.py`
- Frontend: Change port in package.json dev script

### Getting Help

1. **Check existing documentation** in `/docs/`
2. **Review CLAUDE.md** for project-specific patterns
3. **Look at similar existing code** for patterns
4. **Check test files** for usage examples

---

## Next Steps

### Immediate Tasks
1. **Run the application** using `./start.sh`
2. **Create a test room** and play through a game
3. **Explore the codebase** following the organization guide above
4. **Read the Game Lifecycle Documentation** for detailed phase behavior

### Learning Path
1. **Understand game rules** - Play a few games to understand the flow
2. **Study one phase** - Pick a phase and trace it from frontend to backend
3. **Make a small change** - Add a console.log or change some text
4. **Read enterprise architecture** - Understand the automatic broadcasting system

### Advanced Topics
- **Bot AI behavior** - `/backend/engine/bot_manager.py`
- **Performance optimization** - State machine efficiency
- **Error recovery** - Reconnection and state sync
- **Testing strategy** - Unit and integration tests

### Useful Resources
- **Game Lifecycle Documentation** - `/docs/GAME_LIFECYCLE_DOCUMENTATION.md`
- **FastAPI Docs** - https://fastapi.tiangolo.com/
- **React Docs** - https://react.dev/
- **WebSocket Protocol** - See documentation for event specifications

---

## Development Philosophy

This project emphasizes:

- **Enterprise Architecture** - Reliable, maintainable patterns
- **Real-time Synchronization** - Automatic state management
- **Type Safety** - TypeScript for frontend services
- **Testing** - Comprehensive test coverage
- **Code Quality** - Linting and formatting standards
- **Documentation** - Clear, comprehensive guides

Welcome to the team! 🚀