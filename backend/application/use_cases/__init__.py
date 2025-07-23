# application/use_cases/__init__.py
"""
Use cases implement the business operations of the application.

Each use case:
- Represents a single user intention
- Orchestrates domain operations
- Coordinates with infrastructure services
- Returns a specific result
"""

from .create_room import CreateRoomUseCase, RoomCreationResult
from .join_room import JoinRoomUseCase, JoinRoomResult
from .start_game import StartGameUseCase, StartGameResult
from .play_turn import PlayTurnUseCase, PlayTurnResult
from .declare_piles import DeclarePilesUseCase, DeclareResult

__all__ = [
    'CreateRoomUseCase',
    'RoomCreationResult',
    'JoinRoomUseCase',
    'JoinRoomResult',
    'StartGameUseCase',
    'StartGameResult',
    'PlayTurnUseCase',
    'PlayTurnResult',
    'DeclarePilesUseCase',
    'DeclareResult',
]