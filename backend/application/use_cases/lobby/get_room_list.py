"""
Use case for getting a list of available rooms.

This use case handles room discovery in the lobby, providing
filtered and paginated room listings.
"""

import logging
from typing import Optional, List
from datetime import datetime

from application.base import UseCase
from application.dto.lobby import GetRoomListRequest, GetRoomListResponse, RoomSummary
from application.interfaces import UnitOfWork, MetricsCollector
from application.exceptions import ValidationException
from application.utils import PropertyMapper

logger = logging.getLogger(__name__)


class GetRoomListUseCase(UseCase[GetRoomListRequest, GetRoomListResponse]):
    """
    Retrieves a list of available rooms.

    This use case:
    1. Queries rooms based on filters
    2. Applies sorting and pagination
    3. Checks player's current room
    4. Formats room summaries
    """

    def __init__(
        self, unit_of_work: UnitOfWork, metrics: Optional[MetricsCollector] = None
    ):
        """
        Initialize the use case.

        Args:
            unit_of_work: Unit of work for data access
            metrics: Optional metrics collector
        """
        self._uow = unit_of_work
        self._metrics = metrics

    async def execute(self, request: GetRoomListRequest) -> GetRoomListResponse:
        """
        Get list of rooms.

        Args:
            request: The list request with filters

        Returns:
            Response with room list and pagination

        Raises:
            ValidationException: If request is invalid
        """
        # Validate request
        self._validate_request(request)

        async with self._uow:
            # Get all active rooms
            all_rooms = await self._uow.rooms.list_active(limit=1000)

            # Apply filters
            filtered_rooms = self._apply_filters(all_rooms, request)

            # Sort rooms
            sorted_rooms = self._sort_rooms(filtered_rooms, request)

            # Get player's current room if player_id provided
            player_current_room = None
            if request.player_id:
                current_room = await self._uow.rooms.find_by_player(request.player_id)
                if current_room:
                    player_current_room = self._create_room_summary(current_room)

            # Apply pagination
            total_items = len(sorted_rooms)
            start_index = (request.page - 1) * request.page_size
            end_index = start_index + request.page_size
            paginated_rooms = sorted_rooms[start_index:end_index]

            # Create room summaries
            room_summaries = [
                self._create_room_summary(room) for room in paginated_rooms
            ]

            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "lobby.room_list_retrieved",
                    tags={
                        "total_rooms": str(len(all_rooms)),
                        "filtered_rooms": str(len(filtered_rooms)),
                        "page": str(request.page),
                    },
                )

            # Create response
            response = GetRoomListResponse(
                rooms=room_summaries,
                player_current_room=player_current_room,
                page=request.page,
                page_size=request.page_size,
                total_items=total_items,
            )

            logger.debug(
                f"Retrieved {len(room_summaries)} rooms for lobby",
                extra={
                    "total_rooms": len(all_rooms),
                    "filtered_rooms": len(filtered_rooms),
                    "page": request.page,
                    "player_id": request.player_id,
                },
            )

            self._log_execution(request, response)
            return response

    def _validate_request(self, request: GetRoomListRequest) -> None:
        """Validate the list request."""
        errors = {}

        if request.sort_by not in ["created_at", "player_count", "room_name"]:
            errors["sort_by"] = "Invalid sort field"

        if request.sort_order not in ["asc", "desc"]:
            errors["sort_order"] = "Sort order must be 'asc' or 'desc'"

        if request.page < 1:
            errors["page"] = "Page must be positive"

        if request.page_size < 1 or request.page_size > 100:
            errors["page_size"] = "Page size must be between 1 and 100"

        if errors:
            raise ValidationException(errors)

    def _apply_filters(self, rooms: List, request: GetRoomListRequest) -> List:
        """Apply filters to room list."""
        filtered = []

        for room in rooms:
            # Skip private rooms unless requested
            is_private = PropertyMapper.get_room_attr(room, "settings.is_private")
            if is_private and not request.include_private:
                continue

            # Skip full rooms unless requested
            player_count = len([s for s in room.slots if s])
            if player_count >= room.max_slots and not request.include_full:
                continue

            # Skip rooms with games in progress unless requested
            if room.game and not request.include_in_game:
                continue

            # Filter by host if specified
            if request.filter_by_host and room.host_name != request.filter_by_host:
                continue

            filtered.append(room)

        return filtered

    def _sort_rooms(self, rooms: List, request: GetRoomListRequest) -> List:
        """Sort rooms according to request."""
        reverse = request.sort_order == "desc"

        if request.sort_by == "created_at":
            # Since rooms don't have created_at, sort by room_id (newer rooms have higher IDs)
            return sorted(rooms, key=lambda r: r.room_id, reverse=reverse)
        elif request.sort_by == "player_count":
            return sorted(
                rooms, key=lambda r: len([s for s in r.slots if s]), reverse=reverse
            )
        elif request.sort_by == "room_name":
            return sorted(
                rooms, key=lambda r: f"{r.host_name}'s Room".lower(), reverse=reverse
            )

        return rooms

    def _create_room_summary(self, room) -> RoomSummary:
        """Create room summary from room aggregate."""
        # Use PropertyMapper to get consistent room attributes
        room_mapped = PropertyMapper.map_room_for_use_case(room)

        return RoomSummary(
            room_id=room.room_id,
            room_code=room_mapped["code"],
            room_name=room_mapped["name"],
            host_name=room.host_name,
            player_count=room_mapped["player_count"],
            max_players=room.max_slots,
            game_in_progress=room.game is not None,
            is_private=room_mapped["settings"]["is_private"],
            created_at=room_mapped["created_at"],
        )
