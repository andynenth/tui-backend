import random
from engine.piece import Piece
from engine.player import Player
from engine.ai import choose_best_play
from engine.rules import is_valid_play, get_play_type, compare_plays
from engine.scoring import calculate_score
import ui.cli as cli

class Game:
    def __init__(self):
        self.players = [
            Player("P1", is_bot=False),
            Player("P2", is_bot=False),
            Player("P3", is_bot=False),
            Player("P4", is_bot=False)
        ]
        self.current_order = []
        self.round_number = 0
        self.max_score = 50
        self.last_round_winner = None  # 🆕 เพิ่มเพื่อกำหนดผู้เริ่มในรอบถัดไป

    def start_game(self):
        while all(p.score < self.max_score for p in self.players):
            self.round_number += 1
            print(f"\n===== ROUND {self.round_number} =====")
            self._deal_pieces()
            self._set_round_start_player()
            self.play_round()
            self._print_scores()

        self._announce_winner()

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
                    print(f"{player.name} starts the game (has GENERAL_RED)")
                    return

    def play_round(self):
        for p in self.players:
            p.declared = 0
        declared_total = 0

        print("\n--- Declare Phase ---")
        for i, player in enumerate(self.current_order):
            is_last = i == len(self.current_order) - 1
            if player.is_bot:
                options = [0, 1, 2, 3, 4, 5, 6, 7, 8]
                player.declared = random.choice([o for o in options if not (is_last and declared_total + o == 8)])
                print(f"{player.name} declares {player.declared}")
                declared_total += player.declared
            else:
                value = cli.declare_input(player, declared_total, is_last)
                player.record_declaration(value)
                declared_total += value

        turn_winner = self.current_order[0]
        total_turns = 0
        pile_counts = {p.name: 0 for p in self.players}

        ##
        round_scores = {p.name: 0 for p in self.players}

        while all(len(p.hand) > 0 for p in self.players):
            print(f"\n--- Turn {total_turns + 1} ---")
            turn_starter = turn_winner
            index = self.players.index(turn_starter)
            self.current_order = self.players[index:] + self.players[:index]

            # 🆕 กำหนดจำนวนหมากที่ต้องลง จากผู้เล่นแรก
            while True:
                if turn_starter.is_bot:
                    selected = choose_best_play(turn_starter.hand)
                else:
                    selected = cli.select_play_input(turn_starter)

                if 1 <= len(selected) <= 6 and is_valid_play(selected):
                    break
                else:
                    print("❌ Invalid opening play. Please select a valid set (1-6 pieces).")

            required_count = len(selected)
            turn_plays = [(turn_starter, selected, True)]

            for player in self.current_order[1:]:
                if len(player.hand) < required_count:
                    print(f"{player.name} cannot play: not enough pieces.")
                    turn_plays.append((player, [], False))
                    continue

                if player.is_bot:
                    valid_options = [p for p in choose_best_play(player.hand) if len(p) == required_count]
                    selected = valid_options if valid_options else []
                else:
                    while True:
                        selected = cli.select_play_input(player)
                        if len(selected) != required_count:
                            print(f"❌ You must play exactly {required_count} pieces.")
                        else:
                            break

                is_valid = is_valid_play(selected)
                turn_plays.append((player, selected, is_valid))
                play_type = get_play_type(selected)
                cli.print_played_pieces(player, selected, is_valid, play_type)

            # 🆕 หาผู้ชนะ: เรียงตามลำดับการเล่น หากแต้มเท่ากัน
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
                turn_winner = winner  # 🆕 ได้เริ่มตาต่อไป
                pile_count = len(winning_play)
                pile_counts[winner.name] += pile_count
                round_scores[winner.name] += pile_count

                print(f">>> {winner.name} wins {pile_count} pts the turn with {winning_play}, the current score is {round_scores[winner.name]}")

            else:
                print(">>> No valid plays. No one wins this turn.")

            # 🆕 ลบหมากจากมือ
            for player, pieces, _ in turn_plays:
                for piece in pieces:
                    if piece in player.hand:
                        player.hand.remove(piece)

            total_turns += 1

        # 🆕 จบรอบ: คิดคะแนนตามประกาศ vs กองที่กินได้จริง
        print("\n--- End of Round ---")
        for player in self.players:
            actual = pile_counts[player.name]
            declared = player.declared
            score_delta = calculate_score(declared, actual)
            player.score += score_delta
            print(f"{player.name}: declared {declared}, got {actual} → {score_delta:+} pts")

        self.last_round_winner = turn_winner

    def _print_scores(self):
        print("\n--- Total Scores ---")
        for player in self.players:
            print(f"{player.name}: {player.score} pts")

    def _announce_winner(self):
        winner = max(self.players, key=lambda p: p.score)
        print(f"\n🏆 {winner.name} wins the game with {winner.score} points!")
