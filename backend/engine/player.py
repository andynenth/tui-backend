# backend/engine/player.py

class Player:
    def __init__(self, name, is_bot=False):
        self.name = name                   # Player's name (e.g., "P1", "P2", etc.)
        self.hand = []                    # List of current pieces in hand (max 8 at the start of each round)
        self.score = 0                    # Total score accumulated throughout the game
        self.declared = 0                 # Number of piles the player declared for this round
        self.captured_piles = 0           # Number of pieces captured this round (reset each round)
        self.is_bot = is_bot              # Whether this player is AI-controlled
        self.zero_declares_in_a_row = 0   # Counter for how many rounds this player has declared 0 in a row
        
        # Game statistics (cumulative across all rounds)
        self.turns_won = 0                # Total number of turns won in the game
        self.perfect_rounds = 0           # Number of rounds where declared == actual (non-zero)

    def has_red_general(self):
        """
        Check if the player has the RED GENERAL piece.
        This determines who starts the first round.
        """
        return any(p.name == "GENERAL" and p.color == "RED" for p in self.hand)

    def __repr__(self):
        # Display format for debugging/logging: e.g., "P1 - 12 pts"
        return f"{self.name} - {self.score} pts"

    def record_declaration(self, value):
        """
        Update player's state when they declare how many piles they aim to capture.
        - If value == 0, increment the zero-declare streak.
        - Otherwise, reset the zero-declare streak.
        """
        self.declared = value
        if value == 0:
            self.zero_declares_in_a_row += 1
        else:
            self.zero_declares_in_a_row = 0
    
    def reset_for_next_round(self):
        self.declared = 0
        self.captured_piles = 0
        self.hand.clear()