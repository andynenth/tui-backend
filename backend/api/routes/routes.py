# backend/api/routes/routes.py

from fastapi import APIRouter, HTTPException, Query
from engine.game import Game
from engine.rules import is_valid_play, get_play_type
from engine.ai import choose_declare, choose_best_play
from engine.win_conditions import is_game_over, get_winners
from backend.socket_manager import broadcast
from backend.shared_instances import shared_room_manager
import asyncio
import time
from typing import Optional

router = APIRouter()
room_manager = shared_room_manager

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
    """
    ✅ Enhanced game starting with race condition prevention
    """
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        # ✅ Use the thread-safe method
        result = await room.start_game_safe()
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail="Failed to start game")
        
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
                    "zero_declares_in_a_row": p.zero_declares_in_a_row  # Add this for frontend
                }
                for p in room.game.players
            ],
            "operation_id": result["operation_id"]
        })
        
        # Check if the starter is a bot and trigger bot declarations
        starter = room.game.current_order[0]
        if starter.is_bot:
            print(f"🤖 Starter is bot: {starter.name}, triggering bot declarations")
            asyncio.create_task(handle_bot_declarations(room_id, starter.name))
        
        return {
            "ok": True,
            "operation_id": result["operation_id"]
        }
        
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
    """
    Handles a player's declaration of a value.
    """
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
    
    # Broadcast player declaration
    await broadcast(room_id, "declare", {
        "player": player_name,
        "value": value,
        "is_bot": False
    })
    
    print(f"📢 {player_name} declared {value}")
    
    # Trigger bot declarations
    asyncio.create_task(handle_bot_declarations(room_id, player_name))
    if room.game.all_players_declared():
        print(f"✅ All players declared - checking if first player is bot")
        first_player = room.game.current_order[0]
        if first_player.is_bot:
            print(f"🤖 First player {first_player.name} is a bot - should trigger bot play")
            
    return result

@router.post("/play-turn")
async def play_turn(
    room_id: str = Query(...), 
    player_name: str = Query(...), 
    piece_indexes: str = Query(...)
):
    """
    ✅ Enhanced play-turn with proper bot continuation and round scoring
    """
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
        # Get pieces before they're removed (from the result)
        if "pieces" in result:
            selected_pieces = result["pieces"]
        else:
            # Fallback: reconstruct from indices if still in hand
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

    # ✅ Handle different turn states
    if result.get("status") == "waiting":
        # First play sets the piece count - trigger remaining bot plays
        print(f"🎯 Turn started by {player_name}, triggering bot plays in order")
        asyncio.create_task(handle_bot_plays_in_order(room_id))
        
    elif result.get("status") == "resolved":
        # Turn is complete - broadcast result
        await broadcast(room_id, "turn_resolved", {
            "plays": result["plays"],
            "winner": result["winner"],
            "pile_count": result["pile_count"]
        })
        
        # ✅ Check if round is complete (all hands empty)
        all_hands_empty = all(len(p.hand) == 0 for p in room.game.players)
        
        if all_hands_empty:
            print(f"🏁 Round {room.game.round_number} complete - triggering scoring")
            await asyncio.sleep(0.5)  # Brief pause before scoring
            await trigger_round_scoring(room_id)
        elif result["winner"]:
            # More turns to play - start next turn with winner
            print(f"🎯 Starting next turn with winner: {result['winner']}")
            await asyncio.sleep(0.5)
            await start_next_turn(room_id, result["winner"])

    return result

async def trigger_round_scoring(room_id: str):
    """
    ✅ Trigger round scoring when all hands are empty
    """
    try:
        room = room_manager.get_room(room_id)
        if not room or not room.game:
            print(f"❌ Room {room_id} or game not found for scoring")
            return
        
        game = room.game
        print(f"📊 Scoring round {game.round_number}")
        
        # Score the round
        summary = game.score_round()
        game_over = is_game_over(game)
        winners = get_winners(game) if game_over else []
        
        # Broadcast score results
        await broadcast(room_id, "score", {
            "summary": summary,
            "game_over": game_over,
            "winners": [p.name for p in winners]
        })
        
        # If game is not over, start next round
        if not game_over:
            print(f"🆕 Starting round {game.round_number + 1}")
            await asyncio.sleep(2)  # Give players time to see scores
            await start_next_round(room_id)
        else:
            print(f"🎮 Game over! Winners: {[p.name for p in winners]}")
            
    except Exception as e:
        print(f"❌ Error in round scoring: {e}")
        import traceback
        traceback.print_exc()

async def start_next_round(room_id: str):
    """
    ✅ Start the next round of the game
    """
    try:
        room = room_manager.get_room(room_id)
        if not room or not room.game:
            return
        
        game = room.game
        
        # Prepare the new round
        round_data = game.prepare_round()
        
        # Broadcast new round start
        await broadcast(room_id, "start_round", {
            "round": round_data["round"],
            "starter": round_data["starter"],
            "hands": round_data["hands"],
            "players": [
                {
                    "name": p.name,
                    "score": p.score,
                    "is_bot": p.is_bot,
                    "zero_declares_in_a_row": p.zero_declares_in_a_row
                }
                for p in game.players
            ]
        })
        
        # If starter is a bot, trigger bot declarations
        starter = game.current_order[0]
        if starter.is_bot:
            print(f"🤖 New round starter is bot: {starter.name}")
            await asyncio.sleep(1)
            asyncio.create_task(handle_bot_declarations(room_id, starter.name))
            
    except Exception as e:
        print(f"❌ Error starting next round: {e}")
        import traceback
        traceback.print_exc()

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
    """Notify lobby clients about new room creation"""
    try:
        from backend.socket_manager import ensure_lobby_ready
        ensure_lobby_ready()
        
        await broadcast("lobby", "room_created", {
            "room_id": room_data["room_id"],
            "host_name": room_data["host_name"],
            "timestamp": asyncio.get_event_loop().time()
        })
        
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
    """Notify lobby clients about room updates"""
    try:
        from backend.socket_manager import ensure_lobby_ready
        ensure_lobby_ready()
        
        await broadcast("lobby", "room_updated", {
            "room_id": room_data["room_id"],
            "occupied_slots": room_data["occupied_slots"],
            "total_slots": room_data["total_slots"],
            "timestamp": asyncio.get_event_loop().time()
        })
        
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
        
        available_rooms = room_manager.list_rooms()
        await broadcast("lobby", "room_list_update", {
            "rooms": available_rooms,
            "timestamp": asyncio.get_event_loop().time(),
            "reason": "room_closed"
        })
        print(f"✅ Notified lobby about room closure: {room_id}")
    except Exception as e:
        print(f"❌ Failed to notify lobby about room closure: {e}")
        
async def handle_bot_declarations(room_id: str, triggering_player: str = None):
    """
    ✅ Enhanced bot declarations with better order tracking
    """
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        return
    
    game = room.game
    
    print(f"\n🤖 Bot declarations triggered by: {triggering_player}")
    print(f"📍 Declaration order: {[p.name for p in game.current_order]}")
    
    await asyncio.sleep(0.5)  # Brief delay for UI
    
    # Process each player in declaration order
    for i, player in enumerate(game.current_order):
        # Skip non-bots or already declared
        if not player.is_bot or player.declared != 0:
            continue
            
        # Check if it's this bot's turn (all previous players have declared)
        should_declare = True
        for j in range(i):
            prev_player = game.current_order[j]
            if prev_player.declared == 0:
                should_declare = False
                break
        
        if not should_declare:
            continue
            
        print(f"\n🤖 Bot {player.name} declaring (position {i})")
        
        # Get previous declarations
        previous_declarations = [p.declared for p in game.players if p.declared != 0]
        must_declare_nonzero = player.zero_declares_in_a_row >= 2
        
        try:
            # Bot chooses declaration
            value = choose_declare(
                hand=player.hand,
                is_first_player=(i == 0),
                position_in_order=i,
                previous_declarations=previous_declarations,
                must_declare_nonzero=must_declare_nonzero,
                verbose=True
            )
            
            # Handle last player restriction
            if i == 3:  # Last player
                total_so_far = sum(p.declared for p in game.players)
                forbidden = 8 - total_so_far
                if value == forbidden and 0 <= forbidden <= 8:
                    print(f"⚠️ Bot {player.name} cannot declare {value} (total would be 8)")
                    value = 1 if forbidden != 1 else 2
            
            # Make declaration
            result = game.declare(player.name, value)
            
            if result["status"] == "ok":
                await broadcast(room_id, "declare", {
                    "player": player.name,
                    "value": value,
                    "is_bot": True
                })
                print(f"✅ Bot {player.name} declared {value}")
            else:
                print(f"❌ Bot {player.name} declaration failed: {result}")
                
        except Exception as e:
            print(f"❌ Error in bot {player.name} declaration: {e}")
            # Fallback declaration
            try:
                game.declare(player.name, 1)
                await broadcast(room_id, "declare", {
                    "player": player.name,
                    "value": 1,
                    "is_bot": True
                })
            except:
                pass
        
        await asyncio.sleep(0.5)  # Delay between declarations
    
async def handle_bot_turns(room_id: str, last_winner: str):
    """
    Handle bot turns after a human player or previous bot has played
    """
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        return
    
    game = room.game
    
    # Wait a bit for UI effect
    await asyncio.sleep(1)
    
    # Determine turn order starting from last winner
    winner_player = game.get_player(last_winner)
    if not winner_player:
        return
    
    turn_order = game._rotate_players_starting_from(winner_player)
    
    # Check if any bots need to play
    for player in turn_order:
        if player.is_bot and len(player.hand) > 0:
            # Check if this bot has already played this turn
            already_played = any(
                play.player == player for play in game.current_turn_plays
            )
            
            if not already_played:
                # Determine required piece count
                required_count = game.required_piece_count
                
                # Bot chooses play
                selected = choose_best_play(
                    player.hand, 
                    required_count=required_count,
                    verbose=True
                )
                
                # Find indices of selected pieces
                indices = []
                hand_copy = list(player.hand)
                for piece in selected:
                    if piece in hand_copy:
                        idx = hand_copy.index(piece)
                        indices.append(idx)
                        hand_copy[idx] = None  # Mark as used
                
                # Make the play
                result = game.play_turn(player.name, indices)
                
                # Broadcast the play
                await broadcast(room_id, "play", {
                    "player": player.name,
                    "pieces": [str(p) for p in selected],
                    "valid": result.get("is_valid", True),
                    "play_type": result.get("play_type", "UNKNOWN")
                })
                
                # If turn is resolved, broadcast result
                if result.get("status") == "resolved":
                    await broadcast(room_id, "turn_resolved", {
                        "plays": result["plays"],
                        "winner": result["winner"],
                        "pile_count": result["pile_count"]
                    })
                    
                    # If there's a new winner and more pieces to play, continue bot turns
                    if result["winner"] and any(p.hand for p in game.players):
                        await asyncio.sleep(0.5)
                        await handle_bot_turns(room_id, result["winner"])
                
                # Wait between bot plays
                await asyncio.sleep(0.5)
            
async def handle_bot_plays_in_order(room_id: str):
    """
    ✅ Handle bot plays in correct turn order after human plays
    """
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        return
    
    game = room.game
    required_count = game.required_piece_count
    
    if not required_count:
        print("❌ No required piece count set for bot plays")
        return
    
    print(f"\n🤖 Processing bot plays ({required_count} pieces each)")
    await asyncio.sleep(0.5)
    
    # Get turn order and process remaining players
    for player in game.turn_order:
        # Skip if already played this turn
        if any(play.player == player for play in game.current_turn_plays):
            continue
            
        # Only handle bots
        if not player.is_bot:
            continue
            
        print(f"🤖 Bot {player.name} playing {required_count} pieces")
        
        try:
            # Bot chooses play
            selected = choose_best_play(
                player.hand, 
                required_count=required_count,
                verbose=True
            )
            
            # Find indices of selected pieces
            indices = []
            hand_copy = list(player.hand)
            for piece in selected:
                if piece in hand_copy:
                    idx = hand_copy.index(piece)
                    indices.append(idx)
                    hand_copy[idx] = None  # Mark as used
            
            # Make the play
            result = game.play_turn(player.name, indices)
            
            # Broadcast the bot's play
            await broadcast(room_id, "play", {
                "player": player.name,
                "pieces": [str(p) for p in selected],
                "valid": result.get("is_valid", True),
                "play_type": result.get("play_type", "UNKNOWN")
            })
            
            await asyncio.sleep(0.5)  # Delay between bot plays
            
            # If turn is resolved, broadcast and handle next steps
            if result.get("status") == "resolved":
                await broadcast(room_id, "turn_resolved", {
                    "plays": result["plays"],
                    "winner": result["winner"],
                    "pile_count": result["pile_count"]
                })
                
                # Check if round is complete
                all_hands_empty = all(len(p.hand) == 0 for p in game.players)
                
                if all_hands_empty:
                    print(f"🏁 Round complete after bot play")
                    await asyncio.sleep(0.5)
                    await trigger_round_scoring(room_id)
                elif result["winner"]:
                    # Continue with next turn
                    print(f"🎯 Next turn will start with: {result['winner']}")
                    await asyncio.sleep(0.5)
                    await start_next_turn(room_id, result["winner"])
                
                break  # Turn is resolved, stop processing
                
        except Exception as e:
            print(f"❌ Error in bot {player.name} play: {e}")
            import traceback
            traceback.print_exc()
        
async def start_next_turn(room_id: str, winner_name: str):
    """
    ✅ Start the next turn with winner as first player
    """
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        return
    
    game = room.game
    winner = game.get_player(winner_name)
    
    if not winner or len(winner.hand) == 0:
        print(f"⚠️ Cannot start turn: {winner_name} has no pieces left")
        return
    
    print(f"\n🎯 Starting new turn with {winner_name} as first player")
    
    # Check if winner is a bot
    if winner.is_bot:
        try:
            # Bot plays first
            selected = choose_best_play(winner.hand, required_count=None, verbose=True)
            
            # Find indices
            indices = []
            hand_copy = list(winner.hand)
            for piece in selected:
                if piece in hand_copy:
                    idx = hand_copy.index(piece)
                    indices.append(idx)
                    hand_copy[idx] = None
            
            # Make the play
            result = game.play_turn(winner.name, indices)
            
            # Broadcast the play
            await broadcast(room_id, "play", {
                "player": winner.name,
                "pieces": [str(p) for p in selected],
                "valid": result.get("is_valid", True),
                "play_type": result.get("play_type", "UNKNOWN")
            })
            
            # Continue with other bot plays if waiting
            if result.get("status") == "waiting":
                await asyncio.sleep(0.5)
                await handle_bot_plays_in_order(room_id)
                
        except Exception as e:
            print(f"❌ Error in bot turn start: {e}")
            import traceback
            traceback.print_exc()
            
            