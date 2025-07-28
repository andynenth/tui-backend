"""
Use case for getting detailed information about a specific room.

This use case provides comprehensive room information for players
considering joining a room.
"""

import logging
from typing import Optional, Dict, Any, List

from application.base import UseCase
from application.dto.lobby import (
    GetRoomDetailsRequest,
    GetRoomDetailsResponse,
    RoomDetails
)
from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
from application.interfaces import UnitOfWork, MetricsCollector
from application.exceptions import ResourceNotFoundException, ValidationException
from application.utils import PropertyMapper
from datetime import datetime

logger = logging.getLogger(__name__)


class GetRoomDetailsUseCase(UseCase[GetRoomDetailsRequest, GetRoomDetailsResponse]):
    """
    Retrieves detailed information about a room.
    
    This use case:
    1. Retrieves comprehensive room information
    2. Includes game settings and state
    3. Provides player statistics
    4. Evaluates join eligibility
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
    
    async def execute(self, request: GetRoomDetailsRequest) -> GetRoomDetailsResponse:
        """
        Get room details.
        
        Args:
            request: The details request
            
        Returns:
            Response with comprehensive room information
            
        Raises:
            ResourceNotFoundException: If room not found
            ValidationException: If request is invalid
        """
        # Validate request
        if not request.room_code and not request.room_id:
            raise ValidationException({
                "room": "Either room code or room ID is required"
            })
        
        async with self._uow:
            # Find the room
            room = None
            if request.room_code:
                room = await self._uow.rooms.get_by_code(request.room_code)
            elif request.room_id:
                room = await self._uow.rooms.get_by_id(request.room_id)
            
            if not room:
                raise ResourceNotFoundException(
                    "Room",
                    request.room_code or request.room_id
                )
            
            # Create room info
            room_info = self._create_room_info(room)
            
            # Get game settings
            game_settings = {
                "win_condition_type": PropertyMapper.get_room_attr(room, "settings.win_condition_type"),
                "win_condition_value": PropertyMapper.get_room_attr(room, "settings.win_condition_value"),
                "max_players": room.max_slots,
                "allow_bots": PropertyMapper.get_room_attr(room, "settings.allow_bots"),
                "is_private": PropertyMapper.get_room_attr(room, "settings.is_private"),
                "rounds_per_game": 20,  # Default game setting
                "time_limit_seconds": None  # No time limit by default
            }
            
            # Get game state summary if game in progress
            game_state_summary = None
            if request.include_game_details and room.game:
                game = await self._uow.games.get_by_id(room.game.game_id)
                if game:
                    game_state_summary = self._create_game_summary(game)
            
            # Get player statistics if requested
            player_stats = None
            if request.include_player_stats:
                player_stats = await self._get_player_stats(room)
            
            # Evaluate join eligibility
            join_restrictions = []
            can_join = True
            join_error = None
            
            # Check if room is full
            if room.is_full():
                join_restrictions.append("Room is full")
                can_join = False
                join_error = "Room is at maximum capacity"
            
            # Check if game in progress
            if room.game:
                join_restrictions.append("Game in progress")
                can_join = False
                join_error = "Cannot join while game is active"
            
            # Check if private room
            if PropertyMapper.get_room_attr(room, "settings.is_private"):
                join_restrictions.append("Private room - invite only")
            
            # Check if player already in a room
            if request.requesting_player_id:
                existing_room = await self._uow.rooms.find_by_player(
                    request.requesting_player_id
                )
                if existing_room and existing_room.room_id != room.room_id:
                    can_join = False
                    join_error = f"Already in room {existing_room.room_id}"
            
            # Create room details
            room_details = RoomDetails(
                room_info=room_info,
                game_settings=game_settings,
                game_state_summary=game_state_summary,
                player_stats=player_stats,
                is_joinable=can_join and not PropertyMapper.get_room_attr(room, "settings.is_private"),
                join_restrictions=join_restrictions
            )
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "lobby.room_details_retrieved",
                    tags={
                        "room_code": room.room_id,
                        "has_game": str(room.game is not None).lower(),
                        "can_join": str(can_join).lower()
                    }
                )
            
            # Create response
            response = GetRoomDetailsResponse(
                success=True,
                request_id=request.request_id,
                room_details=room_details,
                can_join=can_join,
                join_error=join_error
            )
            
            logger.info(
                f"Retrieved details for room {room.room_id}",
                extra={
                    "room_id": room.room_id,
                    "requesting_player": request.requesting_player_id,
                    "can_join": can_join
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
                    player_id=PropertyMapper.generate_player_id(room.room_id, i),
                    player_name=slot.name,
                    is_bot=slot.is_bot,
                    is_host=PropertyMapper.generate_player_id(room.room_id, i) == PropertyMapper.get_room_attr(room, "host_id"),
                    status=PlayerStatus.CONNECTED if getattr(slot, 'is_connected', True) else PlayerStatus.DISCONNECTED,
                    seat_position=i,
                    score=slot.score,
                    games_played=PropertyMapper.get_safe(slot, "games_played", 0),
                    games_won=PropertyMapper.get_safe(slot, "games_won", 0)
                ))
        
        return RoomInfo(
            room_id=room.room_id,
            room_code=room.room_id,
            room_name=f"{room.host_name}'s Room",
            host_id=PropertyMapper.get_room_attr(room, "host_id"),
            status=RoomStatus.IN_GAME if room.game else RoomStatus.WAITING,
            players=players,
            max_players=room.max_slots,
            created_at=datetime.utcnow(),
            game_in_progress=room.game is not None,
            current_game_id=room.game.game_id if room.game else None
        )
    
    def _create_game_summary(self, game) -> Dict[str, Any]:
        """Create summary of current game state."""
        return {
            "round_number": game.round_number,
            "total_rounds": 20,
            "phase": game.phase.value if hasattr(game.phase, 'value') else str(game.phase),
            "current_leader": self._get_current_leader(game),
            "scores": {p.id: p.score for p in game.players},
            "time_elapsed_seconds": None,  # Would calculate from game start time
            "estimated_completion_minutes": self._estimate_completion_time(game)
        }
    
    def _get_current_leader(self, game) -> Dict[str, Any]:
        """Get current game leader."""
        if not game.players:
            return None
        
        leader = max(game.players, key=lambda p: p.score)
        return {
            "player_id": leader.id,
            "player_name": leader.name,
            "score": leader.score
        }
    
    def _estimate_completion_time(self, game) -> int:
        """Estimate minutes until game completion."""
        rounds_remaining = 20 - game.round_number
        # Assume 3 minutes per round on average
        return rounds_remaining * 3
    
    async def _get_player_stats(self, room) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all players in room."""
        stats = {}
        
        for slot in room.slots:
            if slot and not slot.is_bot:
                player_stats = await self._uow.player_stats.get_stats(PropertyMapper.generate_player_id(room.room_id, i))
                stats[PropertyMapper.generate_player_id(room.room_id, i)] = {
                    "total_games": player_stats.get("total_games", 0),
                    "games_won": player_stats.get("games_won", 0),
                    "win_rate": player_stats.get("win_rate", 0.0),
                    "average_score": player_stats.get("average_score", 0),
                    "highest_score": player_stats.get("highest_score", 0),
                    "favorite_play_style": player_stats.get("favorite_play_style", "balanced")
                }
        
        return stats