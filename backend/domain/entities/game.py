# backend/domain.entities/game.py

"""
Game Entity - Aggregate Root for Liap Tui Game
This file should have ZERO external dependencies!
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from uuid import uuid4
import random

from .player import Player
from .piece import Piece, PieceColor, PieceType
from ..value_objects.game_phase import GamePhase, PhaseTransition


@dataclass
class Game:
    """
    Game Aggregate Root - Coordinates all game activities
    
    This is the main entity that orchestrates the entire game.
    It maintains consistency across all game objects and enforces
    business rules that span multiple entities.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    players: List[Player] = field(default_factory=list)
    phase: GamePhase = GamePhase.WAITING
    current_player_index: int = 0
    round_number: int = 1
    deck: List[Piece] = field(default_factory=list)
    played_pieces: List[Piece] = field(default_factory=list)
    max_players: int = 4
    min_players: int = 2
    
    def __post_init__(self):
        """Initialize game with a fresh deck if not provided"""
        if not self.deck:
            self.deck = self._create_standard_deck()
    
    # ===== PLAYER MANAGEMENT =====
    
    def add_player(self, player: Player) -> bool:
        """
        Add a player to the game
        
        Args:
            player: Player to add
            
        Returns:
            True if player added successfully, False otherwise
            
        Raises:
            ValueError: If game is full or player already exists
        """
        if len(self.players) >= self.max_players:
            raise ValueError(f"Game is full (max {self.max_players} players)")
        
        if any(p.name == player.name for p in self.players):
            raise ValueError(f"Player '{player.name}' already exists in game")
        
        if self.phase != GamePhase.WAITING:
            raise ValueError("Cannot add players after game has started")
        
        self.players.append(player)
        return True
    
    def remove_player(self, player_name: str) -> bool:
        """Remove a player from the game"""
        if self.phase not in [GamePhase.WAITING, GamePhase.ABANDONED]:
            # In active games, mark as abandoned rather than removing
            self._transition_to_phase(GamePhase.ABANDONED, "Player left during game")
            return False
        
        self.players = [p for p in self.players if p.name != player_name]
        return True
    
    @property
    def is_ready_to_start(self) -> bool:
        """Check if game has enough players to start"""
        return (
            len(self.players) >= self.min_players and 
            self.phase == GamePhase.WAITING
        )
    
    # ===== GAME FLOW MANAGEMENT =====
    
    def start_game(self) -> bool:
        """
        Start the game if conditions are met
        
        Returns:
            True if game started successfully
            
        Raises:
            ValueError: If game cannot be started
        """
        if not self.is_ready_to_start:
            raise ValueError(
                f"Need {self.min_players}-{self.max_players} players to start"
            )
        
        # Deal initial hands
        self._deal_initial_hands()
        
        # Transition to redeal phase
        self._transition_to_phase(GamePhase.REDEAL, "Game started")
        
        return True
    
    def advance_to_next_phase(self) -> PhaseTransition:
        """
        Advance game to the next logical phase
        
        Returns:
            PhaseTransition object describing the change
        """
        next_phase = self._determine_next_phase()
        return self._transition_to_phase(next_phase, "Phase progression")
    
    def _determine_next_phase(self) -> GamePhase:
        """Determine what the next phase should be based on current state"""
        if self.phase == GamePhase.REDEAL:
            return GamePhase.DECLARATION
        elif self.phase == GamePhase.DECLARATION:
            return GamePhase.PLAYING
        elif self.phase == GamePhase.PLAYING:
            # Check if game should end
            if self._is_game_finished():
                return GamePhase.FINISHED
            return GamePhase.PLAYING  # Continue playing
        else:
            return self.phase  # No transition needed
    
    def _transition_to_phase(self, new_phase: GamePhase, reason: str) -> PhaseTransition:
        """Safely transition to a new phase with validation"""
        transition = PhaseTransition(
            from_phase=self.phase,
            to_phase=new_phase,
            reason=reason
        )
        
        if not transition.is_valid:
            raise ValueError(f"Invalid phase transition: {transition.description}")
        
        self.phase = new_phase
        return transition
    
    # ===== TURN MANAGEMENT =====
    
    @property
    def current_player(self) -> Optional[Player]:
        """Get the player whose turn it is"""
        if not self.players:
            return None
        return self.players[self.current_player_index % len(self.players)]
    
    def advance_turn(self) -> Player:
        """Move to the next player's turn"""
        if not self.players:
            raise ValueError("No players in game")
        
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # Check if we've completed a full round
        if self.current_player_index == 0:
            self.round_number += 1
        
        return self.current_player
    
    # ===== PIECE MANAGEMENT =====
    
    def play_pieces(self, player_name: str, pieces: List[Piece]) -> bool:
        """
        Player plays pieces from their hand
        
        Args:
            player_name: Name of player making the move
            pieces: List of pieces to play
            
        Returns:
            True if move was valid and executed
            
        Raises:
            ValueError: If move is invalid
        """
        if self.phase != GamePhase.PLAYING:
            raise ValueError(f"Cannot play pieces during {self.phase.display_name}")
        
        player = self._get_player_by_name(player_name)
        if not player:
            raise ValueError(f"Player '{player_name}' not found")
        
        if player != self.current_player:
            raise ValueError(f"Not {player_name}'s turn")
        
        # Validate pieces are in player's hand
        for piece in pieces:
            if piece not in player.hand:
                raise ValueError(f"Player doesn't have piece: {piece}")
        
        # Execute the move
        for piece in pieces:
            player.hand.remove(piece)
            self.played_pieces.append(piece)
        
        # Advance turn
        self.advance_turn()
        
        return True
    
    def _deal_initial_hands(self, hand_size: int = 7) -> None:
        """Deal initial hands to all players"""
        random.shuffle(self.deck)
        
        for player in self.players:
            player.reset_hand()
            for _ in range(hand_size):
                if self.deck:
                    piece = self.deck.pop()
                    player.hand.append(piece)
    
    def _create_standard_deck(self) -> List[Piece]:
        """Create a standard deck of game pieces"""
        deck = []
        
        # Create pieces for each color and value
        for color in PieceColor:
            for value in range(1, 14):  # 1-13 like playing cards
                deck.append(Piece(value=value, color=color))
        
        # Add some special pieces
        for color in PieceColor:
            deck.append(Piece(value=14, color=color, piece_type=PieceType.SPECIAL))
        
        return deck
    
    # ===== GAME STATE QUERIES =====
    
    def _is_game_finished(self) -> bool:
        """Check if the game should end"""
        # Game ends when any player has no pieces left
        return any(len(player.hand) == 0 for player in self.players)
    
    def get_winner(self) -> Optional[Player]:
        """Get the winning player if game is finished"""
        if self.phase != GamePhase.FINISHED:
            return None
        
        # Winner is player with highest score
        return max(self.players, key=lambda p: p.score, default=None)
    
    def _get_player_by_name(self, name: str) -> Optional[Player]:
        """Find player by name"""
        return next((p for p in self.players if p.name == name), None)
    
    @property
    def game_summary(self) -> Dict:
        """Get a summary of current game state"""
        return {
            "id": self.id,
            "phase": self.phase.display_name,
            "players": [p.name for p in self.players],
            "current_player": self.current_player.name if self.current_player else None,
            "round": self.round_number,
            "pieces_played": len(self.played_pieces)
        }
    
    def __str__(self) -> str:
        """String representation of the game"""
        player_names = ", ".join(p.name for p in self.players)
        return f"Game({self.id[:8]}, {self.phase.display_name}, players=[{player_names}])"


# Quick tests to ensure it works
if __name__ == "__main__":
    # Test game creation
    game = Game()
    print(f"✅ Created game: {game}")
    
    # Test adding players
    alice = Player("Alice")
    bob = Player("Bob", is_bot=True)
    
    game.add_player(alice)
    game.add_player(bob)
    print(f"✅ Added players: {[p.name for p in game.players]}")
    
    # Test game start
    if game.is_ready_to_start:
        game.start_game()
        print(f"✅ Game started, phase: {game.phase.display_name}")
        print(f"✅ Current player: {game.current_player.name}")
        print(f"✅ Alice's hand size: {len(alice.hand)}")
    
    # Test phase transition
    transition = game.advance_to_next_phase()
    print(f"✅ Phase transition: {transition}")
    
    # Test game summary
    print(f"✅ Game summary: {game.game_summary}")
    
    print("✅ Game aggregate root works!")