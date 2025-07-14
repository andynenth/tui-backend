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
        """Validate and sanitize player name"""
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
        """Validate and sanitize room ID"""
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
        """Validate declaration value"""
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
        """Validate slot index"""
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
        """Validate comma-separated piece indices string"""
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
                status_code=400, detail="Invalid piece indices format. Must be comma-separated integers"
            )

        if len(indices) == 0:
            raise HTTPException(status_code=400, detail="Must select at least one piece")

        if len(indices) > 6:
            raise HTTPException(
                status_code=400, detail="Cannot play more than 6 pieces at once"
            )

        # Check for valid range and duplicates
        seen_indices = set()
        for idx in indices:
            if not (0 <= idx <= 31):  # 32 pieces total
                raise HTTPException(
                    status_code=400, detail=f"Piece index {idx} out of valid range (0-31)"
                )
            if idx in seen_indices:
                raise HTTPException(
                    status_code=400, detail=f"Duplicate piece index: {idx}"
                )
            seen_indices.add(idx)

        return indices

    @staticmethod
    def validate_redeal_choice(choice: str) -> str:
        """Validate redeal choice"""
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
        """Validate cleanup parameter"""
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
        """Validate sequence number for event queries"""
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
        """Validate event query limit"""
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
    """FastAPI dependency for validating player name"""
    return RestApiValidator.validate_player_name(name)


def get_validated_room_id(room_id: str = Query(...)) -> str:
    """FastAPI dependency for validating room ID"""
    return RestApiValidator.validate_room_id(room_id)


def get_validated_declaration(
    player_name: str = Query(...), value: int = Query(...)
) -> Tuple[str, int]:
    """FastAPI dependency for validating declaration"""
    return (
        RestApiValidator.validate_player_name(player_name),
        RestApiValidator.validate_declaration_value(value),
    )


def get_validated_play_turn(
    player_name: str = Query(...), piece_indexes: str = Query(...)
) -> Tuple[str, list[int]]:
    """FastAPI dependency for validating play turn"""
    return (
        RestApiValidator.validate_player_name(player_name),
        RestApiValidator.validate_piece_indices_string(piece_indexes),
    )