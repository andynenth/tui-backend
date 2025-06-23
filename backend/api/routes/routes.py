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
from typing import Optional
import backend.socket_manager
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

        # Create GameAction for piece playing
        action = GameAction(
            player_name=player_name,
            action_type=ActionType.PLAY_PIECES,
            payload={"piece_indices": indices}
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