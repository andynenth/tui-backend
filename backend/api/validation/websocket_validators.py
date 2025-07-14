# backend/api/validation/websocket_validators.py

from typing import Any, Dict, List, Optional, Tuple, Union


class WebSocketMessageValidator:
    """Validates WebSocket messages for security and data integrity"""

    # Maximum allowed values for various fields
    MAX_PLAYER_NAME_LENGTH = 50
    MAX_ROOM_ID_LENGTH = 50
    MAX_MESSAGE_LENGTH = 1000
    MAX_ARRAY_LENGTH = 100
    MAX_PIECE_INDEX = 31  # 32 pieces total (0-31)
    MIN_PIECE_INDEX = 0
    MAX_DECLARATION_VALUE = 8
    MIN_DECLARATION_VALUE = 0
    MAX_SLOT_ID = 4
    MIN_SLOT_ID = 1

    # Allowed event names
    ALLOWED_EVENTS = {
        # Lobby events
        "request_room_list",
        "get_rooms",
        "client_ready",
        "create_room",
        "join_room",
        # Room management events
        "get_room_state",
        "remove_player",
        "add_bot",
        "leave_room",
        "start_game",
        # Game events
        "declare",
        "play",
        "play_pieces",
        "request_redeal",
        "accept_redeal",
        "decline_redeal",
        "redeal_decision",
        "player_ready",
        "leave_game",
        # System events
        "ack",
        "sync_request",
    }

    # Allowed redeal choices
    ALLOWED_REDEAL_CHOICES = {"accept", "decline"}

    @staticmethod
    def validate_base_message(message: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate basic WebSocket message structure.
        
        Args:
            message: The WebSocket message to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if message is valid, False otherwise
            - error_message: Description of validation error, or None if valid
        """
        if not isinstance(message, dict):
            return False, "Message must be a dictionary"

        if "event" not in message:
            return False, "Message must contain 'event' field"

        event_name = message.get("event")
        if not isinstance(event_name, str):
            return False, "Event name must be a string"

        if len(event_name) > 100:
            return False, "Event name too long"

        if event_name not in WebSocketMessageValidator.ALLOWED_EVENTS:
            return False, f"Unknown event type: {event_name}"

        # event_data is optional but must be dict if present
        if "data" in message:
            if not isinstance(message["data"], dict):
                return False, "Event data must be a dictionary"

        return True, None

    @staticmethod
    def validate_player_name(
        player_name: Any, required: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate and sanitize player name.
        
        Checks for:
        - Proper type (string)
        - Non-empty value
        - Maximum length limit
        - Dangerous characters (XSS prevention)
        
        Args:
            player_name: The player name to validate
            required: Whether the field is required (default: True)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if player_name is None:
            if required:
                return False, "Player name is required"
            return True, None

        if not isinstance(player_name, str):
            return False, "Player name must be a string"

        if len(player_name) == 0:
            return False, "Player name cannot be empty"

        if len(player_name) > WebSocketMessageValidator.MAX_PLAYER_NAME_LENGTH:
            return False, "Player name too long"

        # Check for dangerous characters
        if any(char in player_name for char in ["<", ">", "&", '"', "'", "\n", "\r"]):
            return False, "Player name contains invalid characters"

        return True, None

    @staticmethod
    def validate_room_id(room_id: Any, required: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate and sanitize room ID.
        
        Checks for:
        - Proper type (string)
        - Non-empty value
        - Maximum length limit
        - Dangerous characters
        
        Args:
            room_id: The room ID to validate
            required: Whether the field is required (default: True)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if room_id is None:
            if required:
                return False, "Room ID is required"
            return True, None

        if not isinstance(room_id, str):
            return False, "Room ID must be a string"

        if len(room_id) == 0:
            return False, "Room ID cannot be empty"

        if len(room_id) > WebSocketMessageValidator.MAX_ROOM_ID_LENGTH:
            return False, "Room ID too long"

        # Check for dangerous characters
        if any(char in room_id for char in ["<", ">", "&", '"', "'", "\n", "\r"]):
            return False, "Room ID contains invalid characters"

        return True, None

    @staticmethod
    def validate_declaration_value(value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate player's pile declaration value.
        
        Ensures the value is:
        - An integer
        - Within valid range (0-8)
        
        Args:
            value: The declaration value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return False, "Declaration value is required"

        if not isinstance(value, int):
            return False, "Declaration value must be an integer"

        if not (
            WebSocketMessageValidator.MIN_DECLARATION_VALUE
            <= value
            <= WebSocketMessageValidator.MAX_DECLARATION_VALUE
        ):
            return (
                False,
                f"Declaration value must be between {WebSocketMessageValidator.MIN_DECLARATION_VALUE} and {WebSocketMessageValidator.MAX_DECLARATION_VALUE}",
            )

        return True, None

    @staticmethod
    def validate_piece_indices(indices: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate array of piece indices for playing cards.
        
        Checks for:
        - Proper type (list)
        - Non-empty array
        - Maximum pieces per play (6)
        - Valid index range (0-31)
        - No duplicate indices
        
        Args:
            indices: List of piece indices to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(indices, list):
            return False, "Piece indices must be an array"

        if len(indices) == 0:
            return False, "Must select at least one piece"

        if len(indices) > 6:  # Maximum pieces that can be played at once
            return False, "Cannot play more than 6 pieces at once"

        seen_indices = set()
        for idx in indices:
            if not isinstance(idx, int):
                return False, "All piece indices must be integers"

            if not (
                WebSocketMessageValidator.MIN_PIECE_INDEX
                <= idx
                <= WebSocketMessageValidator.MAX_PIECE_INDEX
            ):
                return False, f"Piece index {idx} out of valid range"

            if idx in seen_indices:
                return False, f"Duplicate piece index: {idx}"

            seen_indices.add(idx)

        return True, None

    @staticmethod
    def validate_slot_id(slot_id: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate player slot ID.
        
        Ensures the slot ID is:
        - Numeric (handles both string and int)
        - Within valid range (1-4)
        
        Args:
            slot_id: The slot ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if slot_id is None:
            return False, "Slot ID is required"

        # Handle both string and int slot IDs
        try:
            slot_int = int(slot_id)
        except (ValueError, TypeError):
            return False, "Slot ID must be a number"

        if not (
            WebSocketMessageValidator.MIN_SLOT_ID
            <= slot_int
            <= WebSocketMessageValidator.MAX_SLOT_ID
        ):
            return (
                False,
                f"Slot ID must be between {WebSocketMessageValidator.MIN_SLOT_ID} and {WebSocketMessageValidator.MAX_SLOT_ID}",
            )

        return True, None

    @staticmethod
    def validate_redeal_choice(choice: Any) -> Tuple[bool, Optional[str]]:
        """Validate redeal choice"""
        if not isinstance(choice, str):
            return False, "Redeal choice must be a string"

        if choice not in WebSocketMessageValidator.ALLOWED_REDEAL_CHOICES:
            return False, f"Invalid redeal choice. Must be one of: {WebSocketMessageValidator.ALLOWED_REDEAL_CHOICES}"

        return True, None

    @staticmethod
    def validate_sequence_number(sequence: Any) -> Tuple[bool, Optional[str]]:
        """Validate sequence number for acknowledgments"""
        if sequence is None:
            return False, "Sequence number is required"

        if not isinstance(sequence, int):
            return False, "Sequence number must be an integer"

        if sequence < 0:
            return False, "Sequence number must be non-negative"

        return True, None

    @staticmethod
    def validate_client_id(client_id: Any) -> Tuple[bool, Optional[str]]:
        """Validate client ID"""
        if not isinstance(client_id, str):
            return False, "Client ID must be a string"

        if len(client_id) == 0:
            return False, "Client ID cannot be empty"

        if len(client_id) > 100:
            return False, "Client ID too long"

        return True, None

    @classmethod
    def validate_message(cls, message: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate a complete WebSocket message
        Returns: (is_valid, error_message, sanitized_data)
        """
        # First validate base structure
        is_valid, error = cls.validate_base_message(message)
        if not is_valid:
            return False, error, None

        event_name = message["event"]
        event_data = message.get("data", {})
        sanitized_data = {}

        # Validate based on event type
        if event_name == "create_room":
            is_valid, error = cls.validate_player_name(event_data.get("player_name"))
            if not is_valid:
                return False, error, None
            sanitized_data["player_name"] = event_data["player_name"].strip()

        elif event_name == "join_room":
            is_valid, error = cls.validate_room_id(event_data.get("room_id"))
            if not is_valid:
                return False, error, None
            is_valid, error = cls.validate_player_name(event_data.get("player_name"))
            if not is_valid:
                return False, error, None
            sanitized_data["room_id"] = event_data["room_id"]
            sanitized_data["player_name"] = event_data["player_name"].strip()

        elif event_name == "declare":
            is_valid, error = cls.validate_player_name(event_data.get("player_name"))
            if not is_valid:
                return False, error, None
            is_valid, error = cls.validate_declaration_value(event_data.get("value"))
            if not is_valid:
                return False, error, None
            sanitized_data["player_name"] = event_data["player_name"].strip()
            sanitized_data["value"] = event_data["value"]

        elif event_name in ["play", "play_pieces"]:
            is_valid, error = cls.validate_player_name(event_data.get("player_name"))
            if not is_valid:
                return False, error, None

            # Handle different field names for indices
            indices_field = "piece_indices" if event_name == "play" else "indices"
            indices = event_data.get(indices_field, [])
            is_valid, error = cls.validate_piece_indices(indices)
            if not is_valid:
                return False, error, None

            sanitized_data["player_name"] = event_data["player_name"].strip()
            sanitized_data["indices"] = indices

        elif event_name in ["request_redeal", "accept_redeal", "decline_redeal", "player_ready"]:
            is_valid, error = cls.validate_player_name(event_data.get("player_name"))
            if not is_valid:
                return False, error, None
            sanitized_data["player_name"] = event_data["player_name"].strip()

        elif event_name == "redeal_decision":
            is_valid, error = cls.validate_player_name(event_data.get("player_name"))
            if not is_valid:
                return False, error, None
            is_valid, error = cls.validate_redeal_choice(event_data.get("choice"))
            if not is_valid:
                return False, error, None
            sanitized_data["player_name"] = event_data["player_name"].strip()
            sanitized_data["choice"] = event_data["choice"]

        elif event_name in ["remove_player", "add_bot"]:
            is_valid, error = cls.validate_slot_id(event_data.get("slot_id"))
            if not is_valid:
                return False, error, None
            sanitized_data["slot_id"] = int(event_data["slot_id"])

        elif event_name == "leave_room":
            is_valid, error = cls.validate_player_name(
                event_data.get("player_name"), required=False
            )
            if not is_valid:
                return False, error, None
            if event_data.get("player_name"):
                sanitized_data["player_name"] = event_data["player_name"].strip()

        elif event_name == "ack":
            is_valid, error = cls.validate_sequence_number(event_data.get("sequence"))
            if not is_valid:
                return False, error, None
            is_valid, error = cls.validate_client_id(event_data.get("client_id", "unknown"))
            if not is_valid:
                return False, error, None
            sanitized_data["sequence"] = event_data["sequence"]
            sanitized_data["client_id"] = event_data.get("client_id", "unknown")

        elif event_name == "sync_request":
            is_valid, error = cls.validate_client_id(event_data.get("client_id", "unknown"))
            if not is_valid:
                return False, error, None
            sanitized_data["client_id"] = event_data.get("client_id", "unknown")

        elif event_name in ["request_room_list", "get_rooms", "client_ready", "get_room_state", "start_game", "leave_game"]:
            # These events may have optional data but don't require specific validation
            if event_name == "leave_game" and "player_name" in event_data:
                is_valid, error = cls.validate_player_name(event_data["player_name"])
                if not is_valid:
                    return False, error, None
                sanitized_data["player_name"] = event_data["player_name"].strip()

        return True, None, sanitized_data


def validate_websocket_message(
    message: Dict[str, Any]
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Convenience function to validate WebSocket messages
    Returns: (is_valid, error_message, sanitized_data)
    """
    return WebSocketMessageValidator.validate_message(message)