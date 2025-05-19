# engine/interface.py

class GameInterface:
    """
    Represents the interface layer between Game logic and external input/output.
    All player inputs and game events should be routed through here.
    """

    def __init__(self, declare_inputs, play_inputs, on_play=None):
        """
        Parameters:
            declare_inputs (dict): player_name → function(total, is_last) → int
            play_inputs (dict): player_name → function() → List[Piece]
            on_play (function): (player, pieces, is_valid, play_type) → None
        """
        self.declare_inputs = declare_inputs
        self.play_inputs = play_inputs
        self.on_play = on_play or (lambda *_: None)  # no-op fallback
