# game.py

import random
from engine.piece import Piece
from engine.player import Player
from engine.ai import choose_best_play
from engine.rules import is_valid_play, get_play_type, get_valid_declares
from engine.scoring import calculate_round_scores
from engine.win_conditions import is_game_over, get_winners, WinConditionType
from engine.turn_resolution import resolve_turn, TurnPlay
import ui.cli as cli

class Game:
    def __init__(self, win_condition_type=WinConditionType.FIRST_TO_REACH_50):
        # Initialize the game with 4 players and default win conditions
        self.players = [
            Player("P1", is_bot=False),
            Player("P2", is_bot=False),
            Player("P3", is_bot=False),
            Player("P4", is_bot=False)
        ]
        self.current_order = []
        self.round_number = 0
        self.max_score = 50
        self.max_rounds = 20
        self.win_condition_type = win_condition_type
        
        self.last_round_winner = None  # Used to determine who starts the next round
        self.redeal_multiplier = 1     # Score multiplier when a redeal occurs

    def start_game(self):
        # Main game loop: continue until win condition is met
        while not is_game_over(self):
            self.round_number += 1
            cli.show_round_banner(self.round_number)

            # Deal pieces until a valid hand is dealt (or a redeal is accepted)
            while True:
                self._deal_pieces()
                self._set_round_start_player()
                if self._check_redeal():
                    continue  # Someone requested a redeal, repeat deal
                break

            # Play one round (declare → play turns → scoring)
            self.play_round()

        # Game ends → determine winners and display results
        winners = get_winners(self)
        cli.show_winner(winners)

    def _deal_pieces(self):
        # Shuffle and deal 32 pieces evenly among 4 players (8 each)
        deck = Piece.build_deck()
        random.shuffle(deck)
        for player in self.players:
            player.hand.clear()
        for i in range(32):
            self.players[i % 4].hand.append(deck[i])

    def _set_round_start_player(self):
        # Choose starting player for the round:
        # - If there's a previous round winner → they start
        # - Else, the player who holds the RED GENERAL goes first
        if self.last_round_winner:
            index = self.players.index(self.last_round_winner)
            self.current_order = self.players[index:] + self.players[:index]
        else:
            for i, player in enumerate(self.players):
                if player.has_red_general():
                    self.current_order = self.players[i:] + self.players[:i]
                    cli.print_game_starter(player)
                    return

    def _check_redeal(self):
        # Check if any player has a "weak hand" (no piece > 9 points)
        # If so, they are allowed to request a redeal
        for player in self.players:
            has_strong_piece = any(p.point > 9 for p in player.hand)  # ELEPHANT_BLACK = 9
            if not has_strong_piece:
                if cli.ask_redeal(player):
                    cli.print_redeal_request(player)
                    self.last_round_winner = player  # That player gets to start the next round
                    self.redeal_multiplier += 1     # Score multiplier increases with each redeal
                    return True
        return False

    def play_round(self):
        # Reset declarations from previous round
        for p in self.players:
            p.declared = 0
        declared_total = 0

        # Initialize tracking for piles captured and temporary scores
        round_scores = {p.name: 0 for p in self.players}
        pile_counts = {p.name: 0 for p in self.players}

        # ----------------------------------------
        # Phase 1: Declaration
        # ----------------------------------------
        # Each player declares how many "piles" (sets of pieces) they aim to capture this round.
        # Valid options are 0–8, but:
        # - Declaring 0 three rounds in a row is not allowed (must choose at least 1)
        # - The sum of all declarations cannot equal exactly 8 (enforced by rule logic)

        cli.print_declare_phase_banner()
        valid_declare = False
        while not valid_declare:
            declared_total = 0
            for i, player in enumerate(self.current_order):
                is_last = i == len(self.current_order) - 1

                # Get valid declare options based on current state
                options = get_valid_declares(player, declared_total, is_last)

                # Warn player if they are forced to declare non-zero
                if player.zero_declares_in_a_row >= 2:
                    cli.print_warning(f"{player.name} must declare at least 1 this round.")

                # Prompt until a valid declaration is entered
                while True:
                    value = cli.declare_input(player, declared_total, is_last)
                    if value in options:
                        break
                    else:
                        cli.print_error(f"Invalid declaration. Choose from {options}.")

                player.record_declaration(value)
                declared_total += value

            valid_declare = True  # Rule checks already handled by get_valid_declares()

        # ----------------------------------------
        # Phase 2: Turn-by-turn play
        # ----------------------------------------
        # Players take turns playing sets of 1–6 pieces.
        # The first player defines the number of pieces; others must match that count.
        # The best valid set wins the turn and collects the pile.
        # Turns continue until all players have no pieces left.

        turn_winner = self.current_order[0]  # First player to play
        total_turns = 0

        while all(len(p.hand) > 0 for p in self.players):
            cli.print_turn_banner(total_turns + 1)

            # Determine play order based on last turn's winner
            turn_starter = turn_winner
            index = self.players.index(turn_starter)
            self.current_order = self.players[index:] + self.players[:index]

            # --- First player makes the opening play ---
            while True:
                selected = cli.select_play_input(turn_starter)
                if 1 <= len(selected) <= 6 and is_valid_play(selected):
                    break
                else:
                    cli.print_error("Invalid opening play. Please select a valid set (1–6 pieces).")

            is_valid = is_valid_play(selected)
            play_type = get_play_type(selected)
            cli.print_played_pieces(turn_starter, selected, is_valid, play_type)

            required_piece_count = len(selected)
            turn_plays = [TurnPlay(turn_starter, selected, True)]

            # --- Other players respond ---
            for player in self.current_order[1:]:
                # If a player doesn't have enough pieces, it's an error
                if len(player.hand) < required_piece_count:
                    cli.print_error(
                        f"ERROR: {player.name} has only {len(player.hand)} pieces but needs {required_piece_count}."
                    )
                    raise RuntimeError("Invalid state: player has insufficient pieces for this turn.")

                # Prompt until a play with the correct number of pieces is selected
                while True:
                    selected = cli.select_play_input(player)
                    if len(selected) != required_piece_count:
                        cli.print_error(f"You must play exactly {required_piece_count} pieces.")
                    else:
                        break

                is_valid = is_valid_play(selected)
                play_type = get_play_type(selected)
                cli.print_played_pieces(player, selected, is_valid, play_type)
                turn_plays.append(TurnPlay(player, selected, is_valid))

            # --- Determine turn winner ---
            turn_result = resolve_turn(turn_plays)

            if turn_result.winner:
                winner = turn_result.winner.player
                pieces = turn_result.winner.pieces
                pile_count = len(pieces)

                # Update pile count and score
                pile_counts[winner.name] += pile_count
                round_scores[winner.name] += pile_count
                cli.print_turn_winner(turn_result, pile_count, round_scores)
                turn_winner = winner
            else:
                cli.print_error(">>> No valid plays. No one wins this turn.")

            # --- Remove played pieces from hands ---
            for play in turn_plays:
                for piece in play.pieces:
                    if piece in play.player.hand:
                        play.player.hand.remove(piece)

            total_turns += 1

        # ----------------------------------------
        # Phase 3: Scoring
        # ----------------------------------------
        # Compare number of piles each player captured vs. their declaration.
        # Score is based on:
        # - Exact match → declared + 5 bonus
        # - Over/under → penalty
        # - Declared 0 → +3 if succeeded, minus actual if failed
        # If this round was a redeal → multiply score accordingly

        cli.print_end_of_round_banner()
        score_data = calculate_round_scores(self.players, pile_counts, self.redeal_multiplier)
        cli.print_score_summary(score_data)

        # Prepare for next round
        self.redeal_multiplier = 1
        self.last_round_winner = turn_winner
