"""
Service interfaces for the domain layer.

These interfaces define contracts for services that may have
different implementations or need infrastructure support.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple

from domain.value_objects.piece import Piece
from domain.entities.player import Player


class BotStrategy(ABC):
    """
    Interface for bot AI strategies.

    Different bot implementations can provide varying
    levels of difficulty and play styles.
    """

    @abstractmethod
    def get_difficulty_level(self) -> str:
        """
        Get the difficulty level of this strategy.

        Returns:
            Difficulty level (e.g., "easy", "medium", "hard")
        """
        pass

    @abstractmethod
    def choose_declaration(
        self,
        hand: List[Piece],
        current_declarations: Dict[str, int],
        is_last_to_declare: bool,
    ) -> int:
        """
        Choose pile count declaration for the bot.

        Args:
            hand: Bot's current hand
            current_declarations: Declarations already made
            is_last_to_declare: Whether bot declares last

        Returns:
            Number of piles to declare (0-8)
        """
        pass

    @abstractmethod
    def choose_play(
        self,
        hand: List[Piece],
        current_plays: List[Tuple[str, List[Piece]]],
        required_piece_count: Optional[int],
    ) -> List[int]:
        """
        Choose pieces to play in a turn.

        Args:
            hand: Bot's current hand
            current_plays: Plays already made this turn
            required_piece_count: Number of pieces required

        Returns:
            Indices of pieces to play from hand
        """
        pass

    @abstractmethod
    def should_accept_redeal(
        self, hand: List[Piece], current_score: int, opponent_scores: Dict[str, int]
    ) -> bool:
        """
        Decide whether to accept a redeal offer.

        Args:
            hand: Current hand
            current_score: Bot's current score
            opponent_scores: Scores of other players

        Returns:
            True to accept redeal, False to decline
        """
        pass


class NotificationService(ABC):
    """
    Interface for sending notifications to players.

    Infrastructure can implement this to send notifications
    via different channels (WebSocket, email, push, etc).
    """

    @abstractmethod
    async def notify_game_started(self, room_id: str, player_names: List[str]) -> None:
        """
        Notify players that a game has started.

        Args:
            room_id: Room where game started
            player_names: Names of all players
        """
        pass

    @abstractmethod
    async def notify_turn_result(
        self, room_id: str, winner_name: str, plays: Dict[str, List[str]]
    ) -> None:
        """
        Notify players of turn results.

        Args:
            room_id: Room ID
            winner_name: Winner of the turn
            plays: What each player played
        """
        pass

    @abstractmethod
    async def notify_round_complete(
        self, room_id: str, scores: Dict[str, int], totals: Dict[str, int]
    ) -> None:
        """
        Notify players that a round is complete.

        Args:
            room_id: Room ID
            scores: Scores for this round
            totals: Total scores
        """
        pass

    @abstractmethod
    async def notify_game_over(
        self, room_id: str, winner_name: Optional[str], final_scores: Dict[str, int]
    ) -> None:
        """
        Notify players that the game is over.

        Args:
            room_id: Room ID
            winner_name: Winner name (None if tie)
            final_scores: Final scores
        """
        pass


class RoomManager(ABC):
    """
    Interface for managing game rooms at a system level.

    Provides operations beyond single room CRUD.
    """

    @abstractmethod
    async def create_room(self, room_id: str, host_name: str) -> str:
        """
        Create a new room.

        Args:
            room_id: Desired room ID
            host_name: Name of the host player

        Returns:
            Created room ID

        Raises:
            ValueError: If room ID already exists
        """
        pass

    @abstractmethod
    async def find_available_room(self) -> Optional[str]:
        """
        Find a room with available slots.

        Returns:
            Room ID if found, None otherwise
        """
        pass

    @abstractmethod
    async def cleanup_abandoned_rooms(self) -> int:
        """
        Clean up rooms with no human players.

        Returns:
            Number of rooms cleaned up
        """
        pass

    @abstractmethod
    async def get_room_statistics(self) -> Dict[str, any]:
        """
        Get statistics about rooms.

        Returns:
            Dictionary with room statistics
        """
        pass


class MetricsCollector(ABC):
    """
    Interface for collecting domain metrics.

    Infrastructure can implement this to track
    domain events and performance.
    """

    @abstractmethod
    def record_game_started(self, room_id: str, player_count: int) -> None:
        """Record that a game started."""
        pass

    @abstractmethod
    def record_game_completed(
        self, room_id: str, duration_seconds: float, rounds_played: int
    ) -> None:
        """Record that a game completed."""
        pass

    @abstractmethod
    def record_turn_played(
        self, room_id: str, play_type: str, piece_count: int
    ) -> None:
        """Record that a turn was played."""
        pass

    @abstractmethod
    def record_event_processed(
        self, event_type: str, processing_time_ms: float
    ) -> None:
        """Record domain event processing metrics."""
        pass

    @abstractmethod
    def get_metrics_summary(self) -> Dict[str, any]:
        """Get summary of collected metrics."""
        pass
