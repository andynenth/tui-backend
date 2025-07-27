"""
Archive strategy for hybrid persistence.

Defines policies and strategies for archiving completed games.
"""

from typing import Dict, List, Optional, Any, Protocol, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class ArchivalTrigger(Enum):
    """Triggers for archival."""
    GAME_COMPLETED = "game_completed"
    TIME_BASED = "time_based"
    MEMORY_PRESSURE = "memory_pressure"
    MANUAL = "manual"
    SHUTDOWN = "shutdown"


class ArchivalPriority(Enum):
    """Priority levels for archival."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ArchivalPolicy:
    """Policy for archiving entities."""
    name: str
    entity_type: str
    
    # Triggers
    triggers: Set[ArchivalTrigger] = field(default_factory=set)
    
    # Time-based settings
    archive_after: Optional[timedelta] = None
    check_interval: timedelta = timedelta(minutes=5)
    
    # Memory-based settings
    memory_threshold_percent: float = 80.0
    max_entities_in_memory: Optional[int] = None
    
    # Retention settings
    retention_period: Optional[timedelta] = None
    compress_after: Optional[timedelta] = timedelta(days=1)
    
    # Performance settings
    batch_size: int = 100
    max_concurrent_archives: int = 5
    archive_timeout: timedelta = timedelta(seconds=30)
    
    def should_archive(self, entity: Any, current_time: datetime) -> bool:
        """Check if entity should be archived based on policy."""
        # Check if entity has required attributes
        if not hasattr(entity, 'created_at'):
            return False
        
        # Time-based check
        if self.archive_after and ArchivalTrigger.TIME_BASED in self.triggers:
            age = current_time - entity.created_at
            if age >= self.archive_after:
                return True
        
        # Game completion check
        if ArchivalTrigger.GAME_COMPLETED in self.triggers:
            if hasattr(entity, 'status') and entity.status == 'completed':
                return True
        
        return False
    
    def should_compress(self, archived_at: datetime, current_time: datetime) -> bool:
        """Check if archived entity should be compressed."""
        if not self.compress_after:
            return False
        
        age = current_time - archived_at
        return age >= self.compress_after
    
    def should_delete(self, archived_at: datetime, current_time: datetime) -> bool:
        """Check if archived entity should be deleted."""
        if not self.retention_period:
            return False
        
        age = current_time - archived_at
        return age >= self.retention_period


@dataclass
class ArchivalRequest:
    """Request to archive an entity."""
    entity_id: str
    entity_type: str
    entity: Any
    trigger: ArchivalTrigger
    priority: ArchivalPriority = ArchivalPriority.NORMAL
    requested_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchivalResult:
    """Result of an archival operation."""
    entity_id: str
    entity_type: str
    success: bool
    archived_at: datetime = field(default_factory=datetime.utcnow)
    archive_location: Optional[str] = None
    size_bytes: Optional[int] = None
    compressed: bool = False
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class IArchivalBackend(Protocol):
    """Protocol for archival backends."""
    
    async def archive(self, entity_id: str, entity_type: str, data: bytes) -> str:
        """Archive entity data and return location."""
        ...
    
    async def retrieve(self, archive_location: str) -> bytes:
        """Retrieve archived data."""
        ...
    
    async def delete(self, archive_location: str) -> bool:
        """Delete archived data."""
        ...
    
    async def list_archives(self, entity_type: str, 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[str]:
        """List archived entities."""
        ...


class ArchivalStrategy(ABC):
    """Abstract base class for archival strategies."""
    
    def __init__(self, backend: IArchivalBackend):
        """Initialize archival strategy."""
        self.backend = backend
        self._metrics = {
            'total_archived': 0,
            'total_retrieved': 0,
            'total_deleted': 0,
            'failed_archives': 0,
            'compression_ratio': 0.0
        }
    
    @abstractmethod
    async def should_archive(self, entity_id: str, entity: Any, 
                           policy: ArchivalPolicy) -> bool:
        """Determine if entity should be archived."""
        pass
    
    @abstractmethod
    async def prepare_for_archive(self, entity: Any) -> bytes:
        """Prepare entity data for archival."""
        pass
    
    @abstractmethod
    async def restore_from_archive(self, data: bytes) -> Any:
        """Restore entity from archived data."""
        pass
    
    async def archive_entity(self, request: ArchivalRequest, 
                           policy: ArchivalPolicy) -> ArchivalResult:
        """Archive an entity using the strategy."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Check if should archive
            if not await self.should_archive(request.entity_id, request.entity, policy):
                return ArchivalResult(
                    entity_id=request.entity_id,
                    entity_type=request.entity_type,
                    success=False,
                    error="Entity does not meet archival criteria"
                )
            
            # Prepare data
            data = await self.prepare_for_archive(request.entity)
            original_size = len(data)
            
            # Compress if needed
            compressed = False
            if policy.compress_after and policy.compress_after.total_seconds() == 0:
                data = await self._compress_data(data)
                compressed = True
                self._update_compression_ratio(original_size, len(data))
            
            # Archive to backend
            location = await self.backend.archive(
                request.entity_id,
                request.entity_type,
                data
            )
            
            # Update metrics
            self._metrics['total_archived'] += 1
            
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return ArchivalResult(
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                success=True,
                archive_location=location,
                size_bytes=len(data),
                compressed=compressed,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to archive entity {request.entity_id}: {e}")
            self._metrics['failed_archives'] += 1
            
            return ArchivalResult(
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                success=False,
                error=str(e)
            )
    
    async def retrieve_entity(self, entity_id: str, archive_location: str) -> Any:
        """Retrieve an entity from archive."""
        try:
            # Retrieve from backend
            data = await self.backend.retrieve(archive_location)
            
            # Decompress if needed
            if self._is_compressed(data):
                data = await self._decompress_data(data)
            
            # Restore entity
            entity = await self.restore_from_archive(data)
            
            # Update metrics
            self._metrics['total_retrieved'] += 1
            
            return entity
            
        except Exception as e:
            logger.error(f"Failed to retrieve entity {entity_id}: {e}")
            raise
    
    async def _compress_data(self, data: bytes) -> bytes:
        """Compress data for storage."""
        import gzip
        return gzip.compress(data, compresslevel=6)
    
    async def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data from storage."""
        import gzip
        return gzip.decompress(data)
    
    def _is_compressed(self, data: bytes) -> bool:
        """Check if data is compressed (gzip magic number)."""
        return len(data) >= 2 and data[0:2] == b'\x1f\x8b'
    
    def _update_compression_ratio(self, original_size: int, compressed_size: int):
        """Update compression ratio metric."""
        if original_size > 0:
            ratio = 1 - (compressed_size / original_size)
            # Running average
            current = self._metrics['compression_ratio']
            count = self._metrics['total_archived']
            self._metrics['compression_ratio'] = (current * count + ratio) / (count + 1)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get archival metrics."""
        return self._metrics.copy()


class GameArchivalStrategy(ArchivalStrategy):
    """Archival strategy specifically for game entities."""
    
    async def should_archive(self, entity_id: str, entity: Any, 
                           policy: ArchivalPolicy) -> bool:
        """Determine if game should be archived."""
        # Games should be archived when completed
        if hasattr(entity, 'status') and entity.status == 'completed':
            return True
        
        # Also check time-based policy
        if hasattr(entity, 'last_activity'):
            inactive_time = datetime.utcnow() - entity.last_activity
            if policy.archive_after and inactive_time >= policy.archive_after:
                return True
        
        return False
    
    async def prepare_for_archive(self, entity: Any) -> bytes:
        """Prepare game data for archival."""
        import json
        
        # Convert game to archival format
        archive_data = {
            'id': entity.id,
            'room_id': entity.room_id,
            'players': [self._serialize_player(p) for p in entity.players],
            'rounds': [self._serialize_round(r) for r in entity.rounds],
            'current_scores': entity.current_scores,
            'winner': entity.winner,
            'status': entity.status,
            'created_at': entity.created_at.isoformat(),
            'completed_at': getattr(entity, 'completed_at', datetime.utcnow()).isoformat(),
            'metadata': {
                'version': '1.0',
                'archived_at': datetime.utcnow().isoformat(),
                'game_duration_seconds': (
                    getattr(entity, 'completed_at', datetime.utcnow()) - entity.created_at
                ).total_seconds()
            }
        }
        
        # Convert to JSON bytes
        return json.dumps(archive_data, separators=(',', ':')).encode('utf-8')
    
    async def restore_from_archive(self, data: bytes) -> Any:
        """Restore game from archived data."""
        import json
        from domain.entities import Game, Player, Round
        
        # Parse JSON data
        archive_data = json.loads(data.decode('utf-8'))
        
        # Reconstruct game entity
        game = Game(
            id=archive_data['id'],
            room_id=archive_data['room_id']
        )
        
        # Restore players
        for player_data in archive_data['players']:
            player = Player(
                id=player_data['id'],
                name=player_data['name'],
                is_bot=player_data['is_bot']
            )
            game.players.append(player)
        
        # Restore rounds
        for round_data in archive_data['rounds']:
            round_obj = Round(number=round_data['number'])
            # Restore round details...
            game.rounds.append(round_obj)
        
        # Restore other attributes
        game.current_scores = archive_data['current_scores']
        game.winner = archive_data['winner']
        game.status = archive_data['status']
        game.created_at = datetime.fromisoformat(archive_data['created_at'])
        
        return game
    
    def _serialize_player(self, player) -> Dict[str, Any]:
        """Serialize player for archival."""
        return {
            'id': player.id,
            'name': player.name,
            'is_bot': player.is_bot,
            'total_score': getattr(player, 'total_score', 0)
        }
    
    def _serialize_round(self, round_obj) -> Dict[str, Any]:
        """Serialize round for archival."""
        return {
            'number': round_obj.number,
            'status': getattr(round_obj, 'status', 'completed'),
            'scores': getattr(round_obj, 'scores', {}),
            'winner_id': getattr(round_obj, 'winner_id', None)
        }


# Default policies

DEFAULT_GAME_POLICY = ArchivalPolicy(
    name="default_game_policy",
    entity_type="game",
    triggers={ArchivalTrigger.GAME_COMPLETED, ArchivalTrigger.TIME_BASED},
    archive_after=timedelta(hours=1),  # Archive 1 hour after completion
    check_interval=timedelta(minutes=5),
    memory_threshold_percent=80.0,
    max_entities_in_memory=1000,
    retention_period=timedelta(days=90),  # Keep for 90 days
    compress_after=timedelta(hours=24),  # Compress after 24 hours
    batch_size=50,
    max_concurrent_archives=3
)

DEFAULT_ROOM_POLICY = ArchivalPolicy(
    name="default_room_policy",
    entity_type="room",
    triggers={ArchivalTrigger.TIME_BASED},
    archive_after=timedelta(hours=24),  # Archive inactive rooms after 24 hours
    check_interval=timedelta(hours=1),
    memory_threshold_percent=90.0,
    max_entities_in_memory=500,
    retention_period=timedelta(days=30),  # Keep for 30 days
    compress_after=timedelta(days=7),
    batch_size=100,
    max_concurrent_archives=5
)