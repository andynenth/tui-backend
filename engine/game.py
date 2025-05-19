# game.py

import random
from engine.piece import Piece
from engine.player import Player
from engine.rules import is_valid_play, get_play_type, compare_plays
from engine.scoring import calculate_round_scores
from engine.win_conditions import is_game_over, get_winners, WinConditionType
from engine.turn_resolution import resolve_turn_winner, TurnPlay
from engine.interface import GameInterface

class Game:
    """
    Core game engine that manages players, turns, declaration, and scoring.
    Designed for 4 players. Each round follows a fixed sequence:
    - Deal pieces
    - Declaration phase
    - Turn-based play phase
    - Scoring phase
    """

    def __init__(self, win_condition_type=WinConditionType.FIRST_TO_REACH_50):
        # Game initialization
        self.players = [
            Player("P1", is_bot=False),
            Player("P2", is_bot=False),
            Player("P3", is_bot=False),
            Player("P4", is_bot=False)
        ]
        self.current_order = []           # Turn order for current round
        self.round_number = 0             # Current round number
        self.max_score = 50               # Default win condition
        self.max_rounds = 20
        self.win_condition_type = win_condition_type

        self.last_round_winner = None     # Used to determine first player in next round
        self.redeal_multiplier = 1        # Score multiplier when redeal is triggered

    def _deal_pieces(self):
        """
        Randomly deals 8 pieces to each player from a full deck of 32.
        """
        deck = Piece.build_deck()
        random.shuffle(deck)
        for player in self.players:
            player.hand.clear()
        for i in range(32):
            self.players[i % 4].hand.append(deck[i])

    def _set_round_start_player(self):
        """
        Sets the player order for this round.
        - If there was a winner last round, they start first.
        - Otherwise, the player who holds the red GENERAL starts first.
        """
        if self.last_round_winner:
            index = self.players.index(self.last_round_winner)
            self.current_order = self.players[index:] + self.players[:index]
        else:
            for i, player in enumerate(self.players):
                if player.has_red_general():
                    self.current_order = self.players[i:] + self.players[:i]
                    break

        # Ensure that a starting player is found
        assert self.current_order, (
            "❌ ERROR: No player has GENERAL(RED). Cannot determine starting player. "
            "This likely means there's a bug in the dealing logic or piece definitions."
        )

    def _check_redeal(self):
        """
        Checks if any player has no strong piece (point > 9).
        If true, triggers a redeal with increased score multiplier.
        """
        for player in self.players:
            has_strong_piece = any(p.point > 9 for p in player.hand)
            if not has_strong_piece:
                self.last_round_winner = player  # Player who requested redeal starts next round
                self.redeal_multiplier += 1
                return True
        return False

    def play_round(self, interface: GameInterface):

        """
        Executes one full round: Declaration → Play turns → Scoring.
        Input functions are passed in as dicts to allow CLI/AI integration.
        Returns score summary for the round.
        """

        # Reset all players' declarations at the beginning of the round
        for player in self.players:
            player.reset_for_new_round()
        declared_total = 0
        
        # Prepare tracking dicts for turn-by-turn results
        round_scores = {p.name: 0 for p in self.players}
        pile_counts = {p.name: 0 for p in self.players}

        # -------------------------------
        # Declaration Phase
        # -------------------------------
        for i, player in enumerate(self.current_order):
            is_last = i == len(self.current_order) - 1
            # Each player declares how many sets they plan to capture
            input_func = interface.declare_inputs[player.name]
            player.choose_declaration(declared_total, is_last, input_func)
            declared_total += player.declared

        # First turn is started by first player in the order
        turn_winner = self.current_order[0]
        total_turns = 0

        # -------------------------------
        # Turn-Based Play Phase
        # -------------------------------
        while all(len(p.hand) > 0 for p in self.players):

            # Determine new play order (starting from last turn winner)
            turn_starter = turn_winner
            index = self.players.index(turn_starter)
            self.current_order = self.players[index:] + self.players[:index]

            # First player makes a valid opening play (1–6 pieces)
            while True:
                selected = interface.play_inputs[turn_starter.name]()
                if 1 <= len(selected) <= 6 and is_valid_play(selected):
                    break
                else:
                    raise ValueError("Invalid opening play.")

            play_type = get_play_type(selected)

            interface.on_play(turn_starter, selected, True, play_type)

            required_piece_count = len(selected)
            turn_plays = [TurnPlay(turn_starter, selected, True)]


            # All other players must respond with the same number of pieces
            for player in self.current_order[1:]:
                if len(player.hand) < required_piece_count:
                    raise RuntimeError(f"{player.name} has insufficient pieces.")

                selected, is_valid = player.choose_play(
                    required_piece_count,
                    interface.play_inputs[player.name],
                    is_valid_play
                )
                play_type = get_play_type(selected) if is_valid else "INVALID"

                interface.on_play(player, selected, is_valid, play_type)

                turn_plays.append(TurnPlay(player, selected, is_valid))


            # Determine winner of this turn (based on highest valid play)
            winning_play = resolve_turn_winner(turn_plays)

            if winning_play:
                winner = winning_play.player
                pieces = winning_play.pieces
                pile_count = len(pieces)
                pile_counts[winner.name] += pile_count
                round_scores[winner.name] += pile_count
                turn_winner = winner  # Winner starts next turn

            # Remove played pieces from players' hands
            for play in turn_plays:
                play.player.remove_pieces(play.pieces)

            total_turns += 1

        # -------------------------------
        # Scoring Phase
        # -------------------------------
        score_data = calculate_round_scores(self.players, pile_counts, self.redeal_multiplier)

        # Reset redeal multiplier for next round
        self.redeal_multiplier = 1
        self.last_round_winner = turn_winner

        return score_data
