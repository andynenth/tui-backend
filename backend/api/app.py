# api/app.py
"""
FastAPI application using clean architecture.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from .websocket import websocket_router
from .routes import health, debug
from .routes.routes import router as api_router
from .dependencies import get_container

# Load environment variables
load_dotenv()

# Set up logging configuration
try:
    from config.logging_config import setup_logging
    setup_logging()
except ImportError:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Configuration from environment
STATIC_DIR = os.getenv("STATIC_DIR", "backend/static")
INDEX_FILE = os.getenv("INDEX_FILE", "index.html")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Liap Tui API...")
    container = get_container()
    
    # Start cleanup task for rooms
    try:
        from backend.api.routes.ws import start_cleanup_task
        start_cleanup_task()
    except ImportError:
        logger.warning("Could not import cleanup task from old ws module")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Liap Tui API...")
    await container.cleanup()


# Create FastAPI app
app = FastAPI(
    title="Liap Tui Game API",
    description="""
    **Backend API for Liap Tui Board Game**
    
    A real-time multiplayer board game with clean architecture implementation.
    
    ## Features
    
    * **Clean Architecture** - Domain-driven design with proper separation of concerns
    * **Event-Driven** - Full event sourcing and CQRS patterns
    * **Real-time Gameplay** - WebSocket-based communication
    * **Bot Support** - AI strategies with different difficulty levels
    
    ## Architecture Layers
    
    1. **Domain** - Pure business logic and entities
    2. **Application** - Use cases and orchestration
    3. **Infrastructure** - External concerns (WebSocket, persistence)
    4. **API** - Clean interface layer
    
    ## WebSocket Connection
    
    Connect to `ws://localhost:8000/ws/{room_id}` for real-time game events.
    Special lobby connection: `ws://localhost:8000/ws/lobby`
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(debug.router, prefix="/api", tags=["debug"])
app.include_router(websocket_router, tags=["websocket"])

# Serve static files - must be last to catch all
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="root")