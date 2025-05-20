from dataclasses import dataclass
from typing import List, Optional
from engine.player import Player
from engine.piece import Piece
from engine.rules import compare_plays

@dataclass
class TurnPlay:
    """
    A data structure representing one player's action during a single turn.
    """
    player: Player
    pieces: List[Piece]
    is_valid: bool


@dataclass
class TurnResult:
    """
    Encapsulates the result of a full turn, including all plays and the winner.
    """
    plays: List[TurnPlay]                 # All plays in order
    winner: Optional[TurnPlay] = None     # Winning play (or None if no valid plays)


def resolve_turn(turn_plays: List[TurnPlay]) -> TurnResult:
    """
    Evaluates all plays in a turn and returns the full result (plays + winner).

    Returns:
        TurnResult: Includes all TurnPlay objects and the winning TurnPlay if any.
    """
    winner: Optional[TurnPlay] = None
    winning_pieces: Optional[List[Piece]] = None

    for play in turn_plays:
        if not play.is_valid:
            continue

        if not winner:
            winner = play
            winning_pieces = play.pieces
        else:
            result = compare_plays(winning_pieces, play.pieces)
            if result == 2:
                winner = play
                winning_pieces = play.pieces

    return TurnResult(plays=turn_plays, winner=winner)
