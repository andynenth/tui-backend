# application/services/game_service.py
"""
Game service orchestrates game-related operations.
"""

import logging
from typing import Optional, List, Dict, Any

from domain.entities.game import Game
from domain.entities.player import Player
from domain.value_objects.game_state import GamePhase
from domain.services.game_rules import GameRules
from domain.services.scoring import ScoringService
from domain.interfaces.event_publisher import EventPublisher
from domain.events.game_events import (
    RoundStartedEvent,
    CardsDealtEvent,
    PhaseChangedEvent,
    RoundEndedEvent,
    GameEndedEvent
)

from ..interfaces.notification_service import NotificationService


logger = logging.getLogger(__name__)


class GameService:
    """
    Application service for game operations.
    
    This service orchestrates complex game operations that involve
    multiple domain objects and external services.
    """
    
    def __init__(
        self,
        game_repository,  # Will be defined in infrastructure
        event_publisher: EventPublisher,
        notification_service: NotificationService
    ):
        self._game_repository = game_repository
        self._event_publisher = event_publisher
        self._notification_service = notification_service
        self._scoring_service = ScoringService()
    
    async def get_game(self, game_id: str) -> Optional[Game]:
        """Get a game by ID."""
        return await self._game_repository.get(game_id)
    
    async def save_game(self, game: Game) -> None:
        """Save a game."""
        await self._game_repository.save(game)
    
    async def start_new_round(
        self,
        game_id: str,
        room_id: str
    ) -> Dict[str, Any]:
        """
        Start a new round in the game.
        
        Returns:
            Dict with round info and dealt cards
        """
        game = await self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        # Start the round
        game.start_round()
        
        # Save the updated game
        await self.save_game(game)
        
        # Publish round started event
        await self._event_publisher.publish(
            RoundStartedEvent(
                game_id=game_id,
                room_id=room_id,
                round_number=game.round_number,
                dealer=game.get_dealer().name
            )
        )
        
        # Get dealt cards for each player
        dealt_cards = {}
        for player in game.players:
            dealt_cards[player.name] = [
                {"value": p.value, "suit": p.suit}
                for p in player.pieces
            ]
        
        # Publish cards dealt event
        await self._event_publisher.publish(
            CardsDealtEvent(
                game_id=game_id,
                room_id=room_id,
                round_number=game.round_number
            )
        )
        
        # Notify each player of their cards
        for player_name, cards in dealt_cards.items():
            await self._notification_service.notify_player(
                player_name,
                "cards_dealt",
                {
                    "round_number": game.round_number,
                    "cards": cards,
                    "dealer": game.get_dealer().name
                }
            )
        
        return {
            "round_number": game.round_number,
            "dealer": game.get_dealer().name,
            "dealt_cards": dealt_cards
        }
    
    async def transition_phase(
        self,
        game_id: str,
        room_id: str,
        to_phase: GamePhase
    ) -> None:
        """
        Transition the game to a new phase.
        
        Args:
            game_id: The game ID
            room_id: The room ID
            to_phase: The target phase
        """
        game = await self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        old_phase = game.current_phase
        
        # Transition to new phase
        game.transition_to_phase(to_phase)
        
        # Save the updated game
        await self.save_game(game)
        
        # Publish phase changed event
        await self._event_publisher.publish(
            PhaseChangedEvent(
                game_id=game_id,
                room_id=room_id,
                from_phase=old_phase.value,
                to_phase=to_phase.value,
                round_number=game.round_number
            )
        )
        
        # Notify all players
        await self._notification_service.notify_room(
            room_id,
            "phase_changed",
            {
                "from_phase": old_phase.value,
                "to_phase": to_phase.value,
                "round_number": game.round_number
            }
        )
    
    async def calculate_round_scores(
        self,
        game_id: str,
        room_id: str
    ) -> Dict[str, int]:
        """
        Calculate and apply scores for the current round.
        
        Returns:
            Dict of player scores for this round
        """
        game = await self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        # Calculate scores
        round_scores = {}
        for player in game.players:
            score = self._scoring_service.calculate_round_score(
                declared_piles=player.declared_piles,
                actual_piles=player.pile_count,
                is_winner=player.pile_count == 0,
                total_piles_in_play=sum(p.pile_count for p in game.players)
            )
            
            round_scores[player.name] = score.total_score
            player.add_score(score.total_score)
        
        # Save the updated game
        await self.save_game(game)
        
        # Publish round ended event
        await self._event_publisher.publish(
            RoundEndedEvent(
                game_id=game_id,
                room_id=room_id,
                round_number=game.round_number,
                scores=round_scores,
                total_scores={p.name: p.total_score for p in game.players}
            )
        )
        
        # Check for game end
        if game.is_finished():
            winner = game.get_winner()
            await self._event_publisher.publish(
                GameEndedEvent(
                    game_id=game_id,
                    room_id=room_id,
                    winner=winner.name if winner else None,
                    final_scores={p.name: p.total_score for p in game.players},
                    total_rounds=game.round_number
                )
            )
        
        return round_scores
    
    async def handle_weak_hand_request(
        self,
        game_id: str,
        room_id: str,
        player_name: str
    ) -> bool:
        """
        Handle a weak hand redeal request.
        
        Returns:
            True if redeal should happen
        """
        game = await self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        player = game.get_player(player_name)
        if not player:
            raise ValueError(f"Player {player_name} not found")
        
        # Check if player has weak hand
        is_weak = GameRules.is_weak_hand(player.pieces)
        if not is_weak:
            return False
        
        # Mark player as requesting redeal
        player.request_redeal()
        
        # Save the game
        await self.save_game(game)
        
        # Notify all players
        await self._notification_service.notify_room(
            room_id,
            "redeal_requested",
            {
                "player": player_name,
                "reason": "weak_hand"
            }
        )
        
        return True
    
    async def get_game_state(
        self,
        game_id: str
    ) -> Dict[str, Any]:
        """
        Get the current state of a game.
        
        Returns:
            Dict with complete game state
        """
        game = await self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        return {
            "game_id": game_id,
            "round_number": game.round_number,
            "current_phase": game.current_phase.value,
            "turn_number": game.turn_number,
            "players": [
                {
                    "name": p.name,
                    "total_score": p.total_score,
                    "pieces_count": len(p.pieces),
                    "pile_count": p.pile_count,
                    "declared_piles": p.declared_piles,
                    "is_connected": p.is_connected
                }
                for p in game.players
            ],
            "is_finished": game.is_finished(),
            "winner": game.get_winner().name if game.is_finished() and game.get_winner() else None
        }