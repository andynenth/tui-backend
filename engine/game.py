# game.py

import random
from engine.piece import Piece
from engine.player import Player
from engine.ai import choose_best_play
from engine.rules import is_valid_play, get_play_type, compare_plays
from engine.scoring import calculate_score
from engine.win_conditions import is_game_over, get_winners, WinConditionType
import ui.cli as cli

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

    def start_game(self):
        while not is_game_over(self):
            self.round_number += 1
            cli.show_round_banner(self.round_number) 

            while True:
                self._deal_pieces()
                self._set_round_start_player()
                if self._check_redeal():
                    continue
                break

            self.play_round()
            cli.print_total_scores(self.players)

        winners = get_winners(self)
        cli.show_winner(winners)


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
                    cli.print_game_starter(player)
                    return

    def _check_redeal(self):
        for player in self.players:
            has_strong_piece = any(p.point > 9 for p in player.hand)  # ELEPHANT_BLACK = 9
            if not has_strong_piece:
                if cli.ask_redeal(player):
                    cli.print_redeal_request(player)
                    self.last_round_winner = player  # ได้เริ่มรอบถัดไป
                    self.redeal_multiplier += 1
                    return True  # redeal เกิดขึ้น
        return False

    def play_round(self):
        for p in self.players:
            p.declared = 0
        declared_total = 0
        round_scores = {p.name: 0 for p in self.players}
        pile_counts = {p.name: 0 for p in self.players}

        cli.print_declare_phase_banner()
        for i, player in enumerate(self.current_order):
            is_last = i == len(self.current_order) - 1
            value = cli.declare_input(player, declared_total, is_last)
            player.record_declaration(value)
            declared_total += value

        turn_winner = self.current_order[0]
        total_turns = 0

        while all(len(p.hand) > 0 for p in self.players):
            cli.print_turn_banner(total_turns + 1)
            turn_starter = turn_winner
            index = self.players.index(turn_starter)
            self.current_order = self.players[index:] + self.players[:index]

            while True:
                selected = cli.select_play_input(turn_starter)
                if 1 <= len(selected) <= 6 and is_valid_play(selected):
                    break
                else:
                    cli.print_error("Invalid opening play. Please select a valid set (1–6 pieces).")

            is_valid = is_valid_play(selected)
            play_type = get_play_type(selected)
            cli.print_played_pieces(turn_starter, selected, is_valid, play_type)
            
            required_count = len(selected)
            turn_plays = [(turn_starter, selected, True)]

            for player in self.current_order[1:]:
                if len(player.hand) < required_count:
                    cli.print_error("{player.name} cannot play: not enough pieces.")
                    turn_plays.append((player, [], False))
                    continue

                while True:
                    selected = cli.select_play_input(player)
                    if len(selected) != required_count:
                        cli.print_error("You must play exactly {required_count} pieces.")
                    else:
                        break

                is_valid = is_valid_play(selected)
                play_type = get_play_type(selected)
                cli.print_played_pieces(player, selected, is_valid, play_type)
                turn_plays.append((player, selected, is_valid))

            winner = None
            winning_play = None
            for player, play, valid in turn_plays:
                if not valid:
                    continue
                if not winning_play:
                    winner = player
                    winning_play = play
                else:
                    result = compare_plays(winning_play, play)
                    if result == 2:
                        winner = player
                        winning_play = play

            if winner:
                pile_count = len(winning_play)
                pile_counts[winner.name] += pile_count
                round_scores[winner.name] += pile_count
                cli.print_turn_winner(winner, winning_play, pile_count, round_scores)

                turn_winner = winner
            else:
                cli.print_error(">>> No valid plays. No one wins this turn.")

            for player, pieces, _ in turn_plays:
                for piece in pieces:
                    if piece in player.hand:
                        player.hand.remove(piece)

            total_turns += 1

        cli.print_end_of_round_banner()

        score_data = []
        for player in self.players:
            actual = pile_counts[player.name]
            declared = player.declared
            delta = calculate_score(declared, actual) * self.redeal_multiplier
            player.score += delta
            score_data.append({
                "player": player,
                "declared": declared,
                "actual": actual,
                "delta": delta,
                "multiplier": self.redeal_multiplier,
                "total": player.score
            })
        
        cli.print_score_summary(score_data)

        self.redeal_multiplier = 1
        self.last_round_winner = turn_winner

