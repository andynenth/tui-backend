"""
Use case for synchronizing client state.

When clients reconnect or miss events, they need to synchronize their
state with the server. This use case provides the current state.
"""

from typing import Optional, Dict, Any, List
import logging

from application.base import UseCase
from application.dto.connection import SyncClientStateRequest, SyncClientStateResponse
from application.interfaces import UnitOfWork
from application.exceptions import ResourceNotFoundException
from domain.entities.game import GamePhase
from application.utils import PropertyMapper

logger = logging.getLogger(__name__)


class SyncClientStateUseCase(UseCase[SyncClientStateRequest, SyncClientStateResponse]):
    """
    Synchronizes client state with server.
    
    This use case:
    1. Retrieves current room state
    2. Retrieves current game state if active
    3. Retrieves player's hand if in game
    4. Calculates missed events based on sequence number
    """
    
    def __init__(self, unit_of_work: UnitOfWork):
        """
        Initialize the use case.
        
        Args:
            unit_of_work: Unit of work for data access
        """
        self._uow = unit_of_work
    
    async def execute(self, request: SyncClientStateRequest) -> SyncClientStateResponse:
        """
        Synchronize client state.
        
        Args:
            request: The sync request
            
        Returns:
            Response with current state
            
        Raises:
            ResourceNotFoundException: If player not found
        """
        async with self._uow:
            room_state = None
            game_state = None
            player_hand = None
            current_sequence = 0
            
            # If room_id provided, get room state
            if request.room_id:
                room = await self._uow.rooms.get_by_id(request.room_id)
                if room:
                    room_state = self._serialize_room_state(room, request.player_id)
                    
                    # Get game state if requested and game is active
                    if request.include_game_state and room.game:
                        game = await self._uow.games.get_by_id(room.game.game_id)
                        if game:
                            game_state = self._serialize_game_state(game, request.player_id)
                            
                            # Get player hand if requested
                            if request.include_player_hands:
                                player_hand = self._get_player_hand(game, request.player_id)
                    
                    # Get current sequence number (would come from event store)
                    current_sequence = getattr(room, '_sequence_number', 0)
            
            else:
                # Player not in a room - find if they're in any room
                room = await self._uow.rooms.find_by_player(request.player_id)
                if room:
                    request.room_id = room.room_id
                    # Recursive call with room_id set
                    return await self.execute(request)
            
            # Calculate events missed
            events_missed = 0
            if request.last_known_sequence and current_sequence > request.last_known_sequence:
                events_missed = current_sequence - request.last_known_sequence
            
            # Create response
            response = SyncClientStateResponse(
                success=True,
                request_id=request.request_id,
                player_id=request.player_id,
                room_state=room_state,
                game_state=game_state,
                player_hand=player_hand,
                current_sequence=current_sequence,
                events_missed=events_missed
            )
            
            logger.info(
                f"Synchronized state for player {request.player_id}",
                extra={
                    "player_id": request.player_id,
                    "room_id": request.room_id,
                    "events_missed": events_missed,
                    "has_game_state": game_state is not None
                }
            )
            
            self._log_execution(request, response)
            return response
    
    def _serialize_room_state(self, room, player_id: str) -> Dict[str, Any]:
        """Serialize room state for client."""
        players = []
        for i, slot in enumerate(room.slots):
            if slot:
                players.append({
                    "player_id": PropertyMapper.generate_player_id(room.room_id, i),
                    "player_name": slot.name,
                    "is_bot": slot.is_bot,
                    "is_host": PropertyMapper.generate_player_id(room.room_id, i) == PropertyMapper.get_room_attr(room, "host_id"),
                    "is_connected": getattr(slot, 'is_connected', True),
                    "is_ready": getattr(slot, 'is_ready', False),
                    "seat_position": i,
                    "score": slot.score
                })
        
        return {
            "room_id": room.room_id,
            "room_code": room.room_id,
            "room_name": f"{room.host_name}'s Room",
            "host_id": PropertyMapper.get_room_attr(room, "host_id"),
            "players": players,
            "max_players": room.max_players,
            "game_in_progress": room.game is not None,
            "settings": room.settings.to_dict() if hasattr(room, 'settings') else {}
        }
    
    def _serialize_game_state(self, game, player_id: str) -> Dict[str, Any]:
        """Serialize game state for client."""
        return {
            "game_id": game.game_id,
            "round_number": game.round_number,
            "turn_number": game.turn_number,
            "phase": game.phase.value if hasattr(game.phase, 'value') else str(game.phase),
            "current_player_id": getattr(game, 'current_player_id', None),
            "declarations": self._get_declarations(game),
            "last_play": self._get_last_play(game),
            "scores": self._get_scores(game),
            "pieces_remaining": self._get_pieces_remaining(game)
        }
    
    def _get_player_hand(self, game, player_id: str) -> Dict[str, Any]:
        """Get player's current hand."""
        for player in game.players:
            if PropertyMapper.get_player_attr(player, "id", room.room_id, i) == player_id:
                return {
                    "pieces": [
                        {"value": p.value, "kind": p.kind}
                        for p in player.hand
                    ],
                    "piece_count": len(player.hand)
                }
        return {"pieces": [], "piece_count": 0}
    
    def _get_declarations(self, game) -> Dict[str, int]:
        """Get all player declarations."""
        declarations = {}
        if hasattr(game, 'declarations'):
            for player_id, declaration in game.declarations.items():
                declarations[player_id] = declaration
        return declarations
    
    def _get_last_play(self, game) -> Optional[Dict[str, Any]]:
        """Get information about the last play."""
        if hasattr(game, 'last_play') and game.last_play:
            return {
                "player_id": game.last_play.get("player_id"),
                "pieces_count": game.last_play.get("pieces_count"),
                "play_type": game.last_play.get("play_type")
            }
        return None
    
    def _get_scores(self, game) -> Dict[str, int]:
        """Get current scores."""
        scores = {}
        for player in game.players:
            scores[PropertyMapper.get_player_attr(player, "id", room.room_id, i)] = player.score
        return scores
    
    def _get_pieces_remaining(self, game) -> Dict[str, int]:
        """Get pieces remaining for each player."""
        pieces = {}
        for player in game.players:
            pieces[PropertyMapper.get_player_attr(player, "id", room.room_id, i)] = len(player.hand)
        return pieces