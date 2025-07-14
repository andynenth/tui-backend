# backend/api/routes/__init__.py

# Import the individual routers from the 'routes' and 'ws' modules.
# These routers contain specific API endpoints (REST) and WebSocket routes.
from .routes import (
    router as api_router,
)  # Imports the router for RESTful API endpoints.
from .ws import router as ws_router  # Imports the router for WebSocket communication.
from fastapi import (
    APIRouter,
)  # Imports APIRouter from FastAPI to create a new router instance.

# Create a new top-level APIRouter instance.
# This router will act as a central point to include other sub-routers,
# allowing for a more organized structure of API endpoints.
router = APIRouter()

# Include the REST API router into the main router.
# All endpoints defined in `backend.api.routes.routes.py` will now be accessible
# through this `router` instance.
router.include_router(api_router)

# Include the WebSocket router into the main router.
# All WebSocket routes defined in `backend.api.routes.ws.py` will now be accessible
# through this `router` instance.
router.include_router(ws_router)
