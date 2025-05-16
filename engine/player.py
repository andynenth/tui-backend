class Player:
    def __init__(self, name, is_bot=False):
        self.name = name
        self.hand = []
        self.score = 0
        self.declared = 0
        self.is_bot = is_bot
        self.zero_declares_in_a_row = 0

    def has_red_general(self):
        return any(p.name == "GENERAL" and p.color == "RED" for p in self.hand)

    def __repr__(self):
        return f"{self.name} - {self.score} pts"

    def record_declaration(self, value):
        """อัปเดตสถานะเมื่อผู้เล่นประกาศ"""
        self.declared = value
        if value == 0:
            self.zero_declares_in_a_row += 1
        else:
            self.zero_declares_in_a_row = 0
