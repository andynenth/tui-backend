# backend/api/routes/routes.py

from fastapi import APIRouter, HTTPException, Query # Import FastAPI components for routing, HTTP exceptions, and query parameters.
from engine.game import Game # Import the Game class from the game engine.
from engine.rules import is_valid_play, get_play_type # Import game rule functions.
from engine.win_conditions import is_game_over, get_winners # Import win condition functions.
from backend.socket_manager import broadcast
from backend.shared_instances import shared_room_manager # Import the shared RoomManager instance.
import asyncio # Standard library for asynchronous programming.
from typing import Optional
import backend.socket_manager
print(f"socket_manager id in {__name__}: {id(backend.socket_manager)}")

router = APIRouter() # Create a new FastAPI APIRouter instance.
# room_manager = RoomManager() # (Commented out) Direct instantiation of RoomManager.
room_manager = shared_room_manager # Use the globally shared RoomManager instance.

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
    Creates a new game room.
    Args:
        name (str): The name of the player creating the room (host).
    Returns:
        dict: A dictionary containing the new room's ID and the host's name.
    """
    room_id = room_manager.create_room(name) # Create a new room and get its ID.
    room = room_manager.get_room(room_id) # Retrieve the newly created room object.
    # ❌ Removed the direct broadcast here. Room state updates should happen after join/assign actions.
    # await broadcast(room_id, "room_state_update", {"slots": room.summary()["slots"], "host_name": room.host_name})
    return {"room_id": room_id, "host_name": room.host_name}

@router.get("/list-rooms")
async def list_rooms():
    """
    Lists all currently available game rooms.
    Returns:
        dict: A dictionary containing a list of available rooms.
    """
    return {"rooms": room_manager.list_rooms()}

@router.post("/join-room")
async def join_room(room_id: str = Query(...), name: str = Query(...)):
    """
    Allows a player to join an existing game room.
    Automatically assigns to first available slot.
    """
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        slot_index = room.join_room(name)  # join_room จะคืน slot index
        # ไม่ต้องเรียก assign_slot อีก เพราะ join_room ทำให้แล้ว
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Broadcast updated room state
    await broadcast(room_id, "room_state_update", {
        "slots": room.summary()["slots"], 
        "host_name": room.host_name
    })
    
    return {
        "slots": room.summary()["slots"], 
        "host_name": room.host_name,
        "assigned_slot": slot_index  # บอกด้วยว่าได้ slot ไหน
    }

@router.post("/assign-slot")
async def assign_slot(
    room_id: str = Query(...), 
    slot: int = Query(...),
    name: Optional[str] = Query(None)  # Make name optional with None default
):
    """
    Assigns a player (or None to unassign) to a specific slot in a room.
    Args:
        room_id (str): The ID of the room.
        name (Optional[str]): The name of the player to assign, or None to clear the slot.
        slot (int): The 0-indexed slot number to assign to.
    Returns:
        dict: A confirmation dictionary.
    Raises:
        HTTPException: If the room is not found or assignment fails.
    """
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        # Pass None if name is None or "null" string
        if name == "null":
            name = None
        room.assign_slot(slot, name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    updated_summary = room.summary()
    print(f"DEBUG: assign_slot - Broadcasting update for room {room_id}. New slots: {updated_summary['slots']}")
    
    await broadcast(room_id, "room_state_update", {
        "slots": updated_summary["slots"], 
        "host_name": updated_summary["host_name"]
    })
    await asyncio.sleep(0)

    return {"ok": True}

@router.post("/set-bot")
async def set_bot(room_id: str = Query(...), slot: int = Query(...)):
    """
    Sets a bot in a specific slot.
    Note: It's recommended that `set_bot()` internally calls `assign_slot()`
    or that `set_bot()` is refactored to use `assign_slot()` directly.
    Args:
        room_id (str): The ID of the room.
        slot (int): The 0-indexed slot number for the bot.
    Returns:
        dict: A confirmation dictionary.
    Raises:
        HTTPException: If the room is not found.
    """
    room = room_manager.get_room(room_id) # Get the room object.
    if not room:
        raise HTTPException(status_code=404, detail="Room not found") # Raise 404 if room doesn't exist.
    room.set_bot(slot) # Call the room's set_bot method.
    # Should broadcast after the change.
    await broadcast(room_id, "room_state_update", {"slots": room.summary()["slots"]})
    return {"ok": True}

@router.post("/start-game")
async def start_game(room_id: str = Query(...)):
    """
    Starts the game in a specific room.
    Args:
        room_id (str): The ID of the room to start the game in.
    Returns:
        dict: A confirmation dictionary.
    Raises:
        HTTPException: If the room is not found or starting the game fails.
    """
    room = room_manager.get_room(room_id) # Get the room object.
    if not room:
        raise HTTPException(status_code=404, detail="Room not found") # Raise 404 if room doesn't exist.
    try:
        room.start_game() # Attempt to start the game.
        await broadcast(room_id, "start_game", {"message": "Game started."}) # Broadcast game start event.
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) # Raise 400 if starting fails (e.g., not enough players).
    return {"ok": True}

@router.post("/exit-room")
async def exit_room(room_id: str = Query(...), name: str = Query(...)):
    """
    Allows a player to exit a room. If the host exits, the room is deleted.
    Args:
        room_id (str): The ID of the room.
        name (str): The name of the player exiting.
    Returns:
        dict: A confirmation dictionary.
    Raises:
        HTTPException: If the room is not found.
    """
    room = room_manager.get_room(room_id) # Get the room object.
    if not room:
        raise HTTPException(status_code=404, detail="Room not found") # Raise 404 if room doesn't exist.

    is_host = room.exit_room(name) # Player exits, returns True if the exiting player was the host.

    if is_host:
        room_manager.delete_room(room_id) # If host exited, delete the room.
        # When the room is closed, broadcast a 'room_closed' event to everyone in that room.
        await broadcast(room_id, "room_closed", {"message": "Host has exited the room."})
        # Note: WebSocket connections for this room should ideally be closed automatically when clients disconnect.
    else:
        # When a player exits, broadcast the updated room state.
        await broadcast(room_id, "room_state_update", {"slots": room.summary()["slots"]})
        await broadcast(room_id, "player_left", {"player": name}) # Can send a separate 'player_left' event or combine.
        
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
    Args:
        room_id (str): The ID of the room.
        player_name (str): The name of the player declaring.
        value (int): The declared value.
    Returns:
        dict: Result of the declaration.
    Raises:
        HTTPException: If the room or game is not found.
    """
    room = room_manager.get_room(room_id) # Get the room.
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found") # Check if room and game exist.

    result = room.game.declare(player_name, value) # Perform the declaration in the game.
    await broadcast(room_id, "declare", {
        "player": player_name,
        "value": value # Broadcast declaration details.
    })
    return result

@router.post("/play-turn")
async def play_turn(room_id: str = Query(...), player_name: str = Query(...), piece_indexes: list[int] = Query(...)):
    """
    Handles a player's turn to play pieces.
    Args:
        room_id (str): The ID of the room.
        player_name (str): The name of the player playing.
        piece_indexes (list[int]): List of indexes of pieces to play from player's hand.
    Returns:
        dict: Result of the play turn, including validity and play type.
    Raises:
        HTTPException: If the room or game is not found.
    """
    room = room_manager.get_room(room_id) # Get the room.
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found") # Check if room and game exist.

    result = room.game.play_turn(player_name, piece_indexes) # Perform the play turn.

    await broadcast(room_id, "play", {
        "player": player_name,
        "pieces": [str(p) for p in result["pieces"]], # Convert pieces to string representation.
        "valid": result["valid"],
        "play_type": result["play_type"]
    })

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
