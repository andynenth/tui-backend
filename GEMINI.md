# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

Liap Tui is a real-time multiplayer board game inspired by traditional Chinese-Thai gameplay. The project uses a Python FastAPI backend with a JavaScript/React frontend, packaged in a single Docker container.

## Game Rules Summary

- **Players**: 4 players, each with 8 pieces per round.
- **Objective**: Be the first to score 50 points.
- **Weak Hand Rule**: A player whose hand has no piece with a point value greater than 9 can request a redeal.
- **Redeal**: If a redeal occurs, all hands are reshuffled, the score multiplier for the round increases (2x, 3x, etc.), and the player who requested the redeal starts the round.
- **Declaration Phase**: Before playing, each player declares how many "piles" (tricks) they intend to win. The sum of all players' declarations cannot be 8.
- **Turn Phase**: Players play sets of 1-6 pieces. The winner of a turn takes the pile and starts the next turn.
- **Scoring**: Points are awarded based on how a player's actual captured piles compare to their declared target.

## Game Flow

The game proceeds in four phases each round:

### 1. Preparation Phase
- Pieces are dealt.
- Players check for "weak hands."
- If a weak hand is present, the player can request a redeal.
- If a redeal happens, the score multiplier is increased, and the requester becomes the round starter.
- If no redeal, the starter is determined:
    - **Round 1**: The player with the GENERAL_RED piece.
    - **Subsequent Rounds**: The winner of the final turn of the previous round.

### 2. Declaration Phase
- In sequence, starting with the round starter, each player declares their target number of piles to win.
- **Restrictions**:
    - A player who declared "0" for two consecutive rounds must declare at least 1.
    - The final player to declare cannot choose a number that would make the total declared piles for the round equal 8.

### 3. Turn Phase
- The turn starter plays a valid set of 1-6 pieces.
- All other players must play the same number of pieces.
- The winner of the turn is determined by the rank of the pieces played.
- The winner collects the played pieces as a "pile" and starts the next turn.
- The phase continues until all pieces have been played.

### 4. Scoring Phase
- Scores are calculated based on the declaration vs. actual piles won.
    - **Declared 0, captured 0**: +3 points
    - **Declared 0, captured > 0**: -points per pile captured
    - **Declared X, captured X**: X + 5 points
    - **Declared X, captured ≠ X**: -points for the absolute difference
- The score is multiplied by the redeal multiplier, if any.
- Total scores are updated, and the game checks for a winner (>= 50 points).

## Key Architecture

The project follows an "Enterprise Architecture" pattern to ensure stability and prevent synchronization bugs.

### Backend
- **FastAPI** with WebSocket support for real-time communication.
- **Enterprise State Machine** (`backend/engine/state_machine/`):
    - **Automatic Broadcasting**: State changes automatically trigger broadcasts to all clients.
    - **Centralized State Management**: All state modifications must go through `update_phase_data()`.
    - **Event Sourcing**: All state changes are logged with sequence numbers and timestamps for debugging and history.
    - **JSON-Safe Serialization**: Game objects are automatically prepared for WebSocket transmission.

### Frontend
- **React 19.1.0** with React Router.
- **ESBuild** for fast bundling and development hot-reloading.
- **Component-based architecture** mirroring the backend's state machine.

## Development Best Practices

- **CRITICAL**: Always run Python commands within the virtual environment (`source venv/bin/activate`).
- **CRITICAL**: Before committing code, run the quality checks to prevent errors.

### **🚀 Enterprise Architecture Guidelines (MANDATORY)**

**For State Machine Development:**
- **✅ ALWAYS USE**: `await self.update_phase_data()` for any state changes. Provide a human-readable reason.
- **❌ NEVER USE**: Direct modification like `self.phase_data['key'] = value`. This will cause sync bugs.
- **✅ ALWAYS USE**: `await self.broadcast_custom_event()` for game events not tied to a direct state change.
- **❌ NEVER USE**: Manual `broadcast()` calls. Broadcasting is automatic.

**Example:**
```python
# ✅ CORRECT - Enterprise pattern
await self.update_phase_data({
    'current_player': next_player,
}, f"Moving to player {next_player.name}")

# ❌ WRONG - Manual pattern (CAUSES BUGS)
self.phase_data['current_player'] = next_player
await broadcast(room_id, "phase_change", self.phase_data)
```

## Development Commands

### Local Development
```bash
# Start backend and frontend with hot reload
./start.sh
```

### Building
```bash
# Build frontend bundle
cd frontend && npm run build

# Build production Docker image
docker build -t liap-tui .
```

### Code Quality
```bash
# Activate Python environment
source venv/bin/activate

# Format and lint backend (from backend/ directory)
cd backend
black .
pylint engine/ api/ tests/
cd ..

# Check and lint frontend (from frontend/ directory)
cd frontend
npm run type-check
npm run lint
cd ..
```

## Key File Locations

- **Game Logic Engine**: `backend/engine/game.py`
- **State Machine**: `backend/engine/state_machine/game_state_machine.py`
- **API Endpoints**: `backend/api/routes/`
- **Frontend Entrypoint**: `frontend/main.js`
- **Game Rules**: `RULES.md`
