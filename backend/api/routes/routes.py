# backend/api/routes/routes.py

import asyncio
import time
from fastapi import APIRouter, HTTPException, Query
from engine.game import Game
from engine.rules import is_valid_play, get_play_type
from engine.win_conditions import is_game_over, get_winners
from backend.socket_manager import broadcast
from backend.shared_instances import shared_room_manager, shared_bot_manager
from typing import Optional
import backend.socket_manager
from ..controllers.RedealController import RedealController
from ..controllers.GameController import GameController, active_game_controllers

print(f"socket_manager id in {__name__}: {id(backend.socket_manager)}")

# Global instances
redeal_controllers = {}
router = APIRouter()
room_manager = shared_room_manager
bot_manager = shared_bot_manager
game_controllers = {}

def get_redeal_controller(room_id: str) -> RedealController:
    """Get or create a RedealController for the specified room"""
    if room_id not in redeal_controllers:
        redeal_controllers[room_id] = RedealController(room_id)
    return redeal_controllers[room_id]

@router.post("/start-redeal-phase")
async def start_redeal_phase(room_id: str = Query(...)):
    """Start the redeal phase for a specific room"""
    controller = get_redeal_controller(room_id)
    success = await controller.start()
    return {"status": "redeal_phase_started" if success else "failed"}

@router.get("/redeal-status")
async def get_redeal_status(room_id: str = Query(...)):
    """Get the current status of redeal phase"""
    controller = get_redeal_controller(room_id)
    return controller.get_status()

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
    """Start game with event-based preparation phase"""
    try:
        # 1. Get room and validate
        room = room_manager.get_room(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
            
        # 2. Create game if not exists
        if not room.game:
            room.create_game()
            
        game = room.game
        
        # 3. Get initial game state
        initial_data = {
            "room_id": room_id,
            "players": [{
                "name": p.name,
                "is_bot": p.is_bot,
                "hand_count": len(p.hand) if p.hand else 0
            } for p in game.players],
            "round_number": 1,
            "phase": "preparation",
            "need_redeal": False,  # Will be determined by controller
            "weak_players": []
        }
        
        # 4. Broadcast game started to all players
        await broadcast(room_id, {
            "type": "game_started",  # This triggers scene transition
            "data": initial_data
        })
        
        # 5. Create and start game controller (async)
        game_controller = GameController(room_id)
        active_game_controllers[room_id] = game_controller
        
        # Start it asynchronously so we don't block the response
        asyncio.create_task(game_controller.start_game(initial_data))
        
        print(f"✅ Game started for room {room_id}")
        return {"status": "game_started", "data": initial_data}
        
    except Exception as e:
        print(f"❌ Failed to start game: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Add handler for player actions
@router.post("/player-action")
async def handle_player_action(
    room_id: str = Query(...),
    action: str = Query(...),
    player_name: str = Query(...),
    data: dict = {}
):
    """Handle player actions"""
    try:
        controller = active_game_controllers.get(room_id)
        if not controller:
            raise HTTPException(status_code=404, detail="Game not found")
            
        # For now, only handle redeal decisions
        if action == "redeal_decision" and controller.preparation_controller:
            decision = data.get("decision", "decline")
            await controller.preparation_controller.handle_redeal_decision(
                player_name, 
                decision
            )
            return {"status": "ok"}
            
        return {"status": "action_not_handled"}
        
    except Exception as e:
        print(f"❌ Error handling player action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/redeal-decision")
async def handle_redeal_decision(
    room_id: str = Query(...), 
    player_name: str = Query(...), 
    choice: str = Query(...)
):
    """Handle redeal decision from player"""
    controller = get_redeal_controller(room_id)
    await controller.handle_player_decision(player_name, choice)
    return {"status": "ok", "choice": choice}

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
    """Player declares their expected score for the round"""
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    player = room.game.get_player(player_name)
    if not player:
        raise HTTPException(status_code=400, detail=f"Player {player_name} not found in game")

    if player.declared != 0:
        print(f"⚠️ Player {player_name} already declared {player.declared}")
        return {"status": "already_declared", "value": player.declared}

    result = room.game.declare(player_name, value)
    
    if result["status"] == "ok":
        # Broadcast player declaration
        await broadcast(room_id, "declare", {
            "player": player_name,
            "value": value,
            "is_bot": False
        })
        
        print(f"📢 {player_name} declared {value}")
        
        # Notify bot manager to handle bot declarations
        await bot_manager.handle_game_event(
            room_id,
            "player_declared", 
            {"player_name": player_name}
        )
        
        # Check if all players have declared
        if room.game.all_players_declared():
            print(f"✅ All players have declared! Starting turn phase...")
            
            # Initialize turn phase
            turn_info = room.game.start_turn_phase()
            
            # Get the first player (starter) for the turn
            first_player_name = turn_info.get("first_player")
            if first_player_name:
                first_player = room.game.get_player(first_player_name)
                print(f"🎯 First player for turn: {first_player.name} (Bot: {first_player.is_bot})")
                
                # If first player is a bot, notify bot manager to start turn
                if first_player.is_bot:
                    await asyncio.sleep(1)  # Small delay for UI
                    await bot_manager.handle_game_event(
                        room_id,
                        "turn_started",
                        {"starter": first_player.name}
                    )
    
    return result

@router.post("/play-turn")
async def play_turn(
    room_id: str = Query(...), 
    player_name: str = Query(...), 
    piece_indexes: str = Query(...)
):
    """Player plays pieces on their turn"""
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Parse comma-separated indices
    try:
        indices = [int(i) for i in piece_indexes.split(',')]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid piece indices format")

    print(f"🎮 {player_name} playing pieces at indices: {indices}")

    # Process the turn
    result = room.game.play_turn(player_name, indices)

    # Get the actual pieces for broadcasting
    player = room.game.get_player(player_name)
    selected_pieces = []
    try:
        if "pieces" in result:
            selected_pieces = result["pieces"]
        else:
            # Get pieces before they're removed from hand
            selected_pieces = []
            for i in sorted(indices):
                if i < len(player.hand):
                    selected_pieces.append(str(player.hand[i]))
    except Exception as e:
        print(f"⚠️ Could not get pieces for broadcast: {e}")
        selected_pieces = [f"Piece_{i}" for i in indices]

    # Broadcast the play immediately
    await broadcast(room_id, "play", {
        "player": player_name,
        "pieces": selected_pieces,
        "valid": result.get("is_valid", True),
        "play_type": result.get("play_type", "UNKNOWN")
    })

    print(f"📡 Broadcasted {player_name}'s play, result status: {result.get('status')}")

    # Handle different result statuses
    if result.get("status") == "waiting":
        # First play of the turn - notify bot manager to handle bot plays
        print(f"⏳ Turn started by {player_name}, notifying bot manager...")
        await bot_manager.handle_game_event(
            room_id,
            "player_played",
            {"player_name": player_name}
        )
    elif result.get("status") == "resolved":
        # Turn is complete
        print(f"✅ Turn resolved, winner: {result.get('winner')}")
        
        # Check if round is complete
        all_hands_empty = all(len(p.hand) == 0 for p in room.game.players)
        
        if all_hands_empty:
            print(f"🏁 Round complete - all hands empty")
            # Bot manager will handle scoring
        elif result.get("winner"):
            # More turns to play
            next_starter = result.get("winner")
            print(f"🎯 Next turn starter: {next_starter}")
            
            # If next starter is a bot, notify bot manager
            next_player = room.game.get_player(next_starter)
            if next_player and next_player.is_bot:
                await asyncio.sleep(0.5)
                await bot_manager.handle_game_event(
                    room_id,
                    "turn_started",
                    {"starter": next_starter}
                )

    return result

@router.post("/redeal")
async def redeal(room_id: str = Query(...), player_name: str = Query(...)):
    """Handle redeal request from a player"""
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    result = room.game.request_redeal(player_name)
    
    if result["redeal_allowed"]:
        # Broadcast redeal event
        await broadcast(room_id, "redeal", {
            "player": player_name,
            "multiplier": room.game.redeal_multiplier
        })
        
        await asyncio.sleep(1)  # Small delay
        new_round_data = room.game.prepare_round()
        
        # Broadcast new hands
        await broadcast(room_id, "new_round", {
            "round": new_round_data["round"],
            "starter": player_name,
            "hands": new_round_data["hands"],
            "multiplier": room.game.redeal_multiplier
        })
    
    return result

@router.post("/score-round")
async def score_round(room_id: str = Query(...)):
    """Score the current round and check for game over conditions"""
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    game = room.game
    summary = game.score_round()
    game_over = is_game_over(game)
    winners = get_winners(game) if game_over else []

    await broadcast(room_id, "score", {
        "summary": summary,
        "game_over": game_over,
        "winners": [p.name for p in winners]
    })

    return {
        "summary": summary,
        "game_over": game_over,
        "winners": [p.name for p in winners]
    }

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