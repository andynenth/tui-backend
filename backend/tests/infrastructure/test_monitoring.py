"""
Comprehensive tests for enterprise monitoring infrastructure.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import gc
import json

from infrastructure.monitoring import (
    # Game metrics
    GameMetricsCollector,
    GameMetricType,
    
    # System metrics
    SystemMetricsCollector,
    
    # Tracing
    StateTracer,
    TraceContext,
    SpanKind,
    
    # Correlation
    get_correlation_id,
    set_correlation_id,
    with_correlation,
    CorrelatedLogger,
    
    # Event stream
    EventStream,
    SystemEvent,
    EventType,
    EventFilter,
    EventLogger,
    
    # Visualization
    StateVisualizationProvider,
    
    # Prometheus
    PrometheusExporter,
    
    # Enterprise monitor
    EnterpriseMonitor,
    configure_enterprise_monitoring
)


class TestGameMetrics:
    """Test game metrics collection."""
    
    @pytest.mark.asyncio
    async def test_game_lifecycle_metrics(self):
        """Test game start and end metrics."""
        collector = GameMetricsCollector()
        
        # Start game
        await collector.record_game_start(
            game_id="game123",
            room_id="room456",
            player_count=4,
            bot_count=2
        )
        
        # Check active games
        assert "game123" in collector._active_games
        assert len(collector._active_games) == 1
        
        # End game
        await collector.record_game_end(
            game_id="game123",
            winner_id="player1",
            final_scores={"player1": 100, "player2": 80},
            abandoned=False
        )
        
        # Check completed
        assert "game123" not in collector._active_games
        assert len(collector._completed_games) == 1
    
    @pytest.mark.asyncio
    async def test_player_action_metrics(self):
        """Test player action recording."""
        collector = GameMetricsCollector()
        
        # Record actions
        await collector.record_player_action(
            player_id="player1",
            action_type="play_piece",
            response_time_ms=150.5,
            game_id="game123"
        )
        
        await collector.record_player_action(
            player_id="bot_1",
            action_type="declare",
            response_time_ms=50.0,
            game_id="game123"
        )
        
        # Check stats
        assert collector._player_stats["player1"]["actions_taken"] == 1
        assert collector._player_stats["bot_1"]["actions_taken"] == 1
    
    @pytest.mark.asyncio
    async def test_phase_duration_metrics(self):
        """Test phase duration recording."""
        collector = GameMetricsCollector()
        
        # Record phase durations
        await collector.record_phase_duration(
            game_id="game123",
            phase="PREPARATION",
            duration_seconds=30.5
        )
        
        await collector.record_phase_duration(
            game_id="game123",
            phase="DECLARATION",
            duration_seconds=45.2
        )
        
        # Get metrics
        phase_metrics = collector.get_phase_metrics()
        assert "PREPARATION" in phase_metrics
        assert phase_metrics["PREPARATION"]["avg_seconds"] == 30.5
    
    @pytest.mark.asyncio
    async def test_websocket_metrics(self):
        """Test WebSocket connection metrics."""
        collector = GameMetricsCollector()
        
        # Connect
        await collector.record_websocket_connection("conn1", connected=True)
        await collector.record_websocket_connection("conn2", connected=True)
        
        assert len(collector._active_connections) == 2
        
        # Disconnect
        await collector.record_websocket_connection("conn1", connected=False)
        
        assert len(collector._active_connections) == 1
        assert "conn2" in collector._active_connections
    
    def test_hourly_metrics(self):
        """Test hourly metric aggregation."""
        collector = GameMetricsCollector()
        
        # Add hourly data
        hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
        collector._hourly_stats[hour_key] = {
            'games_started': 10,
            'games_completed': 8,
            'games_abandoned': 2,
            'total_players': 40,
            'total_turns': 500
        }
        
        # Get metrics
        hourly = collector.get_hourly_metrics(hours=1)
        assert hour_key in hourly
        assert hourly[hour_key]['games_started'] == 10
    
    def test_game_analytics(self):
        """Test game analytics calculation."""
        collector = GameMetricsCollector()
        
        # No games
        analytics = collector.get_game_analytics()
        assert analytics['total_games'] == 0
        
        # Add completed game
        from infrastructure.monitoring.game_metrics import GameStats
        game = GameStats(
            game_id="game1",
            room_id="room1",
            start_time=datetime.utcnow() - timedelta(minutes=30),
            player_count=4,
            bot_count=0
        )
        game.end_time = datetime.utcnow()
        collector._completed_games.append(game)
        
        analytics = collector.get_game_analytics()
        assert analytics['completed_games'] == 1
        assert analytics['avg_duration_minutes'] > 0


class TestSystemMetrics:
    """Test system metrics collection."""
    
    def test_memory_metrics(self):
        """Test memory usage metrics."""
        collector = SystemMetricsCollector(collection_interval=1)
        
        # Collect metrics
        collector._collect_memory_metrics()
        
        # Get summary
        summary = collector.get_memory_summary()
        assert 'current_rss_mb' in summary
        assert summary['current_rss_mb'] > 0
    
    def test_gc_metrics(self):
        """Test garbage collection metrics."""
        collector = SystemMetricsCollector()
        
        # Force GC
        result = collector.force_gc_collection()
        assert 'collected' in result
        assert 'before_counts' in result
        assert 'after_counts' in result
        
        # Get summary
        summary = collector.get_gc_summary()
        assert 'enabled' in summary
        assert summary['enabled'] == gc.isenabled()
    
    def test_cpu_metrics(self):
        """Test CPU usage metrics."""
        collector = SystemMetricsCollector()
        
        # Collect CPU metrics
        collector._collect_cpu_metrics()
        
        # Metrics should be recorded
        # (Can't easily test exact values)
    
    def test_concurrency_metrics(self):
        """Test thread and coroutine metrics."""
        collector = SystemMetricsCollector()
        
        # Collect concurrency metrics
        collector._collect_concurrency_metrics()
        
        # Should track threads
        # (Can't easily test exact values)


class TestTracing:
    """Test distributed tracing."""
    
    def test_trace_context_creation(self):
        """Test trace context creation."""
        tracer = StateTracer()
        
        # Create context
        context = tracer.create_trace_context(correlation_id="corr123")
        
        assert context.trace_id is not None
        assert context.span_id is not None
        assert context.correlation_id == "corr123"
        assert context.parent_span_id is None
    
    def test_child_context(self):
        """Test child context creation."""
        tracer = StateTracer()
        
        # Create parent
        parent = tracer.create_trace_context()
        
        # Create child
        child = parent.child_context()
        
        assert child.trace_id == parent.trace_id
        assert child.span_id != parent.span_id
        assert child.parent_span_id == parent.span_id
    
    @pytest.mark.asyncio
    async def test_state_transition_tracing(self):
        """Test state transition tracing."""
        tracer = StateTracer()
        
        async with tracer.trace_state_transition(
            game_id="game123",
            from_state="PREPARATION",
            to_state="DECLARATION"
        ) as span:
            assert span is not None
            # Perform transition
            await asyncio.sleep(0.01)
        
        # Span should be completed
    
    @pytest.mark.asyncio
    async def test_action_processing_tracing(self):
        """Test action processing tracing."""
        tracer = StateTracer()
        
        async with tracer.trace_action_processing(
            game_id="game123",
            action_type="play_piece",
            player_id="player1"
        ) as span:
            assert span is not None
            # Process action
            await asyncio.sleep(0.01)
    
    def test_context_propagation(self):
        """Test trace context propagation."""
        tracer = StateTracer()
        context = tracer.create_trace_context()
        
        # Propagate to carrier
        carrier = {}
        tracer.propagate_context(context, carrier)
        
        assert carrier['trace_id'] == context.trace_id
        assert carrier['span_id'] == context.span_id
        
        # Extract from carrier
        extracted = tracer.extract_context(carrier)
        assert extracted.trace_id == context.trace_id


class TestCorrelation:
    """Test correlation ID propagation."""
    
    def test_correlation_id_generation(self):
        """Test correlation ID generation."""
        # Set new ID
        corr_id = set_correlation_id()
        assert corr_id is not None
        assert corr_id.startswith("corr_")
        
        # Get current ID
        assert get_correlation_id() == corr_id
        
        # Clear
        clear_correlation()
        assert get_correlation_id() is None
    
    def test_correlation_metadata(self):
        """Test correlation metadata."""
        from infrastructure.monitoring.correlation import add_correlation_metadata
        
        # Set correlation with metadata
        set_correlation_id(metadata={"user": "test"})
        
        # Add more metadata
        add_correlation_metadata("action", "test_action")
        
        # Clear
        clear_correlation()
    
    @pytest.mark.asyncio
    async def test_correlation_decorator(self):
        """Test correlation decorator."""
        
        @with_correlation(generate_new=True)
        async def test_func():
            return get_correlation_id()
        
        # Should generate new ID
        corr_id = await test_func()
        assert corr_id is not None
        
        # Should be cleared after
        assert get_correlation_id() is None
    
    def test_correlated_logger(self):
        """Test correlated logger."""
        import logging
        
        base_logger = logging.getLogger("test")
        logger = CorrelatedLogger(base_logger)
        
        # Set correlation
        set_correlation_id("test123")
        
        # Log should include correlation
        # (Would need to capture log output to test)
        logger.info("Test message")
        
        clear_correlation()


class TestEventStream:
    """Test event streaming."""
    
    @pytest.mark.asyncio
    async def test_event_publishing(self):
        """Test publishing events."""
        stream = EventStream()
        
        # Create event
        event = SystemEvent(
            event_type=EventType.GAME_STARTED,
            game_id="game123",
            room_id="room456",
            data={"players": 4}
        )
        
        # Publish
        await stream.publish_event(event)
        
        # Check history
        history = stream.get_history()
        assert len(history) == 1
        assert history[0].event_type == EventType.GAME_STARTED
    
    @pytest.mark.asyncio
    async def test_event_subscription(self):
        """Test event subscription."""
        stream = EventStream()
        
        # Subscribe
        subscriber = await stream.subscribe("test_sub")
        assert subscriber.subscriber_id == "test_sub"
        
        # Publish event
        event = SystemEvent(event_type=EventType.GAME_STARTED)
        await stream.publish_event(event)
        
        # Get event
        received = await subscriber.get_event(timeout=1.0)
        assert received is not None
        assert received.event_type == EventType.GAME_STARTED
        
        # Unsubscribe
        await stream.unsubscribe("test_sub")
    
    @pytest.mark.asyncio
    async def test_event_filtering(self):
        """Test event filtering."""
        stream = EventStream()
        
        # Subscribe with filter
        filter = EventFilter(
            event_types={EventType.GAME_STARTED, EventType.GAME_ENDED}
        )
        subscriber = await stream.subscribe("filtered", filter)
        
        # Publish various events
        await stream.publish_event(
            SystemEvent(event_type=EventType.GAME_STARTED)
        )
        await stream.publish_event(
            SystemEvent(event_type=EventType.PLAYER_JOINED)
        )
        await stream.publish_event(
            SystemEvent(event_type=EventType.GAME_ENDED)
        )
        
        # Should only receive filtered events
        event1 = await subscriber.get_event(timeout=0.1)
        assert event1.event_type == EventType.GAME_STARTED
        
        event2 = await subscriber.get_event(timeout=0.1)
        assert event2.event_type == EventType.GAME_ENDED
        
        event3 = await subscriber.get_event(timeout=0.1)
        assert event3 is None  # PLAYER_JOINED filtered out
    
    def test_event_statistics(self):
        """Test event stream statistics."""
        stream = EventStream()
        
        stats = stream.get_statistics()
        assert stats['total_events'] == 0
        assert stats['subscriber_count'] == 0
        assert 'events_by_type' in stats


class TestVisualization:
    """Test visualization provider."""
    
    def test_state_node_updates(self):
        """Test state node updates."""
        viz = StateVisualizationProvider()
        
        # Update state
        viz.update_state_node(
            "PREPARATION",
            active_games_delta=5,
            duration_sample=30.0
        )
        
        node = viz._state_nodes["PREPARATION"]
        assert node.active_games == 5
        assert node.avg_duration_seconds == 30.0
    
    def test_state_transitions(self):
        """Test state transition tracking."""
        viz = StateVisualizationProvider()
        
        # Update transition
        viz.update_state_transition(
            from_state="PREPARATION",
            to_state="DECLARATION",
            duration_ms=500.0,
            success=True
        )
        
        key = "PREPARATION->DECLARATION"
        transition = viz._state_transitions[key]
        assert transition.count == 1
        assert transition.avg_duration_ms == 500.0
    
    def test_room_visualization(self):
        """Test room visualization."""
        viz = StateVisualizationProvider()
        
        # Update room
        viz.update_room_visualization(
            room_id="room123",
            game_id="game456",
            current_state="TURN",
            player_count=4
        )
        
        room = viz._room_visualizations["room123"]
        assert room.game_id == "game456"
        assert room.current_state == "TURN"
        assert room.player_count == 4
    
    def test_visualization_exports(self):
        """Test visualization data exports."""
        viz = StateVisualizationProvider()
        
        # Get state diagram
        diagram = viz.get_state_diagram()
        assert diagram['type'] == 'state_diagram'
        assert 'nodes' in diagram
        assert 'edges' in diagram
        
        # Get room status
        status = viz.get_room_status()
        assert status['type'] == 'room_status'
        assert 'summary' in status
        
        # Get all
        all_viz = viz.get_all_visualizations()
        assert 'state_diagram' in all_viz
        assert 'room_status' in all_viz


class TestPrometheusExporter:
    """Test Prometheus metrics export."""
    
    def test_metrics_export(self):
        """Test basic metrics export."""
        game_metrics = GameMetricsCollector()
        system_metrics = SystemMetricsCollector()
        
        exporter = PrometheusExporter(game_metrics, system_metrics)
        
        # Export metrics
        output = exporter.export_metrics()
        
        # Should contain Prometheus format
        assert "# TYPE" in output
        assert "# HELP" in output
        assert "liap_tui" in output
    
    def test_game_metrics_format(self):
        """Test game metrics formatting."""
        exporter = PrometheusExporter()
        
        # Format game metrics
        lines = exporter._format_game_metrics()
        
        # Should be list of strings
        assert isinstance(lines, list)
    
    def test_system_metrics_format(self):
        """Test system metrics formatting."""
        exporter = PrometheusExporter()
        
        # Format system metrics
        lines = exporter._format_system_metrics()
        
        # Should be list of strings
        assert isinstance(lines, list)


class TestEnterpriseMonitor:
    """Test enterprise monitor integration."""
    
    @pytest.mark.asyncio
    async def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = EnterpriseMonitor(service_name="test")
        
        # Check components
        assert monitor.service_name == "test"
        assert monitor.game_metrics is not None
        assert monitor.system_metrics is not None
        assert monitor.event_stream is not None
        assert monitor.visualization is not None
    
    @pytest.mark.asyncio
    async def test_monitor_state_transition(self):
        """Test monitoring state transition."""
        monitor = configure_enterprise_monitoring(enable_tracing=False)
        
        async with monitor.monitor_state_transition(
            game_id="game123",
            from_state="PREPARATION",
            to_state="DECLARATION"
        ):
            # Simulate transition work
            await asyncio.sleep(0.01)
        
        # Check visualization updated
        node = monitor.visualization._state_nodes["DECLARATION"]
        assert node.active_games == 1
    
    @pytest.mark.asyncio
    async def test_monitor_action_processing(self):
        """Test monitoring action processing."""
        monitor = EnterpriseMonitor(enable_tracing=False)
        
        async with monitor.monitor_action_processing(
            game_id="game123",
            action_type="play_piece",
            player_id="player1"
        ):
            # Simulate action processing
            await asyncio.sleep(0.01)
        
        # Check metrics recorded
        stats = monitor.game_metrics._player_stats.get("player1", {})
        assert stats.get("actions_taken", 0) > 0
    
    @pytest.mark.asyncio
    async def test_monitor_game_lifecycle(self):
        """Test monitoring game lifecycle."""
        monitor = EnterpriseMonitor(enable_tracing=False)
        
        # Start game
        await monitor.record_game_start(
            game_id="game123",
            room_id="room456",
            player_count=4,
            bot_count=0
        )
        
        # End game
        await monitor.record_game_end(
            game_id="game123",
            winner_id="player1",
            final_scores={"player1": 100, "player2": 80}
        )
        
        # Check analytics
        analytics = monitor.game_metrics.get_game_analytics()
        assert analytics['completed_games'] == 1
    
    def test_monitor_status(self):
        """Test monitor status reporting."""
        monitor = EnterpriseMonitor(enable_tracing=False)
        
        status = monitor.get_monitoring_status()
        
        assert status['service_name'] == "liap-tui"
        assert 'collectors' in status
        assert 'event_stream' in status
        assert 'game_analytics' in status
    
    @pytest.mark.asyncio
    async def test_monitor_lifecycle(self):
        """Test monitor start/stop."""
        monitor = EnterpriseMonitor(enable_tracing=False)
        
        # Start
        await monitor.start()
        assert len(monitor._tasks) > 0
        
        # Stop
        await monitor.stop()
        assert len(monitor._tasks) == 0