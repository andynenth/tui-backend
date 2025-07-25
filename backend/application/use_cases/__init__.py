"""
Use cases for the application layer.

Use cases represent single business operations that orchestrate
domain logic to achieve specific goals. They are organized by
functional area:

- connection: Client connection management
- room_management: Room lifecycle operations
- lobby: Room discovery and matchmaking
- game: Game play operations
"""

__all__ = [
    "connection",
    "room_management",
    "lobby",
    "game"
]