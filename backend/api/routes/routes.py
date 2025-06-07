# backend/api/routes/routes.py

from fastapi import APIRouter, HTTPException, Query
from engine.game import Game
from engine.rules import is_valid_play, get_play_type
from engine.win_conditions import is_game_over, get_winners
from backend.socket_manager import broadcast
from backend.shared_instances import shared_room_manager, shared_bot_manager
import asyncio
import time
from typing import Optional
import backend.socket_manager


print(f"socket_manager id in {__name__}: {id(backend.socket_manager)}")

router = APIRouter() # Create a new FastAPI APIRouter instance.
# room_manager = RoomManager() # (Commented out) Direct instantiation of RoomManager.
room_manager = shared_room_manager
bot_manager = shared_bot_manager

# ---------- ROOM MANAGEMENT ----------

@router.get("/get-room-state")
async def get_room_state(room_id: str = Query(...)):
    """
    Retrieves the current state of a specific game room.
    Args:
        room_id (str): The ID of the room to retrieve.
    Returns:
        dict: A summary of the room's state, including slots and host_name.
    Raises:
        HTTPException: If the room is not found.
    """
    room = room_manager.get_room(room_id) # Get the room object from the room manager.
    if not room:
        raise HTTPException(status_code=404, detail="Room not found") # Raise 404 if room doesn't exist.
    # Return a summary of the room, which includes its slots and host_name.
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
    """
    Lists all available rooms (not started and not full)
    """
    all_rooms = room_manager.list_rooms()
    
    available_rooms = [
        room for room in all_rooms 
        if room.get("occupied_slots", 0) < room.get("total_slots", 4)
    ]
    
    return {"rooms": available_rooms}

async def join_room(room_id: str = Query(...), name: str = Query(...)):
    """
    ✅ Enhanced join room with lobby notifications
    """
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.is_full():
        raise HTTPException(status_code=409, detail="Selected room is already full.")
    
    # Store previous occupancy
    old_occupancy = room.get_occupied_slots()
    
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

@router.post("/assign-slot")
async def assign_slot(
    room_id: str = Query(...), 
    slot: int = Query(...),
    name: Optional[str] = Query(None)
):
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
        
        # ✅ Notify lobby if occupancy changed
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
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        result = await room.start_game_safe()
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail="Failed to start game")
        
        # Register game with bot manager
        bot_manager.register_game(room_id, room.game)
        
        game_data = room.game.prepare_round()
        
        await broadcast(room_id, "start_game", {
            "message": "Game started",
            "round": game_data["round"],
            "starter": game_data["starter"],
            "hands": game_data["hands"],
            "players": [
                {
                    "name": p.name,
                    "score": p.score,
                    "is_bot": p.is_bot,
                    "zero_declares_in_a_row": p.zero_declares_in_a_row
                }
                for p in room.game.players
            ],
            "operation_id": result["operation_id"]
        })
        
        # Notify bot manager about round start
        await bot_manager.handle_game_event(
            room_id, 
            "round_started", 
            {"starter": game_data["starter"]}
        )
        
        return {"ok": True, "operation_id": result["operation_id"]}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Unexpected error in start_game: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/exit-room")
async def exit_room(room_id: str = Query(...), name: str = Query(...)):
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

# ---------- ROUND PHASES ----------

@router.post("/start-round")
async def start_round(room_id: str = Query(...)):
    """
    Starts a new round in the game.
    Args:
        room_id (str): The ID of the room.
    Returns:
        dict: Result of preparing the round.
    Raises:
        HTTPException: If the room or game is not found.
    """
    room = room_manager.get_room(room_id) # Get the room.
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found") # Check if room and game exist.

    result = room.game.prepare_round() # Prepare the game round.
    await broadcast(room_id, "start_round", result) # Broadcast the start round event.
    return result

@router.post("/redeal")
async def redeal(room_id: str = Query(...), player_name: str = Query(...)):
    """
    Handles a player's request to redeal.
    Args:
        room_id (str): The ID of the room.
        player_name (str): The name of the player requesting redeal.
    Returns:
        dict: Result of the redeal request.
    Raises:
        HTTPException: If the room or game is not found.
    """
    room = room_manager.get_room(room_id) # Get the room.
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found") # Check if room and game exist.

    result = room.game.request_redeal(player_name) # Request redeal in the game.
    await broadcast(room_id, "redeal", {
        "player": player_name,
        "multiplier": room.game.redeal_multiplier # Broadcast redeal details.
    })
    return result

@router.post("/declare")
async def declare(room_id: str = Query(...), player_name: str = Query(...), value: int = Query(...)):
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
    
    return result

@router.post("/play-turn")
async def play_turn(
    room_id: str = Query(...), 
    player_name: str = Query(...), 
    piece_indexes: str = Query(...)
):
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Parse comma-separated indices
    try:
        indices = [int(i) for i in piece_indexes.split(',')]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid piece indices format")

    # Process the turn
    result = room.game.play_turn(player_name, indices)

    # Get the actual pieces for broadcasting
    player = room.game.get_player(player_name)
    selected_pieces = []
    try:
        if "pieces" in result:
            selected_pieces = result["pieces"]
        else:
            # Reconstruct from indices if still in hand
            for i in indices:
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

    # Notify bot manager to handle bot plays
    if result.get("status") == "waiting":
        await bot_manager.handle_game_event(
            room_id,
            "player_played",
            {"player_name": player_name}
        )

    return result

@router.post("/score-round")
async def score_round(room_id: str = Query(...)):
    """
    Scores the current round and checks for game over conditions.
    Args:
        room_id (str): The ID of the room.
    Returns:
        dict: Summary of the round score, game over status, and winners.
    Raises:
        HTTPException: If the room or game is not found.
    """
    room = room_manager.get_room(room_id) # Get the room.
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found") # Check if room and game exist.

    game = room.game # Get the game instance.
    summary = game.score_round() # Score the current round.
    game_over = is_game_over(game) # Check if the game is over.
    winners = get_winners(game) if game_over else [] # Get winners if game is over.

    await broadcast(room_id, "score", {
        "summary": summary,
        "game_over": game_over,
        "winners": [p.name for p in winners] # Broadcast score details.
    })

    return {
        "summary": summary,
        "game_over": game_over,
        "winners": [p.name for p in winners]
    }

# ---------- DEBUG / STATUS ----------

@router.get("/check-game-over")
async def check_game_over(room_id: str = Query(...)):
    """
    Checks if the game in a specific room is over.
    Args:
        room_id (str): The ID of the room.
    Returns:
        dict: Game over status, round number, and current scores.
    Raises:
        HTTPException: If the room or game is not found.
    """
    room = room_manager.get_room(room_id) # Get the room.
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found") # Check if room and game exist.

    game = room.game # Get the game instance.
    over = game.is_game_over() # Check game over status.

    return {
        "game_over": over,
        "round": game.round_number,
        "scores": {p.name: p.score for p in game.players} # Return current scores.
    }

@router.get("/deal")
async def deal(room_id: str = Query(...)):
    """
    Deals pieces for a new round (for debugging/testing).
    Args:
        room_id (str): The ID of the room.
    Returns:
        dict: Current round number and players' hands.
    Raises:
        HTTPException: If the room or game is not found or not started.
    """
    room = room_manager.get_room(room_id) # Get the room.
    if not room or not room.started or not room.game:
        raise HTTPException(status_code=400, detail="Game not found or not started") # Check game status.

    game = room.game # Get the game instance.
    game._deal_pieces() # Deal pieces to players.
    game._set_round_start_player() # Set the starting player for the round.

    hands = {
        player.name: [str(p) for p in player.hand] # Get string representation of each player's hand.
        for player in game.players
    }
    return {"round": game.round_number, "hands": hands}

@router.post("/play")
async def play(data: dict):
    """
    Validates a play (for debugging/testing).
    Args:
        data (dict): Dictionary containing room_id, player_index, and piece_indexes.
    Returns:
        dict: Validity of the play, play type, and pieces played.
    Raises:
        HTTPException: If data is missing, room/game not found.
    """
    room_id = data.get("room_id")
    player_index = data.get("player_index")
    piece_indexes = data.get("piece_indexes")

    if room_id is None or player_index is None or piece_indexes is None:
        raise HTTPException(status_code=400, detail="Missing data") # Check for missing data.

    room = room_manager.get_room(room_id) # Get the room.
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found") # Check if room and game exist.

    player = room.game.players[player_index] # Get the player object.
    pieces = [player.hand[i] for i in piece_indexes] # Get the actual pieces from player's hand.

    valid = is_valid_play(pieces) # Check if the play is valid.
    play_type = get_play_type(pieces) if valid else None # Get play type if valid.

    return {
        "valid": valid,
        "play_type": play_type,
        "pieces": [str(p) for p in pieces] # Return string representation of pieces.
    }

@router.get("/debug/room-stats")
async def get_room_stats(room_id: Optional[str] = Query(None)):
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

async def notify_lobby_room_created(room_data):
    """
    Notify lobby clients about new room creation
    """
    try:
        # Ensure lobby is ready before broadcasting
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
        import traceback
        traceback.print_exc()

async def notify_lobby_room_updated(room_data):
    """
    Notify lobby clients about room updates (occupancy changes)
    """
    try:
        # Ensure lobby is ready before broadcasting
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
        import traceback
        traceback.print_exc()

async def notify_lobby_room_closed(room_id, reason="Room closed"):
    """
    Notify lobby clients about room closure
    """
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