# backend/api/routes/telemetry.py
"""
Minimal telemetry endpoint for receiving client-side bundle loading data.
This is a simplified version for the hybrid approach.
"""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

router = APIRouter(tags=["telemetry"])
logger = logging.getLogger(__name__)

class TelemetryPayload(BaseModel):
    sessionId: str
    events: List[Dict[str, Any]]

@router.post("/telemetry")
async def receive_telemetry(
    payload: TelemetryPayload
):
    """
    Receive telemetry data from clients (minimal implementation).
    
    This endpoint logs bundle loading errors and performance metrics
    to help diagnose mobile loading issues.
    """
    # Process synchronously for now to avoid issues
    try:
        for event in payload.events:
            event_type = event.get('event', 'unknown')
            
            # Focus on critical bundle loading events
            if event_type in ['bundle_error', 'load_timeout', 'load_failed']:
                logger.error(
                    f"Client bundle load failure: {event_type}",
                    extra={
                        'session_id': payload.sessionId,
                        'user_agent': event.get('userAgent', 'Unknown'),
                        'attempt': event.get('attempt', 1),
                        'load_time': event.get('loadTime'),
                        'connection': event.get('connection', {}),
                        'error': event.get('error', 'Unknown error')
                    }
                )
            elif event_type == 'bundle_load_success':
                logger.info(
                    f"Bundle loaded successfully",
                    extra={
                        'session_id': payload.sessionId,
                        'attempt': event.get('attempt', 1),
                        'load_time': event.get('loadTime'),
                        'connection': event.get('connection', {})
                    }
                )
            elif event_type == 'performance_metrics':
                logger.info(
                    f"Client performance metrics",
                    extra={
                        'session_id': payload.sessionId,
                        'transfer_size': event.get('transferSize'),
                        'encoded_size': event.get('encodedBodySize'),
                        'decoded_size': event.get('decodedBodySize'),
                        'duration': event.get('duration')
                    }
                )
    except Exception as e:
        logger.error(f"Failed to process telemetry: {str(e)}")
    
    return {"status": "accepted"}