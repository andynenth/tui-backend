"""
Use case for getting current room state.

This use case retrieves the current state of a room, including
player information and game state if active.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from application.base import UseCase
from application.dto.room_management import GetRoomStateRequest, GetRoomStateResponse
from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
from application.interfaces import UnitOfWork, MetricsCollector
from application.exceptions import ResourceNotFoundException, AuthorizationException

logger = logging.getLogger(__name__)


class GetRoomStateUseCase(UseCase[GetRoomStateRequest, GetRoomStateResponse]):
    """
    Retrieves current room state.
    
    This use case:
    1. Validates access permissions
    2. Retrieves room information
    3. Includes game state if requested
    4. Formats response for client
    """
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        metrics: Optional[MetricsCollector] = None
    ):
        """
        Initialize the use case.
        
        Args:
            unit_of_work: Unit of work for data access
            metrics: Optional metrics collector
        """
        self._uow = unit_of_work
        self._metrics = metrics
    
    async def execute(self, request: GetRoomStateRequest) -> GetRoomStateResponse:
        """
        Get room state.
        
        Args:
            request: The state request
            
        Returns:
            Response with room and game state
            
        Raises:
            ResourceNotFoundException: If room not found
            AuthorizationException: If player not authorized
        """
        async with self._uow:
            # Get the room
            room = await self._uow.rooms.get_by_id(request.room_id)
            if not room:
                raise ResourceNotFoundException("Room", request.room_id)
            
            # Check authorization if player ID provided
            if request.requesting_player_id:
                player_in_room = any(
                    slot and slot.id == request.requesting_player_id
                    for slot in room.slots
                )
                
                # For private rooms, only allow players in the room
                if room.settings.is_private and not player_in_room:
                    raise AuthorizationException(
                        "view room state",
                        f"room {request.room_id}"
                    )
            
            # Create room info
            room_info = self._create_room_info(room)
            
            # Get game state if requested and available
            game_state = None
            if request.include_game_state and room.game:
                # The game is already loaded in the room entity
                game_state = self._serialize_game_state(room.game, room)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "room.state_retrieved",
                    tags={
                        "has_game": str(room.game is not None).lower(),
                        "is_private": "false"  # Room entity doesn't have settings
                    }
                )
            
            # Create response
            response = GetRoomStateResponse(
                success=True,
                request_id=request.request_id,
                room_info=room_info,
                game_state=game_state
            )
            
            logger.debug(
                f"Retrieved state for room {room.code}",
                extra={
                    "room_id": room.id,
                    "requesting_player": request.requesting_player_id,
                    "has_game_state": game_state is not None
                }
            )
            
            self._log_execution(request, response)
            return response
    
    def _create_room_info(self, room) -> RoomInfo:
        """Create RoomInfo DTO from room aggregate."""
        players = []
        
        for i, slot in enumerate(room.slots):
            if slot:
                players.append(PlayerInfo(
                    player_id=f"{room.room_id}_p{i}",  # Generate player ID
                    player_name=slot.name,
                    is_bot=slot.is_bot,
                    is_host=slot.name == room.host_name,  # Compare names, not IDs
                    status=PlayerStatus.CONNECTED if getattr(slot, 'is_connected', True) else PlayerStatus.DISCONNECTED,
                    seat_position=i,
                    score=slot.score,
                    games_played=getattr(slot, 'games_played', 0),  # Player entity might not have this
                    games_won=getattr(slot, 'games_won', 0)  # Player entity might not have this
                ))
        
        return RoomInfo(
            room_id=room.room_id,
            room_code=room.room_id,  # Using room_id as code
            room_name=f"{room.host_name}'s Room",  # Generate room name from host
            host_id=f"{room.room_id}_p0",  # Host is always first player
            status=RoomStatus.IN_GAME if room.game else RoomStatus.WAITING,
            players=players,
            max_players=room.max_slots,
            created_at=datetime.utcnow(),  # Room entity doesn't track creation time
            game_in_progress=room.game is not None,
            current_game_id=room.game.game_id if room.game else None
        )
    
    def _serialize_game_state(self, game, room) -> Dict[str, Any]:
        """Serialize game state for response."""
        # Get current phase info
        phase_info = {
            "name": game.phase.value if hasattr(game.phase, 'value') else str(game.phase),
            "round_number": game.round_number,
            "turn_number": game.turn_number
        }
        
        # Get player game states
        player_states = {}
        for i, player in enumerate(game.players):
            player_id = f"{room.room_id}_p{i}"  # Generate consistent player ID
            player_states[player_id] = {
                "pieces_in_hand": len(player.hand),
                "piles_captured": getattr(player, 'captured_piles', 0),  # Use captured_piles
                "declaration": getattr(player, 'declared_piles', None),  # Use declared_piles
                "current_round_score": getattr(player, 'score', 0)  # Use score
            }
        
        # Get current turn info
        current_turn = None
        if hasattr(game, 'current_player_id') and game.current_player_id:
            current_turn = {
                "player_id": game.current_player_id,
                "player_name": self._get_player_name(room, game.current_player_id),
                "action_required": self._get_required_action(game)
            }
        
        # Get last play info
        last_play = None
        if hasattr(game, 'last_play') and game.last_play:
            last_play = {
                "player_id": game.last_play.get("player_id"),
                "player_name": self._get_player_name(room, game.last_play.get("player_id")),
                "pieces_count": game.last_play.get("pieces_count"),
                "play_type": game.last_play.get("play_type")
            }
        
        return {
            "game_id": game.game_id if hasattr(game, 'game_id') else f"{room.room_id}_game",
            "phase": phase_info,
            "player_states": player_states,
            "current_turn": current_turn,
            "last_play": last_play,
            "scores": {f"{room.room_id}_p{i}": p.score for i, p in enumerate(game.players)},
            "settings": {
                "win_condition_type": "score",  # Default win condition
                "win_condition_value": 50,  # Default win value
                "rounds_played": game.round_number - 1,
                "winner": getattr(game, 'winner_id', None)
            }
        }
    
    def _get_player_name(self, room, player_id: str) -> Optional[str]:
        """Get player name from room."""
        # Extract player index from ID format: room_id_p0, room_id_p1, etc.
        try:
            player_index = int(player_id.split('_p')[1])
            slot = room.slots[player_index]
            return slot.name if slot else None
        except (IndexError, ValueError):
            return None
        return None
    
    def _get_required_action(self, game) -> str:
        """Determine what action is required from current player."""
        phase = game.phase.value if hasattr(game.phase, 'value') else str(game.phase)
        
        if phase == "DECLARATION":
            return "declare_piles"
        elif phase == "TURN":
            return "play_pieces"
        elif phase == "PREPARATION":
            if hasattr(game, 'weak_hand_detected'):
                return "respond_to_redeal"
            return "wait"
        else:
            return "wait"