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
        
        # Event-driven support
        self.current_phase = None          # Track current phase for controllers


    def prepare_round(self) -> dict:
        """Prepare for a new round: shuffle and deal pieces, determine starting player, reset declarations."""
        print(f"🔄 DEBUG: Starting prepare_round() - Round {self.round_number + 1}")
        
        self.round_number += 1
        # self._deal_pieces()
        self._deal_weak_hand(0)
        # self._deal_guaranteed_no_redeal()
        # self._deal_red_general_no_redeal(0)
        
        self._set_round_start_player()
                
        # Initialize pile and score tracking
        self.pile_counts = {p.name: 0 for p in self.players}
        self.round_scores = {p.name: 0 for p in self.players}
        
        # Reset player declarations
        for player in self.players:
            player.declared = 0

        print(f"🔍 DEBUG: Checking for weak hands...")
        
        # ✅ ใช้ refactored method แทน duplicate code
        weak_players = self.get_weak_hand_players(include_details=False)
        need_redeal = self.has_weak_hand_players()
        
        print(f"🔍 DEBUG: weak_players: {weak_players}")
        print(f"🔍 DEBUG: need_redeal: {need_redeal}")
        
        result = {
            "round": self.round_number,
            "starter": self.current_order[0].name,
            "hands": {
                player.name: [str(piece) for piece in player.hand]
                for player in self.players
            },
            "weak_players": weak_players,  # ✅ backward compatible format
            "need_redeal": need_redeal
        }
        
        print(f"🔍 DEBUG: prepare_round() result keys: {list(result.keys())}")
        print(f"🔍 DEBUG: prepare_round() returning: {result}")
        
        return result

    # ======================================
    # ✨ NEW: EVENT-DRIVEN METHODS
    # ======================================

    def get_weak_hand_players(self, include_details=False):
        """
        หา players ที่มี weak hand (ไม่มีไพ่ > 9 คะแนน)
        
        Args:
            include_details (bool): ถ้า True จะ return ข้อมูลละเอียด
                                   ถ้า False จะ return แค่ names (backward compatible)
        
        Returns:
            List: ถ้า include_details=False → ['player1', 'player2']
                  ถ้า include_details=True → [{'name': ..., 'is_bot': ..., ...}]
        """
        weak_players = []
        
        for player in self.players:
            # ใช้ logic เดิมที่ proven แล้ว
            has_strong = any(p.point > 9 for p in player.hand)
            
            if not has_strong:
                if include_details:
                    # Return rich data สำหรับ controllers
                    hand_strength = sum(p.point for p in player.hand)
                    weak_players.append({
                        'name': player.name,
                        'is_bot': player.is_bot,
                        'hand_strength': hand_strength,
                        'hand': [str(piece) for piece in player.hand]
                    })
                else:
                    # Return แค่ names (backward compatible)
                    weak_players.append(player.name)
        
        # เรียงตาม hand strength ถ้า include_details=True
        if include_details:
            weak_players.sort(key=lambda p: p['hand_strength'])
        
        return weak_players
    
    def has_weak_hand_players(self) -> bool:
        """Quick check ว่ามี weak hand players หรือไม่"""
        return len(self.get_weak_hand_players()) > 0
    
    def execute_redeal_for_player(self, player_name: str) -> dict:
        """
        ให้ไพ่ใหม่กับ player และ return ข้อมูลสำหรับ event
        
        Args:
            player_name (str): ชื่อ player ที่จะ redeal
            
        Returns:
            dict: ข้อมูล redeal สำหรับ broadcast events
        """
        player_obj = self.get_player(player_name)
        
        # เพิ่ม multiplier
        self.redeal_multiplier += 0.5
        
        # สร้างไพ่ใหม่
        new_hand = self._generate_new_hand_for_player(player_obj)
        player_obj.hand = new_hand
        
        print(f"🔄 Executed redeal for {player_name}, new multiplier: {self.redeal_multiplier}")
        
        return {
            'player': player_name,
            'new_hand': [str(piece) for piece in new_hand],
            'multiplier': self.redeal_multiplier,
            'hand_strength': sum(p.point for p in new_hand),
            'success': True
        }
    
    def _generate_new_hand_for_player(self, player):
        """
        สร้างไพ่ใหม่สำหรับ redeal
        TODO: Implement proper redeal logic based on game rules
        """
        # ตอนนี้ใช้ placeholder - ต้องปรับตาม game rules จริง
        # สามารถใช้ existing dealing logic หรือสร้างใหม่
        
        # Simple implementation: สุ่มไพ่ใหม่
        deck = Piece.build_deck()
        random.shuffle(deck)
        return deck[:8]  # เอา 8 ใบแรก
    
    def get_game_phase_info(self) -> dict:
        """ข้อมูลสำหรับ controllers ตัดสินใจ phase ต่อไป"""
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
        """Controllers สามารถ track current phase"""
        old_phase = self.current_phase
        self.current_phase = phase_name
        print(f"🎮 Game phase: {old_phase} → {phase_name}")
    
    def get_declaration_eligible_players(self, include_details=False):
        """
        หา players ที่ยังไม่ declare
        
        Args:
            include_details (bool): ถ้า True จะ return ข้อมูลละเอียด
                                   ถ้า False จะ return แค่ Player objects
        
        Returns:
            List: players ที่ยังไม่ declare
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
        ตรวจสอบ declaration ว่าถูกต้องไหม
        
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
        บันทึก declaration และ return ข้อมูลสำหรับ events
        
        Returns:
            dict: ข้อมูล declaration สำหรับ broadcast
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
        หา players ที่ยังไม่เล่น turn นี้
        TODO: Implement turn tracking logic
        """
        # Placeholder - ต้อง implement turn tracking
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
        ตรวจสอบการเล่น turn ว่าถูกต้องไหม
        
        Args:
            player_name (str): ชื่อ player
            piece_indexes (list): index ของไพ่ที่จะเล่น
            
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
        บันทึกการเล่น turn และ return ผลลัพธ์
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

    def _set_round_start_player(self):
        """Set the starting player order for the round based on game rules."""
        if self.last_round_winner:
            start_index = self.players.index(self.last_round_winner)
        else:
            # First round: find player with RED_GENERAL
            start_index = 0
            for i, player in enumerate(self.players):
                if any("GENERAL_RED" in str(piece) for piece in player.hand):
                    start_index = i
                    break
        
        self.current_order = self.players[start_index:] + self.players[:start_index]
        print(f"🔧 DEBUG: Round {self.round_number} starting player: {self.current_order[0].name}")