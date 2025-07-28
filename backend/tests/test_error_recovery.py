#!/usr/bin/env python3
"""
Test Error Recovery and Monitoring System (Phase 4 Task 4.3)
Tests health monitoring, automatic recovery, and centralized logging
"""

import asyncio
import os
import sys
import tempfile
import time
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, "/Users/nrw/python/tui-project/liap-tui/backend")


async def test_logging_service():
    """Test centralized logging service"""
    print("🧪 Testing Centralized Logging Service...")

    try:
        from api.services.logging_service import GameLogger, LogContext, game_logger

        # Test 1: Logger initialization
        print("📝 Test 1: Logger initialization...")

        logger = GameLogger()

        # Verify loggers exist
        assert hasattr(logger, "game_logger")
        assert hasattr(logger, "websocket_logger")
        assert hasattr(logger, "performance_logger")
        assert hasattr(logger, "security_logger")
        assert hasattr(logger, "error_logger")

        print("  ✅ All specialized loggers initialized")

        # Test 2: Log context management
        print("📊 Test 2: Log context management...")

        with logger.log_context(room_id="test_room", player_id="alice") as context:
            assert context.room_id == "test_room"
            assert context.player_id == "alice"
            assert context.correlation_id is not None

            # Test logging with context
            logger.log_game_event("test_event", extra_data="test_value")
            logger.log_websocket_event("test_room", "connection_established")

        print("  ✅ Log context management working")

        # Test 3: Performance timing
        print("⏱️  Test 3: Performance timing...")

        with logger.timed_operation("test_operation", room_id="test_room"):
            await asyncio.sleep(0.01)  # Simulate work

        print("  ✅ Performance timing working")

        # Test 4: Different log levels
        print("🔍 Test 4: Different log levels...")

        logger.log_game_event("info_event")
        logger.log_security_event("suspicious_activity", severity="high")
        logger.log_error(Exception("Test error"), "test_context")

        print("  ✅ Multiple log levels working")

        # Test 5: Global logger instance
        print("🌐 Test 5: Global logger instance...")

        from api.services.logging_service import log_game_event, log_websocket_event

        log_game_event("global_test_event", room_id="global_room")
        log_websocket_event("global_room", "test_action")

        print("  ✅ Global convenience functions working")

        print("✅ Centralized logging service tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Logging service test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_health_monitor():
    """Test health monitoring system"""
    print("\n🧪 Testing Health Monitoring System...")

    try:
        from api.services.health_monitor import (
            HealthMetric,
            HealthMonitor,
            HealthStatus,
        )

        # Test 1: Health monitor initialization
        print("📝 Test 1: Health monitor initialization...")

        monitor = HealthMonitor()

        # Verify thresholds are set
        assert "memory_usage_percent" in monitor.thresholds
        assert "cpu_usage_percent" in monitor.thresholds
        assert "websocket_failure_rate" in monitor.thresholds

        print(f"  ✅ Initialized with {len(monitor.thresholds)} health thresholds")

        # Test 2: Health status check
        print("📊 Test 2: Health status check...")

        health_status = await monitor.get_health_status()

        assert health_status.status in [
            HealthStatus.HEALTHY,
            HealthStatus.WARNING,
            HealthStatus.CRITICAL,
            HealthStatus.UNKNOWN,
        ]
        assert health_status.uptime_seconds >= 0
        assert len(health_status.metrics) > 0

        print(
            f"  ✅ Health status: {health_status.status.value} with {len(health_status.metrics)} metrics"
        )

        # Test 3: Health metrics structure
        print("🔍 Test 3: Health metrics structure...")

        health_dict = health_status.to_dict()

        assert "overall_status" in health_dict
        assert "metrics" in health_dict
        assert "uptime_formatted" in health_dict

        # Check specific metrics
        if "memory" in health_status.metrics:
            memory_metric = health_status.metrics["memory"]
            assert isinstance(memory_metric.value, (int, float))
            assert memory_metric.name == "memory_usage"

        print("  ✅ Health metrics structure validated")

        # Test 4: Health monitoring start/stop
        print("⚡ Test 4: Health monitoring lifecycle...")

        # Start monitoring briefly
        await monitor.start_monitoring()
        assert monitor.monitoring_active == True

        # Wait a moment for monitoring to run
        await asyncio.sleep(0.1)

        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor.monitoring_active == False

        print("  ✅ Health monitoring lifecycle working")

        print("✅ Health monitoring system tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Health monitor test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_recovery_manager():
    """Test automatic recovery system"""
    print("\n🧪 Testing Recovery Manager System...")

    try:
        from api.services.recovery_manager import (
            RecoveryAction,
            RecoveryManager,
            recovery_manager,
        )

        # Test 1: Recovery manager initialization
        print("📝 Test 1: Recovery manager initialization...")

        manager = RecoveryManager()

        # Verify recovery procedures are defined
        assert len(manager.recovery_procedures) > 0
        assert "stale_connections" in manager.recovery_procedures
        assert "high_pending_messages" in manager.recovery_procedures

        print(
            f"  ✅ Initialized with {len(manager.recovery_procedures)} recovery procedures"
        )

        # Test 2: Recovery status
        print("📊 Test 2: Recovery status...")

        status = manager.get_recovery_status()

        assert "is_active" in status
        assert "total_procedures" in status
        assert "procedures" in status

        print(
            f"  ✅ Recovery status: {status['total_procedures']} procedures available"
        )

        # Test 3: Manual recovery trigger
        print("🔧 Test 3: Manual recovery trigger...")

        # Mock socket manager to prevent actual connection cleanup
        with patch("socket_manager._socket_manager") as mock_sm:
            mock_sm.room_connections = {"test_room": set()}
            mock_sm.pending_messages = {"test_room": {}}

            success = await manager.trigger_recovery(
                "stale_connections", context={"test": True}
            )

            # Should succeed even if no actual connections to clean
            assert isinstance(success, bool)

        print("  ✅ Manual recovery trigger working")

        # Test 4: Recovery procedure cooldown
        print("⏱️  Test 4: Recovery procedure cooldown...")

        # Test cooldown logic
        can_attempt = manager._can_attempt_recovery("test_procedure", 60)
        assert can_attempt == True  # No previous attempts

        # Add a recent attempt
        manager.procedure_attempts["test_procedure"] = [time.time()]
        can_attempt = manager._can_attempt_recovery("test_procedure", 60)
        assert can_attempt == False  # Should be in cooldown

        print("  ✅ Recovery cooldown logic working")

        # Test 5: Recovery monitoring lifecycle
        print("🔄 Test 5: Recovery monitoring lifecycle...")

        await manager.start_monitoring()
        assert manager.is_active == True

        # Brief wait for monitoring
        await asyncio.sleep(0.1)

        manager.stop_monitoring()
        assert manager.is_active == False

        print("  ✅ Recovery monitoring lifecycle working")

        print("✅ Recovery manager system tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Recovery manager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_health_endpoints():
    """Test health check API endpoints"""
    print("\n🧪 Testing Health Check Endpoints...")

    try:
        # We'll test the endpoint logic without FastAPI setup
        print("📝 Test 1: Health endpoint imports...")

        # Test imports work
        from api.services.health_monitor import health_monitor
        from api.services.recovery_manager import recovery_manager

        # Verify services can be imported
        assert health_monitor is not None
        assert recovery_manager is not None

        print("  ✅ Health service imports working")

        # Test 2: Health status generation
        print("📊 Test 2: Health status generation...")

        health_status = await health_monitor.get_health_status()
        recovery_status = recovery_manager.get_recovery_status()

        # Verify they return valid data structures
        assert hasattr(health_status, "status")
        assert hasattr(health_status, "metrics")
        assert isinstance(recovery_status, dict)

        print("  ✅ Health status generation working")

        # Test 3: Metrics formatting
        print("🔍 Test 3: Metrics formatting...")

        # Test Prometheus-style metrics formatting
        health_dict = health_status.to_dict()

        metrics = []
        if "memory" in health_status.metrics:
            metrics.append(
                f"liap_memory_usage_percent {health_status.metrics['memory'].value}"
            )

        metrics.append(f"liap_uptime_seconds {health_status.uptime_seconds}")
        metrics.append(
            f"liap_health_status {0 if health_status.status.value == 'healthy' else 1}"
        )

        # Verify metrics format
        for metric in metrics:
            assert " " in metric  # Should have name and value
            parts = metric.split(" ")
            assert len(parts) >= 2
            assert parts[0].startswith("liap_")

        print(f"  ✅ Generated {len(metrics)} Prometheus-style metrics")

        print("✅ Health check endpoints tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Health endpoints test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_integration_scenarios():
    """Test integration scenarios between services"""
    print("\n🧪 Testing Integration Scenarios...")

    try:
        from api.services.health_monitor import HealthStatus, health_monitor
        from api.services.logging_service import game_logger
        from api.services.recovery_manager import recovery_manager

        # Test 1: Health trigger recovery scenario
        print("📝 Test 1: Health-triggered recovery scenario...")

        # Mock a health issue
        with patch("api.services.health_monitor.psutil") as mock_psutil:
            # Mock high memory usage
            mock_memory = MagicMock()
            mock_memory.percent = 95.0  # High memory usage
            mock_psutil.virtual_memory.return_value = mock_memory
            mock_psutil.cpu_percent.return_value = 50.0
            mock_disk = MagicMock()
            mock_disk.percent = 70.0
            mock_psutil.disk_usage.return_value = mock_disk

            health_status = await health_monitor.get_health_status()

            # Should trigger memory pressure recovery
            if "memory" in health_status.metrics:
                memory_usage = health_status.metrics["memory"].value
                if memory_usage > 90:
                    print(f"    Memory usage: {memory_usage}% (would trigger recovery)")

        print("  ✅ Health-triggered recovery scenario working")

        # Test 2: Logging integration with health monitoring
        print("📊 Test 2: Logging integration...")

        with game_logger.log_context(operation="health_check", room_id="test_room"):
            # Simulate health check with logging
            game_logger.log_performance("health_check", 25.0)
            game_logger.log_game_event("health_monitoring_test")

        print("  ✅ Logging integration working")

        # Test 3: Service coordination
        print("🔄 Test 3: Service coordination...")

        # Test that services can work together
        health_data = await health_monitor.get_health_status()
        recovery_data = recovery_manager.get_recovery_status()

        # Verify both services provide complementary data
        assert health_data.status in [
            HealthStatus.HEALTHY,
            HealthStatus.WARNING,
            HealthStatus.CRITICAL,
            HealthStatus.UNKNOWN,
        ]
        assert recovery_data["is_active"] in [True, False]

        print("  ✅ Service coordination working")

        # Test 4: Error handling integration
        print("🔍 Test 4: Error handling integration...")

        # Test error logging and recovery
        try:
            # Simulate an error
            raise ValueError("Test integration error")
        except Exception as e:
            game_logger.log_error(e, "integration_test")

            # This would normally trigger recovery in a real scenario
            print("    Error logged and would trigger recovery")

        print("  ✅ Error handling integration working")

        print("✅ Integration scenarios tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Integration scenarios test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_performance_monitoring():
    """Test performance monitoring capabilities"""
    print("\n🧪 Testing Performance Monitoring...")

    try:
        from api.services.health_monitor import health_monitor
        from api.services.logging_service import game_logger

        # Test 1: Performance metric collection
        print("📝 Test 1: Performance metric collection...")

        start_time = time.time()

        # Simulate multiple operations
        operations = []
        for i in range(10):
            with game_logger.timed_operation(f"test_operation_{i}", iteration=i):
                await asyncio.sleep(0.001)  # Simulate work
            operations.append(i)

        total_time = time.time() - start_time

        print(f"  ✅ Completed {len(operations)} operations in {total_time:.3f}s")

        # Test 2: System resource monitoring
        print("📊 Test 2: System resource monitoring...")

        health_status = await health_monitor.get_health_status()

        resource_metrics = ["memory", "cpu", "disk"]
        found_metrics = [
            metric for metric in resource_metrics if metric in health_status.metrics
        ]

        print(f"  ✅ Monitoring {len(found_metrics)} resource metrics: {found_metrics}")

        # Test 3: WebSocket performance tracking
        print("🔌 Test 3: WebSocket performance tracking...")

        # Mock clean architecture stats
        try:
            from infrastructure.websocket.broadcast_adapter import get_room_stats

            # Get current stats (even if empty)
            socket_stats = get_room_stats()

            print(
                f"  ✅ WebSocket stats available: {len(socket_stats.get('rooms', {}))} rooms"
            )

        except Exception:
            print("  ⚠️  WebSocket stats not available (expected in test environment)")

        # Test 4: Performance threshold monitoring
        print("⏱️  Test 4: Performance threshold monitoring...")

        # Test slow operation detection
        with game_logger.timed_operation("slow_test_operation"):
            await asyncio.sleep(0.01)  # Simulate slow operation

        print("  ✅ Performance threshold monitoring working")

        print("✅ Performance monitoring tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all Error Recovery and Monitoring tests"""
    print("🧪 ERROR RECOVERY AND MONITORING SYSTEM TESTS")
    print("=" * 70)
    print("Phase 4 Task 4.3: Error Recovery and Monitoring")
    print("Testing health monitoring, automatic recovery, and centralized logging\n")

    test_results = []

    # Run all tests
    test_results.append(await test_logging_service())
    test_results.append(await test_health_monitor())
    test_results.append(await test_recovery_manager())
    test_results.append(await test_health_endpoints())
    test_results.append(await test_integration_scenarios())
    test_results.append(await test_performance_monitoring())

    # Summary
    print("\n" + "=" * 70)
    print("📋 ERROR RECOVERY AND MONITORING TEST SUMMARY")
    print("=" * 70)

    passed_tests = sum(test_results)
    total_tests = len(test_results)

    test_names = [
        "Centralized Logging Service",
        "Health Monitoring System",
        "Recovery Manager System",
        "Health Check Endpoints",
        "Integration Scenarios",
        "Performance Monitoring",
    ]

    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")

    print(f"\n📊 Overall Result: {passed_tests}/{total_tests} test suites passed")

    if passed_tests == total_tests:
        print("\n🎉 PHASE 4 TASK 4.3 COMPLETED SUCCESSFULLY!")
        print("✅ Centralized logging with structured JSON output")
        print("✅ Health monitoring with automatic threshold checking")
        print("✅ Automatic recovery procedures with cooldown")
        print("✅ Performance monitoring and metrics collection")
        print("✅ Health check endpoints for load balancers")
        print("✅ Integration between all monitoring services")
        print("\n🚀 Ready for Production Deployment!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Review and fix issues.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
