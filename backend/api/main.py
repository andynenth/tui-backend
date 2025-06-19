# backend/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.api.routes.routes import router as api_router
from backend.api.routes.ws import router as ws_router
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import logging

# Set up logging
logger = logging.getLogger(__name__)

# ✅ Load environment variables from the .env file
load_dotenv()

# ✅ Read configuration values from environment variables
STATIC_DIR = os.getenv("STATIC_DIR", "backend/static")
INDEX_FILE = os.getenv("INDEX_FILE", "index.html")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")


# ✅ Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - startup and shutdown events.
    This replaces the deprecated @app.on_event decorators.
    """
    # ===== STARTUP LOGIC =====
    logger.info("🚀 Starting Liap Tui backend...")
    
    # If you have any startup logic (like dependency wiring), add it here:
    try:
        # Example: If you need to wire up dependencies
        # from backend.shared_instances import get_bot_manager, get_game_controller
        # bot_manager = get_bot_manager()
        # bot_manager.set_game_controller_getter(get_game_controller)
        # logger.info("✅ Dependencies wired")
        
        # For now, just log that we started
        logger.info("✅ Backend started successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    # This yield is important! The app runs while yielded
    yield
    
    # ===== SHUTDOWN LOGIC =====
    logger.info("🛑 Shutting down Liap Tui backend...")
    
    # If you have any cleanup logic, add it here:
    try:
        # Example: Close database connections, cleanup resources
        # await database.disconnect()
        # await cache.close()
        
        logger.info("✅ Backend shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# ✅ Create the FastAPI application instance with lifespan
app = FastAPI(
    title="Liap Tui API",
    description="Backend API for Liap Tui Board Game",
    version="1.0",
    lifespan=lifespan  # ← This is the key change!
)

# ✅ Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include the API and WebSocket routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

# ✅ Serve static files
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# ✅ Optional fallback: Define a GET endpoint for the root path
@app.get("/")
def read_index():
    return FileResponse(os.path.join(STATIC_DIR, INDEX_FILE))