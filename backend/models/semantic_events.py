# backend/models/semantic_events.py

from enum import Enum
from typing import Dict, Any, List, Optional


class SemanticEventType(Enum):
    """High-level game events that capture meaningful state changes."""

    # Game lifecycle events
    GAME_STARTED = "game_started"
    GAME_COMPLETED = "game_completed"

    # Round lifecycle events
    ROUND_STARTED = "round_started"
    ROUND_COMPLETED = "round_completed"

    # Game phase events (compressed)
    HANDS_DEALT = "hands_dealt"  # Includes weak hand handling
    DECLARATIONS_COMPLETED = "declarations_completed"  # All 4 declarations in one
    TURN_COMPLETED = "turn_completed"  # All plays for one turn

    # Player events
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    PLAYER_RECONNECTED = "player_reconnected"

    # Connection lifecycle events
    PLAYER_DISCONNECTED = "player_disconnected"
    CONNECTION_LOST = "connection_lost"  # Network failure vs intentional disconnect
    PLAYER_RECONNECTED_FAILED = "player_reconnected_failed"

    # Bot control events
    BOT_TAKEOVER_SCHEDULED = "bot_takeover_scheduled"
    BOT_TAKEOVER_CANCELLED = "bot_takeover_cancelled"
    BOT_TAKEOVER_ACTIVATED = "bot_takeover_activated"
    BOT_CONTROL_RELEASED = "bot_control_released"
    BOT_CONTROL_FAILED_RELEASE = "bot_control_failed_release"

    # Action attribution events
    HUMAN_ACTION = "human_action"
    BOT_ACTION = "bot_action"
    ACTION_BLOCKED = "action_blocked"  # When human tries to act but bot has control

    # Grace period events
    GRACE_PERIOD_EXPIRED = "grace_period_expired"

    # Recovery events
    GAME_RECOVERED = "game_recovered"
    STATE_SNAPSHOT = "state_snapshot"  # Periodic full state capture


class EventImportance(Enum):
    """Event importance levels for filtering."""

    CRITICAL = 1.0  # Must store (game start/end, round complete)
    HIGH = 0.8  # Important game events (declarations, turns)
    MEDIUM = 0.5  # State updates that affect gameplay
    LOW = 0.3  # Minor updates, can be reconstructed
    DEBUG = 0.1  # Debug/trace events, usually filtered


class EventMapping:
    """Maps raw events to semantic events with compression rules."""

    # Events that should be stored as-is (no compression)
    STORE_AS_IS = {
        "game_started": SemanticEventType.GAME_STARTED,
        "game_over": SemanticEventType.GAME_COMPLETED,
        "game_complete": SemanticEventType.GAME_COMPLETED,
        "round_started": SemanticEventType.ROUND_STARTED,
        "round_complete": SemanticEventType.ROUND_COMPLETED,
        "round_completed": SemanticEventType.ROUND_COMPLETED,
        "hands_dealt": SemanticEventType.HANDS_DEALT,
        "player_joined": SemanticEventType.PLAYER_JOINED,
        "player_left": SemanticEventType.PLAYER_LEFT,
        "player_reconnected": SemanticEventType.PLAYER_RECONNECTED,
        "game_recovered": SemanticEventType.GAME_RECOVERED,
        # All new events MUST be stored for debugging
        "player_disconnected": SemanticEventType.PLAYER_DISCONNECTED,
        "connection_lost": SemanticEventType.CONNECTION_LOST,
        "player_reconnected_failed": SemanticEventType.PLAYER_RECONNECTED_FAILED,
        "bot_takeover_scheduled": SemanticEventType.BOT_TAKEOVER_SCHEDULED,
        "bot_takeover_cancelled": SemanticEventType.BOT_TAKEOVER_CANCELLED,
        "bot_takeover_activated": SemanticEventType.BOT_TAKEOVER_ACTIVATED,
        "bot_control_released": SemanticEventType.BOT_CONTROL_RELEASED,
        "bot_control_failed_release": SemanticEventType.BOT_CONTROL_FAILED_RELEASE,
        "human_action": SemanticEventType.HUMAN_ACTION,
        "bot_action": SemanticEventType.BOT_ACTION,
        "action_blocked": SemanticEventType.ACTION_BLOCKED,
        "grace_period_expired": SemanticEventType.GRACE_PERIOD_EXPIRED,
    }

    # Events that should be accumulated and compressed
    COMPRESS_EVENTS = {
        # Declaration events - accumulate all 4 into one
        "player_declared": "accumulate_declarations",
        "declaration": "accumulate_declarations",
        # Turn events - compress entire turn sequence
        "turn_started": "accumulate_turn",
        "pieces_played": "accumulate_turn",
        "play": "accumulate_turn",
        "turn_resolved": "accumulate_turn",
        "turn_completed": "compress_turn",
        # Phase updates - mostly redundant
        "phase_change": "filter_redundant",
        "phase_data_update": "filter_redundant",
    }

    # Event importance scoring
    IMPORTANCE_SCORES = {
        # Critical events
        "game_started": EventImportance.CRITICAL,
        "game_over": EventImportance.CRITICAL,
        "round_complete": EventImportance.CRITICAL,
        # High importance
        "round_started": EventImportance.HIGH,
        "hands_dealt": EventImportance.HIGH,
        "declarations_completed": EventImportance.HIGH,
        "turn_completed": EventImportance.HIGH,
        # Medium importance
        "player_declared": EventImportance.MEDIUM,
        "pieces_played": EventImportance.MEDIUM,
        # Low importance
        "phase_change": EventImportance.LOW,
        "phase_data_update": EventImportance.LOW,
        # Debug level
        "action_processed": EventImportance.DEBUG,
    }


class CompressedEvent:
    """Represents a compressed semantic event."""

    def __init__(self, event_type: SemanticEventType, payload: Dict[str, Any]):
        # Store event_type as string to avoid serialization issues
        self.event_type = (
            event_type.value
            if isinstance(event_type, SemanticEventType)
            else event_type
        )
        self.payload = payload
        self.original_event_count = payload.get("_original_count", 1)
        self.compression_ratio = payload.get("_compression_ratio", 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "event_type": self.event_type.value,
            "payload": self.payload,
            "compressed": True,
            "original_count": self.original_event_count,
            "compression_ratio": self.compression_ratio,
        }

    @classmethod
    def from_turn_events(cls, turn_events: List[Dict[str, Any]]) -> "CompressedEvent":
        """Create compressed turn event from multiple raw events."""
        turn_data = {
            "turn_number": None,
            "starter": None,
            "plays": {},
            "winner": None,
            "piles_won": 0,
            "_original_count": len(turn_events),
        }

        # Extract data from all events
        for event in turn_events:
            payload = event.get("payload", {})
            event_type = event.get("event_type", "")

            if "turn_number" in payload:
                turn_data["turn_number"] = payload["turn_number"]
            elif "current_turn_number" in payload:
                turn_data["turn_number"] = payload["current_turn_number"]

            if "starter" in payload:
                turn_data["starter"] = payload["starter"]
            elif "current_turn_starter" in payload:
                turn_data["starter"] = payload["current_turn_starter"]

            # Collect plays
            if event_type in ["pieces_played", "play"]:
                player = payload.get("player_name") or payload.get("player")
                if player:
                    turn_data["plays"][player] = {
                        "pieces": payload.get("pieces", []),
                        "count": payload.get("count", len(payload.get("pieces", []))),
                    }

            # Turn result
            if "winner" in payload:
                turn_data["winner"] = payload["winner"]
                turn_data["piles_won"] = payload.get("piles_won", 0)

        # Calculate compression ratio
        turn_data["_compression_ratio"] = 1 / len(turn_events) if turn_events else 1.0

        return cls(SemanticEventType.TURN_COMPLETED, turn_data)

    @classmethod
    def from_declaration_events(
        cls, declaration_events: List[Dict[str, Any]]
    ) -> "CompressedEvent":
        """Create compressed declarations event from individual declarations."""
        declarations = {}
        total_declared = 0

        for event in declaration_events:
            payload = event.get("payload", {})
            player = payload.get("player_name") or payload.get("player")
            value = payload.get("declaration") or payload.get("value", 0)

            if player:
                declarations[player] = value
                total_declared += value

        declaration_data = {
            "declarations": declarations,
            "total_declared": total_declared,
            "valid": total_declared != 8,  # Total must not equal 8
            "_original_count": len(declaration_events),
            "_compression_ratio": (
                1 / len(declaration_events) if declaration_events else 1.0
            ),
        }

        return cls(SemanticEventType.DECLARATIONS_COMPLETED, declaration_data)
