# backend/api/routes/play_history.py

from fastapi import APIRouter, HTTPException, Query, Request, Path
from typing import Optional, List
import time
import json
import logging
from backend.models.play_history import PlayHistoryResponse
from backend.models.error_responses import (
    ErrorResponse,
    create_error_response,
    create_validation_error_response,
    ErrorCodes,
)
from backend.api.middleware.logging_middleware import PlayHistoryLoggingMiddleware
from backend.services.monitoring_service import play_history_metrics
from backend.services.alert_service import alert_service
from backend.api.docs.play_history_examples import (
    PLAY_HISTORY_FULL_EXAMPLE,
    PLAY_HISTORY_COMPACT_EXAMPLE,
    ERROR_ROOM_NOT_FOUND,
    ERROR_NO_ACTIVE_GAME,
    ERROR_INVALID_RANGE,
)
import os

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/rooms/{room_id}/play-history",
    response_model=None,  # Allow dict response for frontend format
    response_model_exclude_none=True,
    responses={
        200: {
            "description": "Successful response with play history",
            "content": {
                "application/json": {
                    "examples": {
                        "full": {
                            "summary": "Full response with all details",
                            "description": "Complete play history including hands, AI analysis, and full turn details",
                            "value": PLAY_HISTORY_FULL_EXAMPLE,
                        },
                        "compact": {
                            "summary": "Compact response",
                            "description": "Minimal play history with summary data only (format=compact)",
                            "value": PLAY_HISTORY_COMPACT_EXAMPLE,
                        },
                    }
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Room not found",
            "content": {"application/json": {"example": ERROR_ROOM_NOT_FOUND}},
        },
        400: {
            "model": ErrorResponse,
            "description": "Bad request - room has no active game",
            "content": {"application/json": {"example": ERROR_NO_ACTIVE_GAME}},
        },
    },
    tags=["game", "monitoring"],
    summary="Get complete play history for a room",
    description="""
    Retrieve comprehensive play history for all rounds in a game room.

    This endpoint provides detailed information about game progression including:
    - Player information and types (human vs AI)
    - Initial game state and starter determination
    - Hands dealt to each player (sorted by color then value)
    - Declaration phase with each player's target
    - Turn-by-turn play history with hand states
    - Scoring calculations and cumulative scores
    - AI decision analysis and reasoning (optional)

    **Performance Notes:**
    - Alerts trigger if response time exceeds 1s (warning) or 3s (critical)
    - Use `format=compact` for reduced response size
    - Use `include_hands=false` to exclude hand details
    - Use `include_ai_analysis=false` to exclude AI reasoning

    **Authentication:** None required (public endpoint)

    **Rate Limiting:** 100 requests per minute per IP
    """,
)
async def get_play_history(
    request: Request,
    room_id: str = Path(
        ..., description="The unique room identifier", example="ROOM123"
    ),
    rounds: Optional[str] = Query(
        None,
        description="Comma-separated list of specific round numbers to retrieve",
        example="1,3,5",
    ),
    include_hands: bool = Query(
        True, description="Include detailed hand information for each player"
    ),
    include_ai_analysis: bool = Query(
        True, description="Include AI decision analysis and reasoning (AI players only)"
    ),
    format: Optional[str] = Query(
        None, description="Response format", enum=["compact", "full"], example="compact"
    ),
    player_focus: Optional[str] = Query(
        None, description="Focus on specific player (filter plays)", example="Player 1"
    ),
):
    """
    Get complete play history for a room.

    This endpoint is the primary way to retrieve game history for analysis.
    It provides comprehensive data about game progression, player decisions,
    and outcomes. The data can be used for:
    - AI behavior analysis and improvement
    - Player strategy understanding
    - Game balance verification
    - Debugging and issue investigation

    Query Parameters:
        rounds: Filter to specific rounds (e.g., "1,3,5" for rounds 1, 3, and 5)
        include_hands: Set to false to exclude hand details (reduces response size)
        include_ai_analysis: Set to false to exclude AI reasoning data
        format: Use "compact" for minimal response (30-50% smaller)
        player_focus: Filter plays to show only a specific player (not implemented)

    Performance Notes:
        - Response time monitored with alerts at 1s (warning) and 3s (critical)
        - Use compact format for better performance with large games
        - Specific round filtering is more efficient than fetching all rounds

    Returns:
        PlayHistoryResponse with complete game history

    Raises:
        404: Room not found
        400: Room has no active game
    """
    from backend.services.play_history_db import play_history_db_service

    # Get request ID for logging
    request_id = getattr(request.state, "request_id", None)

    # Log request details
    PlayHistoryLoggingMiddleware.log_play_history_request(
        room_id=room_id,
        rounds=rounds,
        include_hands=include_hands,
        include_ai_analysis=include_ai_analysis,
        format=format,
        request_id=request_id,
    )

    # Start timing for performance monitoring
    start_time = time.time()

    # Get play history in simplified frontend format
    simplified_data = await play_history_db_service.get_play_history(room_id)

    if not simplified_data:
        error_response, status_code = create_error_response(
            code=ErrorCodes.ROOM_NOT_FOUND,
            message=f"Room with ID '{room_id}' not found or has no game history",
            status_code=404,
            context={"room_id": room_id},
            path=str(request.url.path),
        )
        raise HTTPException(status_code=status_code, detail=error_response.model_dump())

    # Return simplified format directly
    return simplified_data


@router.get("/rooms/{room_id}/play-history/round/{round_number}")
async def get_round_history(
    room_id: str,
    round_number: int,
    include_hands: bool = Query(True),
    include_ai_analysis: bool = Query(True),
):
    """Get play history for a specific round."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get(
    "/rooms/{room_id}/play-history/rounds",
    response_model=None,  # Allow dict response for frontend format
    response_model_exclude_none=True,
    responses={
        200: {
            "description": "Successful response with play history for specified rounds",
            "content": {
                "application/json": {
                    "examples": {
                        "range": {
                            "summary": "Rounds 1-2 response",
                            "description": "Play history for rounds 1 through 2",
                            "value": PLAY_HISTORY_FULL_EXAMPLE,
                        }
                    }
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Room not found",
            "content": {"application/json": {"example": ERROR_ROOM_NOT_FOUND}},
        },
        400: {
            "model": ErrorResponse,
            "description": "Bad request - invalid range or no active game",
            "content": {"application/json": {"example": ERROR_INVALID_RANGE}},
        },
        422: {
            "model": ErrorResponse,
            "description": "Validation error - invalid parameters",
        },
    },
    tags=["game", "monitoring"],
    summary="Get play history for a specific range of rounds",
    description="""
    Retrieve play history for a specific range of rounds in a game.

    This endpoint is optimized for fetching historical data for specific rounds,
    useful for reviewing particular game segments or analyzing specific rounds.

    **Usage Examples:**
    - Get rounds 1-5: `/api/rooms/ROOM123/play-history/rounds?from=1&to=5`
    - Get single round: `/api/rooms/ROOM123/play-history/rounds?from=3&to=3`
    - Get compact format: Add `&format=compact`

    **Performance Notes:**
    - More efficient than filtering with the main endpoint for large games
    - Missing rounds within the range are silently skipped
    - Alerts trigger if response time exceeds thresholds

    **Authentication:** None required (public endpoint)

    **Rate Limiting:** 100 requests per minute per IP
    """,
)
async def get_rounds_range(
    request: Request,
    room_id: str = Path(
        ..., description="The unique room identifier", example="ROOM123"
    ),
    from_round: int = Query(
        1,
        alias="from",
        ge=1,
        description="Starting round number (inclusive)",
        example=1,
    ),
    to_round: int = Query(
        ..., alias="to", ge=1, description="Ending round number (inclusive)", example=5
    ),
    include_hands: bool = Query(
        True, description="Include detailed hand information for each player"
    ),
    include_ai_analysis: bool = Query(
        True, description="Include AI decision analysis and reasoning (AI players only)"
    ),
    format: Optional[str] = Query(
        None, description="Response format", enum=["compact", "full"], example="compact"
    ),
):
    """Get play history for a range of rounds.

    This endpoint is optimized for fetching a contiguous range of rounds,
    which is more efficient than using the main endpoint with comma-separated
    round numbers for sequential rounds.

    Use Cases:
        - Review specific game segments (e.g., rounds 5-10)
        - Analyze game progression over time
        - Debug issues that occurred in specific rounds

    Performance:
        More efficient than the main endpoint for sequential rounds
        due to simplified filtering logic.
    """
    if from_round > to_round:
        error_response, status_code = create_error_response(
            code=ErrorCodes.INVALID_RANGE,
            message="'from' must be less than or equal to 'to'",
            status_code=400,
            field="from",
            context={"from": from_round, "to": to_round},
            path=str(request.url.path),
        )
        # Pass the full error response as detail for our custom handler
        raise HTTPException(status_code=status_code, detail=error_response.model_dump())

    # TODO: Implement using play_history_db service with round filtering
    raise HTTPException(status_code=501, detail="Not implemented yet")
