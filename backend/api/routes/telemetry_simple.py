# backend/api/routes/telemetry_simple.py
"""
Simplified telemetry endpoint for testing
"""

from fastapi import APIRouter
import logging

router = APIRouter(tags=["telemetry"])
logger = logging.getLogger(__name__)

@router.post("/api/telemetry")
async def receive_telemetry(payload: dict):
    """Receive telemetry data - simplified version"""
    try:
        logger.info(f"Received telemetry: {payload}")
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Telemetry error: {str(e)}")
        return {"status": "error", "message": str(e)}