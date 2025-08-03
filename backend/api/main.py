# backend/api/main.py

import os  # Standard library for interacting with the operating system (e.g., environment variables).

from backend.api.routes.routes import (
    router as api_router,  # Import the API router for REST endpoints.
)
from backend.api.routes.ws import (
    router as ws_router,  # Import the WebSocket router for real-time communication.
)
from backend.api.routes.debug import (
    router as debug_router,  # Import the debug router for event store access.
)
from backend.api.middleware import (
    RateLimitMiddleware,
)  # Import rate limiting middleware
from dotenv import (  # Library to load environment variables from a .env file.
    load_dotenv,
)
from fastapi import FastAPI  # Import FastAPI framework for building the API.
from fastapi.middleware.cors import (  # Middleware for handling Cross-Origin Resource Sharing (CORS).
    CORSMiddleware,
)
from fastapi.responses import FileResponse  # Used to return a file as a response.
from fastapi.staticfiles import StaticFiles  # Utility to serve static files.

# ✅ Load environment variables from the .env file.
# This makes configuration values available via os.getenv().
load_dotenv()

# ✅ Set up logging configuration
try:
    from config.logging_config import setup_logging

    setup_logging()
except ImportError:
    print("Warning: Logging configuration not available, using defaults")

# ✅ Set up log buffer for Claude AI access
import logging
from backend.api.services.log_buffer import log_buffer_handler

def setup_log_buffer():
    """Configure log buffer handler for Claude AI debugging access"""
    root_logger = logging.getLogger()
    
    # Add the log buffer handler to capture all logs
    root_logger.addHandler(log_buffer_handler)
    
    # Ensure we capture all log levels (the individual loggers can still filter)
    if root_logger.level > logging.DEBUG:
        root_logger.setLevel(logging.DEBUG)
    
    print("✅ Log buffer enabled for Claude AI access")

setup_log_buffer()

# ✅ Read configuration values from environment variables.
# These variables control the static file directory, the main HTML file, and allowed origins for CORS.
STATIC_DIR = os.getenv(
    "STATIC_DIR", "backend/static"
)  # Directory where static frontend files are served from. Defaults to "backend/static".
INDEX_FILE = os.getenv(
    "INDEX_FILE", "index.html"
)  # The main HTML file to serve. Defaults to "index.html".
# ✅ Production configuration
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
if DEBUG:
    print("⚠️  DEBUG MODE ENABLED - Not for production")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(
    ","
)  # A comma-separated list of allowed origins for CORS. Defaults to "*" (all origins).

# ✅ Create the FastAPI application instance.
app = FastAPI(
    title="Castellan API",
    description="""
    **Backend API for Castellan Board Game**
    
    A real-time multiplayer medieval strategy board game.
    
    ## Features
    
    * **Room Management** - Create and join game rooms
    * **Real-time Gameplay** - WebSocket-based real-time communication
    * **Game Logic** - Complete game flow with validation
    * **Event Sourcing** - Full game event history and recovery
    * **Health Monitoring** - Comprehensive health checks and metrics
    
    ## Game Flow
    
    1. **Lobby** - Players create/join rooms
    2. **Preparation** - Cards dealt, weak hand redeals
    3. **Declaration** - Players declare target pile counts
    4. **Turn Play** - Turn-based piece playing
    5. **Scoring** - Round scoring and win condition checks
    
    ## WebSocket Connection
    
    Connect to `ws://localhost:8000/ws/{room_id}` for real-time game events.
    Special lobby connection: `ws://localhost:8000/ws/lobby`
    """,
    version="1.0.0",
    contact={
        "name": "Castellan Development Team",
        "url": "https://github.com/your-org/castellan",
    },
    license_info={
        "name": "MIT",
    },
    tags_metadata=[
        {
            "name": "rooms",
            "description": "Room management operations - create, join, configure rooms",
        },
        {
            "name": "game",
            "description": "Core game operations - declarations, turns, scoring",
        },
        {
            "name": "events",
            "description": "Event sourcing and game state recovery",
        },
        {
            "name": "health",
            "description": "Health checks and system monitoring",
        },
        {
            "name": "recovery",
            "description": "System recovery and maintenance operations",
        },
        {
            "name": "debug",
            "description": "Debug endpoints for event store access and game replay",
        },
    ],
)

# ✅ Add CORS middleware to the application.
# This is crucial for allowing the frontend (running on a different origin) to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Specifies which origins are allowed to make requests.
    allow_credentials=True,  # Indicates that cookies/authentication headers can be sent with requests.
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.).
    allow_headers=["*"],  # Allows all HTTP headers.
)

# ✅ Add Rate Limiting middleware (if enabled)
# This protects the API from abuse and ensures fair usage
rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
if rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)
    print("Rate limiting is enabled")
else:
    print("WARNING: Rate limiting is disabled")

# ✅ Include the API and WebSocket routers.
# These routers define the specific endpoints and their handlers for the application.
app.include_router(
    api_router, prefix="/api"
)  # Mounts the REST API router under the "/api" prefix.
app.include_router(
    ws_router
)  # Mounts the WebSocket router at the root (or its defined paths).
app.include_router(debug_router)  # Mounts the debug router for event store access.

# ✅ Serve static files.
# This mounts the specified directory to the root path "/", meaning files like index.html, bundle.js, etc.,
# will be served directly from this directory. `html=True` ensures that `index.html` is served for root.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


# ✅ Optional fallback: Define a GET endpoint for the root path.
# This ensures that if the static files mount doesn't catch the root path for some reason,
# or for direct access, index.html is still served.
@app.get("/")
def read_index():
    """
    Serve the main index.html file.

    This is a fallback endpoint in case the static file mount
    doesn't catch the root path for some reason.

    Returns:
        FileResponse: The index.html file from the static directory
    """
    return FileResponse(os.path.join(STATIC_DIR, INDEX_FILE))


@app.on_event("startup")
async def startup_event():
    """
    Run startup tasks when the application starts.
    """
    # Start the room cleanup background task
    from backend.api.routes.ws import start_cleanup_task

    start_cleanup_task()
