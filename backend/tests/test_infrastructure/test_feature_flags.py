"""
Tests for the feature flags system.
"""

import pytest
from unittest.mock import Mock, patch
import json
from typing import Dict, Any

from infrastructure.feature_flags import (
    FeatureFlagManager,
    FeatureFlags,
    FlagEvaluationContext,
)


class TestFeatureFlagManager:
    """Test feature flag manager functionality."""

    def test_initialization_with_defaults(self):
        """Test that manager initializes with default flags."""
        manager = FeatureFlagManager()

        # Check some default flags
        assert FeatureFlags.USE_CLEAN_ARCHITECTURE in manager._flags
        assert FeatureFlags.USE_DOMAIN_EVENTS in manager._flags
        assert FeatureFlags.USE_APPLICATION_LAYER in manager._flags

    def test_initialization_from_config(self):
        """Test initialization from configuration."""
        config = {
            FeatureFlags.USE_CLEAN_ARCHITECTURE: {"enabled": True, "percentage": 50},
            "custom_flag": {"enabled": False},
        }

        manager = FeatureFlagManager(config)

        # Check configured flags
        assert manager._flags[FeatureFlags.USE_CLEAN_ARCHITECTURE]["percentage"] == 50
        assert manager._flags["custom_flag"]["enabled"] is False

    def test_simple_boolean_flag(self):
        """Test simple boolean flag evaluation."""
        manager = FeatureFlagManager({"test_flag": {"enabled": True}})

        assert manager.is_enabled("test_flag") is True

        manager._flags["test_flag"]["enabled"] = False
        assert manager.is_enabled("test_flag") is False

    def test_percentage_based_flag(self):
        """Test percentage-based flag evaluation."""
        manager = FeatureFlagManager({"test_flag": {"enabled": True, "percentage": 50}})

        # Mock the hash function to control results
        with patch.object(manager, "_get_hash_for_context") as mock_hash:
            # Hash below threshold - should be enabled
            mock_hash.return_value = 25
            assert manager.is_enabled("test_flag", {"user_id": "user1"}) is True

            # Hash above threshold - should be disabled
            mock_hash.return_value = 75
            assert manager.is_enabled("test_flag", {"user_id": "user1"}) is False

    def test_whitelist_evaluation(self):
        """Test whitelist-based flag evaluation."""
        manager = FeatureFlagManager(
            {"test_flag": {"enabled": False, "whitelist": ["user1", "user2"]}}
        )

        # Whitelisted user
        assert manager.is_enabled("test_flag", {"user_id": "user1"}) is True

        # Non-whitelisted user
        assert manager.is_enabled("test_flag", {"user_id": "user3"}) is False

    def test_blacklist_evaluation(self):
        """Test blacklist-based flag evaluation."""
        manager = FeatureFlagManager(
            {"test_flag": {"enabled": True, "blacklist": ["user1", "user2"]}}
        )

        # Blacklisted user
        assert manager.is_enabled("test_flag", {"user_id": "user1"}) is False

        # Non-blacklisted user
        assert manager.is_enabled("test_flag", {"user_id": "user3"}) is True

    def test_evaluation_context_creation(self):
        """Test evaluation context creation from different inputs."""
        manager = FeatureFlagManager()

        # Dict context
        ctx = manager._create_evaluation_context(
            {"user_id": "user1", "room_id": "room1"}
        )
        assert ctx.user_id == "user1"
        assert ctx.room_id == "room1"

        # FlagEvaluationContext
        eval_ctx = FlagEvaluationContext(user_id="user2")
        ctx = manager._create_evaluation_context(eval_ctx)
        assert ctx.user_id == "user2"

        # None context
        ctx = manager._create_evaluation_context(None)
        assert ctx.user_id is None

    def test_consistent_hashing(self):
        """Test that hashing is consistent for same input."""
        manager = FeatureFlagManager()

        # Same context should produce same hash
        ctx1 = FlagEvaluationContext(user_id="user1", session_id="session1")
        ctx2 = FlagEvaluationContext(user_id="user1", session_id="session1")

        hash1 = manager._get_hash_for_context("test_flag", ctx1)
        hash2 = manager._get_hash_for_context("test_flag", ctx2)

        assert hash1 == hash2

        # Different context should produce different hash
        ctx3 = FlagEvaluationContext(user_id="user2", session_id="session1")
        hash3 = manager._get_hash_for_context("test_flag", ctx3)

        assert hash1 != hash3

    def test_override_flags(self):
        """Test overriding flags at runtime."""
        manager = FeatureFlagManager({"test_flag": {"enabled": False}})

        assert manager.is_enabled("test_flag") is False

        # Override the flag
        manager.override_flag("test_flag", {"enabled": True})
        assert manager.is_enabled("test_flag") is True

    def test_get_all_flags(self):
        """Test getting all flag configurations."""
        config = {
            "flag1": {"enabled": True},
            "flag2": {"enabled": False, "percentage": 30},
        }
        manager = FeatureFlagManager(config)

        all_flags = manager.get_all_flags()

        assert "flag1" in all_flags
        assert "flag2" in all_flags
        assert all_flags["flag1"]["enabled"] is True
        assert all_flags["flag2"]["percentage"] == 30

    def test_complex_evaluation_rules(self):
        """Test complex evaluation with multiple rules."""
        manager = FeatureFlagManager(
            {
                "complex_flag": {
                    "enabled": True,
                    "percentage": 60,
                    "whitelist": ["special_user"],
                    "blacklist": ["banned_user"],
                }
            }
        )

        # Whitelisted user - always enabled
        assert manager.is_enabled("complex_flag", {"user_id": "special_user"}) is True

        # Blacklisted user - always disabled
        assert manager.is_enabled("complex_flag", {"user_id": "banned_user"}) is False

        # Regular user - depends on percentage
        with patch.object(manager, "_get_hash_for_context") as mock_hash:
            mock_hash.return_value = 50  # Below 60% threshold
            assert (
                manager.is_enabled("complex_flag", {"user_id": "regular_user"}) is True
            )

            mock_hash.return_value = 70  # Above 60% threshold
            assert (
                manager.is_enabled("complex_flag", {"user_id": "regular_user"}) is False
            )

    def test_missing_flag_defaults_to_disabled(self):
        """Test that missing flags default to disabled."""
        manager = FeatureFlagManager()

        assert manager.is_enabled("non_existent_flag") is False

    def test_environment_variable_override(self):
        """Test that environment variables can override flags."""
        with patch.dict(
            "os.environ", {"FEATURE_FLAGS": json.dumps({"env_flag": {"enabled": True}})}
        ):
            manager = FeatureFlagManager()

            # Should pick up flag from environment
            assert manager.is_enabled("env_flag") is True

    def test_gradual_rollout_simulation(self):
        """Test gradual rollout by increasing percentage."""
        manager = FeatureFlagManager(
            {"rollout_flag": {"enabled": True, "percentage": 0}}
        )

        # Simulate 100 users
        users_enabled = []
        for i in range(100):
            user_id = f"user_{i}"
            if manager.is_enabled("rollout_flag", {"user_id": user_id}):
                users_enabled.append(user_id)

        # At 0%, no users should be enabled
        assert len(users_enabled) == 0

        # Increase to 50%
        manager.override_flag("rollout_flag", {"enabled": True, "percentage": 50})
        users_enabled = []
        for i in range(100):
            user_id = f"user_{i}"
            if manager.is_enabled("rollout_flag", {"user_id": user_id}):
                users_enabled.append(user_id)

        # Roughly 50% should be enabled (with some variance)
        assert 35 <= len(users_enabled) <= 65

        # Increase to 100%
        manager.override_flag("rollout_flag", {"enabled": True, "percentage": 100})
        users_enabled = []
        for i in range(100):
            user_id = f"user_{i}"
            if manager.is_enabled("rollout_flag", {"user_id": user_id}):
                users_enabled.append(user_id)

        # All users should be enabled
        assert len(users_enabled) == 100


class TestFeatureFlags:
    """Test the FeatureFlags constants."""

    def test_flag_naming_convention(self):
        """Test that all flags follow naming convention."""
        # Get all flag constants
        flags = [
            attr
            for attr in dir(FeatureFlags)
            if not attr.startswith("_") and isinstance(getattr(FeatureFlags, attr), str)
        ]

        for flag_attr in flags:
            flag_value = getattr(FeatureFlags, flag_attr)
            # Flag value should be lowercase with underscores
            assert flag_value.islower() or "_" in flag_value
            # Flag attribute should be uppercase
            assert flag_attr.isupper()

    def test_no_duplicate_flag_values(self):
        """Test that all flag values are unique."""
        flags = [
            getattr(FeatureFlags, attr)
            for attr in dir(FeatureFlags)
            if not attr.startswith("_") and isinstance(getattr(FeatureFlags, attr), str)
        ]

        # Check for duplicates
        assert len(flags) == len(set(flags))
