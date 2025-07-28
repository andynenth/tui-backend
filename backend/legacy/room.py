# backend/engine/room.py

import asyncio
import logging
import os
import time
from typing import (  # Import Optional for type hinting variables that can be None.
    Optional,
)

from engine.game import Game  # Import the Game class, representing the core game logic.
from engine.player import (  # Import the Player class, representing a player in the game.
    Player,
)
from engine.state_machine.core import GamePhase
from engine.state_machine.game_state_machine import GameStateMachine

logger = logging.getLogger(__name__)


class Room:
    """
    The Room class manages the state of a single game room, including players,
    game status, and provides methods for managing room participants.
    """

    # Timeout configuration for different disconnect scenarios
    IN_GAME_CLEANUP_TIMEOUT_SECONDS = int(os.getenv("IN_GAME_CLEANUP_TIMEOUT", "30"))
    PRE_GAME_CLEANUP_TIMEOUT_SECONDS = 0  # Always immediate for pre-game

    def __init__(self, room_id: str, host_name: str):
        """
        Initializes a new game room.
        Args:
            room_id (str): The unique identifier for the room.
            host_name (str): The name of the player who created and hosts the room.
        """
        self.room_id = room_id  # Unique ID of the room.
        self.host_name = host_name  # Name of the room's host.
        # Initialize player slots. There are 4 slots (P1-P4), initially all None.
        self.players = [None, None, None, None]
        self.started = (
            False  # Boolean flag indicating if the game in this room has started.
        )
        self.game: Optional[Game] = (
            None  # The Game instance associated with this room, initially None.
        )
        self.game_state_machine: Optional[GameStateMachine] = (
            None  # State machine for game logic
        )

        self._assign_lock = asyncio.Lock()  # Prevent concurrent slot assignments
        self._join_lock = asyncio.Lock()  # Prevent concurrent room joins
        self._state_lock = asyncio.Lock()  # Protect room state changes

        self._pending_operations = set()  # Track ongoing operations
        self._last_operation_id = 0  # For operation sequencing

        # Cleanup tracking
        self.last_human_disconnect_time = None  # When last human left
        self.cleanup_scheduled = False  # Flag to prevent duplicate scheduling

        # Assign the host to the first slot (P1).
        self.players[0] = Player(host_name, is_bot=False, available_colors=self.get_available_colors())

        # Assign bots to the remaining slots (P2-P4) by default.
        for i in range(1, 4):
            self.players[i] = Player(f"Bot {i+1}", is_bot=True)

    @property
    def CLEANUP_TIMEOUT_SECONDS(self):
        """Dynamic timeout based on room state"""
        timeout = (
            self.IN_GAME_CLEANUP_TIMEOUT_SECONDS
            if self.started
            else self.PRE_GAME_CLEANUP_TIMEOUT_SECONDS
        )
        logger.info(
            f"⏱️ [ROOM_DEBUG] Room '{self.room_id}' using cleanup timeout: {timeout}s (started={self.started})"
        )
        return timeout

    def _generate_operation_id(self) -> str:
        """Generate unique operation ID for tracking"""
        self._last_operation_id += 1
        return f"{self.room_id}_{self._last_operation_id}"

    def get_available_colors(self) -> list[str]:
        """Get list of avatar colors not currently in use by human players"""
        all_colors = ["blue", "purple", "orange", "red", "green", "teal", "pink", "yellow"]
        used_colors = []
        
        for player in self.players:
            if player and not player.is_bot and player.avatar_color:
                used_colors.append(player.avatar_color)
        
        available = [color for color in all_colors if color not in used_colors]
        logger.debug(f"[Room {self.room_id}] Available colors: {available}, Used: {used_colors}")
        return available

    async def assign_slot_safe(self, slot: int, name_or_none: Optional[str]) -> dict:
        """
        ✅ Thread-safe slot assignment with operation tracking
        """
        operation_id = self._generate_operation_id()

        try:
            # Check if operation is already in progress
            if operation_id in self._pending_operations:
                raise ValueError(f"Operation {operation_id} already in progress")

            self._pending_operations.add(operation_id)

            async with self._assign_lock:

                # Validate slot number first
                if slot < 0 or slot > 3:
                    raise ValueError("Invalid slot number")

                # Get current state
                old_state = self._get_slot_state_snapshot()

                # Perform the assignment
                kicked_player = self.get_kicked_player(slot, name_or_none)
                self.assign_slot(slot, name_or_none)

                # Get new state
                new_state = self._get_slot_state_snapshot()

                return {
                    "success": True,
                    "operation_id": operation_id,
                    "kicked_player": kicked_player,
                    "old_state": old_state,
                    "new_state": new_state,
                    "timestamp": asyncio.get_event_loop().time(),
                }

        except Exception as e:
            raise
        finally:
            # Always remove from pending operations
            self._pending_operations.discard(operation_id)

    async def join_room_safe(self, player_name: str) -> dict:
        """
        ✅ Thread-safe room joining with duplicate prevention
        """
        operation_id = self._generate_operation_id()

        try:
            self._pending_operations.add(operation_id)

            async with self._join_lock:

                # Check if player already exists (more thorough check)
                existing_slots = []
                for i, player in enumerate(self.players):
                    if player and player.name == player_name and not player.is_bot:
                        existing_slots.append(i)

                if existing_slots:
                    return {
                        "success": False,
                        "reason": f"Player '{player_name}' already in room at slots: {existing_slots}",
                        "existing_slots": existing_slots,
                        "operation_id": operation_id,
                    }

                # Check room capacity
                if self.is_full():
                    return {
                        "success": False,
                        "reason": "Room is full",
                        "operation_id": operation_id,
                    }

                # Find and assign slot
                assigned_slot = self.join_room(player_name)

                return {
                    "success": True,
                    "assigned_slot": assigned_slot,
                    "operation_id": operation_id,
                    "room_state": self.summary(),
                    "timestamp": asyncio.get_event_loop().time(),
                }

        except Exception as e:
            return {"success": False, "reason": str(e), "operation_id": operation_id}
        finally:
            self._pending_operations.discard(operation_id)

    async def start_game_safe(self, broadcast_callback=None) -> dict:
        """
        ✅ Thread-safe game starting
        """
        operation_id = self._generate_operation_id()

        try:
            self._pending_operations.add(operation_id)

            async with self._state_lock:

                if self.started:
                    raise ValueError("Game already started")

                # Validate all slots are filled
                empty_slots = [i for i, p in enumerate(self.players) if p is None]
                if empty_slots:
                    raise ValueError(
                        f"Cannot start game: slots {empty_slots} are empty. All slots must be filled."
                    )

                # สร้าง Game instance
                self.game = Game(self.players)
                self.game.start_time = time.time()

                # Initialize GameStateMachine with WebSocket broadcasting
                self.game_state_machine = GameStateMachine(
                    self.game, broadcast_callback
                )
                self.game_state_machine.room_id = (
                    self.room_id
                )  # Add room_id for bot manager

                # Register with bot manager BEFORE starting state machine to avoid race conditions
                from .bot_manager import BotManager

                bot_manager = BotManager()
                bot_manager.register_game(
                    self.room_id, self.game, self.game_state_machine
                )

                await self.game_state_machine.start(GamePhase.PREPARATION)

                self.started = True

                return {
                    "success": True,
                    "operation_id": operation_id,
                    "game_created": True,
                    "state_machine_initialized": True,
                    "timestamp": asyncio.get_event_loop().time(),
                }

        except Exception as e:
            raise
        finally:
            self._pending_operations.discard(operation_id)

    def _get_slot_state_snapshot(self) -> dict:
        """Get current snapshot of all slots for debugging"""
        return {
            f"P{i+1}": {
                "name": p.name if p else None,
                "is_bot": p.is_bot if p else None,
            }
            for i, p in enumerate(self.players)
        }

    def validate_state(self) -> dict:
        """
        ✅ Enhanced state validation with detailed reporting
        """
        issues = []
        warnings = []

        # Check slot consistency
        occupied_calculated = sum(1 for p in self.players if p is not None)
        occupied_reported = self.get_occupied_slots()
        if occupied_calculated != occupied_reported:
            issues.append(
                f"Slot count mismatch: calculated={occupied_calculated}, reported={occupied_reported}"
            )

        # Check host exists
        host_slots = [
            i
            for i, p in enumerate(self.players)
            if p and p.name == self.host_name and not p.is_bot
        ]
        if not host_slots:
            issues.append(f"Host '{self.host_name}' not found in any slot")
        elif len(host_slots) > 1:
            warnings.append(
                f"Host '{self.host_name}' found in multiple slots: {host_slots}"
            )

        # Check for duplicate players (non-bot)
        player_counts = {}
        for i, p in enumerate(self.players):
            if p and not p.is_bot:
                if p.name not in player_counts:
                    player_counts[p.name] = []
                player_counts[p.name].append(i)

        duplicates = {
            name: slots for name, slots in player_counts.items() if len(slots) > 1
        }
        if duplicates:
            for name, slots in duplicates.items():
                issues.append(f"Player '{name}' appears in multiple slots: {slots}")

        # Check pending operations
        if self._pending_operations:
            warnings.append(f"Pending operations: {list(self._pending_operations)}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "state_snapshot": self._get_slot_state_snapshot(),
            "pending_operations": list(self._pending_operations),
        }

    def get_occupied_slots(self) -> int:
        """
        Counts the number of occupied slots (by both human players and bots).
        Returns:
            int: The count of non-empty slots.
        """
        return sum(1 for player in self.players if player is not None)

    def get_total_slots(self) -> int:
        """
        Returns the total number of slots available in the room.
        Returns:
            int: The total number of player slots.
        """
        return len(self.players)

    def is_full(self) -> bool:
        """
        Checks if the room is completely full (all slots are occupied).
        Returns:
            bool: True if the room is full, False otherwise.
        """
        return self.get_occupied_slots() >= self.get_total_slots()

    def migrate_host(self) -> Optional[str]:
        """
        Migrates host privileges to the next suitable player.
        Prefers human players over bots.
        Returns:
            Optional[str]: Name of the new host, or None if no suitable host found.
        """
        # First, try to find a human player who isn't the current host
        for player in self.players:
            if player and not player.is_bot and player.name != self.host_name:
                old_host = self.host_name
                self.host_name = player.name
                logger.info(
                    f"[Room {self.room_id}] Host migrated from '{old_host}' to '{self.host_name}'"
                )
                return self.host_name

        # If no human players available, select the first bot
        for player in self.players:
            if player and player.is_bot:
                old_host = self.host_name
                self.host_name = player.name
                logger.info(
                    f"[Room {self.room_id}] Host migrated from '{old_host}' to bot '{self.host_name}'"
                )
                return self.host_name

        # No suitable host found (room is empty?)
        logger.warning(f"[Room {self.room_id}] No suitable host found for migration")
        return None

    def is_host(self, player_name: str) -> bool:
        """
        Check if a player is the current host.
        Args:
            player_name (str): The name of the player to check.
        Returns:
            bool: True if the player is the host, False otherwise.
        """
        return self.host_name == player_name

    def summary(self):
        """
        Generates a summary of the room's current state, suitable for sending to clients.
        Includes information about occupied and total slots.
        Returns:
            dict: A dictionary containing room_id, host_name, started status,
                  slot information, occupied slots count, and total slots count.
        """

        def slot_info(player: Optional[Player], slot_index: int):
            """
            Helper function to get simplified information for a player slot.
            Args:
                player (Optional[Player]): The Player object or None if the slot is empty.
                slot_index (int): The slot index (0-3) to determine if this is the host slot.
            Returns:
                dict or None: A dictionary with player name, bot status, and host status, or None if the slot is empty.
            """
            if player is None:
                return None  # Return None if the slot is empty.
            return {
                "name": player.name,  # Always use player.name, regardless of whether it's a bot or human.
                "is_bot": player.is_bot,
                "is_host": slot_index == 0,  # Host is always in slot 0 (P1)
                "avatar_color": getattr(
                    player, "avatar_color", None
                ),  # Add avatar color
            }

        return {
            "room_id": self.room_id,
            "host_name": self.host_name,
            "started": self.started,
            "slots": {
                # Create a dictionary mapping slot names (P1, P2, etc.) to their info.
                f"P{i+1}": slot_info(p, i)
                for i, p in enumerate(self.players)
            },
            "players": [
                slot_info(p, i) for i, p in enumerate(self.players)
            ],  # ✅ Added players array for frontend
            "occupied_slots": self.get_occupied_slots(),  # ✅ Added occupied slots count.
            "total_slots": self.get_total_slots(),  # ✅ Added total slots count.
        }

    def assign_slot(self, slot: int, name_or_none: Optional[str]):
        """
        Assigns a player (human or bot) or clears a slot.
        If a human player is assigned to a slot, and they were previously in another slot,
        their old slot is cleared.
        Args:
            slot (int): The 0-indexed slot number (0 to 3).
            name_or_none (Optional[str]): The name of the player/bot to assign, or None to clear the slot.
        Raises:
            ValueError: If the slot number is invalid.
        """
        if slot < 0 or slot > 3:
            raise ValueError("Invalid slot number")  # Validate slot index.

        # If a human player is being assigned, check for duplicates and move them.
        if name_or_none and not (
            name_or_none.startswith("BOT_") or name_or_none.startswith("Bot")
        ):
            # Check if this player is already in another slot in the room.
            for i, player in enumerate(self.players):
                if (
                    i != slot
                    and player
                    and player.name == name_or_none
                    and not player.is_bot
                ):
                    self.players[i] = (
                        None  # Clear the old slot if the player is found elsewhere.
                    )
                    break

        # Assign the new player/bot or clear the slot.
        if name_or_none is None:
            self.players[slot] = None  # Clear the slot.
        elif name_or_none.startswith("BOT_") or name_or_none.startswith("Bot"):
            self.players[slot] = Player(name_or_none, is_bot=True)  # Assign a bot.
        else:
            self.players[slot] = Player(
                name_or_none, is_bot=False, available_colors=self.get_available_colors()
            )  # Assign a human player.

    def join_room(self, player_name: str) -> int:
        """
        Allows a player to join the room.
        Automatically assigns the player to the first available empty slot.
        If no empty slots, replaces the first available bot.
        Args:
            player_name (str): The name of the player attempting to join.
        Returns:
            int: The index of the slot the player joined.
        Raises:
            ValueError: If the player is already in the room or no available slots.
        """
        # Allow duplicate names - players distinguished by color
        # for i, player in enumerate(self.players):
        #     if player and player.name == player_name and not player.is_bot:
        #         raise ValueError(f"Player '{player_name}' is already in this room.")

        # 2. Find the first truly empty slot (None).
        for i, player in enumerate(self.players):
            if player is None:
                self.players[i] = Player(player_name, is_bot=False, available_colors=self.get_available_colors())
                return i

        # 3. If no empty slots, find the first bot slot to replace.
        for i, player in enumerate(self.players):
            if player and player.is_bot:
                self.players[i] = Player(player_name, is_bot=False, available_colors=self.get_available_colors())
                return i

        # If no suitable slot was found (all slots are filled by other human players).
        raise ValueError("No available slot (all slots are filled by human players).")

    def exit_room(self, player_name: str) -> bool:
        """
        Handles a player exiting the room.
        If the host exits, the room should be considered for deletion.
        Args:
            player_name (str): The name of the player exiting.
        Returns:
            bool: True if the exiting player was the host, False otherwise.
        """
        logger.info(
            f"🚪 [ROOM_DEBUG] exit_room called for player '{player_name}' in room '{self.room_id}'"
        )

        if player_name == self.host_name:
            logger.info(
                f"👑 [ROOM_DEBUG] Host '{player_name}' is exiting room '{self.room_id}' - room will be deleted"
            )
            return True  # If the host exits, signal to remove the entire room.

        # Find and remove the specific human player.
        for i, player in enumerate(self.players):
            if player and not player.is_bot and player.name == player_name:
                self.players[i] = None  # Set the player's slot to None (empty).
                logger.info(
                    f"👥 [ROOM_DEBUG] Regular player '{player_name}' removed from slot {i} in room '{self.room_id}'"
                )
                return False  # Player exited, but not the host.

        logger.info(
            f"⚠️ [ROOM_DEBUG] Player '{player_name}' not found or was a bot in room '{self.room_id}'"
        )
        return False  # Player not found or was a bot.

    def start_game(self):
        """
        Starts the game within the room.
        """
        if self.started:
            raise ValueError("Game already started")

        # Validate all slots are filled
        empty_slots = [i for i, p in enumerate(self.players) if p is None]
        if empty_slots:
            raise ValueError(
                f"Cannot start game: slots {empty_slots} are empty. All slots must be filled."
            )

        self.game = Game(self.players)
        self.started = True

    def get_kicked_player(
        self, slot: int, new_assignment: Optional[str]
    ) -> Optional[str]:
        """
        Checks if a player will be kicked from a slot when a new assignment is made.
        Args:
            slot (int): The 0-indexed slot number being assigned to.
            new_assignment (Optional[str]): The name of the new player/bot, or None if clearing the slot.
        Returns:
            Optional[str]: The name of the player who would be kicked, or None if no one is kicked.
        """
        current = self.players[slot]  # Get the current player/bot in the slot.

        # If the slot is currently empty or has a bot, no one is kicked.
        if not current or current.is_bot:
            return None

        # If a bot is being assigned to a slot currently held by a human player, that player is kicked.
        if new_assignment and (
            new_assignment.startswith("Bot") or new_assignment.startswith("BOT_")
        ):
            return current.name

        # If a different human player is being assigned to a slot currently held by another human player,
        # the current player is kicked.
        if new_assignment and new_assignment != current.name:
            return current.name

        return None  # No player is kicked in other scenarios.

    def has_any_human_players(self) -> bool:
        """
        Check if there are ANY human players in the room (connected or disconnected).
        This is used to determine if the room should continue existing.
        Returns:
            bool: True if at least one human player exists, False if all are bots
        """
        if not self.game:
            logger.info(
                f"🎮 [ROOM_DEBUG] has_any_human_players: No game object for room '{self.room_id}'"
            )
            return False

        human_count = 0
        bot_count = 0
        for player in self.game.players:
            if player:
                if player.is_bot:
                    bot_count += 1
                else:
                    human_count += 1

        logger.info(
            f"👥 [ROOM_DEBUG] Room '{self.room_id}' player count: {human_count} humans, {bot_count} bots"
        )
        return human_count > 0

    def mark_for_cleanup(self):
        """Mark room for cleanup after all humans disconnect"""
        if not self.has_any_human_players():
            self.last_human_disconnect_time = time.time()
            self.cleanup_scheduled = True
            logger.info(
                f"🗑️ [ROOM_DEBUG] Room '{self.room_id}' marked for cleanup at {self.last_human_disconnect_time}, timeout={self.CLEANUP_TIMEOUT_SECONDS}s"
            )
        else:
            logger.info(
                f"❌ [ROOM_DEBUG] Room '{self.room_id}' NOT marked for cleanup - still has human players"
            )

    def cancel_cleanup(self):
        """Cancel pending cleanup when human reconnects"""
        self.last_human_disconnect_time = None
        self.cleanup_scheduled = False
        logger.info(
            f"✅ [ROOM_DEBUG] Cleanup cancelled for room '{self.room_id}' - human player reconnected"
        )

    def should_cleanup(self) -> bool:
        """Check if room should be cleaned up based on timeout"""
        if not self.cleanup_scheduled:
            return False

        if self.last_human_disconnect_time is None:
            return False

        elapsed = time.time() - self.last_human_disconnect_time
        should_cleanup = elapsed >= self.CLEANUP_TIMEOUT_SECONDS

        if should_cleanup:
            logger.info(
                f"📢 [ROOM_DEBUG] Room '{self.room_id}' should be cleaned up: elapsed={elapsed:.2f}s >= timeout={self.CLEANUP_TIMEOUT_SECONDS}s"
            )

        return should_cleanup
