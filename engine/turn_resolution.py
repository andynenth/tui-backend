# turn_resolution.py

from dataclasses import dataclass
from typing import List, Optional
from engine.player import Player
from engine.piece import Piece
from engine.rules import compare_plays

@dataclass
class TurnPlay:
    """
    A data structure representing one player's action during a single turn.

    Attributes:
        player (Player): The player who played this turn.
        pieces (List[Piece]): The list of pieces the player selected to play.
        is_valid (bool): Whether the selected pieces form a valid play according to the game rules.
    """
    player: Player
    pieces: List[Piece]
    is_valid: bool


def resolve_turn_winner(turn_plays: List[TurnPlay]) -> Optional[TurnPlay]:
    """
    Determines the winning play in a single turn.

    Args:
        turn_plays (List[TurnPlay]): A list of TurnPlay objects, each representing a player's action during this turn.

    Returns:
        Optional[TurnPlay]: The TurnPlay object of the player who made the strongest valid play.
                            Returns None if there is no valid play or all plays are invalid.

    Note:
        - A valid play is required to be eligible for winning.
        - If multiple valid plays exist, they are compared using game rules to determine the winner.
        - The comparison is done using compare_plays() from the rules module.
    """

    winner: Optional[TurnPlay] = None
    winning_pieces: Optional[List[Piece]] = None

    for play in turn_plays:
        if not play.is_valid:
            # Skip invalid plays
            continue

        if not winner:
            # First valid play becomes the current winner candidate
            winner = play
            winning_pieces = play.pieces
        else:
            # Compare current winning play with the next valid one
            result = compare_plays(winning_pieces, play.pieces)

            if result == 2:
                # If the new play is stronger, update the winner
                winner = play
                winning_pieces = play.pieces

    # Return the winner TurnPlay or None if no one was valid
    return winner
