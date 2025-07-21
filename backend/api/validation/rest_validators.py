# backend/api/validation/rest_validators.py

from typing import Any, Optional, Tuple

from fastapi import HTTPException, Query


class RestApiValidator:
    """Validates REST API inputs for security and data integrity"""

    # Maximum allowed values
    MAX_PLAYER_NAME_LENGTH = 50
    MAX_ROOM_ID_LENGTH = 50
    MAX_DECLARATION_VALUE = 8
    MIN_DECLARATION_VALUE = 0
    MAX_SLOT_INDEX = 3  # 0-3 for slots
    MIN_SLOT_INDEX = 0
    MAX_PIECE_INDICES_LENGTH = 200  # Comma-separated string

    @staticmethod
    def validate_player_name(name: str) -> str:
        """
        Validate and sanitize player name for security and data integrity.

        Checks for proper string type, non-empty value, length limits,
        and dangerous characters that could be used for XSS attacks.

        Args:
            name: The player name to validate

        Returns:
            Sanitized player name string

        Raises:
            HTTPException: If validation fails with 400 status code
        """
        if not name or not isinstance(name, str):
            raise HTTPException(status_code=400, detail="Player name is required")

        name = name.strip()
        if len(name) == 0:
            raise HTTPException(status_code=400, detail="Player name cannot be empty")

        if len(name) > RestApiValidator.MAX_PLAYER_NAME_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Player name too long (max {RestApiValidator.MAX_PLAYER_NAME_LENGTH} characters)",
            )

        # Check for dangerous characters
        if any(char in name for char in ["<", ">", "&", '"', "'", "\n", "\r", "\0"]):
            raise HTTPException(
                status_code=400, detail="Player name contains invalid characters"
            )

        return name

    @staticmethod
    def validate_room_id(room_id: str) -> str:
        """
        Validate and sanitize room ID for security and data integrity.

        Ensures room ID is a proper string, non-empty, within length limits,
        and doesn't contain characters that could be used for injection attacks.

        Args:
            room_id: The room identifier to validate

        Returns:
            Sanitized room ID string

        Raises:
            HTTPException: If validation fails with 400 status code
        """
        if not room_id or not isinstance(room_id, str):
            raise HTTPException(status_code=400, detail="Room ID is required")

        room_id = room_id.strip()
        if len(room_id) == 0:
            raise HTTPException(status_code=400, detail="Room ID cannot be empty")

        if len(room_id) > RestApiValidator.MAX_ROOM_ID_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Room ID too long (max {RestApiValidator.MAX_ROOM_ID_LENGTH} characters)",
            )

        # Check for dangerous characters
        if any(char in room_id for char in ["<", ">", "&", '"', "'", "\n", "\r", "\0"]):
            raise HTTPException(
                status_code=400, detail="Room ID contains invalid characters"
            )

        return room_id

    @staticmethod
    def validate_declaration_value(value: int) -> int:
        """
        Validate player's pile declaration value.

        Ensures the declaration is within game rules (0-8 piles)
        and is a valid integer.

        Args:
            value: The number of piles player declares to win

        Returns:
            Validated declaration value as integer

        Raises:
            HTTPException: If value is not an integer or out of range (0-8)
        """
        if value is None:
            raise HTTPException(status_code=400, detail="Declaration value is required")

        try:
            value = int(value)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, detail="Declaration value must be an integer"
            )

        if not (
            RestApiValidator.MIN_DECLARATION_VALUE
            <= value
            <= RestApiValidator.MAX_DECLARATION_VALUE
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Declaration value must be between {RestApiValidator.MIN_DECLARATION_VALUE} and {RestApiValidator.MAX_DECLARATION_VALUE}",
            )

        return value

    @staticmethod
    def validate_slot_index(slot: int) -> int:
        """
        Validate player slot index in the game.

        Ensures slot index is within valid range (0-3) for 4-player game
        and is a proper integer.

        Args:
            slot: The player slot index to validate

        Returns:
            Validated slot index as integer

        Raises:
            HTTPException: If slot is not an integer or out of range (0-3)
        """
        if slot is None:
            raise HTTPException(status_code=400, detail="Slot index is required")

        try:
            slot = int(slot)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Slot index must be an integer")

        if not (
            RestApiValidator.MIN_SLOT_INDEX <= slot <= RestApiValidator.MAX_SLOT_INDEX
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Slot index must be between {RestApiValidator.MIN_SLOT_INDEX} and {RestApiValidator.MAX_SLOT_INDEX}",
            )

        return slot

    @staticmethod
    def validate_piece_indices_string(piece_indexes: str) -> list[int]:
        """
        Validate and parse comma-separated piece indices for turn play.

        Converts string like "1,3,5" to list of integers, ensuring:
        - Valid format (comma-separated integers)
        - At least 1 piece selected
        - No more than 6 pieces (game rule)
        - All indices in valid range (0-31)
        - No duplicate indices

        Args:
            piece_indexes: Comma-separated string of piece indices

        Returns:
            List of validated piece indices as integers

        Raises:
            HTTPException: If format invalid, too many pieces, or indices out of range
        """
        if not piece_indexes or not isinstance(piece_indexes, str):
            raise HTTPException(status_code=400, detail="Piece indices are required")

        piece_indexes = piece_indexes.strip()
        if len(piece_indexes) > RestApiValidator.MAX_PIECE_INDICES_LENGTH:
            raise HTTPException(status_code=400, detail="Piece indices string too long")

        # Parse comma-separated indices
        try:
            indices = [int(i.strip()) for i in piece_indexes.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid piece indices format. Must be comma-separated integers",
            )

        if len(indices) == 0:
            raise HTTPException(
                status_code=400, detail="Must select at least one piece"
            )

        if len(indices) > 6:
            raise HTTPException(
                status_code=400, detail="Cannot play more than 6 pieces at once"
            )

        # Check for valid range and duplicates
        seen_indices = set()
        for idx in indices:
            if not (0 <= idx <= 31):  # 32 pieces total
                raise HTTPException(
                    status_code=400,
                    detail=f"Piece index {idx} out of valid range (0-31)",
                )
            if idx in seen_indices:
                raise HTTPException(
                    status_code=400, detail=f"Duplicate piece index: {idx}"
                )
            seen_indices.add(idx)

        return indices

    @staticmethod
    def validate_redeal_choice(choice: str) -> str:
        """
        Validate player's response to weak hand redeal offer.

        Ensures choice is either 'accept' or 'decline' (case-insensitive).

        Args:
            choice: Player's redeal decision

        Returns:
            Normalized choice as lowercase string ('accept' or 'decline')

        Raises:
            HTTPException: If choice is not 'accept' or 'decline'
        """
        if not choice or not isinstance(choice, str):
            raise HTTPException(status_code=400, detail="Redeal choice is required")

        choice = choice.strip().lower()
        if choice not in ["accept", "decline"]:
            raise HTTPException(
                status_code=400, detail="Redeal choice must be 'accept' or 'decline'"
            )

        return choice

    @staticmethod
    def validate_older_than_hours(hours: int) -> int:
        """
        Validate hours parameter for cleaning up old game data.

        Used for maintenance endpoints to clean up games older than
        specified hours. Defaults to 24 hours if not provided.

        Args:
            hours: Number of hours for cleanup threshold

        Returns:
            Validated hours as integer (1-720)

        Raises:
            HTTPException: If hours is not an integer or out of range (1-720)
        """
        if hours is None:
            return 24  # Default value

        try:
            hours = int(hours)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, detail="older_than_hours must be an integer"
            )

        if hours < 1:
            raise HTTPException(
                status_code=400, detail="older_than_hours must be at least 1"
            )

        if hours > 720:  # 30 days max
            raise HTTPException(
                status_code=400, detail="older_than_hours cannot exceed 720 (30 days)"
            )

        return hours

    @staticmethod
    def validate_sequence_number(sequence: int) -> int:
        """
        Validate sequence number for event store queries.

        Used for event sourcing to query events after a specific
        sequence number. Must be non-negative.

        Args:
            sequence: Event sequence number to validate

        Returns:
            Validated sequence number as integer

        Raises:
            HTTPException: If sequence is not an integer or negative
        """
        if sequence is None:
            raise HTTPException(status_code=400, detail="Sequence number is required")

        try:
            sequence = int(sequence)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, detail="Sequence number must be an integer"
            )

        if sequence < 0:
            raise HTTPException(
                status_code=400, detail="Sequence number must be non-negative"
            )

        return sequence

    @staticmethod
    def validate_event_limit(limit: Optional[int]) -> Optional[int]:
        """
        Validate limit parameter for event store queries.

        Controls maximum number of events returned in a single query.
        Returns None if not provided (no limit).

        Args:
            limit: Maximum number of events to return

        Returns:
            Validated limit as integer (1-1000) or None

        Raises:
            HTTPException: If limit is not an integer or out of range (1-1000)
        """
        if limit is None:
            return None

        try:
            limit = int(limit)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Limit must be an integer")

        if limit < 1:
            raise HTTPException(status_code=400, detail="Limit must be at least 1")

        if limit > 1000:
            raise HTTPException(
                status_code=400, detail="Limit cannot exceed 1000 events"
            )

        return limit


# Convenience functions for common validations
def get_validated_player_name(name: str = Query(...)) -> str:
    """
    FastAPI dependency for validating player name in route handlers.

    Use as a dependency in FastAPI routes to automatically validate
    and sanitize player names from query parameters.

    Args:
        name: Player name from query parameter

    Returns:
        Validated and sanitized player name

    Raises:
        HTTPException: If validation fails
    """
    return RestApiValidator.validate_player_name(name)


def get_validated_room_id(room_id: str = Query(...)) -> str:
    """
    FastAPI dependency for validating room ID in route handlers.

    Use as a dependency in FastAPI routes to automatically validate
    and sanitize room IDs from query parameters.

    Args:
        room_id: Room ID from query parameter

    Returns:
        Validated and sanitized room ID

    Raises:
        HTTPException: If validation fails
    """
    return RestApiValidator.validate_room_id(room_id)


def get_validated_declaration(
    player_name: str = Query(...), value: int = Query(...)
) -> Tuple[str, int]:
    """
    FastAPI dependency for validating player declaration.

    Validates both player name and declaration value for the
    declaration phase of the game.

    Args:
        player_name: Player name from query parameter
        value: Declaration value from query parameter

    Returns:
        Tuple of (validated_player_name, validated_declaration_value)

    Raises:
        HTTPException: If either validation fails
    """
    return (
        RestApiValidator.validate_player_name(player_name),
        RestApiValidator.validate_declaration_value(value),
    )


def get_validated_play_turn(
    player_name: str = Query(...), piece_indexes: str = Query(...)
) -> Tuple[str, list[int]]:
    """
    FastAPI dependency for validating turn play action.

    Validates player name and parses comma-separated piece indices
    for the turn phase of the game.

    Args:
        player_name: Player name from query parameter
        piece_indexes: Comma-separated piece indices from query parameter

    Returns:
        Tuple of (validated_player_name, list_of_piece_indices)

    Raises:
        HTTPException: If validation fails
    """
    return (
        RestApiValidator.validate_player_name(player_name),
        RestApiValidator.validate_piece_indices_string(piece_indexes),
    )
