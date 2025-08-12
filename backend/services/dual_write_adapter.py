# backend/services/dual_write_adapter.py

import logging
import os
import sqlite3
from typing import Dict, Any, Optional, List

from backend.api.services.event_store import EventStore, event_store
from .event_store_v2 import EventStoreV2

logger = logging.getLogger(__name__)


class DualWriteAdapter:
    """
    Adapter that writes to both old and new schemas during migration.
    
    Phase 3 of database optimization - Ensures data consistency during
    the transition to the optimized schema.
    """
    
    def __init__(self):
        """Initialize adapter with both event stores."""
        self.v1_store = event_store  # Original EventStore
        
        # Use same database path as v1 store
        self.v2_store = EventStoreV2(self.v1_store.db_path)  # New optimized store
        
        # Configuration flags
        self.dual_write_enabled = os.getenv("DB_DUAL_WRITE_MODE", "false").lower() == "true"
        self.v2_primary = os.getenv("DB_V2_PRIMARY", "false").lower() == "true"
        
        logger.info(
            f"DualWriteAdapter initialized - dual_write: {self.dual_write_enabled}, "
            f"v2_primary: {self.v2_primary}"
        )
    
    async def store_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None
    ) -> None:
        """
        Store event in appropriate schema(s).
        
        Args:
            room_id: Room identifier
            event_type: Event type
            payload: Event data
            player_id: Optional player identifier
        """
        # Always write to v1 for now (maintains compatibility)
        await self.v1_store.store_event_buffered(room_id, event_type, payload, player_id)
        
        # Optionally write to v2 if dual-write enabled
        if self.dual_write_enabled:
            try:
                await self._write_to_v2(room_id, event_type, payload, player_id)
            except Exception as e:
                # Log but don't fail - v1 is still primary
                logger.error(f"Failed to write to v2 schema: {e}")
    
    async def _write_to_v2(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None
    ) -> None:
        """
        Write event to v2 schema with appropriate transformations.
        
        Args:
            room_id: Room identifier
            event_type: Event type
            payload: Event data
            player_id: Optional player identifier
        """
        # Handle different event types
        if event_type == "game_started":
            players = payload.get("players", [])
            await self.v2_store.store_game_started(room_id, players)
            
        elif event_type in ["game_completed", "game_over"]:
            final_scores = payload.get("final_scores", {})
            winner = payload.get("winner", "")
            await self.v2_store.store_game_completed(room_id, final_scores, winner)
            
        elif event_type == "round_completed":
            # Extract round snapshot data
            round_data = await self._extract_round_snapshot(room_id, payload)
            if round_data:
                round_number = round_data.get("round_number", 1)
                await self.v2_store.store_round_snapshot(room_id, round_number, round_data)
    
    async def _extract_round_snapshot(
        self,
        room_id: str,
        round_complete_payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract round snapshot data from events.
        
        This reads recent events from v1 store to build complete round snapshot.
        
        Args:
            room_id: Room identifier
            round_complete_payload: Round completion event payload
            
        Returns:
            Complete round snapshot data
        """
        try:
            # Get recent events for this room
            events = await self.v1_store.get_room_events(room_id, limit=200)
            
            # Find round boundaries
            round_number = round_complete_payload.get("round_number", 1)
            
            # Extract data for the round
            round_data = {
                "round_number": round_number,
                "starter_player": "",
                "starter_reason": "default",
                "initial_hands": {},
                "declarations": {},
                "turn_sequence": [],
                "round_scores": round_complete_payload.get("scores", {}),
                "cumulative_scores": round_complete_payload.get("total_scores", {})
            }
            
            # Process events to build round snapshot
            current_turn = None
            for event in reversed(events):  # Process in chronological order
                if event.event_type == "hands_dealt":
                    round_data["initial_hands"] = event.payload.get("hands", {})
                    round_data["starter_player"] = event.payload.get("starter", "")
                    round_data["starter_reason"] = event.payload.get("starter_reason", "default")
                    
                elif event.event_type == "declarations_completed":
                    round_data["declarations"] = event.payload.get("declarations", {})
                    
                elif event.event_type == "turn_completed":
                    turn_data = {
                        "turn_number": event.payload.get("turn_number", 0),
                        "starter": event.payload.get("starter", ""),
                        "plays": event.payload.get("plays", {}),
                        "winner": event.payload.get("winner", ""),
                        "piles_won": event.payload.get("piles_won", 0)
                    }
                    round_data["turn_sequence"].append(turn_data)
            
            return round_data
            
        except Exception as e:
            logger.error(f"Failed to extract round snapshot: {e}")
            return None
    
    async def get_play_history(
        self,
        room_id: str,
        round_numbers: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get play history from appropriate schema.
        
        Args:
            room_id: Room identifier
            round_numbers: Optional specific rounds to retrieve
            
        Returns:
            Play history data
        """
        if self.v2_primary and self.dual_write_enabled:
            # Try v2 first
            try:
                summary = await self.v2_store.get_game_summary(room_id)
                if summary:
                    rounds = await self.v2_store.get_round_snapshots(room_id, round_numbers)
                    return {
                        "room_id": room_id,
                        "summary": summary,
                        "rounds": rounds,
                        "source": "v2"
                    }
            except Exception as e:
                logger.error(f"Failed to read from v2: {e}")
        
        # Fall back to v1 (using existing Play History service)
        from backend.services.event_store_play_history_service import EventStorePlayHistoryService
        
        service = EventStorePlayHistoryService()
        history = await service.build_play_history_from_events(room_id)
        
        return {
            "room_id": room_id,
            "summary": None,  # v1 doesn't have summary
            "rounds": history.rounds,
            "source": "v1"
        }
    
    async def migrate_historical_data(
        self,
        batch_size: int = 100,
        max_rooms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Migrate historical data from v1 to v2 schema.
        
        Args:
            batch_size: Number of rooms to process at once
            max_rooms: Maximum rooms to migrate (None for all)
            
        Returns:
            Migration statistics
        """
        stats = {
            "rooms_processed": 0,
            "rounds_migrated": 0,
            "errors": 0
        }
        
        # Get list of all rooms from v1
        conn = sqlite3.connect(self.v1_store.db_path)
        try:
            cursor = conn.execute("""
                SELECT DISTINCT room_id 
                FROM game_events 
                ORDER BY MIN(created_at)
            """)
            
            all_rooms = [row[0] for row in cursor.fetchall()]
            
            if max_rooms:
                all_rooms = all_rooms[:max_rooms]
            
            logger.info(f"Starting migration of {len(all_rooms)} rooms")
            
            # Process in batches
            for i in range(0, len(all_rooms), batch_size):
                batch = all_rooms[i:i + batch_size]
                
                for room_id in batch:
                    try:
                        await self._migrate_room(room_id)
                        stats["rooms_processed"] += 1
                    except Exception as e:
                        logger.error(f"Failed to migrate room {room_id}: {e}")
                        stats["errors"] += 1
                
                logger.info(f"Migrated {stats['rooms_processed']} rooms so far...")
            
        finally:
            conn.close()
        
        logger.info(f"Migration complete: {stats}")
        return stats
    
    async def _migrate_room(self, room_id: str) -> None:
        """
        Migrate a single room's data to v2 schema.
        
        Args:
            room_id: Room to migrate
        """
        # Get all events for the room
        events = await self.v1_store.get_room_events(room_id)
        
        if not events:
            return
        
        # Process events to build v2 data
        game_started = False
        round_data = None
        current_round = 0
        
        for event in events:
            if event.event_type == "game_started":
                if not game_started:
                    players = event.payload.get("players", [])
                    await self.v2_store.store_game_started(room_id, players)
                    game_started = True
                    
            elif event.event_type == "hands_dealt":
                # Start new round
                if round_data and current_round > 0:
                    # Save previous round
                    await self.v2_store.store_round_snapshot(room_id, current_round, round_data)
                
                current_round = event.payload.get("round_number", current_round + 1)
                round_data = {
                    "round_number": current_round,
                    "starter_player": event.payload.get("starter", ""),
                    "starter_reason": event.payload.get("starter_reason", "default"),
                    "initial_hands": event.payload.get("hands", {}),
                    "declarations": {},
                    "turn_sequence": [],
                    "round_scores": {},
                    "cumulative_scores": {}
                }
                
            elif event.event_type == "declarations_completed" and round_data:
                round_data["declarations"] = event.payload.get("declarations", {})
                
            elif event.event_type == "turn_completed" and round_data:
                turn_data = {
                    "turn_number": event.payload.get("turn_number", 0),
                    "starter": event.payload.get("starter", ""),
                    "plays": event.payload.get("plays", {}),
                    "winner": event.payload.get("winner", ""),
                    "piles_won": event.payload.get("piles_won", 0)
                }
                round_data["turn_sequence"].append(turn_data)
                
            elif event.event_type == "round_completed" and round_data:
                round_data["round_scores"] = event.payload.get("scores", {})
                round_data["cumulative_scores"] = event.payload.get("total_scores", {})
                await self.v2_store.store_round_snapshot(room_id, current_round, round_data)
                round_data = None
                
            elif event.event_type in ["game_completed", "game_over"]:
                final_scores = event.payload.get("final_scores", {})
                winner = event.payload.get("winner", "")
                await self.v2_store.store_game_completed(room_id, final_scores, winner)