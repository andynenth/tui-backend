# backend/engine/player.py

import random


class Player:
    def __init__(self, name, is_bot=False, available_colors=None):
        self.name = name  # Player's name (e.g., "P1", "P2", etc.)
        self.hand = (
            []
        )  # List of current pieces in hand (max 8 at the start of each round)
        self.score = 0  # Total score accumulated throughout the game
        self.declared = 0  # Number of piles the player declared for this round
        self.captured_piles = (
            0  # Number of pieces captured this round (reset each round)
        )
        self.is_bot = is_bot  # Whether this player is AI-controlled
        self.zero_declares_in_a_row = (
            0  # Counter for how many rounds this player has declared 0 in a row
        )

        # Add avatar color assignment
        self.avatar_color = self._assign_avatar_color(available_colors)

        # Game statistics (cumulative across all rounds)
        self.turns_won = 0  # Total number of turns won in the game
        self.perfect_rounds = 0  # Number of rounds where declared == actual (non-zero)

        # Connection tracking (for disconnect handling)
        self.is_connected = True  # Whether player is currently connected
        self.disconnect_time = None  # When player disconnected
        self.original_is_bot = is_bot  # Store original bot state for reconnection

    def _assign_avatar_color(self, available_colors=None):
        """Assign a random avatar color to human players"""
        if self.is_bot:
            return None  # Bots don't get colors

        # Default colors
        all_colors = [
            "blue",
            "purple",
            "orange",
            "red",
            "green",
            "teal",
            "pink",
            "yellow",
        ]

        # Use available colors if provided, otherwise use all colors
        colors_to_choose_from = available_colors if available_colors else all_colors

        if not colors_to_choose_from:
            # Fallback: if no colors available, cycle through colors based on player name hash
            color_index = hash(self.name) % len(all_colors)
            color = all_colors[color_index]
            print(
                f"🎨 DEBUG: Assigned fallback avatar color '{color}' to player '{self.name}' (all colors taken)"
            )
        else:
            color = random.choice(colors_to_choose_from)
            print(
                f"🎨 DEBUG: Assigned avatar color '{color}' to player '{self.name}' from {len(colors_to_choose_from)} available colors"
            )

        return color

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
        """
        Reset player state for the next round.

        Clears the player's hand and resets round-specific counters
        (declared value and captured piles) while preserving game-level
        state like score and zero declaration tracking.
        """
        self.declared = 0
        self.captured_piles = 0
        self.hand.clear()
