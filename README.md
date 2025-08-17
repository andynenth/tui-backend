# 🀄 Liap Tui Online Board Game

[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async--ready-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1-61dafb?logo=react)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎮 Live Demo

<div align="center">
  <a href="https://castellan.andynenth.dev">
    <img src="docs/assets/gameplay-screenshot.png" alt="Castellan Gameplay" width="600">
  </a>
  <br><br>
  <a href="https://castellan.andynenth.dev">
    <img src="https://img.shields.io/badge/Play%20Now-castellan.andynenth.dev-green?style=for-the-badge&logo=gamepad" alt="Play Now">
  </a>
</div>

> **Note**: Screenshot should show Turn Phase with 4 players, some pieces played, and game log visible

> A real-time online multiplayer board game inspired by *Liap Tui*, a traditional Chinese-Thai game.  
> Built with **FastAPI** for the backend and **React 19 + ESBuild** for the frontend.  
> Uses **WebSocket-first architecture** for all game operations, packaged in a single Docker container.

## Table of Contents
- [Live Demo](#-live-demo)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Development](#️-development)
- [Game Rules](#-game-rules)
- [Documentation](#-documentation)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [Support](#-support)
- [License](#-license)

---

## 🎮 Features

### Gameplay
- 🎯 Real-time multiplayer (4 players)
- 🤖 Intelligent AI bots
- 🔄 Complete game flow with 4 phases
- 🏆 Advanced scoring with multipliers

### Technical
- ⚡ WebSocket-first architecture
- 🔐 Event sourcing & recovery
- 📊 Health monitoring & metrics
- 🐳 Single-container deployment

### Frontend
- ⚛️ React 19 with TypeScript
- 🔌 Auto-reconnection
- 📱 Responsive design
- 🧪 82% test coverage

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
git clone https://github.com/andynenth/castellan.git
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
├── frontend/       → React 19 + TypeScript frontend
├── backend/        → FastAPI + Python backend  
├── docs/           → 📚 Comprehensive documentation (30+ guides)
├── nginx/          → SSL configuration
└── scripts/        → Deployment & maintenance
```

See [Project Structure](docs/README.md) for detailed organization.

---

## ⚙️ Configuration

The application uses environment variables for configuration. See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup instructions and all available options.

---

## 🏗️ API Architecture

This project uses a **WebSocket-first architecture** for all game operations. REST API is limited to monitoring and admin functions. See [WebSocket API Guide](docs/WEBSOCKET_API.md) for details.

---

## 🧪 Testing

The project includes comprehensive testing with 78+ backend test suites and frontend coverage. See [TESTING.md](TESTING.md) for complete testing guide, coverage requirements, and best practices.

---

## 🛠️ Development

### Quick Start
```bash
./start.sh  # Starts both frontend and backend with hot reload
```

### Manual Start
```bash
# Backend
docker-compose -f docker-compose.dev.yml up backend

# Frontend
cd frontend && npm run dev
```

See [Development Guide](docs/06-tutorials/LOCAL_DEVELOPMENT.md) for details.

---

## 🚀 Deployment

### Recommended: AWS EC2 (Free Tier Friendly)
```bash
./deploy-ec2.sh  # One-command deployment
```
See [EC2 Deployment Guide](EC2_DEPLOYMENT_GUIDE.md)

### Other Options
- **AWS ECS**: [ECS Guide](docs/deployment/AWS_DEPLOYMENT_CHECKLIST.md)
- **Local Docker**: `docker-compose -f docker-compose.prod.yml up`

---

## 🎯 Game Rules

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

## 📚 Documentation

Comprehensive documentation organized into categories:
- **Architecture & Design**: System overview, patterns, principles
- **Component Guides**: Backend, frontend, state machine deep dives  
- **Tutorials**: Development setup, adding features, debugging
- **API Reference**: WebSocket events, data structures, contracts

📖 See [`/docs`](docs/) for all documentation (30+ guides).

---

<details>
<summary><h2>🤝 Contributing</h2></summary>

We welcome contributions! Areas where you can help:
- 🐛 Bug fixes
- ✨ New features  
- 📝 Documentation
- 🧪 Test coverage
- 🎨 UI/UX improvements

See [Contributing Guide](docs/CONTRIBUTING_GUIDE.md) for detailed guidelines, code standards, and submission process.

</details>

---

## 🏗️ Architecture Evolution

See [CHANGELOG.md](CHANGELOG.md) for the complete development history and architectural evolution of the project.

---

## 🔧 Troubleshooting

For common issues and solutions, see:
- [Troubleshooting Guide](docs/troubleshooting.md) - Comprehensive troubleshooting
- [Operations Guide](OPERATIONS.md) - Production issues
- [Migration Checklist](MIGRATION_CHECKLIST.md) - ECS to EC2 migration

---

## 📞 Support

- **Documentation**: [/docs](docs/)
- **Issues**: [GitHub Issues](https://github.com/andynenth/castellan/issues)
- **Discussions**: [GitHub Discussions](https://github.com/andynenth/castellan/discussions)

For security vulnerabilities, please email directly instead of creating public issues.

---

## 📄 License

MIT © [Andy Nenthong](https://github.com/andynenth/castellan).  
See [LICENSE](LICENSE) for details.