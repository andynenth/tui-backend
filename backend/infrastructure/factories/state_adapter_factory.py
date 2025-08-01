"""
Factory for creating StateManagementAdapter instances.

This factory centralizes the creation of state adapters based on
feature flags and dependency injection.
"""

import logging
from typing import Optional, Dict, Any

from infrastructure.feature_flags import get_feature_flags
from infrastructure.dependencies import get_state_persistence_manager
from application.adapters.state_management_adapter import StateManagementAdapter
from infrastructure.config.state_management_config import (
    get_use_case_config,
    get_current_rollout_phase,
    StateManagementMode
)

logger = logging.getLogger(__name__)


class StateAdapterFactory:
    """
    Factory for creating state management adapters.
    
    This factory checks feature flags and creates the appropriate
    adapter instance or returns None when state management is disabled.
    """
    
    @staticmethod
    def create(context: Optional[Dict[str, Any]] = None) -> Optional[StateManagementAdapter]:
        """
        Create a state management adapter if enabled.
        
        Args:
            context: Optional context for feature flag evaluation
            
        Returns:
            StateManagementAdapter if enabled, None otherwise
        """
        feature_flags = get_feature_flags()
        
        # Check if state persistence is enabled
        if not feature_flags.is_enabled("USE_STATE_PERSISTENCE", context or {}):
            logger.debug("State persistence disabled by feature flag")
            return None
        
        try:
            # Get state persistence manager from DI container
            state_manager = get_state_persistence_manager()
            
            if not state_manager:
                logger.warning("State persistence enabled but no manager available")
                return None
            
            # Create and return adapter
            adapter = StateManagementAdapter(state_manager=state_manager)
            logger.info("Created StateManagementAdapter")
            return adapter
            
        except Exception as e:
            logger.error(f"Failed to create StateManagementAdapter: {e}")
            return None
    
    @staticmethod
    def create_for_use_case(
        use_case_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[StateManagementAdapter]:
        """
        Create a state adapter for a specific use case.
        
        This allows per-use-case configuration of state management.
        
        Args:
            use_case_name: Name of the use case
            context: Optional context for feature flag evaluation
            
        Returns:
            StateManagementAdapter if enabled for this use case, None otherwise
        """
        # First check global flag
        adapter = StateAdapterFactory.create(context)
        if not adapter:
            return None
        
        # Check use-case specific configuration
        config = get_use_case_config(use_case_name)
        
        if not config.enabled:
            logger.debug(f"State persistence disabled for {use_case_name}")
            return None
        
        # Apply use case configuration to adapter
        # This would need to be implemented in StateManagementAdapter
        # For now, just log the configuration
        logger.info(
            f"Created adapter for {use_case_name} with config: "
            f"track_actions={config.track_actions}, "
            f"create_snapshots={config.create_snapshots}"
        )
        
        return adapter
    
    @staticmethod
    def create_with_config(
        context: Optional[Dict[str, Any]] = None,
        track_actions: bool = True,
        create_snapshots: bool = False,
        validate_transitions: bool = True
    ) -> Optional[StateManagementAdapter]:
        """
        Create a state adapter with custom configuration.
        
        Args:
            context: Optional context for feature flag evaluation
            track_actions: Whether to track player actions
            create_snapshots: Whether to create automatic snapshots
            validate_transitions: Whether to validate phase transitions
            
        Returns:
            Configured StateManagementAdapter or None
        """
        adapter = StateAdapterFactory.create(context)
        if not adapter:
            return None
        
        # Apply custom configuration
        # This would need to be implemented in StateManagementAdapter
        # For now, just return the adapter
        return adapter