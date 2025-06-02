# backend/api/routes/__init__.py

from .routes import router as api_router
from .ws import router as ws_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(api_router)
router.include_router(ws_router)
