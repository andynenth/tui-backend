# backend/tests/test_websocket_validation.py

import pytest

from api.validation import WebSocketMessageValidator, validate_websocket_message


class TestWebSocketMessageValidator:
    """Test WebSocket message validation"""

    def test_validate_base_message_valid(self):
        """Test valid base message structure"""
        message = {"event": "declare", "data": {"player_name": "Alice", "value": 3}}
        is_valid, error = WebSocketMessageValidator.validate_base_message(message)
        assert is_valid is True
        assert error is None

    def test_validate_base_message_not_dict(self):
        """Test invalid message type"""
        message = "invalid"
        is_valid, error = WebSocketMessageValidator.validate_base_message(message)
        assert is_valid is False
        assert "must be a dictionary" in error

    def test_validate_base_message_missing_event(self):
        """Test missing event field"""
        message = {"data": {}}
        is_valid, error = WebSocketMessageValidator.validate_base_message(message)
        assert is_valid is False
        assert "must contain 'event' field" in error

    def test_validate_base_message_invalid_event_type(self):
        """Test invalid event type"""
        message = {"event": 123}
        is_valid, error = WebSocketMessageValidator.validate_base_message(message)
        assert is_valid is False
        assert "Event name must be a string" in error

    def test_validate_base_message_unknown_event(self):
        """Test unknown event name"""
        message = {"event": "unknown_event"}
        is_valid, error = WebSocketMessageValidator.validate_base_message(message)
        assert is_valid is False
        assert "Unknown event type" in error

    def test_validate_player_name_valid(self):
        """Test valid player name"""
        is_valid, error = WebSocketMessageValidator.validate_player_name("Alice")
        assert is_valid is True
        assert error is None

    def test_validate_player_name_empty(self):
        """Test empty player name"""
        is_valid, error = WebSocketMessageValidator.validate_player_name("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_validate_player_name_too_long(self):
        """Test player name too long"""
        long_name = "A" * 51
        is_valid, error = WebSocketMessageValidator.validate_player_name(long_name)
        assert is_valid is False
        assert "too long" in error

    def test_validate_player_name_dangerous_characters(self):
        """Test player name with dangerous characters"""
        names = ["<script>", "Alice&Bob", 'Alice"Bob', "Alice\nBob"]
        for name in names:
            is_valid, error = WebSocketMessageValidator.validate_player_name(name)
            assert is_valid is False
            assert "invalid characters" in error

    def test_validate_declaration_value_valid(self):
        """Test valid declaration values"""
        for value in range(0, 9):
            is_valid, error = WebSocketMessageValidator.validate_declaration_value(value)
            assert is_valid is True
            assert error is None

    def test_validate_declaration_value_out_of_range(self):
        """Test declaration value out of range"""
        for value in [-1, 9, 100]:
            is_valid, error = WebSocketMessageValidator.validate_declaration_value(value)
            assert is_valid is False
            assert "must be between" in error

    def test_validate_piece_indices_valid(self):
        """Test valid piece indices"""
        indices = [0, 5, 10, 15]
        is_valid, error = WebSocketMessageValidator.validate_piece_indices(indices)
        assert is_valid is True
        assert error is None

    def test_validate_piece_indices_empty(self):
        """Test empty piece indices"""
        is_valid, error = WebSocketMessageValidator.validate_piece_indices([])
        assert is_valid is False
        assert "at least one piece" in error

    def test_validate_piece_indices_too_many(self):
        """Test too many piece indices"""
        indices = [0, 1, 2, 3, 4, 5, 6]
        is_valid, error = WebSocketMessageValidator.validate_piece_indices(indices)
        assert is_valid is False
        assert "more than 6 pieces" in error

    def test_validate_piece_indices_out_of_range(self):
        """Test piece index out of range"""
        indices = [0, 32]
        is_valid, error = WebSocketMessageValidator.validate_piece_indices(indices)
        assert is_valid is False
        assert "out of valid range" in error

    def test_validate_piece_indices_duplicates(self):
        """Test duplicate piece indices"""
        indices = [0, 5, 5, 10]
        is_valid, error = WebSocketMessageValidator.validate_piece_indices(indices)
        assert is_valid is False
        assert "Duplicate" in error

    def test_validate_slot_id_valid(self):
        """Test valid slot IDs"""
        for slot_id in [1, 2, 3, 4, "1", "2", "3", "4"]:
            is_valid, error = WebSocketMessageValidator.validate_slot_id(slot_id)
            assert is_valid is True
            assert error is None

    def test_validate_slot_id_out_of_range(self):
        """Test slot ID out of range"""
        for slot_id in [0, 5, -1]:
            is_valid, error = WebSocketMessageValidator.validate_slot_id(slot_id)
            assert is_valid is False
            assert "must be between" in error

    def test_validate_redeal_choice_valid(self):
        """Test valid redeal choices"""
        for choice in ["accept", "decline"]:
            is_valid, error = WebSocketMessageValidator.validate_redeal_choice(choice)
            assert is_valid is True
            assert error is None

    def test_validate_redeal_choice_invalid(self):
        """Test invalid redeal choice"""
        is_valid, error = WebSocketMessageValidator.validate_redeal_choice("maybe")
        assert is_valid is False
        assert "Invalid redeal choice" in error

    def test_validate_message_create_room(self):
        """Test create_room message validation"""
        message = {"event": "create_room", "data": {"player_name": "Alice"}}
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["player_name"] == "Alice"

    def test_validate_message_create_room_missing_name(self):
        """Test create_room with missing player name"""
        message = {"event": "create_room", "data": {}}
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is False
        assert "Player name is required" in error

    def test_validate_message_join_room(self):
        """Test join_room message validation"""
        message = {
            "event": "join_room",
            "data": {"room_id": "room123", "player_name": "Bob"},
        }
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["room_id"] == "room123"
        assert sanitized["player_name"] == "Bob"

    def test_validate_message_declare(self):
        """Test declare message validation"""
        message = {"event": "declare", "data": {"player_name": "Alice", "value": 3}}
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["player_name"] == "Alice"
        assert sanitized["value"] == 3

    def test_validate_message_play(self):
        """Test play message validation"""
        message = {
            "event": "play",
            "data": {"player_name": "Alice", "piece_indices": [0, 5, 10]},
        }
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["player_name"] == "Alice"
        assert sanitized["indices"] == [0, 5, 10]

    def test_validate_message_play_pieces(self):
        """Test play_pieces message validation"""
        message = {
            "event": "play_pieces",
            "data": {"player_name": "Alice", "indices": [1, 2, 3]},
        }
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["player_name"] == "Alice"
        assert sanitized["indices"] == [1, 2, 3]

    def test_validate_message_redeal_decision(self):
        """Test redeal_decision message validation"""
        message = {
            "event": "redeal_decision",
            "data": {"player_name": "Alice", "choice": "accept"},
        }
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["player_name"] == "Alice"
        assert sanitized["choice"] == "accept"

    def test_validate_message_remove_player(self):
        """Test remove_player message validation"""
        message = {"event": "remove_player", "data": {"slot_id": 2}}
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["slot_id"] == 2

    def test_validate_message_add_bot(self):
        """Test add_bot message validation"""
        message = {"event": "add_bot", "data": {"slot_id": "3"}}
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["slot_id"] == 3

    def test_validate_message_ack(self):
        """Test ack message validation"""
        message = {"event": "ack", "data": {"sequence": 123, "client_id": "client456"}}
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["sequence"] == 123
        assert sanitized["client_id"] == "client456"

    def test_validate_message_sync_request(self):
        """Test sync_request message validation"""
        message = {"event": "sync_request", "data": {"client_id": "client789"}}
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert error is None
        assert sanitized["client_id"] == "client789"

    def test_validate_message_strips_whitespace(self):
        """Test that player names are stripped of whitespace"""
        message = {
            "event": "create_room",
            "data": {"player_name": "  Alice  "},
        }
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is True
        assert sanitized["player_name"] == "Alice"

    def test_validate_message_sql_injection_attempt(self):
        """Test SQL injection attempt in player name"""
        message = {
            "event": "create_room",
            "data": {"player_name": "Alice'; DROP TABLE users; --"},
        }
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is False
        assert "invalid characters" in error

    def test_validate_message_xss_attempt(self):
        """Test XSS attempt in player name"""
        message = {
            "event": "create_room",
            "data": {"player_name": "<script>alert('XSS')</script>"},
        }
        is_valid, error, sanitized = validate_websocket_message(message)
        assert is_valid is False
        assert "invalid characters" in error