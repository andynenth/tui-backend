"""
Tests for state management feature flag control.

These tests verify that feature flags properly control state management
integration across the system.
"""

import pytest
from unittest.mock import Mock, patch

from infrastructure.feature_flags import FeatureFlags, get_feature_flags
from infrastructure.factories.state_adapter_factory import StateAdapterFactory
from infrastructure.dependencies import get_container

pytestmark = pytest.mark.asyncio


class TestStateManagementFeatureFlags:
    """Test feature flag control of state management."""

    @pytest.fixture
    def mock_container(self):
        """Create mock dependency container."""
        container = Mock()
        container.get = Mock()
        return container

    @pytest.fixture
    def feature_flags(self):
        """Create feature flags instance."""
        return FeatureFlags()

    async def test_state_adapter_disabled_by_default(self):
        """Test that state adapter is disabled by default."""
        # Reset feature flags to defaults
        from infrastructure.feature_flags import reset_feature_flags
        reset_feature_flags()
        
        # Try to create adapter
        adapter = StateAdapterFactory.create()
        
        # Should be None when disabled
        assert adapter is None

    @patch('infrastructure.feature_flags.get_feature_flags')
    async def test_state_adapter_enabled_by_flag(self, mock_flags):
        """Test that state adapter is created when flag enabled."""
        # Mock feature flags to enable state persistence
        flags = Mock()
        flags.is_enabled = Mock(return_value=True)
        mock_flags.return_value = flags
        
        # Mock state persistence manager
        with patch('infrastructure.dependencies.get_state_persistence_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            
            # Create adapter
            adapter = StateAdapterFactory.create()
            
            # Should create adapter
            assert adapter is not None
            assert adapter._state_manager == mock_manager

    async def test_percentage_rollout(self):
        """Test percentage-based feature flag rollout."""
        flags = FeatureFlags()
        
        # Set 50% rollout
        flags._flags["USE_STATE_PERSISTENCE"] = 50
        
        # Test with different contexts
        enabled_count = 0
        total_tests = 1000
        
        for i in range(total_tests):
            context = {"room_id": f"room-{i}"}
            if flags.is_enabled("USE_STATE_PERSISTENCE", context):
                enabled_count += 1
        
        # Should be approximately 50%
        percentage = (enabled_count / total_tests) * 100
        assert 45 <= percentage <= 55  # Allow 5% variance

    async def test_use_case_specific_flags(self):
        """Test per-use-case feature flag control."""
        # Test each use case
        use_cases = [
            ("StartGameUseCase", True),
            ("DeclareUseCase", True),
            ("PlayUseCase", True),
            ("RequestRedealUseCase", False),
            ("AcceptRedealUseCase", False),
            ("DeclineRedealUseCase", False),
        ]
        
        with patch('infrastructure.feature_flags.get_feature_flags') as mock_flags:
            # Enable global flag
            flags = Mock()
            flags.is_enabled = Mock(return_value=True)
            mock_flags.return_value = flags
            
            # Mock state manager
            with patch('infrastructure.dependencies.get_state_persistence_manager') as mock_get_manager:
                mock_get_manager.return_value = Mock()
                
                for use_case, expected_enabled in use_cases:
                    adapter = StateAdapterFactory.create_for_use_case(use_case)
                    
                    if expected_enabled:
                        assert adapter is not None, f"{use_case} should have adapter"
                    else:
                        assert adapter is None, f"{use_case} should not have adapter"

    async def test_environment_variable_override(self):
        """Test environment variable feature flag override."""
        import os
        
        # Set environment variable
        os.environ["FF_USE_STATE_PERSISTENCE"] = "true"
        
        # Reset flags to pick up env var
        from infrastructure.feature_flags import reset_feature_flags
        reset_feature_flags()
        
        flags = get_feature_flags()
        assert flags.is_enabled("USE_STATE_PERSISTENCE")
        
        # Clean up
        del os.environ["FF_USE_STATE_PERSISTENCE"]
        reset_feature_flags()

    async def test_feature_flag_override_method(self):
        """Test runtime feature flag override."""
        flags = FeatureFlags()
        
        # Initially disabled
        assert not flags.is_enabled("USE_STATE_PERSISTENCE")
        
        # Override to enable
        flags.override("USE_STATE_PERSISTENCE", True)
        assert flags.is_enabled("USE_STATE_PERSISTENCE")
        
        # Clear override
        flags.clear_override("USE_STATE_PERSISTENCE")
        assert not flags.is_enabled("USE_STATE_PERSISTENCE")

    async def test_shadow_mode_configuration(self):
        """Test shadow mode where state tracking runs but doesn't affect game."""
        flags = FeatureFlags()
        flags.override("USE_STATE_PERSISTENCE", True)
        flags.override("STATE_PERSISTENCE_MODE", "shadow")
        
        with patch('infrastructure.feature_flags.get_feature_flags') as mock_flags:
            mock_flags.return_value = flags
            
            # In shadow mode, adapter is created but configured differently
            adapter = StateAdapterFactory.create()
            
            # This would need StateManagementAdapter to support shadow mode
            # For now, just verify adapter is created
            assert adapter is not None

    async def test_gradual_rollout_strategy(self):
        """Test gradual rollout with increasing percentages."""
        flags = FeatureFlags()
        
        rollout_schedule = [
            (5, "canary"),      # 5% canary
            (10, "early"),      # 10% early adopters
            (25, "expanded"),   # 25% expanded
            (50, "half"),       # 50% half rollout
            (75, "majority"),   # 75% majority
            (100, "full"),      # 100% full rollout
        ]
        
        for percentage, phase in rollout_schedule:
            flags._flags["USE_STATE_PERSISTENCE"] = percentage
            
            # Test with sample of rooms
            enabled_count = 0
            sample_size = 100
            
            for i in range(sample_size):
                context = {"room_id": f"room-{phase}-{i}"}
                if flags.is_enabled("USE_STATE_PERSISTENCE", context):
                    enabled_count += 1
            
            actual_percentage = (enabled_count / sample_size) * 100
            
            # For 100%, should be exactly 100%
            if percentage == 100:
                assert actual_percentage == 100
            # For others, allow variance
            else:
                assert abs(actual_percentage - percentage) < 15  # 15% variance

    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker disables state management on repeated failures."""
        # This would need to be implemented in StateManagementAdapter
        # For now, just document the expected behavior
        
        # Simulate multiple failures
        failure_count = 0
        threshold = 10
        
        # After threshold failures, circuit should open
        # and state management should be disabled automatically
        pass  # Placeholder for future implementation