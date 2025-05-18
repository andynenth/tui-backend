# piece.py
from engine.constants import PIECE_POINTS

class Piece:
    def __init__(self, kind):  # kind = "GENERAL_RED", "CANNON_BLACK", ...
        self.kind = kind
        self.point = PIECE_POINTS[kind]

    def __repr__(self):
        return f"{self.kind}({self.point})"

    @property
    def name(self):
        return self.kind.split("_")[0]

    @property
    def color(self):
        return self.kind.split("_")[1]
    
    def build_deck():
        counts = {
            "GENERAL": 1,
            "SOLDIER": 5
        }

        deck = []
        for kind in PIECE_POINTS:
            name = kind.split("_")[0]
            count = counts.get(name, 2)  # default = 2
            for _ in range(count):
                deck.append(Piece(kind))
        return deck
