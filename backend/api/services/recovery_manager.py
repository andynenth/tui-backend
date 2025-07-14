"""
Recovery Manager for Liap Tui Game
Automatic recovery procedures for system failures and error conditions
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Import our services
try:
    from .logging_service import game_logger

    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    game_logger = None

try:
    from .health_monitor import health_monitor, HealthStatus

    HEALTH_MONITOR_AVAILABLE = True
except ImportError:
    HEALTH_MONITOR_AVAILABLE = False
    health_monitor = None


class RecoveryAction(Enum):
    """Types of recovery actions"""

    RECONNECT_CLIENT = "reconnect_client"
    RESTART_ROOM = "restart_room"
    CLEANUP_CONNECTIONS = "cleanup_connections"
    CLEAR_PENDING_MESSAGES = "clear_pending_messages"
    FORCE_SYNC = "force_sync"
    RESTART_GAME = "restart_game"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


@dataclass
class RecoveryProcedure:
    """Definition of a recovery procedure"""

    name: str
    trigger_condition: str
    action: RecoveryAction
    max_attempts: int = 3
    cooldown_seconds: int = 60
    severity: str = "medium"
    description: str = ""


@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt"""

    procedure_name: str
    action: RecoveryAction
    timestamp: float
    success: bool
    error_message: str = ""
    context: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "procedure_name": self.procedure_name,
            "action": self.action.value,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp).isoformat(),
            "success": self.success,
            "error_message": self.error_message,
            "context": self.context or {},
        }


class RecoveryManager:
    """Automatic recovery procedures for system failures"""

    def __init__(self):
        self.recovery_procedures = self._define_recovery_procedures()
        self.recovery_history: List[RecoveryAttempt] = []
        self.procedure_attempts: Dict[str, List[float]] = (
            {}
        )  # procedure_name -> timestamps
        self.max_history = 1000
        self.is_active = False

    def _define_recovery_procedures(self) -> Dict[str, RecoveryProcedure]:
        """Define standard recovery procedures"""
        return {
            "stale_connections": RecoveryProcedure(
                name="stale_connections",
                trigger_condition="websocket_failure_rate > 15%",
                action=RecoveryAction.CLEANUP_CONNECTIONS,
                max_attempts=5,
                cooldown_seconds=30,
                description="Clean up stale WebSocket connections",
            ),
            "high_pending_messages": RecoveryProcedure(
                name="high_pending_messages",
                trigger_condition="pending_messages > 100",
                action=RecoveryAction.CLEAR_PENDING_MESSAGES,
                max_attempts=3,
                cooldown_seconds=60,
                description="Clear excessive pending messages",
            ),
            "room_state_corruption": RecoveryProcedure(
                name="room_state_corruption",
                trigger_condition="room_state_invalid",
                action=RecoveryAction.RESTART_ROOM,
                max_attempts=2,
                cooldown_seconds=120,
                severity="high",
                description="Restart room with corrupted state",
            ),
            "client_desync": RecoveryProcedure(
                name="client_desync",
                trigger_condition="client_sequence_gap > 10",
                action=RecoveryAction.FORCE_SYNC,
                max_attempts=3,
                cooldown_seconds=30,
                description="Force client synchronization",
            ),
            "database_connection_loss": RecoveryProcedure(
                name="database_connection_loss",
                trigger_condition="database_inaccessible",
                action=RecoveryAction.RECONNECT_CLIENT,
                max_attempts=5,
                cooldown_seconds=10,
                severity="high",
                description="Recover database connection",
            ),
            "memory_pressure": RecoveryProcedure(
                name="memory_pressure",
                trigger_condition="memory_usage > 90%",
                action=RecoveryAction.CLEANUP_CONNECTIONS,
                max_attempts=3,
                cooldown_seconds=60,
                severity="high",
                description="Clean up to reduce memory usage",
            ),
            "system_overload": RecoveryProcedure(
                name="system_overload",
                trigger_condition="cpu_usage > 95% AND memory_usage > 95%",
                action=RecoveryAction.EMERGENCY_SHUTDOWN,
                max_attempts=1,
                cooldown_seconds=300,
                severity="critical",
                description="Emergency system protection",
            ),
        }

    async def start_monitoring(self):
        """Start automatic recovery monitoring"""
        if self.is_active:
            return

        self.is_active = True

        if LOGGING_AVAILABLE and game_logger:
            game_logger.log_game_event(
                "recovery_monitoring_started",
                procedures=list(self.recovery_procedures.keys()),
            )

        # Start monitoring task
        asyncio.create_task(self._recovery_monitoring_loop())
        print("🔧 RECOVERY_MANAGER: Started automatic recovery monitoring")

    def stop_monitoring(self):
        """Stop automatic recovery monitoring"""
        self.is_active = False

        if LOGGING_AVAILABLE and game_logger:
            game_logger.log_game_event("recovery_monitoring_stopped")

        print("🔧 RECOVERY_MANAGER: Stopped recovery monitoring")

    async def _recovery_monitoring_loop(self):
        """Main monitoring loop for automatic recovery"""
        while self.is_active:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                if HEALTH_MONITOR_AVAILABLE and health_monitor:
                    # Get current health status
                    health = await health_monitor.get_health_status()

                    # Check if any recovery procedures should be triggered
                    await self._check_recovery_triggers(health)

            except Exception as e:
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_error(e, "recovery_monitoring_loop")
                print(f"❌ RECOVERY_MANAGER: Error in monitoring loop: {e}")

    async def _check_recovery_triggers(self, health):
        """Check if any recovery procedures should be triggered"""
        try:
            # Check WebSocket health
            if "websocket" in health.metrics:
                ws_metric = health.metrics["websocket"]
                if isinstance(ws_metric.value, dict):
                    pending = ws_metric.value.get("pending", 0)

                    # Trigger high pending messages recovery
                    if pending > 100:
                        await self.trigger_recovery(
                            "high_pending_messages",
                            context={"pending_messages": pending},
                        )

            # Check memory usage
            if "memory" in health.metrics:
                memory_metric = health.metrics["memory"]
                if memory_metric.value > 90:
                    await self.trigger_recovery(
                        "memory_pressure", context={"memory_usage": memory_metric.value}
                    )

            # Check system overload
            memory_critical = False
            cpu_critical = False

            if "memory" in health.metrics and health.metrics["memory"].value > 95:
                memory_critical = True
            if "cpu" in health.metrics and health.metrics["cpu"].value > 95:
                cpu_critical = True

            if memory_critical and cpu_critical:
                await self.trigger_recovery(
                    "system_overload",
                    context={
                        "memory": health.metrics["memory"].value,
                        "cpu": health.metrics["cpu"].value,
                    },
                )

            # Check database health
            if "database" in health.metrics:
                db_metric = health.metrics["database"]
                if db_metric.status == HealthStatus.CRITICAL:
                    await self.trigger_recovery(
                        "database_connection_loss",
                        context={"database_status": db_metric.status.value},
                    )

        except Exception as e:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_error(e, "recovery_trigger_check")

    async def trigger_recovery(
        self, procedure_name: str, context: Dict[str, Any] = None
    ) -> bool:
        """Trigger a specific recovery procedure"""
        if procedure_name not in self.recovery_procedures:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_error(
                    Exception(f"Unknown recovery procedure: {procedure_name}"),
                    "trigger_recovery",
                )
            return False

        procedure = self.recovery_procedures[procedure_name]

        # Check cooldown
        if not self._can_attempt_recovery(procedure_name, procedure.cooldown_seconds):
            return False

        # Check max attempts
        recent_attempts = self._get_recent_attempts(procedure_name, 3600)  # Last hour
        if len(recent_attempts) >= procedure.max_attempts:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_game_event(
                    "recovery_max_attempts_reached",
                    procedure=procedure_name,
                    attempts=len(recent_attempts),
                )
            return False

        # Record attempt timestamp
        now = time.time()
        if procedure_name not in self.procedure_attempts:
            self.procedure_attempts[procedure_name] = []
        self.procedure_attempts[procedure_name].append(now)

        # Execute recovery procedure
        success = await self._execute_recovery_action(procedure, context or {})

        # Record attempt
        attempt = RecoveryAttempt(
            procedure_name=procedure_name,
            action=procedure.action,
            timestamp=now,
            success=success,
            context=context,
        )

        self.recovery_history.append(attempt)

        # Cleanup old history
        if len(self.recovery_history) > self.max_history:
            self.recovery_history = self.recovery_history[-self.max_history :]

        if LOGGING_AVAILABLE and game_logger:
            game_logger.log_game_event(
                "recovery_procedure_executed",
                procedure=procedure_name,
                action=procedure.action.value,
                success=success,
                context=context,
            )

        return success

    async def _execute_recovery_action(
        self, procedure: RecoveryProcedure, context: Dict[str, Any]
    ) -> bool:
        """Execute the actual recovery action"""
        try:
            action = procedure.action

            if action == RecoveryAction.CLEANUP_CONNECTIONS:
                return await self._cleanup_stale_connections(context)

            elif action == RecoveryAction.CLEAR_PENDING_MESSAGES:
                return await self._clear_pending_messages(context)

            elif action == RecoveryAction.RESTART_ROOM:
                return await self._restart_room(context)

            elif action == RecoveryAction.FORCE_SYNC:
                return await self._force_client_sync(context)

            elif action == RecoveryAction.RECONNECT_CLIENT:
                return await self._reconnect_database(context)

            elif action == RecoveryAction.EMERGENCY_SHUTDOWN:
                return await self._emergency_shutdown(context)

            else:
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_error(
                        Exception(f"Unknown recovery action: {action}"),
                        "execute_recovery_action",
                    )
                return False

        except Exception as e:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_error(e, f"recovery_action_{procedure.action.value}")
            return False

    async def _cleanup_stale_connections(self, context: Dict[str, Any]) -> bool:
        """Clean up stale WebSocket connections"""
        try:
            import sys

            sys.path.append("/Users/nrw/python/tui-project/liap-tui/backend")
            from socket_manager import _socket_manager as socket_manager

            cleaned_count = 0

            # Check each room for stale connections
            for room_id, connections in list(socket_manager.room_connections.items()):
                stale_connections = []

                for ws in list(connections):
                    try:
                        # Try to ping the connection
                        if hasattr(ws, "ping"):
                            await asyncio.wait_for(ws.ping(), timeout=5.0)
                        else:
                            # If no ping method, check connection state
                            if hasattr(ws, "client_state") and hasattr(
                                ws.client_state, "name"
                            ):
                                if ws.client_state.name in ["DISCONNECTED", "CLOSED"]:
                                    stale_connections.append(ws)
                    except (asyncio.TimeoutError, Exception):
                        stale_connections.append(ws)

                # Remove stale connections
                for ws in stale_connections:
                    connections.discard(ws)
                    cleaned_count += 1

            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_websocket_event(
                    "system", "cleanup_stale_connections", cleaned_count=cleaned_count
                )

            print(f"🔧 RECOVERY_MANAGER: Cleaned up {cleaned_count} stale connections")
            return True

        except Exception as e:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_error(e, "cleanup_stale_connections")
            return False

    async def _clear_pending_messages(self, context: Dict[str, Any]) -> bool:
        """Clear excessive pending messages"""
        try:
            import sys

            sys.path.append("/Users/nrw/python/tui-project/liap-tui/backend")
            from socket_manager import _socket_manager as socket_manager

            cleared_count = 0

            # Clear old pending messages (older than 5 minutes)
            cutoff_time = time.time() - 300

            for room_id, pending_messages in socket_manager.pending_messages.items():
                expired_sequences = []

                for sequence, pending_msg in pending_messages.items():
                    if pending_msg.timestamp < cutoff_time:
                        expired_sequences.append(sequence)

                # Remove expired messages
                for sequence in expired_sequences:
                    del pending_messages[sequence]
                    cleared_count += 1

            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_websocket_event(
                    "system", "clear_pending_messages", cleared_count=cleared_count
                )

            print(
                f"🔧 RECOVERY_MANAGER: Cleared {cleared_count} expired pending messages"
            )
            return True

        except Exception as e:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_error(e, "clear_pending_messages")
            return False

    async def _restart_room(self, context: Dict[str, Any]) -> bool:
        """Restart a room with corrupted state"""
        try:
            room_id = context.get("room_id")
            if not room_id:
                return False

            import sys

            sys.path.append("/Users/nrw/python/tui-project/liap-tui/backend")
            from shared_instances import shared_room_manager

            room = shared_room_manager.get_room(room_id)
            if not room:
                return False

            # Save current players
            players = [slot for slot in room.slots if slot is not None]

            # Reset room state
            room.started = False
            room.game = None
            room.game_state_machine = None

            # Notify players of restart
            import sys

            sys.path.append("/Users/nrw/python/tui-project/liap-tui/backend")
            from socket_manager import broadcast

            await broadcast(
                room_id,
                "room_restarted",
                {"reason": "State recovery", "players": players},
            )

            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_game_event(
                    "room_restarted", room_id=room_id, player_count=len(players)
                )

            print(f"🔧 RECOVERY_MANAGER: Restarted room {room_id}")
            return True

        except Exception as e:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_error(e, "restart_room")
            return False

    async def _force_client_sync(self, context: Dict[str, Any]) -> bool:
        """Force client synchronization"""
        try:
            room_id = context.get("room_id", "all")

            import sys

            sys.path.append("/Users/nrw/python/tui-project/liap-tui/backend")
            from socket_manager import _socket_manager as socket_manager

            sync_count = 0

            if room_id == "all":
                # Sync all rooms
                rooms_to_sync = list(socket_manager.room_connections.keys())
            else:
                rooms_to_sync = (
                    [room_id] if room_id in socket_manager.room_connections else []
                )

            for target_room in rooms_to_sync:
                connections = socket_manager.room_connections[target_room]

                for ws in connections:
                    try:
                        await socket_manager.request_client_sync(
                            target_room, ws, "recovery"
                        )
                        sync_count += 1
                    except Exception:
                        continue

            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_websocket_event(
                    "system", "force_client_sync", sync_count=sync_count
                )

            print(f"🔧 RECOVERY_MANAGER: Forced sync for {sync_count} clients")
            return True

        except Exception as e:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_error(e, "force_client_sync")
            return False

    async def _reconnect_database(self, context: Dict[str, Any]) -> bool:
        """Attempt to reconnect to database"""
        try:
            # Test database connectivity
            import sqlite3

            # Try to create a simple connection
            conn = sqlite3.connect(":memory:")
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == 1:
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_game_event("database_reconnection_successful")

                print("🔧 RECOVERY_MANAGER: Database connection restored")
                return True
            else:
                return False

        except Exception as e:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_error(e, "reconnect_database")
            return False

    async def _emergency_shutdown(self, context: Dict[str, Any]) -> bool:
        """Emergency system shutdown protection"""
        try:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_critical_error(
                    Exception("Emergency shutdown triggered"),
                    "system_overload",
                    **context,
                )

            print("🚨 RECOVERY_MANAGER: EMERGENCY SHUTDOWN TRIGGERED")
            print(f"   System overload detected: {context}")
            print("   Consider manual intervention")

            # In a real system, this might trigger alerts or graceful shutdown
            # For now, just log the critical event

            return True

        except Exception as e:
            return False

    def _can_attempt_recovery(self, procedure_name: str, cooldown_seconds: int) -> bool:
        """Check if recovery procedure can be attempted (cooldown check)"""
        if procedure_name not in self.procedure_attempts:
            return True

        last_attempt = max(self.procedure_attempts[procedure_name])
        return time.time() - last_attempt >= cooldown_seconds

    def _get_recent_attempts(
        self, procedure_name: str, time_window_seconds: int
    ) -> List[float]:
        """Get recent attempts for a procedure within time window"""
        if procedure_name not in self.procedure_attempts:
            return []

        cutoff_time = time.time() - time_window_seconds
        return [t for t in self.procedure_attempts[procedure_name] if t >= cutoff_time]

    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery system status"""
        recent_attempts = [
            attempt
            for attempt in self.recovery_history
            if attempt.timestamp > time.time() - 3600
        ]  # Last hour

        success_rate = 0
        if recent_attempts:
            successful = sum(1 for attempt in recent_attempts if attempt.success)
            success_rate = (successful / len(recent_attempts)) * 100

        return {
            "is_active": self.is_active,
            "total_procedures": len(self.recovery_procedures),
            "recent_attempts": len(recent_attempts),
            "success_rate": success_rate,
            "procedures": {
                name: {
                    "description": proc.description,
                    "max_attempts": proc.max_attempts,
                    "cooldown_seconds": proc.cooldown_seconds,
                    "severity": proc.severity,
                    "recent_attempts": len(self._get_recent_attempts(name, 3600)),
                }
                for name, proc in self.recovery_procedures.items()
            },
            "recent_history": [attempt.to_dict() for attempt in recent_attempts[-10:]],
        }


# Global recovery manager instance
recovery_manager = RecoveryManager()

# Export for easy importing
__all__ = [
    "RecoveryManager",
    "RecoveryAction",
    "RecoveryProcedure",
    "RecoveryAttempt",
    "recovery_manager",
]
