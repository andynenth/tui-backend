# backend/api/routes/debug.py

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.api.services.event_store import event_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/events/{room_id}")
async def get_room_events(
    room_id: str,
    limit: Optional[int] = Query(None, description="Limit number of events returned"),
    event_type: Optional[str] = Query(None, description="Filter by event type")
):
    """
    List all events for a room, optionally filtered by type
    
    Args:
        room_id: The room identifier
        limit: Optional limit on number of events
        event_type: Optional event type filter
        
    Returns:
        List of events with metadata
    """
    try:
        if event_type:
            # Get filtered events
            events = await event_store.get_events_by_type(room_id, event_type, limit)
        else:
            # Get all events
            events = await event_store.get_room_events(room_id, limit)
        
        # Convert events to JSON-serializable format
        event_list = []
        for event in events:
            event_list.append({
                "sequence": event.sequence,
                "event_type": event.event_type,
                "player_id": event.player_id,
                "timestamp": event.timestamp,
                "created_at": event.created_at,
                "payload": event.payload
            })
        
        # Get event statistics
        stats = await event_store.get_event_stats()
        room_stats = stats.get("room_stats", {}).get(room_id, 0)
        
        return {
            "room_id": room_id,
            "total_events": len(event_list),
            "room_total_events": room_stats,
            "events": event_list,
            "filter": {
                "event_type": event_type,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving events for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/replay/{room_id}")
async def replay_room_state(room_id: str):
    """
    Replay and show reconstructed state from events
    
    Args:
        room_id: The room identifier
        
    Returns:
        Reconstructed game state from events
    """
    try:
        # Replay the room state
        state = await event_store.replay_room_state(room_id)
        
        # Validate event sequence
        validation = await event_store.validate_event_sequence(room_id)
        
        # Get event statistics
        events = await event_store.get_room_events(room_id)
        event_types = {}
        for event in events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        return {
            "room_id": room_id,
            "reconstructed_state": state,
            "validation": validation,
            "statistics": {
                "total_events": len(events),
                "event_types": event_types,
                "first_event": events[0].created_at if events else None,
                "last_event": events[-1].created_at if events else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error replaying state for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{room_id}/sequence/{seq}")
async def get_events_since_sequence(
    room_id: str,
    seq: int,
    limit: Optional[int] = Query(None, description="Limit number of events returned")
):
    """
    Get events since a specific sequence number
    
    Args:
        room_id: The room identifier
        seq: Sequence number to start from (exclusive)
        limit: Optional limit on number of events
        
    Returns:
        Events after the specified sequence
    """
    try:
        # Get events since sequence
        events = await event_store.get_events_since(room_id, seq)
        
        # Apply limit if specified
        if limit and len(events) > limit:
            events = events[:limit]
        
        # Convert to JSON format
        event_list = []
        for event in events:
            event_list.append({
                "sequence": event.sequence,
                "event_type": event.event_type,
                "player_id": event.player_id,
                "timestamp": event.timestamp,
                "created_at": event.created_at,
                "payload": event.payload
            })
        
        return {
            "room_id": room_id,
            "since_sequence": seq,
            "events_returned": len(event_list),
            "events": event_list,
            "latest_sequence": event_list[-1]["sequence"] if event_list else seq
        }
        
    except Exception as e:
        logger.error(f"Error retrieving events since sequence {seq} for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{room_id}")
async def export_room_history(room_id: str):
    """
    Export complete room history for debugging
    
    Args:
        room_id: The room identifier
        
    Returns:
        Complete room history with timeline and analysis
    """
    try:
        history = await event_store.export_room_history(room_id)
        return history
        
    except Exception as e:
        logger.error(f"Error exporting history for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_event_statistics():
    """
    Get overall event store statistics
    
    Returns:
        Event store statistics including rooms, event types, and counts
    """
    try:
        stats = await event_store.get_event_stats()
        health = await event_store.health_check()
        
        return {
            "health": health,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error retrieving event statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/turns/{room_id}")
async def get_turn_plays(
    room_id: str,
    turn_number: Optional[int] = Query(None, description="Specific turn number to retrieve"),
    player_name: Optional[str] = Query(None, description="Filter by player name")
):
    """
    Get turn play history for a room in a user-friendly format
    
    Args:
        room_id: The room identifier
        turn_number: Optional specific turn number (if not provided, returns all turns)
        player_name: Optional player name filter
        
    Returns:
        Structured turn play data
    """
    try:
        # Get all turn_play events for the room
        events = await event_store.get_events_by_type(room_id, "turn_play")
        
        # Group plays by turn
        turns = {}
        for event in events:
            payload = event.payload
            turn_num = payload.get("turn_number", 0)
            
            if turn_num not in turns:
                turns[turn_num] = {
                    "turn_number": turn_num,
                    "plays": [],
                    "winner": None,
                    "total_pieces": 0
                }
            
            # Extract play data
            play_data = {
                "player": event.player_id,
                "pieces_count": payload.get("pieces_count", 0),
                "play_type": payload.get("play_type", "UNKNOWN"),
                "play_value": payload.get("play_value", 0),
                "pieces": payload.get("pieces", []),
                "valid": payload.get("valid", False),
                "timestamp": event.timestamp
            }
            
            # Apply player filter if specified
            if player_name and play_data["player"] != player_name:
                continue
                
            turns[turn_num]["plays"].append(play_data)
            turns[turn_num]["total_pieces"] += play_data["pieces_count"]
            
            # Track winner if this play won
            if payload.get("won_turn"):
                turns[turn_num]["winner"] = event.player_id
        
        # Get turn results to identify winners
        result_events = await event_store.get_events_by_type(room_id, "turn_result")
        for event in result_events:
            payload = event.payload
            turn_num = payload.get("turn_number", 0)
            if turn_num in turns:
                turns[turn_num]["winner"] = payload.get("winner")
                turns[turn_num]["piles_won"] = payload.get("piles_won", 0)
        
        # Convert to list and sort by turn number
        turn_list = sorted(turns.values(), key=lambda x: x["turn_number"])
        
        # Filter by turn number if specified
        if turn_number is not None:
            turn_list = [t for t in turn_list if t["turn_number"] == turn_number]
        
        return {
            "room_id": room_id,
            "total_turns": len(turn_list),
            "filter": {
                "turn_number": turn_number,
                "player_name": player_name
            },
            "turns": turn_list
        }
        
    except Exception as e:
        logger.error(f"Error retrieving turn plays for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_events(
    older_than_hours: int = Query(24, description="Remove events older than this many hours")
):
    """
    Clean up old events from storage
    
    Args:
        older_than_hours: Age threshold for event removal
        
    Returns:
        Number of events removed
    """
    try:
        if older_than_hours < 1:
            raise HTTPException(status_code=400, detail="Age threshold must be at least 1 hour")
        
        deleted_count = await event_store.cleanup_old_events(older_than_hours)
        
        return {
            "success": True,
            "deleted_events": deleted_count,
            "older_than_hours": older_than_hours
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate/{room_id}")
async def validate_room_events(room_id: str):
    """
    Validate event sequence integrity for a room
    
    Args:
        room_id: The room identifier
        
    Returns:
        Validation results including any gaps or issues
    """
    try:
        validation = await event_store.validate_event_sequence(room_id)
        
        # Get additional diagnostics if invalid
        if not validation["valid"]:
            events = await event_store.get_room_events(room_id)
            
            # Find duplicate sequences
            sequence_counts = {}
            for event in events:
                seq = event.sequence
                sequence_counts[seq] = sequence_counts.get(seq, 0) + 1
            
            duplicates = {seq: count for seq, count in sequence_counts.items() if count > 1}
            
            validation["diagnostics"] = {
                "duplicate_sequences": duplicates,
                "total_unique_sequences": len(sequence_counts)
            }
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating events for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))