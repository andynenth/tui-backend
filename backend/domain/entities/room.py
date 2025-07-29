"""
Room aggregate root - manages the overall game room state.

This is a pure domain entity with no infrastructure dependencies.
Acts as the aggregate root for the entire game bounded context.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum

from domain.entities.player import Player
from domain.entities.game import Game, GamePhase
from domain.value_objects.piece import Piece
from domain.events.base import DomainEvent, GameEvent, EventMetadata


class RoomStatus(Enum):
    """Room status states."""
    WAITING = "WAITING"      # Waiting for players
    READY = "READY"          # All slots filled, can start
    IN_GAME = "IN_GAME"      # Game in progress
    COMPLETED = "COMPLETED"  # Game completed
    ABANDONED = "ABANDONED"  # All humans left


@dataclass(frozen=True)
class RoomCreated(GameEvent):
    """A room has been created."""
    host_name: str
    total_slots: int
    
    def _get_event_data(self) -> Dict:
        data = super()._get_event_data()
        data.update({
            'host_name': self.host_name,
            'total_slots': self.total_slots
        })
        return data


@dataclass(frozen=True)
class PlayerJoinedRoom(GameEvent):
    """A player joined the room."""
    player_name: str
    slot_index: int
    is_bot: bool
    
    def _get_event_data(self) -> Dict:
        data = super()._get_event_data()
        data.update({
            'player_name': self.player_name,
            'slot_index': self.slot_index,
            'is_bot': self.is_bot
        })
        return data


@dataclass(frozen=True)
class PlayerLeftRoom(GameEvent):
    """A player left the room."""
    player_name: str
    slot_index: int
    was_host: bool
    
    def _get_event_data(self) -> Dict:
        data = super()._get_event_data()
        data.update({
            'player_name': self.player_name,
            'slot_index': self.slot_index,
            'was_host': self.was_host
        })
        return data


@dataclass(frozen=True)
class HostMigrated(GameEvent):
    """Host privileges migrated to another player."""
    old_host: str
    new_host: str
    
    def _get_event_data(self) -> Dict:
        data = super()._get_event_data()
        data.update({
            'old_host': self.old_host,
            'new_host': self.new_host
        })
        return data


@dataclass(frozen=True)
class RoomStatusChanged(GameEvent):
    """Room status has changed."""
    old_status: str
    new_status: str
    
    def _get_event_data(self) -> Dict:
        data = super()._get_event_data()
        data.update({
            'old_status': self.old_status,
            'new_status': self.new_status
        })
        return data


@dataclass(frozen=True)
class GameStartedInRoom(GameEvent):
    """A game has started in the room."""
    player_names: List[str]
    
    def _get_event_data(self) -> Dict:
        data = super()._get_event_data()
        data.update({
            'player_names': self.player_names
        })
        return data


@dataclass
class Room:
    """
    Domain entity representing a game room.
    
    This is the aggregate root for the game bounded context.
    Manages room state, players, and game lifecycle.
    """
    room_id: str
    host_name: str
    max_slots: int = 4
    host_id: Optional[str] = None
    
    # Room state
    slots: List[Optional[Player]] = field(default_factory=lambda: [None, None, None, None])
    status: RoomStatus = RoomStatus.WAITING
    game: Optional[Game] = None
    
    # Events
    _events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        """Initialize room with host and bots."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[ROOM_DEBUG] Creating room {self.room_id} with {self.max_slots} slots")
        
        if len(self.slots) != self.max_slots:
            self.slots = [None] * self.max_slots
        
        # Set host_id if not already set (host is always in slot 0)
        if self.host_id is None:
            self.host_id = f"{self.room_id}_p0"
        
        # Emit room created event
        self._emit_event(RoomCreated(
            room_id=self.room_id,
            host_name=self.host_name,
            total_slots=self.max_slots,
            metadata=EventMetadata()
        ))
        
        # Add host to first slot
        logger.info(f"[ROOM_DEBUG] Adding host {self.host_name} to slot 0")
        self.add_player(self.host_name, is_bot=False, slot=0)
        
        # Fill remaining slots with bots
        for i in range(1, self.max_slots):
            bot_name = f"Bot {i+1}"
            logger.info(f"[ROOM_DEBUG] Adding {bot_name} to slot {i}")
            self.add_player(bot_name, is_bot=True, slot=i)
        
        logger.info(f"[ROOM_DEBUG] Room initialization complete. Slots: {[p.name if p else 'empty' for p in self.slots]}")
    
    @property
    def events(self) -> List[DomainEvent]:
        """Get domain events that have occurred."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear the event list."""
        self._events.clear()
    
    def _emit_event(self, event: DomainEvent) -> None:
        """Emit a domain event."""
        self._events.append(event)
    
    def add_player(self, name: str, is_bot: bool = False, slot: Optional[int] = None) -> int:
        """
        Add a player to the room.
        
        Args:
            name: Player name
            is_bot: Whether player is a bot
            slot: Specific slot to assign (optional)
            
        Returns:
            Slot index where player was added
            
        Raises:
            ValueError: If room is full or slot is invalid
        """
        # If slot specified, validate and use it
        if slot is not None:
            if slot < 0 or slot >= self.max_slots:
                raise ValueError(f"Invalid slot {slot}")
            if self.slots[slot] is not None and not self.slots[slot].is_bot:
                raise ValueError(f"Slot {slot} occupied by human player")
            
            import logging
            logger = logging.getLogger(__name__)
            
            self.slots[slot] = Player(name=name, is_bot=is_bot)
            logger.info(f"[ROOM_DEBUG] Added player {name} (bot={is_bot}) to slot {slot} in room {self.room_id}")
            
            self._emit_event(PlayerJoinedRoom(
                room_id=self.room_id,
                player_name=name,
                slot_index=slot,
                is_bot=is_bot,
                metadata=EventMetadata()
            ))
            self._update_room_status()
            return slot
        
        # Find first available slot (empty or bot)
        for i, player in enumerate(self.slots):
            if player is None:
                self.slots[i] = Player(name=name, is_bot=is_bot)
                self._emit_event(PlayerJoinedRoom(
                    room_id=self.room_id,
                    player_name=name,
                    slot_index=i,
                    is_bot=is_bot,
                    metadata=EventMetadata()
                ))
                self._update_room_status()
                return i
        
        # Replace first bot if no empty slots
        if not is_bot:
            for i, player in enumerate(self.slots):
                if player and player.is_bot:
                    self.slots[i] = Player(name=name, is_bot=is_bot)
                    self._emit_event(PlayerJoinedRoom(
                        room_id=self.room_id,
                        player_name=name,
                        slot_index=i,
                        is_bot=is_bot,
                        metadata=EventMetadata()
                    ))
                    self._update_room_status()
                    return i
        
        raise ValueError("No available slots")
    
    def remove_player(self, name: str) -> bool:
        """
        Remove a player from the room.
        
        Args:
            name: Player name to remove
            
        Returns:
            True if player was host, False otherwise
        """
        for i, player in enumerate(self.slots):
            if player and player.name == name:
                was_host = (name == self.host_name)
                self.slots[i] = None
                
                self._emit_event(PlayerLeftRoom(
                    room_id=self.room_id,
                    player_name=name,
                    slot_index=i,
                    was_host=was_host,
                    metadata=EventMetadata()
                ))
                
                # Handle host migration if needed
                if was_host:
                    self._migrate_host()
                
                self._update_room_status()
                return was_host
        
        return False
    
    def _migrate_host(self) -> None:
        """Migrate host to another player."""
        old_host = self.host_name
        
        # Prefer human players
        for player in self.slots:
            if player and not player.is_bot:
                self.host_name = player.name
                self._emit_event(HostMigrated(
                    room_id=self.room_id,
                    old_host=old_host,
                    new_host=self.host_name,
                    metadata=EventMetadata()
                ))
                return
        
        # Fall back to first bot
        for player in self.slots:
            if player:
                self.host_name = player.name
                self._emit_event(HostMigrated(
                    room_id=self.room_id,
                    old_host=old_host,
                    new_host=self.host_name,
                    metadata=EventMetadata()
                ))
                return
    
    def _update_room_status(self) -> None:
        """Update room status based on current state."""
        old_status = self.status
        
        # Check if abandoned (no humans)
        human_count = sum(1 for p in self.slots if p and not p.is_bot)
        if human_count == 0:
            self.status = RoomStatus.ABANDONED
        
        # Check if ready (all slots filled)
        elif all(p is not None for p in self.slots) and self.status in [RoomStatus.WAITING, RoomStatus.READY]:
            self.status = RoomStatus.READY
        
        # Check if waiting (has empty slots)
        elif any(p is None for p in self.slots) and self.status in [RoomStatus.READY, RoomStatus.WAITING]:
            self.status = RoomStatus.WAITING
        
        # Emit event if status changed
        if old_status != self.status:
            self._emit_event(RoomStatusChanged(
                room_id=self.room_id,
                old_status=old_status.value,
                new_status=self.status.value,
                metadata=EventMetadata()
            ))
    
    def start_game(self) -> Game:
        """
        Start a game in the room.
        
        Returns:
            The created Game instance
            
        Raises:
            ValueError: If game cannot be started
        """
        if self.status == RoomStatus.IN_GAME:
            raise ValueError("Game already in progress")
        
        if any(p is None for p in self.slots):
            raise ValueError("Cannot start with empty slots")
        
        # Create game with current players
        players = [p for p in self.slots if p is not None]
        self.game = Game(room_id=self.room_id, players=players)
        
        self.status = RoomStatus.IN_GAME
        
        self._emit_event(GameStartedInRoom(
            room_id=self.room_id,
            player_names=[p.name for p in players],
            metadata=EventMetadata()
        ))
        
        self._emit_event(RoomStatusChanged(
            room_id=self.room_id,
            old_status=RoomStatus.READY.value,
            new_status=RoomStatus.IN_GAME.value,
            metadata=EventMetadata()
        ))
        
        return self.game
    
    def end_game(self) -> None:
        """Mark game as completed."""
        if self.status != RoomStatus.IN_GAME:
            raise ValueError("No game in progress")
        
        self.status = RoomStatus.COMPLETED
        
        self._emit_event(RoomStatusChanged(
            room_id=self.room_id,
            old_status=RoomStatus.IN_GAME.value,
            new_status=RoomStatus.COMPLETED.value,
            metadata=EventMetadata()
        ))
    
    def get_player(self, name: str) -> Optional[Player]:
        """Get player by name."""
        for player in self.slots:
            if player and player.name == name:
                return player
        return None
    
    def get_slot_index(self, name: str) -> Optional[int]:
        """Get slot index for player."""
        for i, player in enumerate(self.slots):
            if player and player.name == name:
                return i
        return None
    
    def is_full(self) -> bool:
        """Check if all slots are occupied."""
        return all(p is not None for p in self.slots)
    
    def is_host(self, name: str) -> bool:
        """Check if player is host."""
        return self.host_name == name
    
    def is_game_started(self) -> bool:
        """Check if a game is currently in progress."""
        return self.status == RoomStatus.IN_GAME and self.game is not None
    
    def migrate_host(self) -> Optional[Player]:
        """Migrate host to another player and return the new host."""
        old_host = self.host_name
        
        # Prefer human players
        for player in self.slots:
            if player and not player.is_bot and player.name != old_host:
                self.host_name = player.name
                self._emit_event(HostMigrated(
                    room_id=self.room_id,
                    old_host=old_host,
                    new_host=self.host_name,
                    metadata=EventMetadata()
                ))
                return player
        
        # Fall back to first bot
        for player in self.slots:
            if player and player.name != old_host:
                self.host_name = player.name
                self._emit_event(HostMigrated(
                    room_id=self.room_id,
                    old_host=old_host,
                    new_host=self.host_name,
                    metadata=EventMetadata()
                ))
                return player
        
        return None
    
    def get_human_count(self) -> int:
        """Count human players in room."""
        return sum(1 for p in self.slots if p and not p.is_bot)
    
    def get_bot_count(self) -> int:
        """Count bot players in room."""
        return sum(1 for p in self.slots if p and p.is_bot)
    
    def to_dict(self) -> dict:
        """Convert room to dictionary for serialization."""
        return {
            "room_id": self.room_id,
            "host_name": self.host_name,
            "status": self.status.value,
            "slots": [
                {
                    "index": i,
                    "player": p.to_dict() if p else None
                }
                for i, p in enumerate(self.slots)
            ],
            "human_count": self.get_human_count(),
            "bot_count": self.get_bot_count(),
            "game_active": self.game is not None
        }