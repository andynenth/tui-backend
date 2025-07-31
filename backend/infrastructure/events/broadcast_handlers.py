"""
Event handlers that convert domain events to WebSocket broadcasts.

These handlers maintain exact compatibility with current WebSocket message formats
while decoupling the domain from infrastructure concerns.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from domain.events.all_events import *
from domain.events.room_events import PlayerRemoved
from infrastructure.events.decorators import event_handler
from infrastructure.websocket.connection_singleton import broadcast

logger = logging.getLogger(__name__)


# Connection Event Handlers


@event_handler(ConnectionHeartbeat, priority=100)
async def handle_connection_heartbeat(event: ConnectionHeartbeat):
    """Convert heartbeat event to pong response."""
    # Direct response to the specific websocket
    response = {
        "event": "pong",
        "data": {
            "timestamp": event.client_timestamp,
            "server_time": event.server_timestamp,
            "room_id": None,  # Will be filled by adapter if in room
        },
    }
    # Note: This requires the websocket_id to be mapped to actual websocket
    # This will be handled by the adapter layer
    logger.debug(f"Heartbeat response prepared for {event.websocket_id}")


@event_handler(ClientReady, priority=100)
async def handle_client_ready(event: ClientReady):
    """Handle client ready event - no broadcast needed for this."""
    # Client ready doesn't trigger a broadcast in current system
    logger.debug(f"Client {event.player_name} ready in room {event.room_id}")


# Room Event Handlers


@event_handler(RoomCreated, priority=100)
async def handle_room_created(event: RoomCreated):
    """Convert room created event to room_created response and update lobby."""
    logger.info(
        f"[BROADCAST_HANDLER_DEBUG] handle_room_created called for room {event.room_id}"
    )
    # This is sent back to the creator, not broadcast
    response = {
        "event": "room_created",
        "data": {
            "room_id": event.room_id,
            "host_name": event.host_name,
            "success": True,
        },
    }
    # Note: Adapter will handle sending to correct websocket
    logger.debug(f"Room {event.room_id} created by {event.host_name}")

    # Broadcast updated room list to lobby
    import asyncio

    try:
        # Use room data from event if available (avoids transaction timing issues)
        if event.room_data:
            logger.info(
                f"[BROADCAST_HANDLER_DEBUG] Using room data from event for {event.room_id}"
            )
            available_rooms = [event.room_data]
        else:
            logger.info(
                f"[BROADCAST_HANDLER_DEBUG] Falling back to database query for {event.room_id}"
            )
            # Fallback to database query (original approach)
            from infrastructure.dependencies import get_unit_of_work
            from application.services.lobby_application_service import (
                LobbyApplicationService,
            )
            from application.dto.lobby import GetRoomListRequest

            # Get updated room list
            uow = get_unit_of_work()
            lobby_service = LobbyApplicationService(unit_of_work=uow)
            list_request = GetRoomListRequest(
                player_id="",
                include_full=True,  # Show full rooms so newly created rooms (4/4 with bots) are visible
                include_in_game=False,
            )
            list_response = await lobby_service._get_room_list_use_case.execute(
                list_request
            )

            # Convert room summaries to legacy format and fetch player details
            available_rooms = []
            async with uow:
                for room_summary in list_response.rooms:
                    # Get full room details to include players
                    room_entity = await uow.rooms.get_by_id(room_summary.room_id)
                    if room_entity:
                        available_rooms.append(
                            {
                                "room_id": room_entity.room_id,
                                "room_code": room_summary.room_code,
                                "room_name": room_summary.room_name,
                                "host_name": room_entity.host_name,
                                "player_count": room_summary.player_count,
                                "max_players": room_summary.max_players,
                                "game_in_progress": room_summary.game_in_progress,
                                "is_private": room_summary.is_private,
                                "players": [
                                    (
                                        {"name": slot.name, "is_bot": slot.is_bot}
                                        if slot
                                        else None
                                    )
                                    for slot in room_entity.slots
                                ],
                            }
                        )

        # Broadcast to lobby
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )
        logger.info(
            f"[BROADCAST_DEBUG] Sent room_list_update to lobby with {len(available_rooms)} rooms after room created"
        )
    except Exception as e:
        logger.error(f"Failed to broadcast room list update: {e}", exc_info=True)


@event_handler(PlayerJoinedRoom, priority=100)
async def handle_player_joined_room(event: PlayerJoinedRoom):
    """Broadcast room update when player joins."""
    # Get actual room state from database
    from infrastructure.dependencies import get_unit_of_work

    try:
        uow = get_unit_of_work()
        async with uow:
            room = await uow.rooms.get_by_id(event.room_id)
            if room:
                # Create room update data with actual room state
                room_update_data = {
                    "room_id": event.room_id,
                    "players": [
                        (
                            {
                                "name": slot.name,
                                "is_bot": slot.is_bot,
                                "is_host": slot.name
                                == room.host_name,  # Add missing is_host field
                                "player_id": getattr(
                                    slot, "player_id", f"{event.room_id}_p{i}"
                                ),
                                "seat_position": i,
                            }
                            if slot
                            else None
                        )
                        for i, slot in enumerate(room.slots)
                    ],
                    "host_name": room.host_name,
                    "started": (
                        room.is_game_started()
                        if hasattr(room, "is_game_started")
                        else False
                    ),
                    "timestamp": datetime.utcnow().timestamp(),
                }

                # Broadcast room update to room participants
                await broadcast(event.room_id, "room_update", room_update_data)
                logger.info(f"Player {event.player_name} joined room {event.room_id}")
            else:
                logger.warning(
                    f"Room {event.room_id} not found for player joined broadcast"
                )
    except Exception as e:
        logger.error(
            f"Error broadcasting player joined room update: {e}", exc_info=True
        )

    # Broadcast updated room list to lobby (same pattern as handle_room_created)
    import asyncio

    try:
        from infrastructure.dependencies import get_unit_of_work
        from application.services.lobby_application_service import (
            LobbyApplicationService,
        )
        from application.dto.lobby import GetRoomListRequest

        # Get updated room list
        uow = get_unit_of_work()
        lobby_service = LobbyApplicationService(unit_of_work=uow)
        list_request = GetRoomListRequest(
            player_id="",
            include_full=True,  # Show full rooms so newly created rooms (4/4 with bots) are visible
            include_in_game=False,
        )
        list_response = await lobby_service._get_room_list_use_case.execute(
            list_request
        )

        # Convert room summaries to legacy format and fetch player details
        available_rooms = []
        async with uow:
            for room_summary in list_response.rooms:
                # Get full room details to include players
                room_entity = await uow.rooms.get_by_id(room_summary.room_id)
                if room_entity:
                    available_rooms.append(
                        {
                            "room_id": room_entity.room_id,
                            "room_code": room_summary.room_code,
                            "room_name": room_summary.room_name,
                            "host_name": room_entity.host_name,
                            "player_count": room_summary.player_count,
                            "max_players": room_summary.max_players,
                            "game_in_progress": room_summary.game_in_progress,
                            "is_private": room_summary.is_private,
                            "players": [
                                (
                                    {"name": slot.name, "is_bot": slot.is_bot}
                                    if slot
                                    else None
                                )
                                for slot in room_entity.slots
                            ],
                        }
                    )

        # Broadcast to lobby
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )
        logger.info(
            f"[BROADCAST_DEBUG] Sent room_list_update to lobby with {len(available_rooms)} rooms after player joined"
        )
    except Exception as e:
        logger.error(
            f"Failed to broadcast room list update after player joined: {e}",
            exc_info=True,
        )


@event_handler(PlayerLeftRoom, priority=100)
async def handle_player_left_room(event: PlayerLeftRoom):
    """Broadcast room update when player leaves."""
    # Get actual room state from database and use standardized formatting
    from infrastructure.dependencies import get_unit_of_work
    from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
    from application.utils import PropertyMapper

    try:
        uow = get_unit_of_work()
        async with uow:
            room = await uow.rooms.get_by_id(event.room_id)
            if room:
                # Debug logging for host detection
                logger.info(
                    f"[HOST_DEBUG] PlayerLeftRoom - room.host_name: '{room.host_name}'"
                )
                logger.info(
                    f"[HOST_DEBUG] PlayerLeftRoom - room.host_id: '{room.host_id}'"
                )
                logger.info(
                    f"[HOST_DEBUG] PlayerLeftRoom - event.player_name: '{event.player_name}'"
                )

                # Create standardized room info DTO like other handlers
                players_info = []
                for i, slot in enumerate(room.slots):
                    if slot:
                        player_info = PlayerInfo(
                            player_id=PropertyMapper.generate_player_id(
                                room.room_id, i
                            ),
                            player_name=slot.name,
                            is_bot=slot.is_bot,
                            is_host=slot.name
                            == room.host_name,  # Explicit host detection
                            status=(
                                PlayerStatus.CONNECTED
                                if getattr(slot, "is_connected", True)
                                else PlayerStatus.DISCONNECTED
                            ),
                            seat_position=i,
                        )
                        players_info.append(player_info)
                        logger.info(
                            f"[HOST_DEBUG] Player {i}: name='{slot.name}', is_host={player_info.is_host}"
                        )

                # Create room info DTO using the same structure as other handlers
                room_info = RoomInfo(
                    room_id=room.room_id,
                    room_code=room.room_id,
                    room_name=f"{room.host_name}'s Room",
                    host_id=room.host_id,
                    status=RoomStatus.WAITING,
                    players=players_info,
                    max_players=4,
                    created_at=datetime.utcnow(),
                    game_in_progress=(
                        room.is_game_started()
                        if hasattr(room, "is_game_started")
                        else False
                    ),
                    current_game_id=None,
                )

                # Format room info for broadcast
                # Build players array maintaining slot positions
                players_array = [None] * 4  # Initialize with 4 None slots
                for player_info in room_info.players:
                    if (
                        player_info.seat_position is not None
                        and 0 <= player_info.seat_position < 4
                    ):
                        players_array[player_info.seat_position] = {
                            "player_id": player_info.player_id,
                            "name": player_info.player_name,
                            "is_bot": player_info.is_bot,
                            "is_host": player_info.is_host,
                            "seat_position": player_info.seat_position,
                        }

                formatted_room = {
                    "room_id": room_info.room_id,
                    "room_code": room_info.room_code,
                    "room_name": room_info.room_name,
                    "host_id": room_info.host_id,
                    "host_name": room.host_name,
                    "players": players_array,
                    "max_players": room_info.max_players,
                    "game_in_progress": room_info.game_in_progress,
                    "started": room_info.game_in_progress,
                    "status": (
                        room_info.status.value
                        if hasattr(room_info.status, "value")
                        else str(room_info.status)
                    ),
                }

                # Add timestamp for event tracking
                formatted_room["timestamp"] = datetime.utcnow().timestamp()
                formatted_room["event_type"] = "player_left"

                # Debug the final formatted data
                logger.info(f"[HOST_DEBUG] Final formatted room players:")
                for i, player in enumerate(formatted_room["players"]):
                    if player:
                        logger.info(
                            f"[HOST_DEBUG] Player {i}: name='{player['name']}', is_host={player['is_host']}"
                        )

                # Broadcast room update to room participants
                await broadcast(event.room_id, "room_update", formatted_room)
                logger.info(f"Player {event.player_name} left room {event.room_id}")
            else:
                logger.warning(
                    f"Room {event.room_id} not found for player left broadcast"
                )
    except Exception as e:
        logger.error(f"Error broadcasting player left room update: {e}", exc_info=True)

    # Broadcast updated room list to lobby (same pattern as handle_room_created)
    import asyncio

    try:
        from infrastructure.dependencies import get_unit_of_work
        from application.services.lobby_application_service import (
            LobbyApplicationService,
        )
        from application.dto.lobby import GetRoomListRequest

        # Get updated room list
        uow = get_unit_of_work()
        lobby_service = LobbyApplicationService(unit_of_work=uow)
        list_request = GetRoomListRequest(
            player_id="",
            include_full=True,  # Show full rooms so newly created rooms (4/4 with bots) are visible
            include_in_game=False,
        )
        list_response = await lobby_service._get_room_list_use_case.execute(
            list_request
        )

        # Convert room summaries to legacy format and fetch player details
        available_rooms = []
        async with uow:
            for room_summary in list_response.rooms:
                # Get full room details to include players
                room_entity = await uow.rooms.get_by_id(room_summary.room_id)
                if room_entity:
                    available_rooms.append(
                        {
                            "room_id": room_entity.room_id,
                            "room_code": room_summary.room_code,
                            "room_name": room_summary.room_name,
                            "host_name": room_entity.host_name,
                            "player_count": room_summary.player_count,
                            "max_players": room_summary.max_players,
                            "game_in_progress": room_summary.game_in_progress,
                            "is_private": room_summary.is_private,
                            "players": [
                                (
                                    {"name": slot.name, "is_bot": slot.is_bot}
                                    if slot
                                    else None
                                )
                                for slot in room_entity.slots
                            ],
                        }
                    )

        # Broadcast to lobby
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )
        logger.info(
            f"[BROADCAST_DEBUG] Sent room_list_update to lobby with {len(available_rooms)} rooms after player left"
        )
    except Exception as e:
        logger.error(
            f"Failed to broadcast room list update after player left: {e}",
            exc_info=True,
        )


@event_handler(RoomClosed, priority=100)
async def handle_room_closed(event: RoomClosed):
    """Broadcast room closure to all participants."""
    logger.info(f"[BROADCAST_DEBUG] Broadcasting room_closed for room {event.room_id}")

    # Broadcast to all participants in the room that it's being closed
    await broadcast(
        event.room_id,
        "room_closed",
        {
            "room_id": event.room_id,
            "reason": event.reason,
            "message": f"Room closed: {event.reason}",
            "final_player_count": event.final_player_count,
        },
    )
    logger.info(f"Room {event.room_id} closed: {event.reason}")


@event_handler(HostChanged, priority=100)
async def handle_host_changed(event: HostChanged):
    """Broadcast host change."""
    await broadcast(
        event.room_id,
        "host_changed",
        {
            "old_host": event.old_host_name,
            "new_host": event.new_host_name,
            "reason": event.reason,
        },
    )


@event_handler(BotAdded, priority=90)
async def handle_bot_added(event: BotAdded):
    """Handle bot addition - triggers room update."""
    # Get actual room state from database
    from infrastructure.dependencies import get_unit_of_work

    try:
        uow = get_unit_of_work()
        async with uow:
            room = await uow.rooms.get_by_id(event.room_id)
            if room:
                # Create room update data with actual room state
                room_update_data = {
                    "room_id": event.room_id,
                    "players": [
                        (
                            {
                                "name": slot.name,
                                "is_bot": slot.is_bot,
                                "is_host": slot.name
                                == room.host_name,  # Add missing is_host field
                                "player_id": getattr(
                                    slot, "player_id", f"{event.room_id}_p{i}"
                                ),
                                "seat_position": i,
                            }
                            if slot
                            else None
                        )
                        for i, slot in enumerate(room.slots)
                    ],
                    "host_name": room.host_name,
                    "started": (
                        room.is_game_started()
                        if hasattr(room, "is_game_started")
                        else False
                    ),
                    "timestamp": datetime.utcnow().timestamp(),
                }

                # Broadcast room update to room participants
                await broadcast(event.room_id, "room_update", room_update_data)
                logger.info(f"Bot {event.bot_name} added to room {event.room_id}")
            else:
                logger.warning(
                    f"Room {event.room_id} not found for bot added broadcast"
                )
    except Exception as e:
        logger.error(f"Error broadcasting bot added room update: {e}", exc_info=True)

    # Broadcast updated room list to lobby (same pattern as handle_room_created)
    import asyncio

    try:
        from infrastructure.dependencies import get_unit_of_work
        from application.services.lobby_application_service import (
            LobbyApplicationService,
        )
        from application.dto.lobby import GetRoomListRequest

        # Get updated room list
        uow = get_unit_of_work()
        lobby_service = LobbyApplicationService(unit_of_work=uow)
        list_request = GetRoomListRequest(
            player_id="",
            include_full=True,  # Show full rooms so newly created rooms (4/4 with bots) are visible
            include_in_game=False,
        )
        list_response = await lobby_service._get_room_list_use_case.execute(
            list_request
        )

        # Convert room summaries to legacy format and fetch player details
        available_rooms = []
        async with uow:
            for room_summary in list_response.rooms:
                # Get full room details to include players
                room_entity = await uow.rooms.get_by_id(room_summary.room_id)
                if room_entity:
                    available_rooms.append(
                        {
                            "room_id": room_entity.room_id,
                            "room_code": room_summary.room_code,
                            "room_name": room_summary.room_name,
                            "host_name": room_entity.host_name,
                            "player_count": room_summary.player_count,
                            "max_players": room_summary.max_players,
                            "game_in_progress": room_summary.game_in_progress,
                            "is_private": room_summary.is_private,
                            "players": [
                                (
                                    {"name": slot.name, "is_bot": slot.is_bot}
                                    if slot
                                    else None
                                )
                                for slot in room_entity.slots
                            ],
                        }
                    )

        # Broadcast to lobby
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )
        logger.info(
            f"[BROADCAST_DEBUG] Sent room_list_update to lobby with {len(available_rooms)} rooms after bot added"
        )
    except Exception as e:
        logger.error(
            f"Failed to broadcast room list update after bot added: {e}", exc_info=True
        )


@event_handler(PlayerRemoved, priority=100)
async def handle_player_removed(event: PlayerRemoved):
    """Handle player removal (including bots) - triggers room and lobby updates."""
    # Get actual room state from database and use standardized formatting
    from infrastructure.dependencies import get_unit_of_work
    from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
    from application.utils import PropertyMapper

    try:
        uow = get_unit_of_work()
        async with uow:
            room = await uow.rooms.get_by_id(event.room_id)
            if room:
                # Debug logging for host detection
                logger.info(
                    f"[HOST_DEBUG] PlayerRemoved - room.host_name: '{room.host_name}'"
                )
                logger.info(
                    f"[HOST_DEBUG] PlayerRemoved - event.removed_player_name: '{event.removed_player_name}'"
                )

                # Create standardized room info DTO like other handlers
                players_info = []
                for i, slot in enumerate(room.slots):
                    if slot:
                        player_info = PlayerInfo(
                            player_id=PropertyMapper.generate_player_id(
                                room.room_id, i
                            ),
                            player_name=slot.name,
                            is_bot=slot.is_bot,
                            is_host=slot.name
                            == room.host_name,  # Explicit host detection
                            status=(
                                PlayerStatus.CONNECTED
                                if getattr(slot, "is_connected", True)
                                else PlayerStatus.DISCONNECTED
                            ),
                            seat_position=i,
                        )
                        players_info.append(player_info)
                        logger.info(
                            f"[HOST_DEBUG] Player {i}: name='{slot.name}', is_host={player_info.is_host}"
                        )

                # Create room info DTO using the same structure as other handlers
                room_info = RoomInfo(
                    room_id=room.room_id,
                    room_code=room.room_id,
                    room_name=f"{room.host_name}'s Room",
                    host_id=room.host_id,
                    status=RoomStatus.WAITING,
                    players=players_info,
                    max_players=4,
                    created_at=datetime.utcnow(),
                    game_in_progress=(
                        room.is_game_started()
                        if hasattr(room, "is_game_started")
                        else False
                    ),
                    current_game_id=None,
                )

                # Format room info for broadcast
                # Build players array maintaining slot positions
                players_array = [None] * 4  # Initialize with 4 None slots
                for player_info in room_info.players:
                    if (
                        player_info.seat_position is not None
                        and 0 <= player_info.seat_position < 4
                    ):
                        players_array[player_info.seat_position] = {
                            "player_id": player_info.player_id,
                            "name": player_info.player_name,
                            "is_bot": player_info.is_bot,
                            "is_host": player_info.is_host,
                            "seat_position": player_info.seat_position,
                        }

                formatted_room = {
                    "room_id": room_info.room_id,
                    "room_code": room_info.room_code,
                    "room_name": room_info.room_name,
                    "host_id": room_info.host_id,
                    "host_name": room.host_name,
                    "players": players_array,
                    "max_players": room_info.max_players,
                    "game_in_progress": room_info.game_in_progress,
                    "started": room_info.game_in_progress,
                    "status": (
                        room_info.status.value
                        if hasattr(room_info.status, "value")
                        else str(room_info.status)
                    ),
                }

                # Add timestamp for event tracking
                formatted_room["timestamp"] = datetime.utcnow().timestamp()
                formatted_room["event_type"] = "player_removed"

                # Debug the final formatted data
                logger.info(
                    f"[HOST_DEBUG] PlayerRemoved - Final formatted room players:"
                )
                for i, player in enumerate(formatted_room["players"]):
                    if player:
                        logger.info(
                            f"[HOST_DEBUG] Player {i}: name='{player['name']}', is_host={player['is_host']}"
                        )

                await broadcast(event.room_id, "room_update", formatted_room)
                logger.info(
                    f"Player {event.removed_player_name} removed from room {event.room_id}"
                )
            else:
                logger.warning(
                    f"Room {event.room_id} not found for player removed broadcast"
                )
    except Exception as e:
        logger.error(
            f"Error broadcasting player removed room update: {e}", exc_info=True
        )

    # Broadcast updated room list to lobby (same pattern as handle_room_created)
    import asyncio

    try:
        from infrastructure.dependencies import get_unit_of_work
        from application.services.lobby_application_service import (
            LobbyApplicationService,
        )
        from application.dto.lobby import GetRoomListRequest

        # Get updated room list
        uow = get_unit_of_work()
        lobby_service = LobbyApplicationService(unit_of_work=uow)
        list_request = GetRoomListRequest(
            player_id="",
            include_full=True,  # Show full rooms so newly created rooms (4/4 with bots) are visible
            include_in_game=False,
        )
        list_response = await lobby_service._get_room_list_use_case.execute(
            list_request
        )

        # Convert room summaries to legacy format and fetch player details
        available_rooms = []
        async with uow:
            for room_summary in list_response.rooms:
                # Get full room details to include players
                room_entity = await uow.rooms.get_by_id(room_summary.room_id)
                if room_entity:
                    available_rooms.append(
                        {
                            "room_id": room_entity.room_id,
                            "room_code": room_summary.room_code,
                            "room_name": room_summary.room_name,
                            "host_name": room_entity.host_name,
                            "player_count": room_summary.player_count,
                            "max_players": room_summary.max_players,
                            "game_in_progress": room_summary.game_in_progress,
                            "is_private": room_summary.is_private,
                            "players": [
                                (
                                    {"name": slot.name, "is_bot": slot.is_bot}
                                    if slot
                                    else None
                                )
                                for slot in room_entity.slots
                            ],
                        }
                    )

        # Broadcast to lobby
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )
        logger.info(
            f"[BROADCAST_DEBUG] Sent room_list_update to lobby with {len(available_rooms)} rooms after player removed"
        )
    except Exception as e:
        logger.error(
            f"Failed to broadcast room list update after player removed: {e}",
            exc_info=True,
        )


# Game Flow Event Handlers


@event_handler(GameStarted, priority=100)
async def handle_game_started(event: GameStarted):
    """Broadcast game start."""
    await broadcast(
        event.room_id,
        "game_started",
        {
            "round_number": event.round_number,
            "players": event.player_names,
            "timestamp": datetime.utcnow().timestamp(),
        },
    )


@event_handler(PhaseChanged, priority=100)
async def handle_phase_changed(event: PhaseChanged):
    """Broadcast phase change - this is the main game state update."""
    logger.info(
        f"[BROADCAST_DEBUG] Broadcasting phase_change event: {event.old_phase} -> {event.new_phase}"
    )
    logger.info(
        f"[BROADCAST_DEBUG] Phase data keys: {list(event.phase_data.keys()) if event.phase_data else 'None'}"
    )

    # Log player hands if present
    if event.phase_data and "players" in event.phase_data:
        for player_name, player_data in event.phase_data["players"].items():
            hand_size = len(player_data.get("hand", [])) if player_data else 0
            logger.info(
                f"[BROADCAST_DEBUG] Player {player_name} has {hand_size} pieces"
            )

    await broadcast(
        event.room_id,
        "phase_change",
        {
            "phase": event.new_phase,
            "previous_phase": event.old_phase,
            "phase_data": event.phase_data,
            "timestamp": datetime.utcnow().timestamp(),
        },
    )

    logger.info(
        f"[BROADCAST_DEBUG] phase_change event broadcast complete for room {event.room_id}"
    )


@event_handler(PiecesPlayed, priority=100)
async def handle_pieces_played(event: PiecesPlayed):
    """Broadcast when pieces are played."""
    await broadcast(
        event.room_id,
        "turn_played",
        {
            "player": event.player_name,
            "pieces": event.pieces,
            "pieces_remaining": 8
            - len(event.pieces) * event.turn_number,  # Approximate
        },
    )


@event_handler(TurnWinnerDetermined, priority=100)
async def handle_turn_winner(event: TurnWinnerDetermined):
    """Broadcast turn results."""
    await broadcast(
        event.room_id,
        "turn_complete",
        {
            "turn_number": event.turn_number,
            "winner": event.winner_name,
            "winning_play": event.winning_play,
            "all_plays": event.all_plays,
        },
    )


@event_handler(DeclarationMade, priority=100)
async def handle_declaration_made(event: DeclarationMade):
    """Broadcast declaration."""
    await broadcast(
        event.room_id,
        "declare",
        {
            "player": event.player_name,
            "value": event.declared_count,
            "timestamp": datetime.utcnow().timestamp(),
        },
    )


@event_handler(WeakHandDetected, priority=100)
async def handle_weak_hand_detected(event: WeakHandDetected):
    """Broadcast weak hands found."""
    await broadcast(
        event.room_id,
        "weak_hands_found",
        {"players": event.weak_hand_players, "round_number": event.round_number},
    )


@event_handler(RedealDecisionMade, priority=100)
async def handle_redeal_decision(event: RedealDecisionMade):
    """Handle individual redeal decisions."""
    # These are typically part of phase_change updates
    logger.info(f"Player {event.player_name} {event.decision} redeal")


@event_handler(RedealExecuted, priority=100)
async def handle_redeal_executed(event: RedealExecuted):
    """Broadcast that redeal was executed."""
    await broadcast(
        event.room_id,
        "redeal_executed",
        {
            "acceptors": event.acceptors,
            "decliners": event.decliners,
            "new_starter": event.new_starter_name,
        },
    )


# Scoring Event Handlers


@event_handler(ScoresCalculated, priority=100)
async def handle_scores_calculated(event: ScoresCalculated):
    """Broadcast score update."""
    await broadcast(
        event.room_id,
        "score_update",
        {
            "round_number": event.round_number,
            "round_scores": event.round_scores,
            "total_scores": event.total_scores,
            "declarations": event.declarations,
            "actual_piles": event.actual_piles,
        },
    )


@event_handler(GameEnded, priority=100)
async def handle_game_ended(event: GameEnded):
    """Broadcast game end."""
    await broadcast(
        event.room_id,
        "game_ended",
        {
            "winner": event.winner_name,
            "final_scores": event.final_scores,
            "total_rounds": event.total_rounds,
            "reason": event.end_reason,
        },
    )


# Error Event Handlers


@event_handler(InvalidActionAttempted, priority=100)
async def handle_invalid_action(event: InvalidActionAttempted):
    """Send error message for invalid action."""
    error_data = {
        "event": "error",
        "data": {
            "message": event.reason,
            "type": event.action_type,
            "details": event.details or {},
        },
    }
    # This should be sent to specific player, not broadcast
    # Adapter will handle routing
    logger.warning(f"Invalid action by {event.player_name}: {event.reason}")


@event_handler(ErrorOccurred, priority=100)
async def handle_error(event: ErrorOccurred):
    """Handle system errors."""
    logger.error(f"System error: {event.error_type} - {event.error_message}")


# Lobby Event Handlers


@event_handler(RoomListUpdated, priority=100)
async def handle_room_list_updated(event: RoomListUpdated):
    """Broadcast updated room list to lobby."""
    # This goes to all clients in lobby, not a specific room
    await broadcast(
        "lobby",
        "room_list_update",
        {
            "rooms": event.rooms,
            "timestamp": datetime.utcnow().timestamp(),
            "reason": event.reason,
        },
    )


# Helper class to provide room state context


class BroadcastEventHandlers:
    """
    Container for broadcast event handlers with state access.

    This class will be initialized with access to room state
    so handlers can include full state in broadcasts.
    """

    def __init__(self, room_manager=None):
        self.room_manager = room_manager

    def get_room_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get current room state for broadcasts."""
        if not self.room_manager:
            return None

        room = self.room_manager.get_room(room_id)
        if not room:
            return None

        # Convert room to broadcast format
        return {
            "room_id": room_id,
            "players": [
                {
                    "name": player.name,
                    "slot": f"P{i+1}",
                    "is_bot": player.is_bot,
                    "connected": player.connected,
                }
                for i, player in enumerate(room.players)
            ],
            "host_name": room.host.name if room.host else None,
            "started": room.game_started,
            "timestamp": datetime.utcnow().timestamp(),
        }
