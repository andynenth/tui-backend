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

- 🎮 Turn-based multiplayer gameplay
- 📡 Real-time updates via WebSocket
- 🧠 Modular game logic with AI and rule system
- 🎨 Scene-based UI using PixiJS and @pixi/ui
- 🐳 Single-container Docker deployment (no separate frontend/backend setup)

---

## 📁 Project Structure

```
frontend/      → PixiJS UI components and scenes  
backend/       → FastAPI app, game engine, WebSocket, AI logic  
build/         → ESBuild output (bundle.js)  
Dockerfile     → Two-stage Docker build (Node + Python)  
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
docker run -p 8080:80 liap-tui
```

Then open your browser:  
👉 `http://localhost:8080`

> The frontend is served from FastAPI’s static files.  
> WebSocket and API routes are available under `/ws/` and `/api`.

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

## 🧠 Liap Tui – Game Rules

> [See `/docs`]  
Includes: Piece types, Turn flow, Declaration, Redeal logic, Scoring system, and more.

---

## 📄 License

MIT © [Andy Nenthong](https://github.com/andynenth/tui-backend).  
See [LICENSE](LICENSE) for details.