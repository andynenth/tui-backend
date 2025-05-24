from fastapi import APIRouter, HTTPException
from engine.game import Game
from engine.rules import is_valid_play, get_play_type

router = APIRouter()

# ⏱ สร้างเกม global (ภายหลังแยก session ได้)
game = Game()

@router.get("/deal")
def deal():
    game._deal_pieces()
    game._set_round_start_player()
    hands = {
        player.name: [str(p) for p in player.hand]
        for player in game.players
    }
    return {"round": game.round_number, "hands": hands}

@router.post("/play")
def play(data: dict):
    player_index = data.get("player_index")
    piece_indexes = data.get("piece_indexes")

    if player_index is None or piece_indexes is None:
        raise HTTPException(status_code=400, detail="Missing data")

    player = game.players[player_index]
    pieces = [player.hand[i] for i in piece_indexes]

    valid = is_valid_play(pieces)
    play_type = get_play_type(pieces) if valid else None

    return {
        "valid": valid,
        "play_type": play_type,
        "pieces": [str(p) for p in pieces]
    }
