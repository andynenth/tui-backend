# backend/domain/entities/room.py
from dataclasses import dataclass, field
from typing import List, Optional, Set
from uuid import UUID, uuid4
from enum import Enum

from ..entities.player import Player
from ..entities.game import Game


class RoomStatus(Enum):
    """Room lifecycle states"""
    WAITING = "waiting"
    FULL = "full"
    IN_GAME = "in_game"
    FINISHED = "finished"
    ABANDONED = "abandoned"


@dataclass
class Room:
    """
    Entity: Multi-player game session management
    
    Identity: Unique room_id that persists throughout lifecycle
    Responsibility: Coordinate players, manage lobby, control game lifecycle
    """
    room_id: UUID = field(default_factory=uuid4)
    max_players: int = 4
    players: List[Player] = field(default_factory=list)
    status: RoomStatus = RoomStatus.WAITING
    current_game: Optional[Game] = None
    creator_name: str = ""
    
    def __post_init__(self):
        """Validate room creation"""
        if self.max_players < 2:
            raise ValueError("Room must allow at least 2 players")
        if self.max_players > 8:
            raise ValueError("Room cannot exceed 8 players")
    
    # === Player Management ===
    
    def add_player(self, player: Player) -> bool:
        """
        Add a player to the room lobby
        
        Business Rules:
        - Cannot add if room is full
        - Cannot add if game is in progress
        - Cannot add duplicate players (by name)
        - Must transition status when appropriate
        """
        if self.status not in [RoomStatus.WAITING, RoomStatus.FULL]:
            raise ValueError(f"Cannot add players when room is {self.status.value}")
        
        if len(self.players) >= self.max_players:
            return False
        
        # Check for duplicate player names
        if any(p.name == player.name for p in self.players):
            raise ValueError(f"Player {player.name} already in room")
        
        self.players.append(player)
        
        # Auto-transition status
        if len(self.players) == self.max_players:
            self.status = RoomStatus.FULL
        
        # Set creator if first player
        if len(self.players) == 1:
            self.creator_name = player.name
        
        return True
    
    def remove_player(self, player_name: str) -> bool:
        """
        Remove a player from the room
        
        Business Rules:
        - Cannot remove during active game
        - If creator leaves, transfer to next player or abandon room
        - Auto-transition status when appropriate
        """
        if self.status == RoomStatus.IN_GAME:
            raise ValueError("Cannot remove players during active game")
        
        # Find and remove player
        player_removed = False
        for i, player in enumerate(self.players):
            if player.name == player_name:
                del self.players[i]
                player_removed = True
                break
        
        if not player_removed:
            return False
        
        # Handle creator leaving
        if self.creator_name == player_name:
            if self.players:
                self.creator_name = self.players[0].name
            else:
                self.status = RoomStatus.ABANDONED
                return True
        
        # Auto-transition status
        if self.status == RoomStatus.FULL and len(self.players) < self.max_players:
            self.status = RoomStatus.WAITING
        
        return True
    
    def get_player_names(self) -> List[str]:
        """Get list of all player names in room"""
        return [player.name for player in self.players]
    
    # === Game Lifecycle Management ===
    
    def can_start_game(self) -> bool:
        """Check if room can start a new game"""
        return (
            len(self.players) >= 2 and
            self.status in [RoomStatus.WAITING, RoomStatus.FULL] and
            self.current_game is None
        )
    
    def start_game(self) -> Game:
        """
        Start a new game session
        
        Business Rules:
        - Must have at least 2 players
        - Cannot start if game already active
        - Must transition room status
        """
        if not self.can_start_game():
            raise ValueError("Cannot start game - conditions not met")
        
        # Create new game with current players
        self.current_game = Game(
            id=str(uuid4()),
            max_players=len(self.players)
        )
        
        # Add all room players to the game
        for player in self.players:
            # Reset player state for new game (clear hand, reset score)
            player.reset_hand()
            player.score = 0
            self.current_game.add_player(player)
        
        self.status = RoomStatus.IN_GAME
        return self.current_game
    
    def finish_game(self) -> None:
        """
        Complete the current game session
        
        Business Rules:
        - Game must be in finished state
        - Room returns to waiting status
        - Players remain in room for potential next game
        """
        if self.current_game is None:
            raise ValueError("No active game to finish")
        
        # Check if game is in a finished state
        from ..value_objects.game_phase import GamePhase
        if self.current_game.phase not in [GamePhase.FINISHED, GamePhase.ABANDONED]:
            raise ValueError("Cannot finish game that is still active")
        
        self.status = RoomStatus.FINISHED
        # Note: We keep current_game for results viewing
        # Could add a clear_game() method for cleanup
    
    def reset_for_new_game(self) -> None:
        """
        Reset room state for a new game
        
        Business Rules:
        - Can only reset after game is finished
        - Clears previous game data
        - Returns to appropriate waiting status
        """
        if self.status not in [RoomStatus.FINISHED]:
            raise ValueError(f"Cannot reset room in {self.status.value} status")
        
        self.current_game = None
        self.status = RoomStatus.FULL if len(self.players) == self.max_players else RoomStatus.WAITING
    
    # === Room Information ===
    
    def is_waiting_for_players(self) -> bool:
        """Check if room is accepting new players"""
        return self.status == RoomStatus.WAITING and len(self.players) < self.max_players
    
    def is_full(self) -> bool:
        """Check if room has maximum players"""
        return len(self.players) >= self.max_players
    
    def is_active_game(self) -> bool:
        """Check if room has an active game in progress"""
        return self.status == RoomStatus.IN_GAME and self.current_game is not None
    
    def get_room_info(self) -> dict:
        """Get comprehensive room information for external systems"""
        return {
            "room_id": str(self.room_id),
            "status": self.status.value,
            "player_count": len(self.players),
            "max_players": self.max_players,
            "players": self.get_player_names(),
            "creator": self.creator_name,
            "has_active_game": self.current_game is not None,
            "can_start_game": self.can_start_game(),
            "is_accepting_players": self.is_waiting_for_players()
        }