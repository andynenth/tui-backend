"""
Migration from v2 to v3 state schema.

Example migration that adds event history and performance metrics.
"""

from typing import Dict, Any, List
import logging
from datetime import datetime

from ..versioning import StateMigration
from ..abstractions import StateVersion


logger = logging.getLogger(__name__)


class V2ToV3Migration(StateMigration):
    """
    Migrates state from v2 to v3.

    Changes:
    - Adds event_history for audit trail
    - Adds performance_metrics for monitoring
    - Restructures transitions into a more detailed format
    """

    @property
    def from_version(self) -> StateVersion:
        """Source version."""
        return StateVersion(2, 0, 0)

    @property
    def to_version(self) -> StateVersion:
        """Target version."""
        return StateVersion(3, 0, 0)

    async def migrate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate state to v3."""
        logger.info("Migrating state from v2 to v3")

        # Copy state
        new_state = state.copy()

        # Ensure state_data exists
        if "state_data" not in new_state:
            new_state["state_data"] = {}

        # Add event history
        if "event_history" not in new_state["state_data"]:
            new_state["state_data"]["event_history"] = []

            # Convert existing transitions to events
            if "transitions" in new_state:
                for i, transition in enumerate(new_state.get("transitions", [])):
                    event = {
                        "event_id": f"migrated_{i}",
                        "event_type": "transition",
                        "timestamp": transition.get(
                            "timestamp", datetime.utcnow().isoformat()
                        ),
                        "data": transition,
                    }
                    new_state["state_data"]["event_history"].append(event)

        # Add performance metrics
        if "performance_metrics" not in new_state["state_data"]:
            new_state["state_data"]["performance_metrics"] = {
                "average_transition_time_ms": 0.0,
                "total_transitions": len(new_state.get("transitions", [])),
                "state_changes": {},
                "last_updated": datetime.utcnow().isoformat(),
            }

        # Enhance transitions format
        if "transitions" in new_state:
            enhanced_transitions = []
            for transition in new_state["transitions"]:
                if isinstance(transition, dict):
                    # Already in dict format, enhance it
                    enhanced = transition.copy()
                    if "duration_ms" not in enhanced:
                        enhanced["duration_ms"] = 0
                    if "metadata" not in enhanced:
                        enhanced["metadata"] = {}
                    enhanced_transitions.append(enhanced)
                else:
                    # Convert from simple format
                    enhanced_transitions.append(
                        {
                            "from_state": "unknown",
                            "to_state": "unknown",
                            "action": str(transition),
                            "timestamp": datetime.utcnow().isoformat(),
                            "duration_ms": 0,
                            "metadata": {"migrated": True},
                        }
                    )

            new_state["transitions"] = enhanced_transitions

        # Update version info
        new_state["_version"] = {
            "version": "3.0.0",
            "migrated_from": "2.0.0",
            "migration_date": None,  # Will be set by versioning system
            "features": [
                "event_history",
                "performance_metrics",
                "enhanced_transitions",
            ],
        }

        return new_state

    async def rollback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback migration."""
        logger.info("Rolling back migration from v3 to v2")

        # Copy state
        old_state = state.copy()

        # Remove v3 additions
        if "state_data" in old_state:
            if "event_history" in old_state["state_data"]:
                del old_state["state_data"]["event_history"]
            if "performance_metrics" in old_state["state_data"]:
                del old_state["state_data"]["performance_metrics"]

        # Simplify transitions format
        if "transitions" in old_state:
            simple_transitions = []
            for transition in old_state["transitions"]:
                if isinstance(transition, dict) and transition.get("metadata", {}).get(
                    "migrated"
                ):
                    # Skip migrated transitions
                    continue
                simple_transitions.append(transition)
            old_state["transitions"] = simple_transitions

        # Update version info
        if "_version" in old_state:
            old_state["_version"] = {"version": "2.0.0", "rolled_back_from": "3.0.0"}

        return old_state
