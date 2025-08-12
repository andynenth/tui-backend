# backend/api/routes/play_history.py

from fastapi import APIRouter, HTTPException, Query, Request, Path
from typing import Optional, List
import time
import json
import logging
from backend.models.play_history import PlayHistoryResponse
from backend.models.error_responses import (
    ErrorResponse, create_error_response, create_validation_error_response,
    ErrorCodes
)
from backend.api.middleware.logging_middleware import PlayHistoryLoggingMiddleware
from backend.services.monitoring_service import play_history_metrics
from backend.services.alert_service import alert_service
from backend.api.docs.play_history_examples import (
    PLAY_HISTORY_FULL_EXAMPLE,
    PLAY_HISTORY_COMPACT_EXAMPLE,
    ERROR_ROOM_NOT_FOUND,
    ERROR_NO_ACTIVE_GAME,
    ERROR_INVALID_RANGE
)
import os

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/rooms/{room_id}/play-history", 
    response_model=PlayHistoryResponse,
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
                            "value": PLAY_HISTORY_FULL_EXAMPLE
                        },
                        "compact": {
                            "summary": "Compact response",
                            "description": "Minimal play history with summary data only (format=compact)",
                            "value": PLAY_HISTORY_COMPACT_EXAMPLE
                        }
                    }
                }
            }
        },
        404: {
            "model": ErrorResponse, 
            "description": "Room not found",
            "content": {
                "application/json": {
                    "example": ERROR_ROOM_NOT_FOUND
                }
            }
        },
        400: {
            "model": ErrorResponse, 
            "description": "Bad request - room has no active game",
            "content": {
                "application/json": {
                    "example": ERROR_NO_ACTIVE_GAME
                }
            }
        }
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
    """
)
async def get_play_history(
    request: Request,
    room_id: str = Path(..., description="The unique room identifier", example="ROOM123"),
    rounds: Optional[str] = Query(None, description="Comma-separated list of specific round numbers to retrieve", example="1,3,5"),
    include_hands: bool = Query(True, description="Include detailed hand information for each player"),
    include_ai_analysis: bool = Query(True, description="Include AI decision analysis and reasoning (AI players only)"),
    format: Optional[str] = Query(None, description="Response format", enum=["compact", "full"], example="compact"),
    player_focus: Optional[str] = Query(None, description="Focus on specific player (filter plays)", example="Player 1")
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
    from backend.shared_instances import shared_room_manager
    from backend.services.play_history_service import PlayHistoryService
    
    # Get request ID for logging
    request_id = getattr(request.state, 'request_id', None)
    
    # Log request details
    PlayHistoryLoggingMiddleware.log_play_history_request(
        room_id=room_id,
        rounds=rounds,
        include_hands=include_hands,
        include_ai_analysis=include_ai_analysis,
        format=format,
        request_id=request_id
    )
    
    # Start timing for performance monitoring
    start_time = time.time()
    
    # Always use v2 service now
    use_v2 = True
    
    # Create service based on configuration
    if use_v2:
        # Use v2 service for optimized performance
        from backend.services.play_history_v2 import PlayHistoryV2Service
        service = PlayHistoryV2Service()
        
        # Build history from v2
        play_history = await service.build_play_history(
            room_id=room_id,
            round_numbers=None,
            include_ai_analysis=include_ai_analysis,
            format=format
        )
        
        # Apply round filtering if specific rounds requested
        if rounds:
            # Parse comma-separated round numbers and filter
            round_numbers = [int(r.strip()) for r in rounds.split(",")]
            play_history.rounds = [r for r in play_history.rounds if r.round_number in round_numbers]
        
        # Update total rounds
        play_history.total_rounds = len(play_history.rounds)
        
        # Handle include_hands parameter with format interaction
        if format != "compact" and not include_hands:
            for round_data in play_history.rounds:
                round_data.hands_dealt = {}
        
        # Edge case: User wants compact format but WITH hands
        if format == "compact" and include_hands:
            # Re-fetch with full format to get hands
            full_history = await service.build_play_history(
                room_id=room_id,
                round_numbers=None,
                include_ai_analysis=include_ai_analysis,
                format=None
            )
            # Copy hands from full history
            for i, round_data in enumerate(play_history.rounds):
                if i < len(full_history.rounds):
                    round_data.hands_dealt = full_history.rounds[i].hands_dealt
        
        # The v2 service handles other parameters internally
        
    else:
        # Use v1 service (original logic)
        service = PlayHistoryService()
    
    # Check if room exists
    room = await shared_room_manager.get_room(room_id)
    
    if not room:
        # Room not in memory - try to get data from SQLite event store
        logger.info(f"Room {room_id} not in memory, attempting SQLite retrieval")
        
        # Create minimal game object for service interface
        from backend.engine.game import Game
        from backend.engine.player import Player
        
        # Create minimal players (will be overridden by event data)
        players = [
            Player("Player 1", is_bot=False),
            Player("Player 2", is_bot=True),
            Player("Player 3", is_bot=True),
            Player("Player 4", is_bot=True)
        ]
        
        minimal_game = Game(players)
        minimal_game.round_number = 0  # No rounds in memory
        minimal_game.current_phase = "WAITING"
        
        # Try to get history from SQLite
        play_history = await service.build_play_history(
            minimal_game, 
            room_id, 
            include_ai_analysis=include_ai_analysis, 
            format=format
        )
        
        # If no data found in SQLite either, then truly not found
        if play_history.total_rounds == 0:
            error_response, status_code = create_error_response(
                code=ErrorCodes.ROOM_NOT_FOUND,
                message=f"Room with ID '{room_id}' not found",
                status_code=404,
                context={"room_id": room_id},
                path=str(request.url.path)
            )
            # Pass the full error response as detail for our custom handler
            raise HTTPException(status_code=status_code, detail=error_response.model_dump())
    else:
        # Room exists in memory
        if not room.game:
            error_response, status_code = create_error_response(
                code=ErrorCodes.NO_ACTIVE_GAME,
                message=f"Room '{room_id}' has no active game",
                status_code=400,
                context={"room_id": room_id},
                path=str(request.url.path)
            )
            # Pass the full error response as detail for our custom handler
            raise HTTPException(status_code=status_code, detail=error_response.model_dump())
        
        # Build play history with actual game
        play_history = await service.build_play_history(
            room.game, 
            room_id, 
            include_ai_analysis=include_ai_analysis, 
            format=format
        )
    
        # Apply round filtering if specific rounds requested
        if rounds:
            # Parse comma-separated round numbers and filter
            # This reduces response size when only specific rounds are needed
            round_numbers = [int(r.strip()) for r in rounds.split(",")]
            play_history.rounds = [r for r in play_history.rounds if r.round_number in round_numbers]
        
        # Handle include_hands parameter with format interaction
        # Compact format excludes hands by default for efficiency
        # Full format includes hands by default but can be excluded
        if format != "compact" and not include_hands:
            # For non-compact format, remove hands if include_hands is false
            # This reduces response size by ~20-30% depending on game length
            for round_data in play_history.rounds:
                round_data.hands_dealt = {}
        
        # Edge case: User wants compact format but WITH hands
        # This is unusual but supported for flexibility
        if format == "compact" and include_hands:
            # Re-extract hands for each round (compact format excludes them by default)
            # For event store data, hands are already included if available
            # Only try to extract from memory if we have game data
            if hasattr(room, 'game') and room.game:
                from backend.services.play_history_service import PlayHistoryService
                temp_service = PlayHistoryService()
                for round_data in play_history.rounds:
                    if not round_data.hands_dealt:  # Only if not already populated
                        hands = temp_service.extract_hands_dealt(room.game, round_data.round_number)
                        round_data.hands_dealt = hands
        
        if not include_ai_analysis:
            # Remove AI analysis to reduce response size and improve performance
            # AI analysis can add significant size for games with many AI players
            for round_data in play_history.rounds:
                for turn in round_data.turn_history:
                    for play in turn.plays:
                        play.ai_decision_analysis = None
    
    # Calculate performance metrics for monitoring
    # Build time includes all extraction and filtering operations
    build_time_ms = (time.time() - start_time) * 1000
    # Response size helps track the effectiveness of compact format and filtering
    response_size = len(play_history.model_dump_json())
    
    # Log response metrics
    PlayHistoryLoggingMiddleware.log_play_history_response(
        room_id=room_id,
        total_rounds=play_history.total_rounds,
        response_size=response_size,
        build_time_ms=build_time_ms,
        request_id=request_id
    )
    
    # Log performance warnings for slow responses
    # This helps identify performance bottlenecks and optimization opportunities
    if build_time_ms > 1000:
        PlayHistoryLoggingMiddleware.log_performance_warning(
            warning_type="slow_play_history_build",
            details={
                "room_id": room_id,
                "total_rounds": play_history.total_rounds,
                "build_time_ms": build_time_ms
            },
            request_id=request_id
        )
    
    # Check for performance alerts
    alert_service.check_response_time(
        operation="play_history",
        duration_ms=build_time_ms,
        context={
            "room_id": room_id,
            "total_rounds": play_history.total_rounds,
            "response_size_bytes": response_size,
            "include_hands": include_hands,
            "include_ai_analysis": include_ai_analysis,
            "format": format or "full",
            "request_id": request_id
        }
    )
    
    # Record specialized play history metrics
    play_history_metrics.record_play_history_request(
        room_id=room_id,
        total_rounds=play_history.total_rounds,
        response_size=response_size,
        build_time_ms=build_time_ms,
        format=format or "full"
    )
    
    return play_history


@router.get("/rooms/{room_id}/play-history/round/{round_number}")
async def get_round_history(
    room_id: str,
    round_number: int,
    include_hands: bool = Query(True),
    include_ai_analysis: bool = Query(True)
):
    """Get play history for a specific round."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get(
    "/rooms/{room_id}/play-history/rounds", 
    response_model=PlayHistoryResponse,
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
                            "value": PLAY_HISTORY_FULL_EXAMPLE
                        }
                    }
                }
            }
        },
        404: {
            "model": ErrorResponse, 
            "description": "Room not found",
            "content": {
                "application/json": {
                    "example": ERROR_ROOM_NOT_FOUND
                }
            }
        },
        400: {
            "model": ErrorResponse, 
            "description": "Bad request - invalid range or no active game",
            "content": {
                "application/json": {
                    "example": ERROR_INVALID_RANGE
                }
            }
        },
        422: {
            "model": ErrorResponse, 
            "description": "Validation error - invalid parameters"
        }
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
    """
)
async def get_rounds_range(
    request: Request,
    room_id: str = Path(..., description="The unique room identifier", example="ROOM123"),
    from_round: int = Query(1, alias="from", ge=1, description="Starting round number (inclusive)", example=1),
    to_round: int = Query(..., alias="to", ge=1, description="Ending round number (inclusive)", example=5),
    include_hands: bool = Query(True, description="Include detailed hand information for each player"),
    include_ai_analysis: bool = Query(True, description="Include AI decision analysis and reasoning (AI players only)"),
    format: Optional[str] = Query(None, description="Response format", enum=["compact", "full"], example="compact")
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
            path=str(request.url.path)
        )
        # Pass the full error response as detail for our custom handler
        raise HTTPException(status_code=status_code, detail=error_response.model_dump())
    
    from backend.shared_instances import shared_room_manager
    from backend.services.play_history_service import PlayHistoryService
    
    # Get request ID for logging
    request_id = getattr(request.state, 'request_id', None)
    
    logger.info(
        "Play history range request",
        extra={
            "request_id": request_id,
            "room_id": room_id,
            "from_round": from_round,
            "to_round": to_round,
            "format": format
        }
    )
    
    start_time = time.time()
    
    # Always use v2 service now
    use_v2 = True
    
    # Create service based on configuration
    if use_v2:
        # Use v2 service for optimized performance
        from backend.services.play_history_v2 import PlayHistoryV2Service
        service = PlayHistoryV2Service()
        
        # Build history from v2 with round range
        round_numbers = list(range(from_round, to_round + 1))
        play_history = await service.build_play_history(
            room_id=room_id,
            round_numbers=round_numbers,
            include_ai_analysis=include_ai_analysis,
            format=format
        )
        
        # Update total rounds
        play_history.total_rounds = len(play_history.rounds)
        
        # Handle include_hands parameter with format interaction
        if format != "compact" and not include_hands:
            for round_data in play_history.rounds:
                round_data.hands_dealt = {}
        
        # Edge case: User wants compact format but WITH hands
        if format == "compact" and include_hands:
            # Re-fetch with full format to get hands
            full_history = await service.build_play_history(
                room_id=room_id,
                round_numbers=None,
                include_ai_analysis=include_ai_analysis,
                format=None
            )
            # Copy hands from full history
            for i, round_data in enumerate(play_history.rounds):
                if i < len(full_history.rounds):
                    round_data.hands_dealt = full_history.rounds[i].hands_dealt
        
        # The v2 service handles other parameters internally
        
    else:
        # Use v1 service (original logic)
        service = PlayHistoryService()
        
        # Check if room exists
        room = await shared_room_manager.get_room(room_id)
        
        if not room:
            # Room not in memory - try to get data from SQLite event store
            logger.info(f"Room {room_id} not in memory, attempting SQLite retrieval for range")
            
            # Create minimal game object for service interface
            from backend.engine.game import Game
            from backend.engine.player import Player
            
            # Create minimal players (will be overridden by event data)
            players = [
                Player("Player 1", is_bot=False),
                Player("Player 2", is_bot=True),
                Player("Player 3", is_bot=True),
                Player("Player 4", is_bot=True)
            ]
            
            minimal_game = Game(players)
            minimal_game.round_number = 0  # No rounds in memory
            minimal_game.current_phase = "WAITING"
            
            # Try to get history from SQLite
            play_history = await service.build_play_history(
                minimal_game, 
                room_id, 
                include_ai_analysis=include_ai_analysis, 
                format=format
            )
            
            # If no data found in SQLite either, then truly not found
            if play_history.total_rounds == 0:
                error_response, status_code = create_error_response(
                    code=ErrorCodes.ROOM_NOT_FOUND,
                    message=f"Room with ID '{room_id}' not found",
                    status_code=404,
                    context={"room_id": room_id},
                    path=str(request.url.path)
                )
                # Pass the full error response as detail for our custom handler
                raise HTTPException(status_code=status_code, detail=error_response.model_dump())
        else:
            # Room exists in memory
            if not room.game:
                error_response, status_code = create_error_response(
                    code=ErrorCodes.NO_ACTIVE_GAME,
                    message=f"Room '{room_id}' has no active game",
                    status_code=400,
                    context={"room_id": room_id},
                    path=str(request.url.path)
                )
                # Pass the full error response as detail for our custom handler
                raise HTTPException(status_code=status_code, detail=error_response.model_dump())
            
            # Build play history with actual game
            play_history = await service.build_play_history(
                room.game, 
                room_id, 
                include_ai_analysis=include_ai_analysis, 
                format=format
            )
    
    # Filter to only include rounds in the requested range
    # This is more efficient than parsing comma-separated values
    # for contiguous ranges of rounds
    filtered_rounds = []
    for round_data in play_history.rounds:
        if from_round <= round_data.round_number <= to_round:
            filtered_rounds.append(round_data)
    
    # Update the response with filtered rounds
    play_history.rounds = filtered_rounds
    play_history.total_rounds = len(filtered_rounds)
    
    # Apply include_hands parameter
    if format != "compact" and not include_hands:
        for round_data in play_history.rounds:
            round_data.hands_dealt = {}
    
    # Handle compact format with hands
    if format == "compact" and include_hands:
        # For event store data, hands are already included if available
        # Only try to extract from memory if we have game data
        if hasattr(room, 'game') and room.game:
            from backend.services.play_history_service import PlayHistoryService
            temp_service = PlayHistoryService()
            for round_data in play_history.rounds:
                if not round_data.hands_dealt:  # Only if not already populated
                    hands = temp_service.extract_hands_dealt(room.game, round_data.round_number)
                    round_data.hands_dealt = hands
    
    if not include_ai_analysis:
        for round_data in play_history.rounds:
            for turn in round_data.turn_history:
                for play in turn.plays:
                    play.ai_decision_analysis = None
    
    # Calculate build time for monitoring
    build_time_ms = (time.time() - start_time) * 1000
    
    # Check for performance alerts
    alert_service.check_response_time(
        operation="play_history_range",
        duration_ms=build_time_ms,
        context={
            "room_id": room_id,
            "from_round": from_round,
            "to_round": to_round,
            "total_rounds": len(filtered_rounds),
            "include_hands": include_hands,
            "include_ai_analysis": include_ai_analysis,
            "format": format or "full",
            "request_id": request_id
        }
    )
    
    return play_history