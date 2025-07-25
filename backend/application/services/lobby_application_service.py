"""
Lobby application service.

This service provides high-level orchestration of lobby operations
including room discovery, matchmaking, and lobby analytics.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from application.base import ApplicationService
from application.interfaces import UnitOfWork, MetricsCollector
from application.use_cases.lobby import GetRoomListUseCase, GetRoomDetailsUseCase
from application.dto.lobby import GetRoomListRequest, GetRoomDetailsRequest
from application.exceptions import ApplicationException

logger = logging.getLogger(__name__)


class LobbyApplicationService(ApplicationService):
    """
    High-level service for lobby operations.
    
    This service:
    1. Provides enhanced room discovery
    2. Implements matchmaking algorithms
    3. Generates lobby statistics
    4. Manages room recommendations
    5. Tracks lobby activity patterns
    """
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        metrics: Optional[MetricsCollector] = None
    ):
        """
        Initialize the service.
        
        Args:
            unit_of_work: Unit of work for transactions
            metrics: Optional metrics collector
        """
        super().__init__()
        self._uow = unit_of_work
        self._metrics = metrics
        
        # Initialize use cases
        self._get_room_list_use_case = GetRoomListUseCase(unit_of_work, metrics)
        self._get_room_details_use_case = GetRoomDetailsUseCase(unit_of_work, metrics)
    
    async def get_recommended_rooms(
        self,
        player_id: str,
        preferences: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get personalized room recommendations.
        
        Args:
            player_id: Player requesting recommendations
            preferences: Player preferences
            limit: Maximum recommendations
            
        Returns:
            List of recommended rooms with match scores
        """
        preferences = preferences or {}
        
        # Get player stats for matching
        player_stats = None
        try:
            player_stats = await self._uow.player_stats.get_stats(player_id)
        except Exception:
            pass
        
        # Get available rooms
        list_request = GetRoomListRequest(
            player_id=player_id,
            include_full=False,
            include_in_game=False,
            page_size=50
        )
        list_response = await self._get_room_list_use_case.execute(list_request)
        
        if not list_response.rooms:
            return []
        
        # Score each room
        scored_rooms = []
        for room_summary in list_response.rooms:
            score = await self._calculate_room_match_score(
                room_summary,
                player_stats,
                preferences
            )
            
            details_request = GetRoomDetailsRequest(
                room_id=room_summary.room_id,
                requesting_player_id=player_id,
                include_player_stats=True
            )
            
            try:
                details_response = await self._get_room_details_use_case.execute(details_request)
                
                scored_rooms.append({
                    "room": room_summary,
                    "details": details_response.room_details,
                    "match_score": score,
                    "match_reasons": self._get_match_reasons(score, preferences)
                })
            except Exception as e:
                self._logger.warning(f"Failed to get room details: {e}")
        
        # Sort by score and return top matches
        scored_rooms.sort(key=lambda x: x["match_score"], reverse=True)
        
        return scored_rooms[:limit]
    
    async def get_lobby_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive lobby statistics.
        
        Returns:
            Lobby statistics and trends
        """
        async with self._uow:
            all_rooms = await self._uow.rooms.list_active(limit=1000)
            
            # Calculate statistics
            total_rooms = len(all_rooms)
            rooms_waiting = sum(1 for r in all_rooms if not r.current_game)
            rooms_in_game = total_rooms - rooms_waiting
            
            total_players = sum(r.player_count for r in all_rooms)
            human_players = sum(
                sum(1 for slot in r.slots if slot and not slot.is_bot)
                for r in all_rooms
            )
            bot_players = total_players - human_players
            
            # Room size distribution
            size_distribution = {}
            for room in all_rooms:
                size = room.settings.max_players
                size_distribution[size] = size_distribution.get(size, 0) + 1
            
            # Activity patterns
            now = datetime.utcnow()
            recent_rooms = [
                r for r in all_rooms
                if (now - r.created_at).total_seconds() < 3600  # Last hour
            ]
            
            stats = {
                "total_rooms": total_rooms,
                "rooms_waiting": rooms_waiting,
                "rooms_in_game": rooms_in_game,
                "total_players": total_players,
                "human_players": human_players,
                "bot_players": bot_players,
                "average_players_per_room": round(total_players / total_rooms, 2) if total_rooms > 0 else 0,
                "room_size_distribution": size_distribution,
                "rooms_created_last_hour": len(recent_rooms),
                "popular_settings": self._analyze_popular_settings(all_rooms),
                "peak_times": self._analyze_peak_times(all_rooms)
            }
            
            if self._metrics:
                self._metrics.gauge("lobby.total_rooms", total_rooms)
                self._metrics.gauge("lobby.total_players", total_players)
                self._metrics.gauge("lobby.human_players", human_players)
            
            return stats
    
    async def find_similar_players(
        self,
        player_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find players with similar skill levels and play patterns.
        
        Args:
            player_id: Reference player
            limit: Maximum similar players
            
        Returns:
            List of similar players with match details
        """
        # Get reference player stats
        try:
            player_stats = await self._uow.player_stats.get_stats(player_id)
        except Exception:
            return []
        
        # Get leaderboard for comparison
        leaderboard = await self._uow.player_stats.get_leaderboard(limit=100)
        
        similar_players = []
        player_score = player_stats.get("average_score", 0)
        player_games = player_stats.get("total_games", 0)
        
        for other_stats in leaderboard:
            if other_stats.get("player_id") == player_id:
                continue
            
            # Calculate similarity score
            score_diff = abs(other_stats.get("average_score", 0) - player_score)
            games_diff = abs(other_stats.get("total_games", 0) - player_games)
            
            similarity = 100 - (score_diff * 0.5 + games_diff * 0.1)
            similarity = max(0, min(100, similarity))
            
            if similarity > 70:  # Threshold for similarity
                similar_players.append({
                    "player_id": other_stats.get("player_id"),
                    "player_name": other_stats.get("player_name", "Unknown"),
                    "similarity_score": round(similarity, 2),
                    "stats": {
                        "average_score": other_stats.get("average_score", 0),
                        "win_rate": other_stats.get("win_rate", 0),
                        "total_games": other_stats.get("total_games", 0)
                    }
                })
        
        similar_players.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_players[:limit]
    
    async def get_trending_rooms(
        self,
        time_window_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get trending/popular rooms based on recent activity.
        
        Args:
            time_window_minutes: Time window for trending calculation
            
        Returns:
            List of trending rooms
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        async with self._uow:
            all_rooms = await self._uow.rooms.list_active(limit=100)
            
            trending_rooms = []
            for room in all_rooms:
                # Skip full or in-game rooms
                if room.is_full() or room.current_game:
                    continue
                
                # Calculate activity score
                activity_score = 0
                
                # Recent creation bonus
                if room.created_at > cutoff_time:
                    age_minutes = (datetime.utcnow() - room.created_at).total_seconds() / 60
                    activity_score += (30 - age_minutes) * 2
                
                # Player count bonus
                activity_score += room.player_count * 10
                
                # Human player bonus
                human_count = sum(
                    1 for slot in room.slots
                    if slot and not slot.is_bot
                )
                activity_score += human_count * 5
                
                if activity_score > 20:  # Threshold for trending
                    trending_rooms.append({
                        "room_id": room.id,
                        "room_code": room.code,
                        "room_name": room.name,
                        "player_count": room.player_count,
                        "max_players": room.settings.max_players,
                        "activity_score": round(activity_score, 2),
                        "created_minutes_ago": round(
                            (datetime.utcnow() - room.created_at).total_seconds() / 60,
                            1
                        )
                    })
            
            trending_rooms.sort(key=lambda x: x["activity_score"], reverse=True)
            return trending_rooms[:10]
    
    async def _calculate_room_match_score(
        self,
        room_summary,
        player_stats: Optional[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> float:
        """Calculate how well a room matches player preferences."""
        score = 50.0  # Base score
        
        # Player count preference
        if "preferred_players" in preferences:
            diff = abs(room_summary.player_count - preferences["preferred_players"])
            score -= diff * 5
        
        # Room size preference
        if "preferred_room_size" in preferences:
            if room_summary.max_players == preferences["preferred_room_size"]:
                score += 20
        
        # Avoid empty rooms
        if room_summary.player_count == 1:
            score -= 10
        
        # Prefer rooms close to starting
        if room_summary.player_count >= room_summary.max_players - 1:
            score += 15
        
        # New room penalty (might be abandoned)
        if hasattr(room_summary, 'created_at'):
            age_minutes = (datetime.utcnow() - room_summary.created_at).total_seconds() / 60
            if age_minutes < 2:
                score -= 5
        
        return max(0, min(100, score))
    
    def _get_match_reasons(
        self,
        score: float,
        preferences: Dict[str, Any]
    ) -> List[str]:
        """Get human-readable match reasons."""
        reasons = []
        
        if score >= 80:
            reasons.append("Excellent match for your preferences")
        elif score >= 60:
            reasons.append("Good match for your preferences")
        
        if preferences.get("preferred_players"):
            reasons.append(f"Close to preferred player count")
        
        return reasons
    
    def _analyze_popular_settings(
        self,
        rooms: List[Any]
    ) -> Dict[str, Any]:
        """Analyze popular room settings."""
        win_conditions = {}
        max_players_dist = {}
        
        for room in rooms:
            # Win condition popularity
            wc_key = f"{room.settings.win_condition_type}_{room.settings.win_condition_value}"
            win_conditions[wc_key] = win_conditions.get(wc_key, 0) + 1
            
            # Max players distribution
            mp = room.settings.max_players
            max_players_dist[mp] = max_players_dist.get(mp, 0) + 1
        
        return {
            "popular_win_conditions": sorted(
                win_conditions.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3],
            "popular_room_sizes": sorted(
                max_players_dist.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        }
    
    def _analyze_peak_times(
        self,
        rooms: List[Any]
    ) -> Dict[str, int]:
        """Analyze peak activity times."""
        hourly_activity = {}
        
        for room in rooms:
            hour = room.created_at.hour
            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
        
        return hourly_activity