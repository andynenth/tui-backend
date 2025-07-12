# backend/engine/game.py

import random
from typing import List
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
        self.round_number = 1
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
        self.turn_number = 0               # Current turn number within the round
        
        # Player tracking for state machine
        self.current_player = None         # Current player (for round start/declarations)
        self.round_starter = None          # Player who starts the round
        self.player_declarations = {}      # Track player declarations for state machine
        self.pile_counts = {}              # Track piles won per player per round
        
        # Event-driven support
        self.current_phase = None          # Track current phase for controllers
        
        # Timing tracking
        self.start_time = None             # Game start timestamp
        self.end_time = None               # Game end timestamp



    # ======================================
    # ✨ NEW: EVENT-DRIVEN METHODS
    # ======================================

    def get_weak_hand_players(self, include_details=False):
        """
        Find players with weak hand (no card > 9 points)
        
        Args:
            include_details (bool): If True, will return detailed information
                                   If False, will return only names (backward compatible)
        
        Returns:
            List: If include_details=False → ['player1', 'player2']
                  If include_details=True → [{'name': ..., 'is_bot': ..., ...}]
        """
        weak_players = []
        
        for player in self.players:
            # Use the existing proven logic
            has_strong = any(p.point > 9 for p in player.hand)
            
            if not has_strong:
                if include_details:
                    # Return rich data for controllers
                    hand_strength = sum(p.point for p in player.hand)
                    weak_players.append({
                        'name': player.name,
                        'is_bot': player.is_bot,
                        'hand_strength': hand_strength,
                        'hand': [str(piece) for piece in player.hand]
                    })
                else:
                    # Return only names (backward compatible)
                    weak_players.append(player.name)
        
        # Sort by hand strength if include_details=True
        if include_details:
            weak_players.sort(key=lambda p: p['hand_strength'])
        
        return weak_players
    
    def has_weak_hand_players(self) -> bool:
        """Quick check whether there are weak hand players or not"""
        return len(self.get_weak_hand_players()) > 0
    
    def execute_redeal_for_player(self, player_name: str) -> dict:
        """
        Deal new cards to player and return data for event
        
        Args:
            player_name (str): Name of player to redeal
            
        Returns:
            dict: Redeal data for broadcast events
        """
        player_obj = self.get_player(player_name)
        
        # Increase multiplier
        self.redeal_multiplier += 0.5
        
        # Create new cards
        new_hand = self._generate_new_hand_for_player(player_obj)
        player_obj.hand = new_hand
        
        
        return {
            'player': player_name,
            'new_hand': [str(piece) for piece in new_hand],
            'multiplier': self.redeal_multiplier,
            'hand_strength': sum(p.point for p in new_hand),
            'success': True
        }
    
    def _generate_new_hand_for_player(self, player):
        """
        Create new cards for redeal
        TODO: Implement proper redeal logic based on game rules
        """
        deck = Piece.build_deck()
        random.shuffle(deck)
        return deck[:8]  # Take the first 8 cards
    
    def get_game_phase_info(self) -> dict:
        """Information for controllers to decide next phase"""
        return {
            'round_number': self.round_number,
            'redeal_multiplier': self.redeal_multiplier,
            'has_weak_hands': self.has_weak_hand_players(),
            'all_declared': self.all_players_declared(),
            'players_count': len(self.players),
            'current_phase': self.current_phase,
            'game_over': self._is_game_over(),
            'max_score': self.max_score,
            'max_rounds': self.max_rounds
        }
    
    def set_current_phase(self, phase_name: str):
        """Controllers can track current phase"""
        old_phase = self.current_phase
        self.current_phase = phase_name
    
    def get_declaration_eligible_players(self, include_details=False):
        """
        Find players who haven't declared yet
        
        Args:
            include_details (bool): If True, will return detailed information
                                   If False, will return only Player objects
        
        Returns:
            List: players who haven't declared yet
        """
        eligible_players = [p for p in self.players if p.declared == 0]
        
        if include_details:
            return [{
                'name': p.name,
                'is_bot': p.is_bot,
                'hand': [str(piece) for piece in p.hand],
                'valid_declarations': get_valid_declares(p.hand),
                'score': p.score
            } for p in eligible_players]
        
        return eligible_players
    
    def validate_player_declaration(self, player_name: str, declaration: int) -> dict:
        """
        Check if declaration is valid
        
        Returns:
            dict: {'valid': bool, 'reason': str, 'valid_options': list}
        """
        try:
            player = self.get_player(player_name)
            
            # Check if already declared
            if player.declared != 0:
                return {
                    'valid': False,
                    'reason': f"{player.name} has already declared {player.declared}",
                    'valid_options': []
                }
            
            # Check zero declaration rule
            if player.zero_declares_in_a_row >= 2 and declaration == 0:
                return {
                    'valid': False,
                    'reason': f"{player.name} must declare at least 1 after two zeros in a row",
                    'valid_options': [i for i in range(1, 9)]
                }
            
            # Check if declaration is in valid range
            valid_declarations = get_valid_declares(player.hand)
            if declaration not in valid_declarations:
                return {
                    'valid': False,
                    'reason': f"Declaration {declaration} not valid for current hand",
                    'valid_options': valid_declarations
                }
            
            return {
                'valid': True,
                'reason': 'Valid declaration',
                'valid_options': valid_declarations
            }
            
        except ValueError as e:
            return {
                'valid': False,
                'reason': str(e),
                'valid_options': []
            }
    
    def record_player_declaration(self, player_name: str, declaration: int) -> dict:
        """
        Record declaration and return data for events
        
        Returns:
            dict: Declaration data for broadcast
        """
        # Validate first
        validation = self.validate_player_declaration(player_name, declaration)
        if not validation['valid']:
            return {
                'success': False,
                'reason': validation['reason'],
                'player': player_name,
                'declaration': declaration
            }
        
        # Record declaration
        player = self.get_player(player_name)
        player.record_declaration(declaration)
        
        # Calculate totals
        total_declared = sum(p.declared for p in self.players)
        declarations = {p.name: p.declared for p in self.players}
        
        return {
            'success': True,
            'player': player_name,
            'declaration': declaration,
            'total_declared': total_declared,
            'declarations': declarations,
            'all_declared': self.all_players_declared()
        }
    
    def get_turn_eligible_players(self, include_details=False):
        """
        Find players who haven't played this turn
        TODO: Implement turn tracking logic
        """
        # Placeholder - need to implement turn tracking
        eligible_players = [p for p in self.players]
        
        if include_details:
            return [{
                'name': p.name,
                'is_bot': p.is_bot,
                'hand': [str(piece) for piece in p.hand],
                'declared': p.declared,
                'current_piles': self.pile_counts.get(p.name, 0)
            } for p in eligible_players]
        
        return eligible_players
    
    def validate_turn_play(self, player_name: str, piece_indexes: list) -> dict:
        """
        Check if turn play is valid
        
        Args:
            player_name (str): Player name
            piece_indexes (list): Index of cards to play
            
        Returns:
            dict: {'valid': bool, 'reason': str, 'play_type': str}
        """
        try:
            player = self.get_player(player_name)
            
            # Convert indexes to pieces
            if not all(0 <= i < len(player.hand) for i in piece_indexes):
                return {
                    'valid': False,
                    'reason': 'Invalid piece indexes',
                    'play_type': None
                }
            
            pieces = [player.hand[i] for i in piece_indexes]
            
            # Use existing validation logic
            is_valid = is_valid_play(pieces)
            if not is_valid:
                return {
                    'valid': False,
                    'reason': 'Invalid piece combination',
                    'play_type': None
                }
            
            play_type = get_play_type(pieces)
            
            return {
                'valid': True,
                'reason': 'Valid play',
                'play_type': play_type,
                'pieces': [str(p) for p in pieces]
            }
            
        except Exception as e:
            return {
                'valid': False,
                'reason': str(e),
                'play_type': None
            }
    
    def execute_turn_play(self, player_name: str, piece_indexes: list) -> dict:
        """
        Record turn play and return results
        TODO: Implement full turn logic
        """
        # Validate first
        validation = self.validate_turn_play(player_name, piece_indexes)
        if not validation['valid']:
            return {
                'success': False,
                'reason': validation['reason'],
                'player': player_name
            }
        
        # Execute turn (placeholder)
        player = self.get_player(player_name)
        pieces = [player.hand[i] for i in piece_indexes]
        
        # Remove pieces from hand
        for i in sorted(piece_indexes, reverse=True):
            player.hand.pop(i)
        
        return {
            'success': True,
            'player': player_name,
            'pieces_played': [str(p) for p in pieces],
            'play_type': validation['play_type'],
            'remaining_hand_size': len(player.hand)
        }

    # ======================================
    # ✅ EXISTING METHODS (PRESERVED)
    # ======================================

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
    
    def get_player_order_from(self, starting_player_name: str) -> List[Player]:
        """Get player order starting from a specific player"""
        try:
            start_player = self.get_player(starting_player_name)
            start_index = self.players.index(start_player)
            return self.players[start_index:] + self.players[:start_index]
        except (ValueError, AttributeError):
            # Fallback: return players in original order
            return self.players

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
        return all(p.declared is not None and p.declared != 0 for p in self.players)

    def play_turn(self, player_name: str, piece_indexes: list[int]) -> dict:
        """Handle a player's move, validate it, and resolve the turn if all players have played."""
        player = self.get_player(player_name)
        
        # Validate piece selection
        if not all(0 <= i < len(player.hand) for i in piece_indexes):
            return {"status": "error", "message": "Invalid piece selection."}
        
        pieces = [player.hand[i] for i in piece_indexes]
        
        if not is_valid_play(pieces):
            return {"status": "error", "message": "Invalid play."}
        
        # Remove pieces from hand and create TurnPlay
        for i in sorted(piece_indexes, reverse=True):
            player.hand.pop(i)
        
        turn_play = TurnPlay(player=player, pieces=pieces, is_valid=True)
        self.current_turn_plays.append(turn_play)
        
        # Check if this is the first turn to set required piece count
        if self.required_piece_count is None:
            self.required_piece_count = len(pieces)
        
        result = {
            "status": "ok",
            "player": player.name,
            "pieces": [str(p) for p in pieces],
            "play_type": get_play_type(pieces)
        }
        
        # If all players have played, resolve the turn
        if len(self.current_turn_plays) == len(self.players):
            turn_result = resolve_turn(self.current_turn_plays)
            
            if turn_result.winner:
                self.pile_counts[turn_result.winner.player.name] += 1
                self.last_turn_winner = turn_result.winner.player
                result["turn_winner"] = turn_result.winner.player.name
            
            # Clear for next turn
            self.current_turn_plays.clear()
            self.required_piece_count = None
            
            # Check if round is over (all hands empty)
            if all(len(p.hand) == 0 for p in self.players):
                round_scores = calculate_round_scores(self.players, self.pile_counts, self.redeal_multiplier)
                for player_name, score in round_scores.items():
                    self.get_player(player_name).score += score
                    self.round_scores[player_name] = score
                
                result["round_complete"] = True
                result["round_scores"] = round_scores
                result["total_scores"] = {p.name: p.score for p in self.players}
                
                if self._is_game_over():
                    result["game_over"] = True
                    result["winners"] = [p.name for p in get_winners(self)]
        
        return result

    def _is_game_over(self) -> bool:
        """Check if the game has ended according to the win condition."""
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
    
    def deal_pieces(self):
        """Public method for dealing pieces - used by state machine"""
        self._deal_pieces()

            
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
        pass

    def _fill_remaining_slots(self, available_pieces):
        """Helper: Fill remaining hand slots for all players"""
        random.shuffle(available_pieces)
        piece_index = 0
        
        for player in self.players:
            while len(player.hand) < 8 and piece_index < len(available_pieces):
                player.hand.append(available_pieces[piece_index])
                piece_index += 1
    
    def _deal_weak_hand(self, weak_player_indices=None, max_weak_points=9, limit=None):
        """
        Deal weak hand to specific players for testing redeal functionality.
        
        Args:
            weak_player_indices: List of player indices to receive weak hands (e.g., [0], [0,1], [0,1,2])
                                If None, defaults to [0]
            max_weak_points: Maximum points for pieces to be considered weak
            limit: Maximum number of redeals allowed before forcing guaranteed no redeal
                  (uses redeal_multiplier to track)
        """
        # Default to player 0 if not specified
        if weak_player_indices is None:
            weak_player_indices = [0]
        
        # Validate indices
        weak_player_indices = [i for i in weak_player_indices if 0 <= i < len(self.players)]
        if not weak_player_indices:
            self._deal_pieces()
            return
        
        # Check if limit is reached using redeal_multiplier
        # For a new round: multiplier = 1 (no redeals yet)
        # After 1st redeal: multiplier = 2
        # After 2nd redeal: multiplier = 3, etc.
        # So if limit=1, we allow dealing weak hands when multiplier is 1 or 2
        
        
        if limit is not None and self.redeal_multiplier > limit:
            self._deal_guaranteed_no_redeal()
            return
        
        
        # Use helper methods
        deck = self._prepare_deck_and_hands()
        categories = self._categorize_pieces(deck)
        
        weak_pieces = categories['weak_pieces'][:]  # Make a copy
        strong_pieces = categories['strong_pieces'][:]  # Make a copy
        if categories['red_general']:
            strong_pieces.append(categories['red_general'])
        
        
        # Shuffle pieces
        random.shuffle(weak_pieces)
        random.shuffle(strong_pieces)
        
        # Calculate how many weak pieces we need
        weak_pieces_needed = len(weak_player_indices) * 8
        
        # Check if we have enough weak pieces
        if len(weak_pieces) < weak_pieces_needed:
            # We'll use all weak pieces and fill with some strong pieces
            pass
        
        # First, ensure non-weak players get at least one strong piece each
        non_weak_players = []
        for i in range(len(self.players)):
            if i not in weak_player_indices:
                non_weak_players.append(i)
        
        # Reserve strong pieces for non-weak players (at least 1 each)
        if len(strong_pieces) < len(non_weak_players):
            self._deal_pieces()
            return
        
        # Deal to weak players first
        weak_piece_index = 0
        for player_idx in weak_player_indices:
            player = self.players[player_idx]
            # Give this player 8 weak pieces (or as many as possible)
            for _ in range(8):
                if weak_piece_index < len(weak_pieces):
                    player.hand.append(weak_pieces[weak_piece_index])
                    weak_piece_index += 1
                else:
                    # Ran out of weak pieces, this shouldn't happen with proper deck
                    break
        
        # Remove used weak pieces
        remaining_weak = weak_pieces[weak_piece_index:]
        
        # Deal to non-weak players - ensure they get at least 1 strong piece
        strong_piece_index = 0
        for player_idx in non_weak_players:
            player = self.players[player_idx]
            
            # Give at least one strong piece first
            if strong_piece_index < len(strong_pieces):
                player.hand.append(strong_pieces[strong_piece_index])
                strong_piece_index += 1
            
            # Fill rest of hand (7 more pieces)
            # Combine remaining pieces and shuffle
            available_for_this_player = remaining_weak + strong_pieces[strong_piece_index:]
            random.shuffle(available_for_this_player)
            
            pieces_added = 1  # Already added 1 strong piece
            for piece in available_for_this_player:
                if pieces_added >= 8:
                    break
                if piece not in [p for player in self.players for p in player.hand]:  # Not already dealt
                    player.hand.append(piece)
                    pieces_added += 1
                    # Remove from lists
                    if piece in remaining_weak:
                        remaining_weak.remove(piece)
                    else:
                        strong_pieces[strong_piece_index:] = [p for p in strong_pieces[strong_piece_index:] if p != piece]
            
            # Shuffle hand to randomize strong piece position
            random.shuffle(player.hand)
            
        # Verify results
        self._verify_and_report_hands()

    def _deal_weak_hand_legacy(self, weak_player_index=0, max_weak_points=9, limit=None):
        """Legacy method for backward compatibility - calls new method with single index"""
        self._deal_weak_hand([weak_player_index], max_weak_points, limit)

    def _deal_guaranteed_no_redeal(self, red_general_player_index=None):
        """
        Deal hands ensuring every player has at least one strong piece (>9 points).
        This prevents any redeal requests.
        
        Args:
            red_general_player_index (int, optional): Index of player who should get RED_GENERAL.
                                                    If None, RED_GENERAL is distributed randomly.
        """
        if red_general_player_index is not None:
            pass
        
        # Use helper methods
        deck = self._prepare_deck_and_hands()
        categories = self._categorize_pieces(deck)
        
        strong_pieces = categories['strong_pieces']
        red_general = categories['red_general']
        weak_pieces = categories['weak_pieces']
        
        
        # Handle RED_GENERAL assignment
        if red_general and red_general_player_index is not None:
            # Validate index
            if 0 <= red_general_player_index < len(self.players):
                target_player = self.players[red_general_player_index]
                target_player.hand.append(red_general)
                
                # Mark this player as already having a strong piece
                players_needing_strong = [i for i in range(len(self.players)) if i != red_general_player_index]
            else:
                strong_pieces.append(red_general)
                players_needing_strong = list(range(len(self.players)))
        else:
            # Add RED_GENERAL to strong pieces for random distribution
            if red_general:
                strong_pieces.append(red_general)
            players_needing_strong = list(range(len(self.players)))
        
        # Ensure we have enough strong pieces for remaining players
        if len(strong_pieces) < len(players_needing_strong):
            # Fall back to regular dealing
            self._deal_pieces()
            return
        
        # Shuffle strong pieces for random distribution
        random.shuffle(strong_pieces)
        random.shuffle(weak_pieces)
        
        # Give each remaining player at least one strong piece
        for i, player_index in enumerate(players_needing_strong):
            player = self.players[player_index]
            player.hand.append(strong_pieces[i])
        
        # Remove distributed strong pieces
        distributed_strong = strong_pieces[:len(players_needing_strong)]
        remaining_strong = strong_pieces[len(players_needing_strong):]
        
        # Combine remaining pieces and shuffle
        remaining_pieces = remaining_strong + weak_pieces
        random.shuffle(remaining_pieces)
        
        # Distribute remaining pieces to fill hands to 8
        piece_index = 0
        for player in self.players:
            while len(player.hand) < 8 and piece_index < len(remaining_pieces):
                player.hand.append(remaining_pieces[piece_index])
                piece_index += 1
        
        # Shuffle each player's hand to randomize position
        for player in self.players:
            random.shuffle(player.hand)
        
        # Verify results
        self._verify_and_report_hands()
        
        # Confirm no weak hands
        weak_players = self.get_weak_hand_players(include_details=False)
    
    def reset_weak_hand_counter(self):
        """Reset the weak hand deal counter (useful for new games or rounds)"""
        self.weak_hand_deal_count = 0
    
    def _deal_double_straight(self, player_index=0, color='RED'):
        """
        Deal a DOUBLE_STRAIGHT hand to a specific player.
        DOUBLE_STRAIGHT requires: 2 CHARIOTs, 2 HORSEs, 2 CANNONs (same color)
        
        Args:
            player_index (int): Index of player to receive DOUBLE_STRAIGHT (default: 0)
            color (str): Color for the DOUBLE_STRAIGHT pieces ('RED' or 'BLACK')
        """
        # Validate inputs
        if not (0 <= player_index < len(self.players)):
            self._deal_pieces()  # Fallback to normal dealing
            return
        
        if color not in ['RED', 'BLACK']:
            color = 'RED'  # Default to RED
        
        # Use helper methods
        deck = self._prepare_deck_and_hands()
        
        # Find required pieces for DOUBLE_STRAIGHT
        required_pieces = {
            f'CHARIOT_{color}': [],
            f'HORSE_{color}': [],
            f'CANNON_{color}': []
        }
        
        remaining_pieces = []
        
        for piece in deck:
            piece_str = str(piece)
            # Check if this is one of our required pieces
            found = False
            for key in required_pieces:
                if key in piece_str and len(required_pieces[key]) < 2:
                    required_pieces[key].append(piece)
                    found = True
                    break
            
            if not found:
                remaining_pieces.append(piece)
        
        # Verify we have enough of each required piece
        for key, pieces in required_pieces.items():
            if len(pieces) < 2:
                # Not enough pieces for DOUBLE_STRAIGHT, fallback to normal dealing
                self._deal_pieces()
                return
        
        # Give DOUBLE_STRAIGHT to target player
        target_player = self.players[player_index]
        for pieces_list in required_pieces.values():
            target_player.hand.extend(pieces_list[:2])  # Add 2 of each type
        
        # Fill remaining 2 slots (8 total - 6 DOUBLE_STRAIGHT = 2)
        random.shuffle(remaining_pieces)
        target_player.hand.extend(remaining_pieces[:2])
        remaining_pieces = remaining_pieces[2:]
        
        # Deal to other players
        random.shuffle(remaining_pieces)
        piece_idx = 0
        for i, player in enumerate(self.players):
            if i != player_index:
                # Give each other player 8 pieces
                for _ in range(8):
                    if piece_idx < len(remaining_pieces):
                        player.hand.append(remaining_pieces[piece_idx])
                        piece_idx += 1
        
        # Shuffle hands to randomize piece positions
        for player in self.players:
            random.shuffle(player.hand)
        
        # Verify the target player has DOUBLE_STRAIGHT
        target_hand = target_player.hand
        piece_names = [str(p) for p in target_hand]
        chariot_count = sum(1 for p in piece_names if f'CHARIOT_{color}' in p)
        horse_count = sum(1 for p in piece_names if f'HORSE_{color}' in p)
        cannon_count = sum(1 for p in piece_names if f'CANNON_{color}' in p)


    def _set_round_start_player(self):
        """Set the starting player order for the round based on game rules."""
        # Check if this is a redeal (multiplier > 1)
        if self.redeal_multiplier > 1:
            # Redeal: The player who requested redeal should start
            # For now, we'll keep the same starter as before
            # (In a full implementation, track who requested the redeal)
            pass
        elif self.last_round_winner:
            # Subsequent rounds: Last round winner starts
            start_index = self.players.index(self.last_round_winner)
            self.current_order = self.players[start_index:] + self.players[:start_index]
        else:
            # First round: find player with RED_GENERAL
            start_index = 0
            for i, player in enumerate(self.players):
                if any("GENERAL_RED" in str(piece) for piece in player.hand):
                    start_index = i
                    break
            self.current_order = self.players[start_index:] + self.players[:start_index]
        
        
