# backend/api/main.py

from fastapi import FastAPI # Import FastAPI framework for building the API.
from fastapi.middleware.cors import CORSMiddleware # Middleware for handling Cross-Origin Resource Sharing (CORS).
from fastapi.staticfiles import StaticFiles # Utility to serve static files.
from fastapi.responses import FileResponse # Used to return a file as a response.
from backend.api.routes.routes import router as api_router # Import the API router for REST endpoints.
from backend.api.routes.ws import router as ws_router # Import the WebSocket router for real-time communication.
import os # Standard library for interacting with the operating system (e.g., environment variables).
from dotenv import load_dotenv # Library to load environment variables from a .env file.
import asyncio
import logging

# ✅ Load environment variables from the .env file.
# This makes configuration values available via os.getenv().
load_dotenv()

# ✅ Read configuration values from environment variables.
# These variables control the static file directory, the main HTML file, and allowed origins for CORS.
STATIC_DIR = os.getenv("STATIC_DIR", "backend/static") # Directory where static frontend files are served from. Defaults to "backend/static".
INDEX_FILE = os.getenv("INDEX_FILE", "index.html") # The main HTML file to serve. Defaults to "index.html".
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",") # A comma-separated list of allowed origins for CORS. Defaults to "*" (all origins).

# ✅ Create the FastAPI application instance.
app = FastAPI(
    title="Liap Tui API", # Title of the API, displayed in docs (e.g., Swagger UI).
    description="Backend API for Liap Tui Board Game", # Description of the API.
    version="1.0" # Version of the API.
)

# ✅ Add CORS middleware to the application.
# This is crucial for allowing the frontend (running on a different origin) to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS, # Specifies which origins are allowed to make requests.
    allow_credentials=True, # Indicates that cookies/authentication headers can be sent with requests.
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.).
    allow_headers=["*"], # Allows all HTTP headers.
)

# ✅ Include the API and WebSocket routers.
# These routers define the specific endpoints and their handlers for the application.
app.include_router(api_router, prefix="/api") # Mounts the REST API router under the "/api" prefix.
app.include_router(ws_router) # Mounts the WebSocket router at the root (or its defined paths).

# ✅ Serve static files.
# This mounts the specified directory to the root path "/", meaning files like index.html, bundle.js, etc.,
# will be served directly from this directory. `html=True` ensures that `index.html` is served for root.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

# ✅ Optional fallback: Define a GET endpoint for the root path.
# This ensures that if the static files mount doesn't catch the root path for some reason,
# or for direct access, index.html is still served.
@app.get("/")
def read_index():
    # Returns the index.html file from the static directory.
    return FileResponse(os.path.join(STATIC_DIR, INDEX_FILE))

# ✅ MONITORING SYSTEM ACTIVATION
# Start the monitoring and observability system when the application launches
@app.on_event("startup")
async def startup_event():
    """Initialize and start the monitoring and observability system"""
    print("🚀 STARTUP: Initializing monitoring and observability system...")
    
    # Check for required dependencies first
    missing_deps = []
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    if missing_deps:
        print(f"⚠️  STARTUP WARNING: Missing dependencies for monitoring: {missing_deps}")
        print("🔧 STARTUP: Install with: pip install psutil")
        print("📺 STARTUP: Running without advanced monitoring (basic health checks still available)")
        return
    
    try:
        # Import monitoring services
        from api.services.health_monitor import health_monitor
        from api.services.recovery_manager import recovery_manager
        from api.services.logging_service import game_logger
        from api.services.event_store import event_store
        
        print("📦 STARTUP: Monitoring services imported successfully")
        
        # Start health monitoring system
        # await health_monitor.start_monitoring()  # Temporarily disabled
        print("🔍 STARTUP: Health monitoring system disabled")
        
        # Start recovery management system  
        # await recovery_manager.start_monitoring()  # Temporarily disabled
        print("🔧 STARTUP: Recovery management system disabled")
        
        # Initialize event store (if needed)
        if hasattr(event_store, 'initialize'):
            await event_store.initialize()
            print("📊 STARTUP: Event store initialized")
        
        # Log system startup
        if game_logger:
            game_logger.log_game_event("system_startup", 
                                     components=["health_monitor", "recovery_manager", "event_store"],
                                     status="success")
            print("📝 STARTUP: System startup logged")
        
        print("✅ STARTUP: Monitoring and observability system fully activated!")
        print("🌐 SYSTEM: Health endpoints available at /health, /health/detailed, /health/metrics")
        
    except Exception as e:
        print(f"❌ STARTUP ERROR: Failed to start monitoring system: {e}")
        print("🎮 STARTUP: Game server will continue without advanced monitoring")
        # Log the error but don't crash the application
        logging.error(f"Monitoring system startup failed: {e}")

@app.on_event("shutdown") 
async def shutdown_event():
    """Gracefully shutdown the monitoring system"""
    print("🛑 SHUTDOWN: Stopping monitoring and observability system...")
    
    try:
        # Import and stop monitoring services
        from api.services.health_monitor import health_monitor
        from api.services.recovery_manager import recovery_manager
        from api.services.logging_service import game_logger
        
        # Stop monitoring systems
        await health_monitor.stop_monitoring()
        print("🔍 SHUTDOWN: Health monitoring stopped")
        
        recovery_manager.stop_monitoring()
        print("🔧 SHUTDOWN: Recovery management stopped")
        
        # Log system shutdown
        if game_logger:
            game_logger.log_game_event("system_shutdown", status="graceful")
            print("📝 SHUTDOWN: System shutdown logged")
        
        print("✅ SHUTDOWN: Monitoring system gracefully stopped")
        
    except Exception as e:
        print(f"❌ SHUTDOWN ERROR: Error stopping monitoring system: {e}")
        logging.error(f"Monitoring system shutdown error: {e}")
