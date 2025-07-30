"""
Game adapters updated to use the domain layer.

These adapters integrate with the pure domain layer created in Phase 3,
using domain entities, services, and events.
"""

from typing import Dict, Any, Optional, List
import logging

# Domain imports
from domain.entities.room import Room
from domain.entities.game import Game
from domain.entities.player import Player
from domain.services.game_rules import GameRules
from domain.services.scoring_service import ScoringService
from domain.services.turn_resolution import TurnResolutionService
from domain.value_objects.piece import Piece
from domain.value_objects.declaration import Declaration, DeclarationSet
from domain.events.game_events import (
    GameStarted,
    PhaseChanged,
    TurnCompleted,
    TurnWinnerDetermined,
    RoundCompleted,
)
from domain.events.player_events import (
    PlayerDeclaredPiles,
    PlayerHandUpdated,
    PlayerCapturedPiles,
    PlayerScoreUpdated,
)

logger = logging.getLogger(__name__)


class DomainGameAdapter:
    """Adapter that bridges WebSocket messages to domain operations."""

    def __init__(self, room_repository, event_publisher):
        """
        Initialize with domain interfaces.

        Args:
            room_repository: Repository for Room persistence
            event_publisher: Publisher for domain events
        """
        self.room_repository = room_repository
        self.event_publisher = event_publisher
        self.game_rules = GameRules()
        self.scoring_service = ScoringService()
        self.turn_resolution = TurnResolutionService()

    async def handle_start_game(
        self, websocket, message: Dict[str, Any], room_id: str
    ) -> Dict[str, Any]:
        """Handle start_game using domain layer."""
        try:
            # Get room from repository
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return {"event": "error", "data": {"message": "Room not found"}}

            # Validate through domain
            if not room.can_start_game():
                return {
                    "event": "error",
                    "data": {"message": "Cannot start game in current state"},
                }

            # Start game through domain
            events = room.start_game()

            # Publish all domain events
            for event in events:
                await self.event_publisher.publish(event)

            # Save updated room
            await self.room_repository.save(room)

            return {
                "event": "game_started",
                "data": {
                    "game_id": room.game.game_id if room.game else None,
                    "phase": room.game.phase.value if room.game else None,
                    "players": [p.to_dict() for p in room.players],
                },
            }

        except Exception as e:
            logger.error(f"Error starting game: {e}")
            return {"event": "error", "data": {"message": str(e)}}

    async def handle_declare(
        self, websocket, message: Dict[str, Any], room_id: str
    ) -> Dict[str, Any]:
        """Handle declaration using domain layer."""
        try:
            data = message.get("data", {})
            player_name = data.get("player_name")
            declaration_value = data.get("value")

            # Get room from repository
            room = await self.room_repository.find_by_id(room_id)
            if not room or not room.game:
                return {"event": "error", "data": {"message": "No active game"}}

            # Create declaration through domain
            player = room.get_player(player_name)
            if not player:
                return {"event": "error", "data": {"message": "Player not found"}}

            # Make declaration through game
            events = room.game.make_declaration(player_name, declaration_value)

            # Publish events
            for event in events:
                await self.event_publisher.publish(event)

            # Save updated room
            await self.room_repository.save(room)

            return {
                "event": "declaration_made",
                "data": {
                    "player": player_name,
                    "value": declaration_value,
                    "declarations": room.game.get_declarations(),
                },
            }

        except ValueError as e:
            return {"event": "error", "data": {"message": str(e)}}

    async def handle_play(
        self, websocket, message: Dict[str, Any], room_id: str
    ) -> Dict[str, Any]:
        """Handle play action using domain layer."""
        try:
            data = message.get("data", {})
            player_name = data.get("player_name")
            pieces_data = data.get("pieces", [])

            # Get room from repository
            room = await self.room_repository.find_by_id(room_id)
            if not room or not room.game:
                return {"event": "error", "data": {"message": "No active game"}}

            # Convert piece data to domain objects
            pieces = []
            for piece_data in pieces_data:
                piece = Piece(kind=piece_data["kind"], color=piece_data["color"])
                pieces.append(piece)

            # Validate play through domain service
            play_type = self.game_rules.identify_play_type(pieces)
            if not self.game_rules.is_valid_play(pieces, play_type):
                return {"event": "error", "data": {"message": "Invalid play"}}

            # Execute play through game
            events = room.game.play_pieces(player_name, pieces)

            # Check if turn is complete
            if room.game.is_turn_complete():
                # Resolve turn winner
                turn_result = self.turn_resolution.resolve_turn(
                    room.game.get_current_turn_plays()
                )

                # Process turn completion
                completion_events = room.game.complete_turn(turn_result)
                events.extend(completion_events)

            # Publish all events
            for event in events:
                await self.event_publisher.publish(event)

            # Save updated room
            await self.room_repository.save(room)

            return {
                "event": "play_made",
                "data": {
                    "player": player_name,
                    "pieces": [p.to_dict() for p in pieces],
                    "play_type": play_type,
                },
            }

        except Exception as e:
            logger.error(f"Error handling play: {e}")
            return {"event": "error", "data": {"message": str(e)}}

    async def handle_redeal_request(
        self, websocket, message: Dict[str, Any], room_id: str
    ) -> Dict[str, Any]:
        """Handle redeal request using domain layer."""
        try:
            data = message.get("data", {})
            player_name = data.get("player_name")

            # Get room from repository
            room = await self.room_repository.find_by_id(room_id)
            if not room or not room.game:
                return {"event": "error", "data": {"message": "No active game"}}

            # Request redeal through game
            events = room.game.request_redeal(player_name)

            # Publish events
            for event in events:
                await self.event_publisher.publish(event)

            # Save updated room
            await self.room_repository.save(room)

            return {
                "event": "redeal_requested",
                "data": {
                    "requester": player_name,
                    "weak_hand_players": room.game.get_weak_hand_players(),
                },
            }

        except Exception as e:
            return {"event": "error", "data": {"message": str(e)}}

    async def handle_redeal_decision(
        self, websocket, message: Dict[str, Any], room_id: str
    ) -> Dict[str, Any]:
        """Handle redeal decision using domain layer."""
        try:
            data = message.get("data", {})
            player_name = data.get("player_name")
            accept = data.get("accept", False)

            # Get room from repository
            room = await self.room_repository.find_by_id(room_id)
            if not room or not room.game:
                return {"event": "error", "data": {"message": "No active game"}}

            # Make redeal decision through game
            if accept:
                events = room.game.accept_redeal(player_name)
            else:
                events = room.game.decline_redeal(player_name)

            # Publish events
            for event in events:
                await self.event_publisher.publish(event)

            # Save updated room
            await self.room_repository.save(room)

            return {
                "event": "redeal_decision_made",
                "data": {
                    "player": player_name,
                    "accepted": accept,
                    "redeal_complete": room.game.is_redeal_complete(),
                },
            }

        except Exception as e:
            return {"event": "error", "data": {"message": str(e)}}
