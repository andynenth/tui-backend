# backend/engine/game.py

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
        print(f"🔄 DEBUG: Starting prepare_round() - Round {self.round_number + 1}")
        
        self.round_number += 1
        # self._deal_pieces()
        # self._deal_weak_hand(0)
        # self._deal_guaranteed_no_redeal()
        self._deal_red_general_no_redeal(0)
        
        self._set_round_start_player()
                
        # Initialize pile and score tracking
        self.pile_counts = {p.name: 0 for p in self.players}
        self.round_scores = {p.name: 0 for p in self.players}
        
        # Reset player declarations
        for player in self.players:
            player.declared = 0

        print(f"🔍 DEBUG: Checking for weak hands...")
        
        # Check for weak hands
        weak_players = []
        for player in self.players:
            player_hand = [str(piece) for piece in player.hand]
            print(f"🔍 DEBUG: {player.name} hand: {player_hand}")
            
            has_strong = any(p.point > 9 for p in player.hand)
            print(f"🔍 DEBUG: {player.name} has_strong: {has_strong}")
            
            if not has_strong:
                weak_players.append(player.name)
                print(f"🔍 DEBUG: {player.name} added to weak_players!")
        
        need_redeal = len(weak_players) > 0
        print(f"🔍 DEBUG: weak_players: {weak_players}")
        print(f"🔍 DEBUG: need_redeal: {need_redeal}")
        
        result = {
            "round": self.round_number,
            "starter": self.current_order[0].name,
            "hands": {
                player.name: [str(piece) for piece in player.hand]
                for player in self.players
            },
            "weak_players": weak_players,
            "need_redeal": need_redeal
        }
        
        print(f"🔍 DEBUG: prepare_round() result keys: {list(result.keys())}")
        print(f"🔍 DEBUG: prepare_round() returning: {result}")
        
        return result

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
            
    # ===== SHARED HELPER METHODS =====

    def _prepare_deck_and_hands(self):
        """Helper: Prepare shuffled deck and clear all player hands"""
        deck = Piece.build_deck()
        random.shuffle(deck)
        
        for player in self.players:
            player.hand.clear()
        
        return deck

    def _categorize_pieces(self, deck, exclude_red_general=False):
        """
        Helper: Categorize pieces by strength and type
        
        Returns:
            dict: {
                'red_general': piece or None,
                'strong_pieces': [pieces > 9 points, excluding RED_GENERAL],
                'weak_pieces': [pieces <= 9 points],
                'all_other': [all pieces excluding RED_GENERAL if specified]
            }
        """
        categories = {
            'red_general': None,
            'strong_pieces': [],
            'weak_pieces': [],
            'all_other': []
        }
        
        for piece in deck:
            if "GENERAL_RED" in str(piece):
                categories['red_general'] = piece
                if not exclude_red_general:
                    categories['all_other'].append(piece)
            elif piece.point > 9:
                categories['strong_pieces'].append(piece)
                categories['all_other'].append(piece)
            else:
                categories['weak_pieces'].append(piece)
                categories['all_other'].append(piece)
        
        return categories

    def _verify_and_report_hands(self, expected_starter=None):
        """Helper: Verify final hands and report results"""
        print(f"🔧 DEBUG: Final hands verification:")
        
        for i, player in enumerate(self.players):
            strong_count = sum(1 for p in player.hand if p.point > 9)
            has_red_general = any("GENERAL_RED" in str(p) for p in player.hand)
            is_expected_starter = (expected_starter is not None and i == expected_starter)
            
            print(f"  {player.name}: {[str(p) for p in player.hand]}")
            print(f"    → Strong pieces (>9): {strong_count}")
            print(f"    → Has RED_GENERAL: {has_red_general}")
            if expected_starter is not None:
                print(f"    → Is expected starter: {is_expected_starter}")
            
            # Warnings
            if strong_count == 0:
                print(f"    ⚠️ WARNING: {player.name} has NO strong pieces!")
            if is_expected_starter and not has_red_general:
                print(f"    ❌ ERROR: Expected starter {player.name} doesn't have RED_GENERAL!")

    def _fill_remaining_slots(self, available_pieces):
        """Helper: Fill remaining hand slots for all players"""
        random.shuffle(available_pieces)
        piece_index = 0
        
        for player in self.players:
            while len(player.hand) < 8 and piece_index < len(available_pieces):
                player.hand.append(available_pieces[piece_index])
                piece_index += 1

    # ===== REFACTORED MAIN METHODS =====

    def _deal_weak_hand(self, weak_player_index=0, max_weak_points=9):
        """Deal weak hand to specific player for testing redeal functionality."""
        print(f"🔧 DEBUG: Dealing weak hand to player {weak_player_index} (max {max_weak_points} points)")
        
        # Use helper methods
        deck = self._prepare_deck_and_hands()
        categories = self._categorize_pieces(deck)
        
        weak_pieces = categories['weak_pieces']
        strong_pieces = categories['strong_pieces']
        if categories['red_general']:
            strong_pieces.append(categories['red_general'])
        
        print(f"🔧 DEBUG: Found {len(weak_pieces)} weak pieces (≤{max_weak_points}), {len(strong_pieces)} strong pieces (>{max_weak_points})")
        
        # Deal weak hand to specified player
        if 0 <= weak_player_index < len(self.players):
            if len(weak_pieces) >= 8:
                self.players[weak_player_index].hand = weak_pieces[:8]
                remaining_pieces = weak_pieces[8:] + strong_pieces
            else:
                self.players[weak_player_index].hand = weak_pieces + strong_pieces[:8-len(weak_pieces)]
                remaining_pieces = strong_pieces[8-len(weak_pieces):]
            
            print(f"🔧 DEBUG: {self.players[weak_player_index].name} weak hand assigned")
        else:
            print(f"🔧 DEBUG: Invalid player index {weak_player_index}")
            remaining_pieces = deck
        
        # Deal to other players
        current_piece = 0
        for i, player in enumerate(self.players):
            if i != weak_player_index and len(player.hand) == 0:
                end_idx = min(current_piece + 8, len(remaining_pieces))
                player.hand = remaining_pieces[current_piece:end_idx]
                current_piece = end_idx
        
        # Verify results
        self._verify_and_report_hands()

    def _deal_guaranteed_no_redeal(self):
        """Alternative implementation using same pattern as _deal_weak_hand"""
        print(f"🔧 DEBUG: Dealing guaranteed NO redeal hands (v2)")
        
        # Use helper methods  
        deck = self._prepare_deck_and_hands()
        categories = self._categorize_pieces(deck)
        
        strong_pieces = categories['strong_pieces']
        if categories['red_general']:
            strong_pieces.append(categories['red_general'])
        weak_pieces = categories['weak_pieces']
        
        print(f"🔧 DEBUG: Found {len(weak_pieces)} weak pieces (≤9), {len(strong_pieces)} strong pieces (>9)")
        
        # Check if we have enough strong pieces
        if len(strong_pieces) < len(self.players):
            print(f"❌ ERROR: Not enough strong pieces for all players! Falling back to regular deal.")
            self._deal_pieces()
            return
        
        # Give each player 1 strong piece + 7 weak pieces (if available)
        for i, player in enumerate(self.players):
            # Give 1 strong piece
            player.hand.append(strong_pieces[i])
            
            # Fill with weak pieces (up to 7 more)
            pieces_to_take = min(7, len(weak_pieces))
            if pieces_to_take > 0:
                player.hand.extend(weak_pieces[:pieces_to_take])
                weak_pieces = weak_pieces[pieces_to_take:]
        
        # If anyone doesn't have 8 pieces yet, use remaining pieces
        remaining_pieces = strong_pieces[len(self.players):] + weak_pieces
        self._fill_remaining_slots(remaining_pieces)
        
        # Verify results
        self._verify_and_report_hands()

    def _deal_red_general_no_redeal(self, starter_player=0):
        """Give specific player RED_GENERAL and ensure NO ONE has weak hands."""
        print(f"🔧 DEBUG: Simple dealing - Player {starter_player} gets RED_GENERAL, no one gets weak hands")
        
        # Use helper methods
        deck = self._prepare_deck_and_hands()
        categories = self._categorize_pieces(deck, exclude_red_general=True)
        
        red_general = categories['red_general']
        strong_pieces = categories['strong_pieces']
        other_pieces = categories['weak_pieces']
        
        if not red_general:
            print(f"❌ ERROR: RED_GENERAL not found in deck!")
            # Fallback to regular dealing
            self._deal_pieces()
            return
        
        print(f"🔧 DEBUG: Found RED_GENERAL: {red_general}")
        print(f"🔧 DEBUG: Other strong pieces: {len(strong_pieces)}")
        print(f"🔧 DEBUG: Other pieces: {len(other_pieces)}")
        
        # Validate starter_player index
        if not (0 <= starter_player < len(self.players)):
            print(f"❌ ERROR: Invalid starter_player index: {starter_player}")
            # Fallback to regular dealing
            self._deal_pieces()
            return
        
        # Check if we have enough strong pieces for non-starter players
        other_players_count = len(self.players) - 1
        if len(strong_pieces) < other_players_count:
            print(f"⚠️ WARNING: Not enough strong pieces! Have {len(strong_pieces)}, need {other_players_count}")
            print("🔄 Falling back to regular dealing to ensure fairness")
            self._deal_pieces()
            return
        
        # Give RED_GENERAL to starter
        self.players[starter_player].hand.append(red_general)
        print(f"🔧 DEBUG: {self.players[starter_player].name} gets RED_GENERAL")
        
        # Give 1 strong piece to each OTHER player
        strong_pieces_used = 0
        for i, player in enumerate(self.players):
            if i != starter_player:
                if strong_pieces_used < len(strong_pieces):
                    player.hand.append(strong_pieces[strong_pieces_used])
                    print(f"🔧 DEBUG: {player.name} gets strong piece: {strong_pieces[strong_pieces_used]}")
                    strong_pieces_used += 1
                else:
                    # This shouldn't happen due to our check above, but just in case
                    print(f"❌ ERROR: Ran out of strong pieces for {player.name}!")
                    # Fallback to regular dealing
                    self._deal_pieces()
                    return
        
        # Prepare remaining pieces for distribution
        remaining_strong = strong_pieces[strong_pieces_used:]
        all_remaining = remaining_strong + other_pieces
        
        # Fill remaining slots using helper method
        self._fill_remaining_slots(all_remaining)
        
        # Verify results
        self._verify_and_report_hands(expected_starter=starter_player)

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
    
    def all_players_declared(self) -> bool:
        """Check if all players have declared."""
        # Check != 0 instead of is not None since we initialize declared to 0
        declared_count = sum(1 for p in self.players if p.declared != 0)
        print(f"📊 Players declared: {declared_count}/{len(self.players)}")
        return declared_count == len(self.players)
    
    def start_turn_phase(self):
        """Initialize the turn phase after declarations are complete"""
        print(f"🎮 Starting turn phase")
        
        # Reset turn state
        self.current_turn_plays = []
        self.required_piece_count = None
        
        # Set initial turn order based on round starter
        if self.current_order:
            self.turn_order = list(self.current_order)
            self.last_turn_winner = self.current_order[0]
            print(f"📍 Initial turn order: {[p.name for p in self.turn_order]}")
            print(f"🎯 First player: {self.turn_order[0].name}")
        else:
            print("❌ No current order set!")
            
        return {
            "phase": "turn_play",
            "first_player": self.turn_order[0].name if self.turn_order else None
        }