"""
Health Monitoring System for Liap Tui Game
Monitors system health and triggers automatic recovery procedures
"""

import asyncio
import time
import psutil
import sqlite3
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
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
    from .event_store import event_store
    EVENT_STORE_AVAILABLE = True
except ImportError:
    EVENT_STORE_AVAILABLE = False
    event_store = None

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    status: HealthStatus
    value: Any
    threshold: Optional[float] = None
    message: str = ""
    last_check: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "last_check": self.last_check,
            "last_check_iso": datetime.fromtimestamp(self.last_check).isoformat()
        }

@dataclass
class SystemHealth:
    """Overall system health status"""
    status: HealthStatus
    metrics: Dict[str, HealthMetric]
    last_check: float = field(default_factory=time.time)
    uptime_seconds: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.status.value,
            "last_check": self.last_check,
            "last_check_iso": datetime.fromtimestamp(self.last_check).isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "uptime_formatted": self._format_uptime(),
            "metrics": {name: metric.to_dict() for name, metric in self.metrics.items()}
        }
    
    def _format_uptime(self) -> str:
        """Format uptime in human-readable format"""
        hours, remainder = divmod(self.uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

class HealthMonitor:
    """Monitor system health and trigger recovery procedures"""
    
    def __init__(self):
        self.start_time = time.time()
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self.health_history: List[SystemHealth] = []
        self.max_history = 100  # Keep last 100 health checks
        
        # Thresholds for health metrics
        self.thresholds = {
            "memory_usage_percent": 85.0,
            "cpu_usage_percent": 80.0,
            "disk_usage_percent": 90.0,
            "websocket_failure_rate": 10.0,  # 10% failure rate
            "message_delivery_rate": 95.0,   # 95% minimum delivery
            "response_time_ms": 1000.0,      # 1 second response time
            "active_connections": 1000,      # Max 1000 connections
            "pending_messages": 100,         # Max 100 pending messages
            "database_response_ms": 500.0    # 500ms database response
        }
    
    async def start_monitoring(self):
        """Start background health monitoring tasks"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        
        if LOGGING_AVAILABLE and game_logger:
            game_logger.log_game_event("health_monitoring_started", 
                                     thresholds=self.thresholds)
        
        # Start monitoring tasks
        tasks = [
            self._monitor_system_resources(),
            self._monitor_websocket_health(),
            self._monitor_database_health(),
            self._monitor_game_performance(),
            self._cleanup_old_health_data()
        ]
        
        self.monitoring_tasks = [asyncio.create_task(task) for task in tasks]
        
        print("🔍 HEALTH_MONITOR: Started monitoring system health")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        
        for task in self.monitoring_tasks:
            task.cancel()
            
        # Wait for tasks to finish
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()
        
        if LOGGING_AVAILABLE and game_logger:
            game_logger.log_game_event("health_monitoring_stopped")
        
        print("🔍 HEALTH_MONITOR: Stopped monitoring")
    
    async def _monitor_system_resources(self):
        """Monitor CPU, memory, and disk usage"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Get system metrics
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=1)
                disk = psutil.disk_usage('/')
                
                metrics = {
                    "memory_usage_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "cpu_usage_percent": cpu_percent,
                    "disk_usage_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                }
                
                # Check thresholds and log warnings
                for metric_name, value in metrics.items():
                    if metric_name in self.thresholds:
                        threshold = self.thresholds[metric_name]
                        
                        if metric_name == "memory_available_gb" or metric_name == "disk_free_gb":
                            # For "available" metrics, warn if below threshold
                            if value < threshold:
                                await self._handle_resource_warning(metric_name, value, threshold)
                        else:
                            # For usage metrics, warn if above threshold
                            if value > threshold:
                                await self._handle_resource_warning(metric_name, value, threshold)
                
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_performance("system_resources_check", 0, **metrics)
                    
            except Exception as e:
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_error(e, "system_resources_monitoring")
                print(f"❌ HEALTH_MONITOR: Error monitoring system resources: {e}")
    
    async def _monitor_websocket_health(self):
        """Monitor WebSocket connection health"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Get WebSocket statistics
                import sys
                sys.path.append('/Users/nrw/python/tui-project/liap-tui/backend')
                from socket_manager import _socket_manager as socket_manager
                
                total_connections = 0
                total_pending = 0
                total_sent = 0
                total_acked = 0
                total_failed = 0
                
                # Aggregate stats from all rooms
                for room_id in socket_manager.room_connections:
                    total_connections += len(socket_manager.room_connections[room_id])
                    
                    if room_id in socket_manager.pending_messages:
                        total_pending += len(socket_manager.pending_messages[room_id])
                    
                    if room_id in socket_manager.message_stats:
                        stats = socket_manager.message_stats[room_id]
                        total_sent += stats.sent
                        total_acked += stats.acknowledged
                        total_failed += stats.failed
                
                # Calculate health metrics
                delivery_rate = (total_acked / max(total_sent, 1)) * 100
                failure_rate = (total_failed / max(total_sent, 1)) * 100
                
                metrics = {
                    "active_connections": total_connections,
                    "pending_messages": total_pending,
                    "message_delivery_rate": delivery_rate,
                    "message_failure_rate": failure_rate,
                    "total_messages_sent": total_sent
                }
                
                # Check thresholds
                if total_connections > self.thresholds["active_connections"]:
                    await self._handle_websocket_warning("too_many_connections", total_connections)
                
                if total_pending > self.thresholds["pending_messages"]:
                    await self._handle_websocket_warning("too_many_pending", total_pending)
                
                if delivery_rate < self.thresholds["message_delivery_rate"]:
                    await self._handle_websocket_warning("low_delivery_rate", delivery_rate)
                
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_websocket_event("system", "health_check", **metrics)
                    
            except Exception as e:
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_error(e, "websocket_health_monitoring")
                print(f"❌ HEALTH_MONITOR: Error monitoring WebSocket health: {e}")
    
    async def _monitor_database_health(self):
        """Monitor database connectivity and performance"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(120)  # Check every 2 minutes
                
                # Test database connectivity and response time
                start_time = time.time()
                
                if EVENT_STORE_AVAILABLE and event_store:
                    # Test event store health
                    health_result = await event_store.health_check()
                    database_healthy = health_result.get("database_accessible", False)
                else:
                    # Test basic SQLite connectivity
                    conn = sqlite3.connect(":memory:")
                    cursor = conn.execute("SELECT 1")
                    cursor.fetchone()
                    conn.close()
                    database_healthy = True
                
                response_time_ms = (time.time() - start_time) * 1000
                
                metrics = {
                    "database_accessible": database_healthy,
                    "database_response_ms": response_time_ms
                }
                
                # Check thresholds
                if response_time_ms > self.thresholds["database_response_ms"]:
                    await self._handle_database_warning("slow_response", response_time_ms)
                
                if not database_healthy:
                    await self._handle_database_warning("connection_failed", response_time_ms)
                
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_performance("database_health_check", response_time_ms, **metrics)
                    
            except Exception as e:
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_error(e, "database_health_monitoring")
                print(f"❌ HEALTH_MONITOR: Error monitoring database health: {e}")
    
    async def _monitor_game_performance(self):
        """Monitor game-specific performance metrics"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(90)  # Check every 90 seconds
                
                # Get room and game statistics
                import sys
                sys.path.append('/Users/nrw/python/tui-project/liap-tui/backend')
                from shared_instances import shared_room_manager
                
                total_rooms = len(shared_room_manager.rooms)
                active_games = 0
                total_players = 0
                
                for room in shared_room_manager.rooms.values():
                    if room.started:
                        active_games += 1
                    total_players += len([slot for slot in room.slots if slot is not None])
                
                metrics = {
                    "total_rooms": total_rooms,
                    "active_games": active_games,
                    "total_players": total_players,
                    "rooms_per_game_ratio": total_rooms / max(active_games, 1)
                }
                
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_game_event("performance_check", **metrics)
                    
            except Exception as e:
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_error(e, "game_performance_monitoring")
                print(f"❌ HEALTH_MONITOR: Error monitoring game performance: {e}")
    
    async def _cleanup_old_health_data(self):
        """Clean up old health check data"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Keep only recent health history
                if len(self.health_history) > self.max_history:
                    self.health_history = self.health_history[-self.max_history:]
                    
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_game_event("health_data_cleanup", 
                                             records_kept=len(self.health_history))
                    
            except Exception as e:
                if LOGGING_AVAILABLE and game_logger:
                    game_logger.log_error(e, "health_data_cleanup")
    
    async def get_health_status(self) -> SystemHealth:
        """Get current system health status"""
        try:
            metrics = {}
            overall_status = HealthStatus.HEALTHY
            
            # System resources
            try:
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=0.1)
                disk = psutil.disk_usage('/')
                
                # Memory health
                memory_status = HealthStatus.HEALTHY
                if memory.percent > self.thresholds["memory_usage_percent"]:
                    memory_status = HealthStatus.CRITICAL
                    overall_status = HealthStatus.CRITICAL
                elif memory.percent > self.thresholds["memory_usage_percent"] * 0.8:
                    memory_status = HealthStatus.WARNING
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.WARNING
                
                metrics["memory"] = HealthMetric(
                    name="memory_usage",
                    status=memory_status,
                    value=memory.percent,
                    threshold=self.thresholds["memory_usage_percent"],
                    message=f"Memory usage: {memory.percent:.1f}%"
                )
                
                # CPU health
                cpu_status = HealthStatus.HEALTHY
                if cpu_percent > self.thresholds["cpu_usage_percent"]:
                    cpu_status = HealthStatus.WARNING
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.WARNING
                
                metrics["cpu"] = HealthMetric(
                    name="cpu_usage",
                    status=cpu_status,
                    value=cpu_percent,
                    threshold=self.thresholds["cpu_usage_percent"],
                    message=f"CPU usage: {cpu_percent:.1f}%"
                )
                
                # Disk health
                disk_status = HealthStatus.HEALTHY
                if disk.percent > self.thresholds["disk_usage_percent"]:
                    disk_status = HealthStatus.CRITICAL
                    overall_status = HealthStatus.CRITICAL
                elif disk.percent > self.thresholds["disk_usage_percent"] * 0.8:
                    disk_status = HealthStatus.WARNING
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.WARNING
                
                metrics["disk"] = HealthMetric(
                    name="disk_usage",
                    status=disk_status,
                    value=disk.percent,
                    threshold=self.thresholds["disk_usage_percent"],
                    message=f"Disk usage: {disk.percent:.1f}%"
                )
                
            except Exception as e:
                metrics["system"] = HealthMetric(
                    name="system_resources",
                    status=HealthStatus.UNKNOWN,
                    value=None,
                    message=f"Failed to get system metrics: {e}"
                )
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.UNKNOWN
            
            # Database health
            try:
                if EVENT_STORE_AVAILABLE and event_store:
                    db_health = await event_store.health_check()
                    db_status = HealthStatus.HEALTHY if db_health.get("database_accessible") else HealthStatus.CRITICAL
                    
                    if db_status == HealthStatus.CRITICAL:
                        overall_status = HealthStatus.CRITICAL
                else:
                    db_status = HealthStatus.UNKNOWN
                
                metrics["database"] = HealthMetric(
                    name="database",
                    status=db_status,
                    value=db_status.value,
                    message="Database connectivity check"
                )
                
            except Exception as e:
                metrics["database"] = HealthMetric(
                    name="database",
                    status=HealthStatus.CRITICAL,
                    value=None,
                    message=f"Database check failed: {e}"
                )
                overall_status = HealthStatus.CRITICAL
            
            # WebSocket health
            try:
                import sys
                sys.path.append('/Users/nrw/python/tui-project/liap-tui/backend')
                from socket_manager import _socket_manager as socket_manager
                
                total_connections = sum(len(conns) for conns in socket_manager.room_connections.values())
                total_pending = sum(len(pending) for pending in socket_manager.pending_messages.values())
                
                ws_status = HealthStatus.HEALTHY
                if total_pending > self.thresholds["pending_messages"]:
                    ws_status = HealthStatus.WARNING
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.WARNING
                
                metrics["websocket"] = HealthMetric(
                    name="websocket",
                    status=ws_status,
                    value={"connections": total_connections, "pending": total_pending},
                    threshold=self.thresholds["pending_messages"],
                    message=f"WebSocket: {total_connections} connections, {total_pending} pending"
                )
                
            except Exception as e:
                metrics["websocket"] = HealthMetric(
                    name="websocket",
                    status=HealthStatus.UNKNOWN,
                    value=None,
                    message=f"WebSocket check failed: {e}"
                )
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.UNKNOWN
            
            # Create health summary
            uptime = time.time() - self.start_time
            health = SystemHealth(
                status=overall_status,
                metrics=metrics,
                uptime_seconds=uptime
            )
            
            # Store in history
            self.health_history.append(health)
            
            return health
            
        except Exception as e:
            if LOGGING_AVAILABLE and game_logger:
                game_logger.log_error(e, "health_status_check")
            
            # Return critical status if health check itself fails
            return SystemHealth(
                status=HealthStatus.CRITICAL,
                metrics={"error": HealthMetric(
                    name="health_check_error",
                    status=HealthStatus.CRITICAL,
                    value=None,
                    message=f"Health check failed: {e}"
                )},
                uptime_seconds=time.time() - self.start_time
            )
    
    async def _handle_resource_warning(self, metric_name: str, value: float, threshold: float):
        """Handle resource threshold warnings"""
        warning_msg = f"Resource warning: {metric_name} = {value:.1f} (threshold: {threshold})"
        
        if LOGGING_AVAILABLE and game_logger:
            game_logger.log_security_event(warning_msg, severity="medium",
                                         metric=metric_name, value=value, threshold=threshold)
        
        print(f"⚠️  HEALTH_MONITOR: {warning_msg}")
    
    async def _handle_websocket_warning(self, warning_type: str, value: float):
        """Handle WebSocket health warnings"""
        warning_msg = f"WebSocket warning: {warning_type} = {value}"
        
        if LOGGING_AVAILABLE and game_logger:
            game_logger.log_websocket_event("system", "health_warning", 
                                          warning_type=warning_type, value=value)
        
        print(f"⚠️  HEALTH_MONITOR: {warning_msg}")
    
    async def _handle_database_warning(self, warning_type: str, value: float):
        """Handle database health warnings"""
        warning_msg = f"Database warning: {warning_type} = {value}"
        
        if LOGGING_AVAILABLE and game_logger:
            game_logger.log_error(Exception(warning_msg), "database_health")
        
        print(f"⚠️  HEALTH_MONITOR: {warning_msg}")

# Global health monitor instance
health_monitor = HealthMonitor()

# Export for easy importing
__all__ = ['HealthMonitor', 'HealthStatus', 'HealthMetric', 'SystemHealth', 'health_monitor']