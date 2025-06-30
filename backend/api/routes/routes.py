# backend/api/routes/routes.py

import asyncio
import time
from fastapi import APIRouter, HTTPException, Query
from engine.game import Game
from engine.rules import is_valid_play, get_play_type
from engine.win_conditions import is_game_over, get_winners
from backend.socket_manager import broadcast
from backend.shared_instances import shared_room_manager, shared_bot_manager
from engine.state_machine.core import ActionType, GameAction
from typing import Optional, List, Dict, Any
import backend.socket_manager

# Import EventStore for recovery endpoints
try:
    from api.services.event_store import event_store
    EVENT_STORE_AVAILABLE = True
except ImportError:
    EVENT_STORE_AVAILABLE = False
    event_store = None

print(f"socket_manager id in {__name__}: {id(backend.socket_manager)}")

# Global instances - REMOVED: RedealController (using state machine instead)
router = APIRouter()
room_manager = shared_room_manager
bot_manager = shared_bot_manager

# REMOVED: All redeal controller endpoints - state machine handles redeal logic

# ---------- ROOM MANAGEMENT ----------

@router.get("/get-room-state")
async def get_room_state(room_id: str = Query(...)):
    """
    Retrieves the current state of a specific game room.
    """
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room.summary()

@router.post("/create-room")
async def create_room(name: str = Query(...)):
    """
    Creates a new game room and notifies lobby clients.
    """
    room_id = room_manager.create_room(name)
    room = room_manager.get_room(room_id)
    
    # Prepare room data for notification
    room_summary = room.summary()
    
    # Notify lobby about new room (async, don't wait)
    asyncio.create_task(notify_lobby_room_created({
        "room_id": room_id,
        "host_name": room.host_name,
        "room_data": room_summary
    }))
    
    return {"room_id": room_id, "host_name": room.host_name}

@router.post("/join-room")
async def join_room(room_id: str = Query(...), name: str = Query(...)):
    """
    ✅ FIXED: Single, complete join_room implementation with enhanced features
    """
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.is_full():
        raise HTTPException(status_code=409, detail="Selected room is already full.")
    
    # Store previous occupancy
    old_occupancy = room.get_occupied_slots()
    
    try:
        result = await room.join_room_safe(name)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["reason"])
        
        new_occupancy = room.get_occupied_slots()
        
        # Broadcast to room
        await broadcast(room_id, "room_state_update", {
            "slots": result["room_state"]["slots"], 
            "host_name": result["room_state"]["host_name"],
            "operation_id": result["operation_id"]
        })
        
        # Notify lobby about occupancy change
        if old_occupancy != new_occupancy:
            await notify_lobby_room_updated(result["room_state"])
        
        return {
            "slots": result["room_state"]["slots"], 
            "host_name": result["room_state"]["host_name"],
            "assigned_slot": result["assigned_slot"],
            "operation_id": result["operation_id"]
        }
        
    except Exception as e:
        # Fallback to simple join if enhanced method fails
        try:
            slot_index = room.join_room(name)
            
            # Broadcast updates
            updated_summary = room.summary()
            await broadcast(room_id, "room_state_update", {
                "slots": updated_summary["slots"], 
                "host_name": updated_summary["host_name"]
            })
            
            # Notify lobby
            await notify_lobby_room_updated(updated_summary)
            
            return {
                "slots": updated_summary["slots"], 
                "host_name": updated_summary["host_name"],
                "assigned_slot": slot_index
            }
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

@router.get("/list-rooms")
async def list_rooms():
    """Lists all available rooms (not started and not full)"""
    all_rooms = room_manager.list_rooms()
    
    available_rooms = [
        room for room in all_rooms 
        if room.get("occupied_slots", 0) < room.get("total_slots", 4)
    ]
    
    return {"rooms": available_rooms}

@router.post("/assign-slot")
async def assign_slot(
    room_id: str = Query(...), 
    slot: int = Query(...),
    name: Optional[str] = Query(None)
):
    """Assign a player or bot to a specific slot"""
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        if name == "null":
            name = None
        
        # Store previous occupancy for comparison
        old_occupancy = room.get_occupied_slots()
        
        result = await room.assign_slot_safe(slot, name)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("reason", "Assignment failed"))
        
        new_occupancy = room.get_occupied_slots()
        updated_summary = room.summary()
        
        # Broadcast to room
        await broadcast(room_id, "room_state_update", {
            "slots": updated_summary["slots"], 
            "host_name": updated_summary["host_name"],
            "operation_id": result["operation_id"]
        })
        
        # Notify lobby if occupancy changed
        if old_occupancy != new_occupancy:
            await notify_lobby_room_updated(updated_summary)
        
        # Handle kicked player
        kicked_player = result.get("kicked_player")
        if kicked_player:
            await broadcast(room_id, "player_kicked", {
                "player": kicked_player,
                "reason": "Host assigned a bot to your slot",
                "operation_id": result["operation_id"]
            })
        
        return {
            "ok": True,
            "operation_id": result["operation_id"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/start-game")
async def start_game(room_id: str = Query(...)):
    """Start the game in a specific room"""
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        # Create broadcast callback for this room
        async def room_broadcast(event_type: str, event_data: dict):
            await broadcast(room_id, event_type, event_data)
        
        # Start game with state machine
        result = await room.start_game_safe(broadcast_callback=room_broadcast)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail="Failed to start game")
        
        # Register game with bot manager and state machine  
        bot_manager.register_game(room_id, room.game, room.game_state_machine)
        
        print(f"🎯 Game started with StateMachine for room {room_id}")
        
        # State machine handles all PREPARATION phase logic automatically
        # including dealing, weak hand detection, redeal logic, etc.
        
        return {"ok": True, "operation_id": result["operation_id"]}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Unexpected error in start_game: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/redeal-decision")
async def handle_redeal_decision(
    room_id: str = Query(...), 
    player_name: str = Query(...), 
    choice: str = Query(...)  # "accept" or "decline"
):
    """Handle redeal decision from player - REPLACED: Now uses state machine only"""
    room = room_manager.get_room(room_id)
    if not room or not room.game_state_machine:
        raise HTTPException(status_code=404, detail="Game not found")

    # Convert choice to boolean
    accept = choice.lower() == "accept"
    
    # Create GameAction for redeal decision - NO controller needed
    action = GameAction(
        player_name=player_name,
        action_type=ActionType.REDEAL_RESPONSE,
        payload={"accept": accept}
    )
    
    try:
        # Route through state machine ONLY
        result = await room.game_state_machine.handle_action(action)
        return {"status": "ok", "choice": choice, "processed": result.get("success", False)}
        
    except Exception as e:
        # Error recovery
        return {"status": "error", "choice": choice, "error": str(e)}

@router.post("/exit-room")
async def exit_room(room_id: str = Query(...), name: str = Query(...)):
    """Exit a room (delete if host leaves)"""
    room = room_manager.get_room(room_id)
    if not room:
        return {"ok": True, "message": "Room does not exist"}

    # Store previous occupancy
    old_occupancy = room.get_occupied_slots()
    is_host = room.exit_room(name)

    if is_host:
        # Host is leaving - room will be deleted
        await broadcast(room_id, "room_closed", {"message": "Host has exited the room."})
        await asyncio.sleep(0.1)
        
        # Notify lobby about room closure
        await notify_lobby_room_closed(room_id, "Host exited")
        
        room_manager.delete_room(room_id)
    else:
        # Player (not host) is leaving
        new_occupancy = room.get_occupied_slots()
        updated_summary = room.summary()
        
        await broadcast(room_id, "room_state_update", {
            "slots": updated_summary["slots"],
            "host_name": updated_summary["host_name"]
        })
        await broadcast(room_id, "player_left", {"player": name})
        
        # Notify lobby about occupancy change
        if old_occupancy != new_occupancy:
            await notify_lobby_room_updated(updated_summary)
        
    return {"ok": True}

# ---------- GAME PHASES ----------

@router.post("/declare")
async def declare(room_id: str = Query(...), player_name: str = Query(...), value: int = Query(...)):
    """Player declares their expected score for the round - STATE MACHINE VERSION"""
    room = room_manager.get_room(room_id)
    if not room or not room.game_state_machine:
        raise HTTPException(status_code=404, detail="Game or state machine not found")

    try:
        # Create GameAction for declaration
        action = GameAction(
            player_name=player_name,
            action_type=ActionType.DECLARE,
            payload={"value": value}
        )
        
        # Send action to state machine
        result = await room.game_state_machine.handle_action(action)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Declaration failed"))
        
        print(f"🎯 Declaration action queued for {player_name}: {value}")
        
        # State machine handles:
        # - Declaration validation
        # - Broadcasting to clients  
        # - Bot notifications
        # - Transition to TURN phase when all players declared
        
        return {"status": "ok", "queued": True}
        
    except Exception as e:
        print(f"❌ Declaration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/play-turn")
async def play_turn(
    room_id: str = Query(...), 
    player_name: str = Query(...), 
    piece_indexes: str = Query(...)
):
    """Player plays pieces on their turn - STATE MACHINE VERSION"""
    room = room_manager.get_room(room_id)
    if not room or not room.game_state_machine:
        raise HTTPException(status_code=404, detail="Game or state machine not found")

    try:
        # Parse comma-separated indices
        try:
            indices = [int(i) for i in piece_indexes.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid piece indices format")

        print(f"🎮 {player_name} playing pieces at indices: {indices}")

        # Create GameAction for piece playing (convert indices to pieces)
        pieces = []
        if hasattr(room.game, 'players'):
            # Find the player and get pieces from their hand by indices
            player = next((p for p in room.game.players if getattr(p, 'name', str(p)) == player_name), None)
            if player and hasattr(player, 'hand'):
                for idx in indices:
                    if 0 <= idx < len(player.hand):
                        pieces.append(player.hand[idx])
        
        action = GameAction(
            player_name=player_name,
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": pieces}  # Send actual pieces, not indices
        )
        
        # Send action to state machine
        result = await room.game_state_machine.handle_action(action)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Play failed"))
        
        print(f"🎯 Play action queued for {player_name}: {indices}")
        
        # State machine handles:
        # - Turn validation (correct player, piece count, etc.)
        # - Piece removal from hands
        # - Winner determination  
        # - Broadcasting to clients
        # - Bot notifications
        # - Transition to next turn or SCORING phase
        
        return {"status": "ok", "queued": True}
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"❌ Play turn error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/redeal")
async def redeal(room_id: str = Query(...), player_name: str = Query(...)):
    """Handle redeal request from a player - REPLACED: Now uses state machine only"""
    room = room_manager.get_room(room_id)
    if not room or not room.game_state_machine:
        raise HTTPException(status_code=404, detail="Game not found")

    # Create GameAction for redeal request - NO direct game calls
    action = GameAction(
        player_name=player_name,
        action_type=ActionType.REDEAL_REQUEST,
        payload={"accept": True}  # This endpoint implies acceptance
    )
    
    try:
        # Route through state machine ONLY
        result = await room.game_state_machine.handle_action(action)
        
        if not result.get("success"):
            return {"redeal_allowed": False, "error": result.get("error", "Redeal not allowed")}
            
        # State machine handles all broadcasting internally
        return {"redeal_allowed": True, "message": "Redeal processed by state machine"}
        
    except Exception as e:
        # Error recovery - never crash the game
        return {"redeal_allowed": False, "error": f"State machine error: {str(e)}"}

@router.post("/score-round")
async def score_round(room_id: str = Query(...)):
    """Score the current round and check for game over conditions - STATE MACHINE VERSION"""
    room = room_manager.get_room(room_id)
    if not room or not room.game_state_machine:
        raise HTTPException(status_code=404, detail="Game or state machine not found")

    try:
        # Create GameAction for viewing scores/game state  
        action = GameAction(
            player_name="system",  # System-initiated action
            action_type=ActionType.GAME_STATE_UPDATE,
            payload={}
        )
        
        # Send action to state machine
        result = await room.game_state_machine.handle_action(action)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Scoring failed"))
        
        print(f"🎯 Scoring action queued for room {room_id}")
        
        # State machine handles:
        # - Score calculation for all players
        # - Redeal multiplier application
        # - Game over detection  
        # - Broadcasting results to clients
        # - Transition to next round (PREPARATION) or game end
        
        return {"status": "ok", "queued": True}
        
    except Exception as e:
        print(f"❌ Scoring error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------- DEBUG / STATUS ----------

@router.get("/debug/room-stats")
async def get_room_stats(room_id: Optional[str] = Query(None)):
    """Get room statistics for debugging"""
    from backend.socket_manager import _socket_manager
    
    stats = _socket_manager.get_room_stats(room_id)
    
    if room_id:
        # Include room validation if specific room requested
        room = room_manager.get_room(room_id)
        if room:
            validation = room.validate_state()
            stats["room_validation"] = validation
            stats["room_summary"] = room.summary()
    
    return {
        "timestamp": time.time(),
        "stats": stats
    }

# ---------- LOBBY NOTIFICATION FUNCTIONS ----------

async def notify_lobby_room_created(room_data):
    """Notify lobby clients about new room creation"""
    try:
        from backend.socket_manager import ensure_lobby_ready
        ensure_lobby_ready()
        
        await broadcast("lobby", "room_created", {
            "room_id": room_data["room_id"],
            "host_name": room_data["host_name"],
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Also send updated room list
        available_rooms = room_manager.list_rooms()
        await broadcast("lobby", "room_list_update", {
            "rooms": available_rooms,
            "timestamp": asyncio.get_event_loop().time(),
            "reason": "new_room_created"
        })
        print(f"✅ Notified lobby about new room: {room_data['room_id']}")
    except Exception as e:
        print(f"❌ Failed to notify lobby about new room: {e}")

async def notify_lobby_room_updated(room_data):
    """Notify lobby clients about room updates (occupancy changes)"""
    try:
        from backend.socket_manager import ensure_lobby_ready
        ensure_lobby_ready()
        
        await broadcast("lobby", "room_updated", {
            "room_id": room_data["room_id"],
            "occupied_slots": room_data["occupied_slots"],
            "total_slots": room_data["total_slots"],
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Send fresh room list
        available_rooms = room_manager.list_rooms()
        await broadcast("lobby", "room_list_update", {
            "rooms": available_rooms,
            "timestamp": asyncio.get_event_loop().time(),
            "reason": "room_updated"
        })
        print(f"✅ Notified lobby about room update: {room_data['room_id']}")
    except Exception as e:
        print(f"❌ Failed to notify lobby about room update: {e}")

async def notify_lobby_room_closed(room_id, reason="Room closed"):
    """Notify lobby clients about room closure"""
    try:
        await broadcast("lobby", "room_closed", {
            "room_id": room_id,
            "reason": reason,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Send updated room list (without the closed room)
        available_rooms = room_manager.list_rooms()
        await broadcast("lobby", "room_list_update", {
            "rooms": available_rooms,
            "timestamp": asyncio.get_event_loop().time(),
            "reason": "room_closed"
        })
        print(f"✅ Notified lobby about room closure: {room_id}")
    except Exception as e:
        print(f"❌ Failed to notify lobby about room closure: {e}")


# ---------- EVENT SOURCING & RECOVERY ENDPOINTS ----------

@router.get("/rooms/{room_id}/events/{since_sequence}")
async def get_room_events_since(room_id: str, since_sequence: int):
    """
    Client recovery: Get events that occurred after a specific sequence number
    
    Args:
        room_id: The room identifier
        since_sequence: Get events after this sequence number
        
    Returns:
        Dict: Events for client recovery
    """
    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")
    
    try:
        events = await event_store.get_events_since(room_id, since_sequence)
        
        return {
            "success": True,
            "room_id": room_id,
            "since_sequence": since_sequence,
            "event_count": len(events),
            "events": [event.to_dict() for event in events],
            "recovery_info": {
                "latest_sequence": events[-1].sequence if events else since_sequence,
                "has_more_events": len(events) > 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve events: {str(e)}")


@router.get("/rooms/{room_id}/state")
async def get_room_reconstructed_state(room_id: str):
    """
    Client recovery: Get current room state reconstructed from events
    
    Args:
        room_id: The room identifier
        
    Returns:
        Dict: Complete room state for recovery
    """
    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")
    
    try:
        # First try to get live room state
        room = room_manager.get_room(room_id)
        if room and room.game:
            # Return live state if available
            return {
                "success": True,
                "room_id": room_id,
                "state_source": "live",
                "state": {
                    "phase": room.game.current_phase,
                    "players": [{"name": p.name, "hand": [str(piece) for piece in p.hand]} for p in room.game.players],
                    "round_number": room.game.round_number,
                    "game_active": True
                },
                "recovery_info": {
                    "live_state_available": True,
                    "reconstructed_from_events": False
                }
            }
        
        # Fallback to reconstructed state from events
        reconstructed_state = await event_store.replay_room_state(room_id)
        
        return {
            "success": True,
            "room_id": room_id,
            "state_source": "reconstructed",
            "state": reconstructed_state,
            "recovery_info": {
                "live_state_available": False,
                "reconstructed_from_events": True,
                "events_processed": reconstructed_state.get('events_processed', 0),
                "last_sequence": reconstructed_state.get('last_sequence', 0)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get room state: {str(e)}")


@router.get("/rooms/{room_id}/events")
async def get_all_room_events(room_id: str, limit: Optional[int] = Query(None, description="Limit number of events returned")):
    """
    Get all events for a room (for debugging and analysis)
    
    Args:
        room_id: The room identifier
        limit: Optional limit on number of events
        
    Returns:
        Dict: All events for the room
    """
    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")
    
    try:
        events = await event_store.get_room_events(room_id, limit)
        
        return {
            "success": True,
            "room_id": room_id,
            "event_count": len(events),
            "events": [event.to_dict() for event in events],
            "analysis": {
                "first_event": events[0].created_at if events else None,
                "last_event": events[-1].created_at if events else None,
                "event_types": list(set(event.event_type for event in events))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve all events: {str(e)}")


@router.get("/event-store/stats")
async def get_event_store_stats():
    """
    Get event store statistics for monitoring
    
    Returns:
        Dict: Event store statistics
    """
    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")
    
    try:
        stats = await event_store.get_event_stats()
        health = await event_store.health_check()
        
        return {
            "success": True,
            "statistics": stats,
            "health": health,
            "features": {
                "event_persistence": True,
                "state_reconstruction": True,
                "client_recovery": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event store stats: {str(e)}")


@router.post("/event-store/cleanup")
async def cleanup_old_events(older_than_hours: int = Query(24, description="Remove events older than this many hours")):
    """
    Clean up old events from the event store
    
    Args:
        older_than_hours: Remove events older than this many hours
        
    Returns:
        Dict: Cleanup results
    """
    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")
    
    try:
        deleted_count = await event_store.cleanup_old_events(older_than_hours)
        
        return {
            "success": True,
            "deleted_events": deleted_count,
            "older_than_hours": older_than_hours,
            "cleanup_completed": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup events: {str(e)}")


# ---------- HEALTH MONITORING & RECOVERY ENDPOINTS ----------

@router.get("/health")
async def health_check():
    """
    Basic health check for load balancers and monitoring systems
    Works with or without advanced monitoring system
    
    Returns:
        Dict: Basic health status
    """
    try:
        # Try to use advanced health monitor if available
        try:
            from api.services.health_monitor import health_monitor
            
            health_status = await health_monitor.get_health_status()
            
            # Determine HTTP status code
            if health_status.status.value == "healthy":
                status_code = 200
            elif health_status.status.value == "warning":
                status_code = 200  # Still operational
            else:  # critical or unknown
                status_code = 503  # Service unavailable
            
            response_data = {
                "status": health_status.status.value,
                "timestamp": health_status.last_check,
                "uptime_seconds": health_status.uptime_seconds,
                "uptime_formatted": health_status._format_uptime(),
                "version": "1.0.0",
                "service": "liap-tui-backend",
                "monitoring": "advanced"
            }
            
            from fastapi.responses import JSONResponse
            return JSONResponse(content=response_data, status_code=status_code)
            
        except Exception:
            # Fall back to basic health check if monitoring system isn't available
            response_data = {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "service": "liap-tui-backend",
                "monitoring": "basic",
                "message": "API is responding (advanced monitoring unavailable)"
            }
            
            from fastapi.responses import JSONResponse
            return JSONResponse(content=response_data, status_code=200)
        
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={
                "status": "critical",
                "error": str(e),
                "timestamp": time.time(),
                "service": "liap-tui-backend",
                "monitoring": "error"
            },
            status_code=503
        )


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health information for monitoring and debugging
    
    Returns:
        Dict: Comprehensive health information
    """
    try:
        # Import health monitor
        from api.services.health_monitor import health_monitor
        
        health_status = await health_monitor.get_health_status()
        
        return {
            "success": True,
            "health": health_status.to_dict(),
            "components": {
                "event_store": EVENT_STORE_AVAILABLE,
                "health_monitor": True,
                "recovery_manager": True,
                "websocket_manager": True,
                "room_manager": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get detailed health: {str(e)}")


@router.get("/health/metrics")
async def health_metrics():
    """
    Prometheus-compatible metrics endpoint
    
    Returns:
        str: Metrics in Prometheus format
    """
    try:
        # Import health monitor and socket manager
        from api.services.health_monitor import health_monitor
        import sys
        sys.path.append('/Users/nrw/python/tui-project/liap-tui/backend')
        from socket_manager import _socket_manager as socket_manager
        
        health_status = await health_monitor.get_health_status()
        
        # Generate Prometheus-style metrics
        metrics = []
        
        # System metrics
        if "memory" in health_status.metrics:
            metrics.append(f"liap_memory_usage_percent {health_status.metrics['memory'].value}")
        
        if "cpu" in health_status.metrics:
            metrics.append(f"liap_cpu_usage_percent {health_status.metrics['cpu'].value}")
        
        if "disk" in health_status.metrics:
            metrics.append(f"liap_disk_usage_percent {health_status.metrics['disk'].value}")
        
        # WebSocket metrics
        total_connections = sum(len(conns) for conns in socket_manager.room_connections.values())
        total_pending = sum(len(pending) for pending in socket_manager.pending_messages.values())
        
        metrics.append(f"liap_websocket_connections_total {total_connections}")
        metrics.append(f"liap_websocket_pending_messages_total {total_pending}")
        
        # Room metrics
        room_count = len(room_manager.rooms)
        active_games = sum(1 for room in room_manager.rooms.values() if room.started)
        
        metrics.append(f"liap_rooms_total {room_count}")
        metrics.append(f"liap_active_games_total {active_games}")
        
        # Health status (0=healthy, 1=warning, 2=critical, 3=unknown)
        status_map = {"healthy": 0, "warning": 1, "critical": 2, "unknown": 3}
        health_value = status_map.get(health_status.status.value, 3)
        metrics.append(f"liap_health_status {health_value}")
        
        # Uptime
        metrics.append(f"liap_uptime_seconds {health_status.uptime_seconds}")
        
        # Message delivery stats
        if socket_manager.message_stats:
            total_sent = sum(stats.sent for stats in socket_manager.message_stats.values())
            total_acked = sum(stats.acknowledged for stats in socket_manager.message_stats.values())
            total_failed = sum(stats.failed for stats in socket_manager.message_stats.values())
            
            metrics.append(f"liap_messages_sent_total {total_sent}")
            metrics.append(f"liap_messages_acknowledged_total {total_acked}")
            metrics.append(f"liap_messages_failed_total {total_failed}")
            
            if total_sent > 0:
                success_rate = (total_acked / total_sent) * 100
                metrics.append(f"liap_message_success_rate_percent {success_rate}")
        
        # Add timestamp
        metrics.append(f"liap_metrics_generated_timestamp {time.time()}")
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content="\n".join(metrics), media_type="text/plain")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")


@router.get("/recovery/status")
async def recovery_status():
    """
    Get recovery system status and recent attempts
    
    Returns:
        Dict: Recovery system status
    """
    try:
        # Import recovery manager
        from api.services.recovery_manager import recovery_manager
        
        status = recovery_manager.get_recovery_status()
        
        return {
            "success": True,
            "recovery_system": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recovery status: {str(e)}")


@router.post("/recovery/trigger/{procedure_name}")
async def trigger_recovery(procedure_name: str, context: dict = None):
    """
    Manually trigger a recovery procedure
    
    Args:
        procedure_name: Name of the recovery procedure to trigger
        context: Optional context data for the recovery procedure
        
    Returns:
        Dict: Recovery execution result
    """
    try:
        # Import recovery manager
        from api.services.recovery_manager import recovery_manager
        
        success = await recovery_manager.trigger_recovery(procedure_name, context or {})
        
        return {
            "success": success,
            "procedure": procedure_name,
            "context": context,
            "triggered": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger recovery: {str(e)}")


@router.get("/system/stats")
async def system_stats():
    """
    Get comprehensive system statistics
    
    Returns:
        Dict: System statistics including health, recovery, and performance data
    """
    try:
        # Import all services
        from api.services.health_monitor import health_monitor
        from api.services.recovery_manager import recovery_manager
        import sys
        sys.path.append('/Users/nrw/python/tui-project/liap-tui/backend')
        from socket_manager import _socket_manager as socket_manager
        
        # Get health status
        health_status = await health_monitor.get_health_status()
        
        # Get recovery status
        recovery_status = recovery_manager.get_recovery_status()
        
        # Get socket manager stats
        socket_stats = socket_manager.get_message_stats()
        
        # Get room stats
        room_stats = {
            "total_rooms": len(room_manager.rooms),
            "active_games": sum(1 for room in room_manager.rooms.values() if room.started),
            "total_players": sum(len([slot for slot in room.slots if slot is not None]) 
                               for room in room_manager.rooms.values())
        }
        
        # Get event store stats if available
        event_stats = {}
        if EVENT_STORE_AVAILABLE and event_store:
            event_stats = await event_store.get_event_stats()
        
        return {
            "success": True,
            "timestamp": time.time(),
            "health": health_status.to_dict(),
            "recovery": recovery_status,
            "websocket": socket_stats,
            "rooms": room_stats,
            "events": event_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")