"""
Connection application service.

This service provides high-level orchestration of connection-related operations
including health monitoring, reconnection handling, and connection analytics.
"""

import logging
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from collections import defaultdict

from application.base import ApplicationService
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.use_cases.connection import (
    HandlePingUseCase,
    MarkClientReadyUseCase,
    AcknowledgeMessageUseCase,
    SyncClientStateUseCase,
)
from application.dto.connection import (
    HandlePingRequest,
    MarkClientReadyRequest,
    SyncClientStateRequest,
)
from application.exceptions import ApplicationException

logger = logging.getLogger(__name__)


class ConnectionApplicationService(ApplicationService):
    """
    High-level service for connection management.

    This service:
    1. Monitors connection health
    2. Handles reconnection flows
    3. Manages client synchronization
    4. Tracks connection analytics
    5. Coordinates connection recovery
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        metrics: Optional[MetricsCollector] = None,
        health_check_interval_seconds: int = 30,
        disconnect_threshold_seconds: int = 60,
    ):
        """
        Initialize the service.

        Args:
            unit_of_work: Unit of work for transactions
            event_publisher: Event publishing service
            metrics: Optional metrics collector
            health_check_interval_seconds: Interval for health checks
            disconnect_threshold_seconds: Time before marking disconnected
        """
        super().__init__()
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._metrics = metrics
        self._health_check_interval = health_check_interval_seconds
        self._disconnect_threshold = disconnect_threshold_seconds

        # Initialize use cases
        self._handle_ping_use_case = HandlePingUseCase(unit_of_work, metrics)
        self._mark_ready_use_case = MarkClientReadyUseCase(
            unit_of_work, event_publisher, metrics
        )
        self._acknowledge_use_case = AcknowledgeMessageUseCase(metrics)
        self._sync_state_use_case = SyncClientStateUseCase(unit_of_work)

        # Connection tracking
        self._active_connections: Dict[str, datetime] = {}
        self._connection_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)

    async def handle_client_connect(
        self,
        player_id: str,
        room_id: Optional[str] = None,
        client_info: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle new client connection with full initialization.

        Args:
            player_id: Connecting player ID
            room_id: Room ID if rejoining
            client_info: Client capabilities and version
            user_id: User ID for tracking

        Returns:
            Connection initialization result
        """
        try:
            # Record connection
            self._active_connections[player_id] = datetime.utcnow()

            # Initialize connection metrics
            self._connection_metrics[player_id] = {
                "connected_at": datetime.utcnow(),
                "ping_count": 0,
                "average_latency": 0,
                "disconnections": 0,
                "client_info": client_info or {},
            }

            result = {
                "player_id": player_id,
                "connected": True,
                "timestamp": datetime.utcnow(),
            }

            # If rejoining a room, sync state and mark ready
            if room_id:
                # Sync current state
                sync_request = SyncClientStateRequest(
                    player_id=player_id, room_id=room_id, user_id=user_id
                )
                sync_response = await self._sync_state_use_case.execute(sync_request)

                result["sync_data"] = {
                    "room_state": sync_response.room_state,
                    "game_state": sync_response.game_state,
                    "player_hand": sync_response.player_hand,
                    "events_missed": sync_response.events_missed,
                }

                # Mark client ready
                ready_request = MarkClientReadyRequest(
                    player_id=player_id,
                    room_id=room_id,
                    client_version=client_info.get("version") if client_info else None,
                    client_capabilities=(
                        client_info.get("capabilities") if client_info else None
                    ),
                    user_id=user_id,
                )
                ready_response = await self._mark_ready_use_case.execute(ready_request)

                result["ready"] = ready_response.is_ready

            self._logger.info(
                f"Client connected: {player_id}",
                extra={
                    "player_id": player_id,
                    "room_id": room_id,
                    "client_version": (
                        client_info.get("version") if client_info else None
                    ),
                },
            )

            if self._metrics:
                self._metrics.increment(
                    "connection.established",
                    tags={
                        "has_room": str(room_id is not None).lower(),
                        "client_version": (
                            client_info.get("version", "unknown")
                            if client_info
                            else "unknown"
                        ),
                    },
                )

            return result

        except Exception as e:
            self._logger.error(f"Failed to handle client connect: {e}", exception=e)
            raise ApplicationException(
                f"Connection initialization failed: {str(e)}",
                code="CONNECTION_INIT_FAILED",
            )

    async def handle_client_disconnect(
        self, player_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle client disconnection.

        Args:
            player_id: Disconnecting player ID
            reason: Disconnection reason

        Returns:
            Disconnection handling result
        """
        # Remove from active connections
        if player_id in self._active_connections:
            del self._active_connections[player_id]

        # Update metrics
        if player_id in self._connection_metrics:
            metrics = self._connection_metrics[player_id]
            metrics["disconnected_at"] = datetime.utcnow()
            metrics["disconnections"] += 1

            # Calculate session duration
            if "connected_at" in metrics:
                duration = (datetime.utcnow() - metrics["connected_at"]).total_seconds()
                metrics["last_session_duration"] = duration

        if self._metrics:
            self._metrics.increment(
                "connection.disconnected", tags={"reason": reason or "unknown"}
            )

        self._logger.info(
            f"Client disconnected: {player_id}",
            extra={"player_id": player_id, "reason": reason},
        )

        return {
            "player_id": player_id,
            "disconnected": True,
            "reason": reason,
            "can_reconnect": True,
            "session_data_preserved": True,
        }

    async def monitor_connection_health(self) -> Dict[str, Any]:
        """
        Monitor health of all active connections.

        Returns:
            Connection health report
        """
        now = datetime.utcnow()
        threshold = now - timedelta(seconds=self._disconnect_threshold)
        warning_threshold = now - timedelta(seconds=self._health_check_interval)

        healthy = []
        warning = []
        unhealthy = []

        for player_id, last_activity in self._active_connections.items():
            if last_activity < threshold:
                unhealthy.append(
                    {
                        "player_id": player_id,
                        "last_activity": last_activity,
                        "seconds_inactive": (now - last_activity).total_seconds(),
                    }
                )
            elif last_activity < warning_threshold:
                warning.append(
                    {
                        "player_id": player_id,
                        "last_activity": last_activity,
                        "seconds_inactive": (now - last_activity).total_seconds(),
                    }
                )
            else:
                healthy.append({"player_id": player_id, "last_activity": last_activity})

        # Mark unhealthy connections as disconnected
        for conn in unhealthy:
            await self.handle_client_disconnect(
                conn["player_id"], reason="health_check_timeout"
            )

        return {
            "total_connections": len(self._active_connections),
            "healthy": len(healthy),
            "warning": len(warning),
            "disconnected": len(unhealthy),
            "unhealthy_players": [c["player_id"] for c in unhealthy],
        }

    async def get_connection_analytics(
        self, player_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get connection analytics for a player or all players.

        Args:
            player_id: Optional specific player

        Returns:
            Connection analytics data
        """
        if player_id:
            # Single player analytics
            if player_id not in self._connection_metrics:
                return {"error": "No connection data for player"}

            metrics = self._connection_metrics[player_id]
            is_connected = player_id in self._active_connections

            analytics = {
                "player_id": player_id,
                "is_connected": is_connected,
                "connection_metrics": {
                    "total_connections": metrics.get("disconnections", 0)
                    + (1 if is_connected else 0),
                    "average_latency_ms": metrics.get("average_latency", 0),
                    "ping_count": metrics.get("ping_count", 0),
                    "last_session_duration_seconds": metrics.get(
                        "last_session_duration", 0
                    ),
                },
                "client_info": metrics.get("client_info", {}),
            }

            if is_connected and "connected_at" in metrics:
                analytics["current_session_duration"] = (
                    datetime.utcnow() - metrics["connected_at"]
                ).total_seconds()

            return analytics

        else:
            # Global analytics
            total_active = len(self._active_connections)
            total_tracked = len(self._connection_metrics)

            # Calculate averages
            total_latency = sum(
                m.get("average_latency", 0) * m.get("ping_count", 1)
                for m in self._connection_metrics.values()
            )
            total_pings = sum(
                m.get("ping_count", 0) for m in self._connection_metrics.values()
            )

            # Client version distribution
            version_dist = defaultdict(int)
            for metrics in self._connection_metrics.values():
                version = metrics.get("client_info", {}).get("version", "unknown")
                version_dist[version] += 1

            return {
                "total_active_connections": total_active,
                "total_tracked_players": total_tracked,
                "average_latency_ms": (
                    round(total_latency / total_pings, 2) if total_pings > 0 else 0
                ),
                "client_version_distribution": dict(version_dist),
                "connection_stability": self._calculate_stability_score(),
            }

    async def handle_bulk_sync(
        self, player_ids: List[str], room_id: str
    ) -> Dict[str, Any]:
        """
        Handle bulk state synchronization for multiple players.

        Args:
            player_ids: List of player IDs to sync
            room_id: Room ID

        Returns:
            Bulk sync results
        """
        results = {"synced": [], "failed": []}

        for player_id in player_ids:
            try:
                sync_request = SyncClientStateRequest(
                    player_id=player_id, room_id=room_id
                )
                sync_response = await self._sync_state_use_case.execute(sync_request)

                results["synced"].append(
                    {
                        "player_id": player_id,
                        "events_missed": sync_response.events_missed,
                    }
                )

            except Exception as e:
                results["failed"].append({"player_id": player_id, "error": str(e)})
                self._logger.warning(f"Failed to sync player {player_id}: {e}")

        return results

    def _calculate_stability_score(self) -> float:
        """Calculate overall connection stability score (0-100)."""
        if not self._connection_metrics:
            return 100.0

        total_disconnections = sum(
            m.get("disconnections", 0) for m in self._connection_metrics.values()
        )

        total_connections = len(self._connection_metrics)

        # Base score of 100, minus 10 for each disconnection per player
        avg_disconnections = total_disconnections / total_connections
        score = max(0, 100 - (avg_disconnections * 10))

        return round(score, 2)

    async def update_ping_metrics(self, player_id: str, latency_ms: float) -> None:
        """Update ping metrics for a player."""
        if player_id in self._connection_metrics:
            metrics = self._connection_metrics[player_id]

            # Update ping count
            ping_count = metrics.get("ping_count", 0) + 1
            metrics["ping_count"] = ping_count

            # Update average latency
            current_avg = metrics.get("average_latency", 0)
            new_avg = ((current_avg * (ping_count - 1)) + latency_ms) / ping_count
            metrics["average_latency"] = round(new_avg, 2)

            # Update last activity
            if player_id in self._active_connections:
                self._active_connections[player_id] = datetime.utcnow()
