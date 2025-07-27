"""
Enterprise monitor that integrates all monitoring components.

Provides a unified interface for comprehensive system monitoring.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from contextlib import asynccontextmanager

from ..observability.metrics import configure_metrics, get_metrics_collector
from .game_metrics import GameMetricsCollector
from .system_metrics import SystemMetricsCollector
from .tracing import StateTracer, TraceContext, configure_tracing
from .correlation import set_correlation_id, get_correlation_id
from .event_stream import EventStream, EventLogger, SystemEvent, EventType
from .visualization import StateVisualizationProvider
from .prometheus_endpoint import configure_prometheus_exporter


logger = logging.getLogger(__name__)


class EnterpriseMonitor:
    """
    Unified enterprise monitoring system.
    
    Integrates all monitoring components:
    - Metrics collection
    - Distributed tracing
    - Event streaming
    - Correlation tracking
    - Visualization
    - Performance monitoring
    """
    
    def __init__(
        self,
        service_name: str = "liap-tui",
        enable_tracing: bool = True,
        enable_console_export: bool = False
    ):
        """Initialize enterprise monitor."""
        self.service_name = service_name
        
        # Configure base metrics
        configure_metrics(service_name)
        
        # Initialize collectors
        self.metrics_collector = get_metrics_collector()
        self.game_metrics = GameMetricsCollector(self.metrics_collector)
        self.system_metrics = SystemMetricsCollector(self.metrics_collector)
        
        # Initialize tracing
        self.tracer = None
        if enable_tracing:
            self.tracer = configure_tracing(service_name, enable_console_export)
        
        # Initialize event stream
        self.event_stream = EventStream()
        self.event_logger = EventLogger(self.event_stream)
        
        # Initialize visualization
        self.visualization = StateVisualizationProvider()
        
        # Configure Prometheus exporter
        configure_prometheus_exporter(self.game_metrics, self.system_metrics)
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        
        logger.info(f"Enterprise monitor initialized for {service_name}")
    
    async def start(self) -> None:
        """Start background monitoring tasks."""
        # Start periodic cleanup
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._tasks.append(cleanup_task)
        
        # Start performance monitoring
        perf_task = asyncio.create_task(self._performance_monitoring_loop())
        self._tasks.append(perf_task)
        
        logger.info("Enterprise monitor started")
    
    async def stop(self) -> None:
        """Stop all monitoring tasks."""
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for cancellation
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self._tasks.clear()
        logger.info("Enterprise monitor stopped")
    
    @asynccontextmanager
    async def monitor_state_transition(
        self,
        game_id: str,
        from_state: str,
        to_state: str,
        correlation_id: Optional[str] = None
    ):
        """Monitor a state transition with full instrumentation."""
        # Set correlation ID
        if not correlation_id:
            correlation_id = set_correlation_id()
        else:
            set_correlation_id(correlation_id)
        
        # Create trace context
        trace_context = None
        if self.tracer:
            trace_context = self.tracer.create_trace_context(correlation_id)
        
        # Log transition start
        await self.event_logger.log_state_transition(
            game_id=game_id,
            from_state=from_state,
            to_state=to_state,
            success=False,  # In progress
            correlation_id=correlation_id
        )
        
        # Start timing
        start_time = datetime.utcnow()
        
        # Update visualization
        self.visualization.update_state_node(from_state, active_games_delta=-1)
        self.visualization.update_state_node(to_state, active_games_delta=1)
        
        try:
            # Start tracing span
            if self.tracer:
                async with self.tracer.trace_state_transition(
                    game_id, from_state, to_state, trace_context
                ) as span:
                    yield span
            else:
                yield None
            
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Update metrics
            await self.game_metrics.record_state_transition(
                game_id=game_id,
                from_state=from_state,
                to_state=to_state,
                transition_time_ms=duration * 1000
            )
            
            # Update visualization
            self.visualization.update_state_transition(
                from_state=from_state,
                to_state=to_state,
                duration_ms=duration * 1000,
                success=True
            )
            
            # Log success
            await self.event_logger.log_state_transition(
                game_id=game_id,
                from_state=from_state,
                to_state=to_state,
                success=True,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            # Update error metrics
            self.visualization.update_state_node(to_state, error_occurred=True)
            self.visualization.record_error(to_state, type(e).__name__)
            
            # Log failure
            await self.event_logger.log_state_transition(
                game_id=game_id,
                from_state=from_state,
                to_state=to_state,
                success=False,
                error=str(e),
                correlation_id=correlation_id
            )
            
            # Log error event
            await self.event_logger.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                game_id=game_id,
                correlation_id=correlation_id
            )
            
            raise
    
    @asynccontextmanager
    async def monitor_action_processing(
        self,
        game_id: str,
        action_type: str,
        player_id: str,
        correlation_id: Optional[str] = None
    ):
        """Monitor action processing with full instrumentation."""
        # Set correlation ID
        if not correlation_id:
            correlation_id = get_correlation_id() or set_correlation_id()
        
        # Log action queued
        await self.event_logger.log_action(
            game_id=game_id,
            action_type=action_type,
            player_id=player_id,
            status='queued',
            correlation_id=correlation_id
        )
        
        # Start timing
        start_time = datetime.utcnow()
        
        try:
            # Log processing start
            await self.event_logger.log_action(
                game_id=game_id,
                action_type=action_type,
                player_id=player_id,
                status='processing',
                correlation_id=correlation_id
            )
            
            # Trace if available
            if self.tracer:
                trace_context = self.tracer.get_trace_context(correlation_id)
                async with self.tracer.trace_action_processing(
                    game_id, action_type, player_id, trace_context
                ) as span:
                    yield span
            else:
                yield None
            
            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Update metrics
            await self.game_metrics.record_player_action(
                player_id=player_id,
                action_type=action_type,
                response_time_ms=duration * 1000,
                game_id=game_id
            )
            
            # Log completion
            await self.event_logger.log_action(
                game_id=game_id,
                action_type=action_type,
                player_id=player_id,
                status='completed',
                data={'duration_ms': duration * 1000},
                correlation_id=correlation_id
            )
            
        except Exception as e:
            # Log failure
            await self.event_logger.log_action(
                game_id=game_id,
                action_type=action_type,
                player_id=player_id,
                status='failed',
                data={'error': str(e)},
                correlation_id=correlation_id
            )
            
            raise
    
    async def record_game_start(
        self,
        game_id: str,
        room_id: str,
        player_count: int,
        bot_count: int
    ) -> None:
        """Record game start with all collectors."""
        await self.game_metrics.record_game_start(
            game_id=game_id,
            room_id=room_id,
            player_count=player_count,
            bot_count=bot_count
        )
        
        self.visualization.update_room_visualization(
            room_id=room_id,
            game_id=game_id,
            current_state='PREPARATION',
            player_count=player_count
        )
        
        event = SystemEvent(
            event_type=EventType.GAME_STARTED,
            game_id=game_id,
            room_id=room_id,
            data={
                'player_count': player_count,
                'bot_count': bot_count
            }
        )
        await self.event_stream.publish_event(event)
    
    async def record_game_end(
        self,
        game_id: str,
        winner_id: Optional[str],
        final_scores: Dict[str, int],
        abandoned: bool = False
    ) -> None:
        """Record game end with all collectors."""
        await self.game_metrics.record_game_end(
            game_id=game_id,
            winner_id=winner_id,
            final_scores=final_scores,
            abandoned=abandoned
        )
        
        event = SystemEvent(
            event_type=EventType.GAME_ENDED,
            game_id=game_id,
            data={
                'winner_id': winner_id,
                'final_scores': final_scores,
                'abandoned': abandoned
            }
        )
        await self.event_stream.publish_event(event)
    
    async def record_websocket_event(
        self,
        connection_id: str,
        event_type: str,
        room_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record WebSocket event."""
        if event_type == 'connect':
            await self.game_metrics.record_websocket_connection(
                connection_id=connection_id,
                connected=True
            )
            
            event = SystemEvent(
                event_type=EventType.CONNECTION_OPENED,
                room_id=room_id,
                data=data or {}
            )
            await self.event_stream.publish_event(event)
            
        elif event_type == 'disconnect':
            await self.game_metrics.record_websocket_connection(
                connection_id=connection_id,
                connected=False
            )
            
            event = SystemEvent(
                event_type=EventType.CONNECTION_CLOSED,
                room_id=room_id,
                data=data or {}
            )
            await self.event_stream.publish_event(event)
            
        elif event_type == 'broadcast':
            if data:
                await self.game_metrics.record_websocket_broadcast(
                    room_id=room_id or 'unknown',
                    recipient_count=data.get('recipient_count', 0),
                    broadcast_time_ms=data.get('broadcast_time_ms', 0),
                    success=data.get('success', True)
                )
    
    async def record_phase_duration(
        self,
        game_id: str,
        phase: str,
        duration_seconds: float
    ) -> None:
        """Record phase duration."""
        await self.game_metrics.record_phase_duration(
            game_id=game_id,
            phase=phase,
            duration_seconds=duration_seconds
        )
        
        # Update visualization
        self.visualization.update_state_node(
            phase,
            duration_sample=duration_seconds
        )
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status."""
        return {
            'service_name': self.service_name,
            'collectors': {
                'metrics': self.metrics_collector is not None,
                'game_metrics': self.game_metrics is not None,
                'system_metrics': self.system_metrics is not None,
                'tracer': self.tracer is not None
            },
            'event_stream': self.event_stream.get_statistics(),
            'game_analytics': self.game_metrics.get_game_analytics(),
            'system_summary': self.system_metrics.get_memory_summary(),
            'active_traces': self.tracer.get_active_traces() if self.tracer else [],
            'visualization_rooms': len(self.visualization._room_visualizations)
        }
    
    async def subscribe_to_events(
        self,
        subscriber_id: Optional[str] = None,
        event_filter: Optional[Any] = None
    ) -> Any:
        """Subscribe to event stream."""
        return await self.event_stream.subscribe(subscriber_id, event_filter)
    
    def get_visualization_data(self, viz_type: Optional[str] = None) -> Dict[str, Any]:
        """Get visualization data."""
        if viz_type == 'state_diagram':
            return self.visualization.get_state_diagram()
        elif viz_type == 'room_status':
            return self.visualization.get_room_status()
        elif viz_type == 'performance':
            return self.visualization.get_performance_metrics()
        elif viz_type == 'errors':
            return self.visualization.get_error_heatmap()
        else:
            return self.visualization.get_all_visualizations()
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of old data."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Clean up event stream
                await self.event_stream.cleanup_inactive_subscribers()
                
                # Clean up visualization data
                self.visualization.cleanup_old_data()
                
                # Clean up trace contexts
                if self.tracer:
                    self.tracer.cleanup_old_contexts()
                
                # Force garbage collection
                self.system_metrics.force_gc_collection()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _performance_monitoring_loop(self) -> None:
        """Monitor system performance metrics."""
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                
                # Record system metrics
                memory_summary = self.system_metrics.get_memory_summary()
                
                # Check for high memory usage
                if memory_summary.get('current_rss_mb', 0) > 1000:
                    await self.event_logger.log_error(
                        error_type='HighMemoryUsage',
                        error_message=f"Memory usage is {memory_summary['current_rss_mb']}MB"
                    )
                
                # Check for high memory growth
                growth_rate = memory_summary.get('growth_rate_mb_per_hour', 0)
                if growth_rate > 50:
                    await self.event_logger.log_error(
                        error_type='HighMemoryGrowth',
                        error_message=f"Memory growing at {growth_rate}MB/hour"
                    )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")


# Global enterprise monitor instance
_enterprise_monitor: Optional[EnterpriseMonitor] = None


def get_enterprise_monitor() -> EnterpriseMonitor:
    """Get global enterprise monitor instance."""
    global _enterprise_monitor
    if _enterprise_monitor is None:
        _enterprise_monitor = EnterpriseMonitor()
    return _enterprise_monitor


def configure_enterprise_monitoring(
    service_name: str = "liap-tui",
    enable_tracing: bool = True,
    enable_console_export: bool = False
) -> EnterpriseMonitor:
    """Configure enterprise monitoring system."""
    global _enterprise_monitor
    _enterprise_monitor = EnterpriseMonitor(
        service_name=service_name,
        enable_tracing=enable_tracing,
        enable_console_export=enable_console_export
    )
    return _enterprise_monitor