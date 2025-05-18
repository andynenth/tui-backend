# player.py

class Player:
    """
    Represents a player in the game.
    Each player has a hand of pieces, a score, and a declared target for the round.
    Can be controlled by a human or AI (is_bot).
    """

    def __init__(self, name, is_bot=False):
        self.name = name                # Unique player name (e.g. "P1")
        self.is_bot = is_bot            # Flag to identify AI-controlled players
        self.hand = []                  # List of Piece objects currently held
        self.score = 0                  # Total score accumulated over rounds
        self.declared = 0              # Number of sets declared to capture this round
        self.zero_declares_in_a_row = 0  # Tracking for behavior patterns or scoring logic

    def reset_for_new_round(self):
        """
        Resets player-specific data at the start of a new round.
        """
        self.declared = 0

    def record_declaration(self, value: int):
        """
        Records the player's declared number of sets for the round.
        Also tracks consecutive zero-declarations (optional logic).
        """
        self.declared = value
        if value == 0:
            self.zero_declares_in_a_row += 1
        else:
            self.zero_declares_in_a_row = 0

    def has_red_general(self):
        """
        Returns True if the player holds the red GENERAL piece.
        Used to determine starting player for the first round.
        """
        return any(p.name == "GENERAL" and p.color == "RED" for p in self.hand)

    def remove_pieces(self, pieces):
        """
        Removes the specified pieces from the player's hand after they are played.
        """
        for piece in pieces:
            if piece in self.hand:
                self.hand.remove(piece)

    def choose_declaration(self, declared_total, is_last, input_func):
        """
        Asks the player to declare how many sets they will try to capture this round.
        The actual input is delegated to the provided input_func (CLI, UI, or AI).
        """
        value = input_func(declared_total, is_last)
        self.record_declaration(value)
        return value

    def choose_play(self, required_count, input_func, validate_play):
        """
        Prompts the player to select a play from their hand.
        Ensures the selected play has the correct number of pieces.
        Returns the selected pieces and whether the play is valid.
        """
        while True:
            selected = input_func()
            if len(selected) != required_count:
                continue
            is_valid = validate_play(selected)
            return selected, is_valid
