# backend/tests/api/test_alerts.py
"""
Test alert functionality and slow query detection.
"""

import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.services.alert_service import alert_service, Alert, AlertThreshold
from backend.shared_instances import shared_room_manager
from backend.engine.game import Game
from backend.engine.player import Player

client = TestClient(app)


class TestAlertService:
    """Test the alert service functionality."""

    def setup_method(self):
        """Reset alert service before each test."""
        alert_service.alerts.clear()
        alert_service.last_alert_time.clear()
        alert_service._setup_default_thresholds()

    def test_threshold_configuration(self):
        """Test alert threshold configuration."""
        # Check default thresholds exist
        assert "play_history_slow" in alert_service.thresholds
        assert "play_history_critical" in alert_service.thresholds

        # Test threshold values
        slow_threshold = alert_service.thresholds["play_history_slow"]
        assert slow_threshold.threshold_ms == 1000
        assert slow_threshold.severity == "warning"

        critical_threshold = alert_service.thresholds["play_history_critical"]
        assert critical_threshold.threshold_ms == 3000
        assert critical_threshold.severity == "critical"

    def test_alert_creation(self):
        """Test alert creation for slow responses."""
        # Test below threshold - no alert
        alert = alert_service.check_response_time(
            operation="play_history", duration_ms=500, context={"test": True}
        )
        assert alert is None
        assert len(alert_service.alerts) == 0

        # Test warning threshold
        alert = alert_service.check_response_time(
            operation="play_history", duration_ms=1500, context={"test": True}
        )
        assert alert is not None
        assert alert.severity == "warning"
        assert "1500ms" in alert.message
        assert len(alert_service.alerts) == 1

        # Test critical threshold
        alert = alert_service.check_response_time(
            operation="play_history", duration_ms=3500, context={"test": True}
        )
        assert alert is not None
        assert alert.severity == "critical"
        assert "3500ms" in alert.message
        assert len(alert_service.alerts) == 2

    def test_alert_cooldown(self):
        """Test alert cooldown prevents spam."""
        # First alert should trigger
        alert1 = alert_service.check_response_time(
            operation="play_history", duration_ms=1500, context={"test": True}
        )
        assert alert1 is not None

        # Second alert within cooldown should not trigger
        alert2 = alert_service.check_response_time(
            operation="play_history", duration_ms=1500, context={"test": True}
        )
        assert alert2 is None

        # Only one alert should be stored
        assert len(alert_service.alerts) == 1

    def test_custom_alert(self):
        """Test custom alert creation."""
        alert = alert_service.create_custom_alert(
            alert_type="test_type",
            severity="warning",
            message="Test message",
            context={"custom": True},
        )

        assert alert is not None
        assert alert.alert_type == "test_type"
        assert alert.severity == "warning"
        assert alert.message == "Test message"
        assert alert.context["custom"] is True

    def test_alert_retrieval(self):
        """Test getting recent alerts."""
        # Create alerts at different times
        alert_service.create_custom_alert(
            alert_type="old_alert", severity="warning", message="Old alert", context={}
        )

        # Modify timestamp to make it old
        alert_service.alerts[-1].timestamp = time.time() - 7200  # 2 hours ago

        # Create recent alert
        alert_service.create_custom_alert(
            alert_type="recent_alert",
            severity="critical",
            message="Recent alert",
            context={},
        )

        # Get alerts from last hour
        recent_alerts = alert_service.get_recent_alerts(minutes=60)
        assert len(recent_alerts) == 1
        assert recent_alerts[0]["alert_type"] == "recent_alert"

        # Get all alerts
        all_alerts = alert_service.get_recent_alerts(minutes=180)
        assert len(all_alerts) == 2

    def test_alert_filtering(self):
        """Test alert filtering by severity and type."""
        # Create various alerts
        alert_service.create_custom_alert("type1", "warning", "msg1", {})
        alert_service.create_custom_alert("type1", "critical", "msg2", {})
        alert_service.create_custom_alert("type2", "warning", "msg3", {})

        # Filter by severity
        warnings = alert_service.get_recent_alerts(severity="warning")
        assert len(warnings) == 2

        criticals = alert_service.get_recent_alerts(severity="critical")
        assert len(criticals) == 1

        # Filter by type
        type1_alerts = alert_service.get_recent_alerts(alert_type="type1")
        assert len(type1_alerts) == 2

    def test_alert_summary(self):
        """Test alert summary generation."""
        # Create some alerts
        alert_service.create_custom_alert("type1", "warning", "msg1", {})
        alert_service.create_custom_alert("type1", "critical", "msg2", {})
        alert_service.create_custom_alert("type2", "warning", "msg3", {})

        summary = alert_service.get_alert_summary()

        assert summary["total_alerts"] == 3
        assert summary["last_hour"]["total"] == 3
        assert summary["last_hour"]["warning"] == 2
        assert summary["last_hour"]["critical"] == 1
        assert summary["last_hour"]["by_type"]["type1"] == 2
        assert summary["last_hour"]["by_type"]["type2"] == 1


class TestAlertEndpoints:
    """Test alert API endpoints."""

    def setup_method(self):
        """Reset alerts before each test."""
        alert_service.alerts.clear()
        alert_service.last_alert_time.clear()

    def test_get_alerts_endpoint(self):
        """Test GET /api/alerts endpoint."""
        # Create test alerts
        alert_service.create_custom_alert("test", "warning", "Test alert", {})

        response = client.get("/api/alerts")
        assert response.status_code == 200
        data = response.json()

        assert "alerts" in data
        assert "count" in data
        assert data["count"] == 1
        assert data["alerts"][0]["alert_type"] == "test"

    def test_get_alerts_with_filters(self):
        """Test alert filtering via API."""
        # Create alerts
        alert_service.create_custom_alert("type1", "warning", "msg1", {})
        alert_service.create_custom_alert("type2", "critical", "msg2", {})

        # Filter by severity
        response = client.get("/api/alerts?severity=warning")
        data = response.json()
        assert data["count"] == 1
        assert data["alerts"][0]["severity"] == "warning"

        # Filter by type
        response = client.get("/api/alerts?alert_type=type2")
        data = response.json()
        assert data["count"] == 1
        assert data["alerts"][0]["alert_type"] == "type2"

    def test_alerts_summary_endpoint(self):
        """Test GET /api/alerts/summary endpoint."""
        # Create alerts
        alert_service.create_custom_alert("test", "warning", "msg", {})

        response = client.get("/api/alerts/summary")
        assert response.status_code == 200
        data = response.json()

        assert "total_alerts" in data
        assert "last_hour" in data
        assert "last_24h" in data
        assert "thresholds" in data

    def test_test_alert_endpoint(self):
        """Test POST /api/alerts/test endpoint."""
        # Test custom alert
        response = client.post("/api/alerts/test?severity=warning&message=Test")
        assert response.status_code == 200
        data = response.json()

        assert data["alert_triggered"] is True
        assert data["alert"]["severity"] == "warning"
        assert data["alert"]["message"] == "Test"

        # Test response time alert
        response = client.post("/api/alerts/test?duration_ms=1500")
        assert response.status_code == 200
        data = response.json()

        assert data["alert_triggered"] is True
        assert "1500" in data["message"]


class TestPlayHistoryAlerts:
    """Test alert integration with play history endpoints."""

    def setup_method(self):
        """Setup test data and reset alerts."""
        alert_service.alerts.clear()
        alert_service.last_alert_time.clear()

    async def create_test_room_with_game(self):
        """Create a test room with a game."""
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]

        room_id = await shared_room_manager.create_room("Bot 1")
        room = await shared_room_manager.get_room(room_id)
        room.game = Game(players)
        room.game.round_number = 1
        room.game.current_phase = "SCORING"

        return room_id

    @patch(
        "backend.services.play_history_service.PlayHistoryService.build_play_history"
    )
    def test_slow_query_alert(self, mock_build):
        """Test that slow play history queries trigger alerts."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create room
        room_id = loop.run_until_complete(self.create_test_room_with_game())

        # Mock slow response with proper attributes
        from backend.models.play_history import PlayHistoryResponse

        mock_response = PlayHistoryResponse(
            room_id=room_id,
            total_rounds=10,
            rounds=[],
            players={},  # Empty dict for players
        )

        # Add artificial delay to trigger alert
        def slow_build(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            return mock_response

        mock_build.side_effect = slow_build

        # Override threshold for testing
        alert_service.thresholds["play_history_slow"].threshold_ms = 50

        # Make request
        response = client.get(f"/api/rooms/{room_id}/play-history")
        assert response.status_code == 200

        # Check that alert was triggered
        assert len(alert_service.alerts) == 1
        alert = alert_service.alerts[0]
        assert alert.alert_type == "play_history_slow_response"
        assert alert.severity == "warning"
        assert room_id in alert.context["room_id"]

    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(shared_room_manager, "rooms"):
            shared_room_manager.rooms.clear()
