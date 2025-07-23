# api/app.py
"""
FastAPI application using clean architecture.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .websocket import websocket_router
from .routes import health, debug
from .dependencies import get_container

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Liap Tui API...")
    container = get_container()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Liap Tui API...")
    await container.cleanup()


# Create FastAPI app
app = FastAPI(
    title="Liap Tui Game API",
    description="Real-time multiplayer board game API using clean architecture",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(debug.router, tags=["debug"])
app.include_router(websocket_router, tags=["websocket"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Liap Tui Game API",
        "version": "2.0.0",
        "architecture": "clean",
        "endpoints": {
            "websocket": {
                "lobby": "/ws/lobby",
                "room": "/ws/{room_id}"
            },
            "rest": {
                "health": "/api/health",
                "debug": "/api/debug"
            }
        }
    }