import random
from engine.piece import Piece
from engine.player import Player
from engine.ai import choose_best_play
from engine.rules import is_valid_play, get_play_type, compare_plays
from engine.scoring import calculate_score, calculate_round_scores
from engine.win_conditions import is_game_over, get_winners, WinConditionType
from engine.turn_resolution import resolve_turn_winner, TurnPlay

class Game:
    def __init__(self, win_condition_type=WinConditionType.FIRST_TO_REACH_50):
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

        self.last_round_winner = None
        self.redeal_multiplier = 1

    def _deal_pieces(self):
        deck = Piece.build_deck()
        random.shuffle(deck)
        for player in self.players:
            player.hand.clear()
        for i in range(32):
            self.players[i % 4].hand.append(deck[i])

    def _set_round_start_player(self):
        if self.last_round_winner:
            index = self.players.index(self.last_round_winner)
            self.current_order = self.players[index:] + self.players[:index]
        else:
            for i, player in enumerate(self.players):
                if player.has_red_general():
                    self.current_order = self.players[i:] + self.players[:i]
                    return

    def _check_redeal(self):
        for player in self.players:
            has_strong_piece = any(p.point > 9 for p in player.hand)  # ELEPHANT_BLACK = 9
            if not has_strong_piece:
                self.last_round_winner = player
                self.redeal_multiplier += 1
                return True  # Assume UI layer confirms redeal
        return False

    def play_round(self, declare_inputs, play_inputs):
        for p in self.players:
            p.declared = 0
        declared_total = 0

        round_scores = {p.name: 0 for p in self.players}
        pile_counts = {p.name: 0 for p in self.players}

        # --- Declaration Phase ---
        for i, player in enumerate(self.current_order):
            is_last = i == len(self.current_order) - 1
            value = declare_inputs[player.name](declared_total, is_last)
            player.record_declaration(value)
            declared_total += value

        turn_winner = self.current_order[0]
        total_turns = 0

        # --- Play Phase ---
        while all(len(p.hand) > 0 for p in self.players):
            turn_starter = turn_winner
            index = self.players.index(turn_starter)
            self.current_order = self.players[index:] + self.players[:index]

            while True:
                selected = play_inputs[turn_starter.name]()
                if 1 <= len(selected) <= 6 and is_valid_play(selected):
                    break
                else:
                    raise ValueError("Invalid opening play.")

            required_piece_count = len(selected)
            turn_plays = [TurnPlay(turn_starter, selected, True)]

            for player in self.current_order[1:]:
                if len(player.hand) < required_piece_count:
                    raise RuntimeError("Invalid state: player has insufficient pieces for this turn.")

                while True:
                    selected = play_inputs[player.name]()
                    if len(selected) != required_piece_count:
                        continue
                    else:
                        break

                is_valid = is_valid_play(selected)
                turn_plays.append(TurnPlay(player, selected, is_valid))

            winning_play = resolve_turn_winner(turn_plays)

            if winning_play:
                winner = winning_play.player
                pieces = winning_play.pieces
                pile_count = len(pieces)
                pile_counts[winner.name] += pile_count
                round_scores[winner.name] += pile_count
                turn_winner = winner

            for play in turn_plays:
                for piece in play.pieces:
                    if piece in play.player.hand:
                        play.player.hand.remove(piece)

            total_turns += 1

        score_data = calculate_round_scores(self.players, pile_counts, self.redeal_multiplier)

        self.redeal_multiplier = 1
        self.last_round_winner = turn_winner
        return score_data
