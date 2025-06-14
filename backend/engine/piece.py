# backend/engine/piece.py

from engine.constants import PIECE_POINTS

class Piece:
    def __init__(self, kind):
        """
        Create a piece from a given kind string, e.g. "GENERAL_RED", "CANNON_BLACK"
        Assigns point value using PIECE_POINTS from constants.py
        """
        self.kind = kind                  # Combined string identifier, e.g., "GENERAL_RED"
        self.point = PIECE_POINTS[kind]   # Point value for scoring and comparison

    def __repr__(self):
        # Display format, e.g., GENERAL_RED(14)
        return f"{self.kind}({self.point})"

    @property
    def name(self):
        # Extract the piece type (e.g., "GENERAL") from kind
        return self.kind.split("_")[0]

    @property
    def color(self):
        # Extract the piece color (e.g., "RED" or "BLACK") from kind
        return self.kind.split("_")[1]

    @staticmethod
    def build_deck():
        """
        Create the full deck of 32 pieces.

        Rules:
        - Some piece types (e.g., SOLDIER) appear more often.
        - Use PIECE_POINTS to determine available kinds (e.g., GENERAL_RED, HORSE_BLACK, etc.)
        - Default count per kind = 2, unless overridden below.
        """

        # How many copies of each piece type to include in the deck
        counts = {
            "GENERAL": 1,   # Only one of each GENERAL (RED and BLACK)
            "SOLDIER": 5    # Five of each SOLDIER (RED and BLACK)
            # All others default to 2
        }

        deck = []
        for kind in PIECE_POINTS:
            name = kind.split("_")[0]
            count = counts.get(name, 2)  # Use default = 2 if not in `counts`
            for _ in range(count):
                deck.append(Piece(kind))
        return deck
