# backend/api/routes/routes.py

from fastapi import APIRouter, HTTPException, Query
from engine.game import Game
from engine.rules import is_valid_play, get_play_type
from engine.room_manager import RoomManager
from engine.win_conditions import is_game_over, get_winners
from socket_manager import broadcast

router = APIRouter()
room_manager = RoomManager()

# ---------- ROOM MANAGEMENT ----------

@router.post("/create-room")
async def create_room(name: str = Query(...)):
    room_id = room_manager.create_room(name)
    return {"room_id": room_id}

@router.get("/list-rooms")
async def list_rooms():
    return {"rooms": room_manager.list_rooms()}

@router.post("/join-room")
async def join_room(room_id: str = Query(...), name: str = Query(...)):
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"slots": room.summary()["slots"]}

@router.post("/assign-slot")
async def assign_slot(room_id: str = Query(...), name: str = Query(...), slot: int = Query(...)):
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    try:
        room.assign_slot(slot, name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}

@router.post("/set-bot")
async def set_bot(room_id: str = Query(...), slot: int = Query(...)):
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    room.set_bot(slot)
    return {"ok": True}

@router.post("/start-game")
async def start_game(room_id: str = Query(...)):
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    try:
        room.start_game()
        await broadcast(room_id, "start_game", {"message": "Game started."})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}

@router.post("/exit-room")
async def exit_room(room_id: str = Query(...), name: str = Query(...)):
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    is_host = room.exit_room(name)

    if is_host:
        room_manager.delete_room(room_id)
        await broadcast(room_id, "room_closed", {"message": "Host has exited the room."})
    else:
        await broadcast(room_id, "player_left", {"player": name})

    return {"ok": True}


# ---------- ROUND PHASES ----------

@router.post("/start-round")
async def start_round(room_id: str = Query(...)):
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    result = room.game.prepare_round()
    await broadcast(room_id, "start_round", result)
    return result

@router.post("/redeal")
async def redeal(room_id: str = Query(...), player_name: str = Query(...)):
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    result = room.game.request_redeal(player_name)
    await broadcast(room_id, "redeal", {
        "player": player_name,
        "multiplier": room.game.redeal_multiplier
    })
    return result

@router.post("/declare")
async def declare(room_id: str = Query(...), player_name: str = Query(...), value: int = Query(...)):
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    result = room.game.declare(player_name, value)
    await broadcast(room_id, "declare", {
        "player": player_name,
        "value": value
    })
    return result

@router.post("/play-turn")
async def play_turn(room_id: str = Query(...), player_name: str = Query(...), piece_indexes: list[int] = Query(...)):
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    result = room.game.play_turn(player_name, piece_indexes)

    await broadcast(room_id, "play", {
        "player": player_name,
        "pieces": [str(p) for p in result["pieces"]],
        "valid": result["valid"],
        "play_type": result["play_type"]
    })

    return result

@router.post("/score-round")
async def score_round(room_id: str = Query(...)):
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

@router.get("/check-game-over")
async def check_game_over(room_id: str = Query(...)):
    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    game = room.game
    over = game.is_game_over()

    return {
        "game_over": over,
        "round": game.round_number,
        "scores": {p.name: p.score for p in game.players}
    }

@router.get("/deal")
async def deal(room_id: str = Query(...)):
    room = room_manager.get_room(room_id)
    if not room or not room.started or not room.game:
        raise HTTPException(status_code=400, detail="Game not found")

    game = room.game
    game._deal_pieces()
    game._set_round_start_player()

    hands = {
        player.name: [str(p) for p in player.hand]
        for player in game.players
    }
    return {"round": game.round_number, "hands": hands}

@router.post("/play")
async def play(data: dict):
    room_id = data.get("room_id")
    player_index = data.get("player_index")
    piece_indexes = data.get("piece_indexes")

    if room_id is None or player_index is None or piece_indexes is None:
        raise HTTPException(status_code=400, detail="Missing data")

    room = room_manager.get_room(room_id)
    if not room or not room.game:
        raise HTTPException(status_code=404, detail="Game not found")

    player = room.game.players[player_index]
    pieces = [player.hand[i] for i in piece_indexes]

    valid = is_valid_play(pieces)
    play_type = get_play_type(pieces) if valid else None

    return {
        "valid": valid,
        "play_type": play_type,
        "pieces": [str(p) for p in pieces]
    }
