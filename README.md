# Castellan - Multiplayer Board Game

<div align="center">
  <img src="docs/assets/gameplay.gif" alt="Castellan Game" width="300">
</div>

> A real-time multiplayer board game inspired by Liap Tui, a traditional Chinese-Thai game.
> Built with FastAPI (Python) + React 19 (TypeScript) + WebSockets.

## Overview

Castellan is a web-based implementation of Liap Tui featuring real-time multiplayer gameplay, AI opponents, and a modern responsive interface. The game supports 4 players per room with automatic matchmaking and configurable AI difficulty levels.

## Technical Architecture

- **Backend**: FastAPI with WebSocket support for real-time communication
- **Frontend**: React 19 with TypeScript and ESBuild for fast compilation
- **Game Engine**: Enterprise state machine pattern with event sourcing
- **Deployment**: Docker containerization with production-ready configuration

## Getting Started

### Docker Development (Recommended)
```bash
git clone https://github.com/andynenth/castellan.git
cd castellan
./dev.sh
# Open http://localhost:5050
```

### Local Development
```bash
# Install dependencies
cd frontend && npm install && cd ..
pip install -r requirements.txt

# Start development server
./start.sh
```

Both methods include hot reload for frontend and backend development.

## Project Structure

```
castellan/
├── frontend/          # React 19 + TypeScript
│   ├── src/          # Components and game logic
│   └── network/      # WebSocket client implementation
├── backend/          # FastAPI + Python 3.11
│   ├── engine/       # Core game logic and state machine
│   ├── api/          # WebSocket and REST endpoints
│   └── ai/           # AI player implementation
└── docs/             # Technical documentation
```

## Development Workflow

### Code Quality
```bash
# Frontend linting and type checking
cd frontend && npm run lint
cd frontend && npm run type-check

# Python formatting and linting
source venv/bin/activate && cd backend && black .
```

### Testing
```bash
# Frontend tests with coverage
cd frontend && npm test -- --coverage

# Backend tests with coverage
pytest --cov=backend
```

Current test coverage: Frontend 82%, Backend 78%

### AI Development
```bash
# Run AI-only games for debugging
python backend/ai_debug_simple.py
```

## Key Features

### Game Implementation
- 4-player real-time gameplay with WebSocket synchronization
- State machine architecture ensuring consistent game state
- Complete game history with event sourcing for debugging
- Configurable AI players with multiple difficulty levels

### Technical Highlights
- Single WebSocket endpoint (`/ws/{room_id}`) for all game operations
- Automatic state broadcasting on all game events
- Docker-based deployment with integrated frontend serving
- Comprehensive error handling and recovery mechanisms

## API Documentation

- **WebSocket Protocol**: See [docs/WEBSOCKET_API.md](docs/WEBSOCKET_API.md)
- **REST Endpoints**: Used for monitoring and debugging only
- **Game Events**: All game operations use WebSocket messages

## Performance Considerations

- WebSocket connection pooling for efficient resource usage
- State machine optimization for sub-100ms response times
- Frontend bundle optimization with ESBuild
- Rate limiting and connection management for production use

## Contributing

This is an independent project. For bug reports or feature suggestions, please use GitHub Issues.

### Development Guidelines
1. Maintain test coverage above 80%
2. Follow existing code patterns and conventions
3. Run linting before committing changes
4. Include tests for new features

## Documentation

- [Game Rules](RULES.md) - Detailed game mechanics
- [Local Development](docs/06-tutorials/LOCAL_DEVELOPMENT.md) - Setup guide
- [WebSocket API](docs/WEBSOCKET_API.md) - Protocol documentation
- [AI System](docs/05-ai-system/) - AI implementation details

## License

MIT © [Andy Nenthong](https://github.com/andynenth). See [LICENSE](LICENSE) for details.
