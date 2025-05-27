import random
from engine.piece import Piece
from engine.player import Player
import engine.ai as ai
from engine.rules import is_valid_play, get_play_type, get_valid_declares
from engine.scoring import calculate_round_scores
from engine.win_conditions import is_game_over, get_winners, WinConditionType
from engine.turn_resolution import resolve_turn, TurnPlay


class Game:
    def __init__(self, players, interface=None, win_condition_type=WinConditionType.FIRST_TO_REACH_50):
        # Core game state
        self.players = players
        self.interface = interface  # Adapter for CLI, GUI, or API
        self.current_order = []     # Player order for each round
        self.round_number = 0
        self.max_score = 50
        self.max_rounds = 20
        self.win_condition_type = win_condition_type

        # Round-specific state
        self.last_round_winner = None      # Player who won the last round
        self.redeal_multiplier = 1         # Score multiplier increases with each redeal
        self.current_turn_plays = []       # Stores TurnPlay objects for current turn
        self.required_piece_count = None   # Number of pieces required this turn
        self.turn_order = []               # Player order for current turn
        self.last_turn_winner = None       # Player who won the last turn


    def prepare_round(self) -> dict:
        """Prepare for a new round: shuffle and deal pieces, determine starting player, reset declarations."""
        self.round_number += 1
        self._deal_pieces()
        self._set_round_start_player()

        # Initialize pile and score tracking
        self.pile_counts = {p.name: 0 for p in self.players}
        self.round_scores = {p.name: 0 for p in self.players}

        # Reset player declarations
        for player in self.players:
            player.declared = 0

        return {
            "round": self.round_number,
            "starter": self.current_order[0].name,
            "hands": {
                player.name: [str(piece) for piece in player.hand]
                for player in self.players
            }
        }

    def request_redeal(self, player_name: str) -> dict:
        """Allow a player to request a redeal if they have no strong pieces."""
        player = self.get_player(player_name)

        has_strong_piece = any(p.point > 9 for p in player.hand)
        if has_strong_piece:
            return {
                "redeal_allowed": False,
                "reason": "You have strong pieces.",
                "hand": [str(p) for p in player.hand]
            }

        self.last_round_winner = player
        self.redeal_multiplier += 1

        return {
            "redeal_allowed": True,
            "new_starter": player.name,
            "multiplier": self.redeal_multiplier
        }

    def get_player(self, name: str) -> Player:
        """Retrieve a Player instance by name."""
        for p in self.players:
            if p.name == name:
                return p
        raise ValueError(f"Player '{name}' not found")

    def declare(self, player_name: str, value: int) -> dict:
        """Allow a player to declare how many piles they plan to win this round."""
        player = self.get_player(player_name)

        if player.declared != 0:
            return {
                "status": "already_declared",
                "message": f"{player.name} has already declared {player.declared}."
            }

        if player.zero_declares_in_a_row >= 2 and value == 0:
            return {
                "status": "error",
                "message": f"{player.name} must declare at least 1 after two zeros in a row."
            }

        player.record_declaration(value)

        total_declared = sum(p.declared for p in self.players)
        declarations = {p.name: p.declared for p in self.players}

        return {
            "status": "ok",
            "declared_by": player.name,
            "value": value,
            "total_declared": total_declared,
            "declarations": declarations
        }

    def all_players_declared(self) -> bool:
        """Check if all players have declared."""
        return all(p.declared is not None for p in self.players)

    def play_turn(self, player_name: str, piece_indexes: list[int]) -> dict:
        """Handle a player's move, validate it, and resolve the turn if all players have played."""
        player = self.get_player(player_name)

        if player not in self.turn_order:
            return {"status": "error", "message": f"{player.name} is not in current turn order."}

        if any(play.player == player for play in self.current_turn_plays):
            return {"status": "error", "message": f"{player.name} has already played this turn."}

        try:
            selected = [player.hand[i] for i in piece_indexes]
        except IndexError:
            return {"status": "error", "message": "Invalid piece index."}

        if not (1 <= len(selected) <= 6):
            return {"status": "error", "message": "You must play between 1–6 pieces."}

        if len(self.current_turn_plays) == 0:
            # First player sets required piece count and determines order
            self.required_piece_count = len(selected)
            self.turn_order = self._rotate_players_starting_from(player)
        else:
            if len(selected) != self.required_piece_count:
                return {"status": "error", "message": f"You must play exactly {self.required_piece_count} pieces."}

        is_valid = is_valid_play(selected)
        play_type = get_play_type(selected) if is_valid else None

        self.current_turn_plays.append(TurnPlay(player, selected, is_valid))

        for piece in selected:
            player.hand.remove(piece)

        if len(self.current_turn_plays) < len(self.players):
            return {
                "status": "waiting",
                "player": player.name,
                "pieces": [str(p) for p in selected],
                "is_valid": is_valid,
                "play_type": play_type
            }

        # All players have played → resolve the turn
        result = resolve_turn(self.current_turn_plays)
        winner = result.winner.player if result.winner else None

        if result.winner:
            pile = len(result.winner.pieces)
            self.pile_counts[winner.name] += pile
            self.round_scores[winner.name] += pile
            self.last_turn_winner = winner
            pile_count = pile
        else:
            pile_count = 0

        turn_summary = {
            "status": "resolved",
            "winner": winner.name if winner else None,
            "plays": [
                {
                    "player": play.player.name,
                    "pieces": [str(p) for p in play.pieces],
                    "is_valid": play.is_valid
                }
                for play in self.current_turn_plays
            ],
            "pile_count": pile_count
        }

        # Reset turn state
        self.current_turn_plays = []
        self.required_piece_count = None

        return turn_summary

    def _rotate_players_starting_from(self, starter: Player) -> list[Player]:
        """Generate a player order starting from a given player."""
        idx = self.players.index(starter)
        return self.players[idx:] + self.players[:idx]

    def score_round(self) -> dict:
        """Finalize the round: calculate scores, apply bonuses, and update total scores."""
        score_data = calculate_round_scores(
            players=self.players,
            pile_counts=self.pile_counts,
            multiplier=self.redeal_multiplier
        )

        for p in self.players:
            p.score += score_data["scores"][p.name]

        summary = {
            "round": self.round_number,
            "scores": score_data["scores"],
            "bonuses": score_data["bonuses"],
            "declares": {p.name: p.declared for p in self.players},
            "captured": self.pile_counts,
            "multiplier": self.redeal_multiplier
        }

        # Reset for next round
        self.redeal_multiplier = 1
        self.last_round_winner = self._get_round_winner()
        self.pile_counts = {}
        self.round_scores = {}

        for player in self.players:
            player.reset_for_next_round()

        return summary

    def _get_round_winner(self) -> Player:
        """Determine the player with the highest total score so far."""
        max_score = -1
        winner = None
        for p in self.players:
            if p.score > max_score:
                max_score = p.score
                winner = p
        return winner

    def is_game_over(self) -> bool:
        """Check if game has ended based on the configured win condition."""
        if self.win_condition_type == WinConditionType.FIRST_TO_REACH_50:
            return any(p.score >= self.max_score for p in self.players)

        if self.win_condition_type == WinConditionType.AFTER_20_ROUNDS:
            return self.round_number >= self.max_rounds

        return False

    def _deal_pieces(self):
        """Shuffle and deal 32 pieces evenly among the 4 players."""
        deck = Piece.build_deck()
        random.shuffle(deck)
        for player in self.players:
            player.hand.clear()
        for i in range(32):
            self.players[i % 4].hand.append(deck[i])

    def _set_round_start_player(self):
        """Determine the starting player for this round."""
        if self.last_round_winner:
            index = self.players.index(self.last_round_winner)
            self.current_order = self.players[index:] + self.players[:index]
        else:
            for i, player in enumerate(self.players):
                if player.has_red_general():
                    self.current_order = self.players[i:] + self.players[:i]
                    return

    def _check_redeal(self):
        """(Optional Legacy) Check for weak hands and allow redeal via interface."""
        for player in self.players:
            has_strong_piece = any(p.point > 9 for p in player.hand)
            if not has_strong_piece:
                if self.interface.ask_redeal(player):
                    self.last_round_winner = player
                    self.redeal_multiplier += 1
                    return True
        return False
