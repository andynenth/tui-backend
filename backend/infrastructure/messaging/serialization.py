"""
Message serialization implementations.

Provides various serialization formats for message transport.
"""

import json
import pickle
from typing import Any, Dict, Type, Optional
from datetime import datetime
import logging

try:
    import msgpack

    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False
    msgpack = None

from .base import (
    Message,
    MessageMetadata,
    MessageStatus,
    MessagePriority,
    IMessageSerializer,
    T,
)


logger = logging.getLogger(__name__)


class JsonMessageSerializer(IMessageSerializer[Any]):
    """
    JSON message serializer.

    Features:
    - Human-readable format
    - Wide compatibility
    - Custom type handling
    """

    def __init__(
        self,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        custom_encoder: Optional[Type[json.JSONEncoder]] = None,
    ):
        """Initialize JSON serializer."""
        self.encoding = encoding
        self.ensure_ascii = ensure_ascii
        self.encoder_class = custom_encoder or DateTimeEncoder

    def serialize(self, message: Message[Any]) -> bytes:
        """Serialize message to JSON bytes."""
        try:
            # Convert to dictionary
            data = {
                "payload": message.payload,
                "metadata": {
                    "message_id": message.metadata.message_id,
                    "timestamp": message.metadata.timestamp.isoformat(),
                    "source": message.metadata.source,
                    "destination": message.metadata.destination,
                    "correlation_id": message.metadata.correlation_id,
                    "reply_to": message.metadata.reply_to,
                    "content_type": message.metadata.content_type,
                    "headers": message.metadata.headers,
                    "attempts": message.metadata.attempts,
                    "last_error": message.metadata.last_error,
                    "expires_at": (
                        message.metadata.expires_at.isoformat()
                        if message.metadata.expires_at
                        else None
                    ),
                },
                "status": message.status.value,
                "priority": message.priority.value,
            }

            # Serialize to JSON
            json_str = json.dumps(
                data, cls=self.encoder_class, ensure_ascii=self.ensure_ascii
            )

            return json_str.encode(self.encoding)

        except Exception as e:
            logger.error(f"Failed to serialize message: {e}")
            raise

    def deserialize(self, data: bytes) -> Message[Any]:
        """Deserialize JSON bytes to message."""
        try:
            # Decode JSON
            json_str = data.decode(self.encoding)
            obj = json.loads(json_str)

            # Reconstruct metadata
            metadata_data = obj["metadata"]
            metadata = MessageMetadata(
                message_id=metadata_data["message_id"],
                timestamp=datetime.fromisoformat(metadata_data["timestamp"]),
                source=metadata_data.get("source"),
                destination=metadata_data.get("destination"),
                correlation_id=metadata_data.get("correlation_id"),
                reply_to=metadata_data.get("reply_to"),
                content_type=metadata_data.get("content_type", "application/json"),
                headers=metadata_data.get("headers", {}),
                attempts=metadata_data.get("attempts", 0),
                last_error=metadata_data.get("last_error"),
                expires_at=(
                    datetime.fromisoformat(metadata_data["expires_at"])
                    if metadata_data.get("expires_at")
                    else None
                ),
            )

            # Reconstruct message
            message = Message(
                payload=obj["payload"],
                metadata=metadata,
                status=MessageStatus(obj.get("status", "pending")),
                priority=MessagePriority(obj.get("priority", 5)),
            )

            return message

        except Exception as e:
            logger.error(f"Failed to deserialize message: {e}")
            raise

    def content_type(self) -> str:
        """Get content type."""
        return "application/json"


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj):
        """Encode datetime objects as ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class PickleMessageSerializer(IMessageSerializer[Any]):
    """
    Pickle message serializer.

    Features:
    - Handles any Python object
    - Efficient binary format
    - Protocol version support
    """

    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL):
        """Initialize pickle serializer."""
        self.protocol = protocol

    def serialize(self, message: Message[Any]) -> bytes:
        """Serialize message using pickle."""
        try:
            return pickle.dumps(message, protocol=self.protocol)
        except Exception as e:
            logger.error(f"Failed to pickle message: {e}")
            raise

    def deserialize(self, data: bytes) -> Message[Any]:
        """Deserialize pickled message."""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Failed to unpickle message: {e}")
            raise

    def content_type(self) -> str:
        """Get content type."""
        return "application/x-python-pickle"


class MessagePackSerializer(IMessageSerializer[Any]):
    """
    MessagePack serializer.

    Features:
    - Efficient binary format
    - Cross-language support
    - Smaller than JSON
    """

    def __init__(self, use_bin_type: bool = True):
        """Initialize MessagePack serializer."""
        if not HAS_MSGPACK:
            raise ImportError("msgpack-python required for MessagePackSerializer")

        self.use_bin_type = use_bin_type

    def serialize(self, message: Message[Any]) -> bytes:
        """Serialize message using MessagePack."""
        try:
            # Convert to serializable format
            data = {
                "payload": message.payload,
                "metadata": {
                    "message_id": message.metadata.message_id,
                    "timestamp": message.metadata.timestamp.timestamp(),
                    "source": message.metadata.source,
                    "destination": message.metadata.destination,
                    "correlation_id": message.metadata.correlation_id,
                    "reply_to": message.metadata.reply_to,
                    "content_type": message.metadata.content_type,
                    "headers": message.metadata.headers,
                    "attempts": message.metadata.attempts,
                    "last_error": message.metadata.last_error,
                    "expires_at": (
                        message.metadata.expires_at.timestamp()
                        if message.metadata.expires_at
                        else None
                    ),
                },
                "status": message.status.value,
                "priority": message.priority.value,
            }

            return msgpack.packb(data, use_bin_type=self.use_bin_type)

        except Exception as e:
            logger.error(f"Failed to serialize with MessagePack: {e}")
            raise

    def deserialize(self, data: bytes) -> Message[Any]:
        """Deserialize MessagePack data."""
        try:
            obj = msgpack.unpackb(data, raw=False)

            # Reconstruct metadata
            metadata_data = obj["metadata"]
            metadata = MessageMetadata(
                message_id=metadata_data["message_id"],
                timestamp=datetime.fromtimestamp(metadata_data["timestamp"]),
                source=metadata_data.get("source"),
                destination=metadata_data.get("destination"),
                correlation_id=metadata_data.get("correlation_id"),
                reply_to=metadata_data.get("reply_to"),
                content_type=metadata_data.get("content_type", "application/msgpack"),
                headers=metadata_data.get("headers", {}),
                attempts=metadata_data.get("attempts", 0),
                last_error=metadata_data.get("last_error"),
                expires_at=(
                    datetime.fromtimestamp(metadata_data["expires_at"])
                    if metadata_data.get("expires_at")
                    else None
                ),
            )

            # Reconstruct message
            message = Message(
                payload=obj["payload"],
                metadata=metadata,
                status=MessageStatus(obj.get("status", "pending")),
                priority=MessagePriority(obj.get("priority", 5)),
            )

            return message

        except Exception as e:
            logger.error(f"Failed to deserialize MessagePack: {e}")
            raise

    def content_type(self) -> str:
        """Get content type."""
        return "application/msgpack"


class CompositeSerializer(IMessageSerializer[Any]):
    """
    Composite serializer that can handle multiple formats.

    Features:
    - Format detection
    - Fallback support
    - Content negotiation
    """

    def __init__(
        self,
        serializers: Optional[Dict[str, IMessageSerializer]] = None,
        default_format: str = "json",
    ):
        """Initialize composite serializer."""
        self.serializers = serializers or {
            "json": JsonMessageSerializer(),
            "pickle": PickleMessageSerializer(),
        }

        if HAS_MSGPACK and "msgpack" not in self.serializers:
            self.serializers["msgpack"] = MessagePackSerializer()

        self.default_format = default_format

    def serialize(self, message: Message[Any]) -> bytes:
        """Serialize using appropriate format."""
        # Determine format from content type
        content_type = message.metadata.content_type
        format_name = self._get_format_from_content_type(content_type)

        serializer = self.serializers.get(format_name)
        if not serializer:
            serializer = self.serializers[self.default_format]

        return serializer.serialize(message)

    def deserialize(self, data: bytes) -> Message[Any]:
        """Deserialize trying different formats."""
        # Try to detect format
        if self._looks_like_json(data):
            try:
                return self.serializers["json"].deserialize(data)
            except:
                pass

        if HAS_MSGPACK and self._looks_like_msgpack(data):
            try:
                return self.serializers["msgpack"].deserialize(data)
            except:
                pass

        # Try pickle as fallback
        try:
            return self.serializers["pickle"].deserialize(data)
        except:
            pass

        # Final attempt with default
        return self.serializers[self.default_format].deserialize(data)

    def content_type(self) -> str:
        """Get default content type."""
        return self.serializers[self.default_format].content_type()

    def _get_format_from_content_type(self, content_type: str) -> str:
        """Determine format from content type."""
        if "json" in content_type:
            return "json"
        elif "msgpack" in content_type:
            return "msgpack"
        elif "pickle" in content_type:
            return "pickle"
        else:
            return self.default_format

    def _looks_like_json(self, data: bytes) -> bool:
        """Check if data looks like JSON."""
        try:
            # Check for JSON markers
            stripped = data.strip()
            return (stripped.startswith(b"{") and stripped.endswith(b"}")) or (
                stripped.startswith(b"[") and stripped.endswith(b"]")
            )
        except:
            return False

    def _looks_like_msgpack(self, data: bytes) -> bool:
        """Check if data looks like MessagePack."""
        if not data:
            return False

        # MessagePack format bytes
        first_byte = data[0]

        # Check for common MessagePack markers
        return (
            (0x80 <= first_byte <= 0x8F)  # fixmap
            or (0x90 <= first_byte <= 0x9F)  # fixarray
            or (0xA0 <= first_byte <= 0xBF)  # fixstr
            or (first_byte in (0xDC, 0xDD, 0xDE, 0xDF))  # array/map markers
        )
