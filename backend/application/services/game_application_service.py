"""
Game application service.

This service provides high-level orchestration of game-related use cases
and cross-cutting concerns for game operations.
"""

import logging
from typing import Optional, Dict, Any, List

from application.base import ApplicationService
from application.interfaces import UnitOfWork, EventPublisher, BotService, MetricsCollector
from application.use_cases.game import (
    StartGameUseCase,
    DeclareUseCase,
    PlayUseCase,
    RequestRedealUseCase,
    AcceptRedealUseCase,
    DeclineRedealUseCase,
    HandleRedealDecisionUseCase,
    MarkPlayerReadyUseCase,
    LeaveGameUseCase
)
from application.dto.game import (
    StartGameRequest, StartGameResponse,
    DeclareRequest, DeclareResponse,
    PlayRequest, PlayResponse
)
from application.exceptions import ApplicationException, ConflictException

logger = logging.getLogger(__name__)


class GameApplicationService(ApplicationService):
    """
    High-level service for game operations.
    
    This service:
    1. Orchestrates multiple game use cases
    2. Handles complex game workflows
    3. Manages cross-cutting concerns
    4. Provides transaction boundaries
    5. Coordinates bot actions
    """
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        bot_service: BotService,
        metrics: Optional[MetricsCollector] = None
    ):
        """
        Initialize the service.
        
        Args:
            unit_of_work: Unit of work for transactions
            event_publisher: Event publishing service
            bot_service: Bot management service
            metrics: Optional metrics collector
        """
        super().__init__()
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._bot_service = bot_service
        self._metrics = metrics
        
        # Initialize use cases
        self._start_game_use_case = StartGameUseCase(unit_of_work, event_publisher, metrics)
        self._declare_use_case = DeclareUseCase(unit_of_work, event_publisher, metrics)
        self._play_use_case = PlayUseCase(unit_of_work, event_publisher, metrics)
        self._request_redeal_use_case = RequestRedealUseCase(unit_of_work, event_publisher, metrics)
        self._accept_redeal_use_case = AcceptRedealUseCase(unit_of_work, event_publisher, metrics)
        self._decline_redeal_use_case = DeclineRedealUseCase(unit_of_work, event_publisher, metrics)
        self._handle_redeal_use_case = HandleRedealDecisionUseCase(unit_of_work, event_publisher, metrics)
        self._mark_ready_use_case = MarkPlayerReadyUseCase(unit_of_work, event_publisher, metrics)
        self._leave_game_use_case = LeaveGameUseCase(unit_of_work, event_publisher, bot_service, metrics)
    
    async def start_game_with_bots(
        self,
        room_id: str,
        requesting_player_id: str,
        user_id: Optional[str] = None
    ) -> StartGameResponse:
        """
        Start a game and handle initial bot actions.
        
        Args:
            room_id: Room to start game in
            requesting_player_id: Player requesting start
            user_id: User ID for tracking
            
        Returns:
            Start game response
            
        Raises:
            ApplicationException: If game cannot be started
        """
        try:
            # Start the game
            request = StartGameRequest(
                room_id=room_id,
                requesting_player_id=requesting_player_id,
                user_id=user_id
            )
            response = await self._start_game_use_case.execute(request)
            
            if response.success:
                # Handle bot actions for weak hands
                await self._handle_bot_redeal_responses(
                    response.game_id,
                    response.weak_hands_detected
                )
                
                self._logger.info(
                    f"Game started with bot handling",
                    extra={
                        "game_id": response.game_id,
                        "room_id": room_id,
                        "weak_hands": len(response.weak_hands_detected)
                    }
                )
            
            return response
            
        except Exception as e:
            self._logger.error(
                f"Failed to start game with bots: {e}",
                exception=e
            )
            raise ApplicationException(
                f"Failed to start game: {str(e)}",
                code="GAME_START_FAILED"
            )
    
    async def complete_game_turn(
        self,
        game_id: str,
        player_id: str,
        pieces: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete a game turn including bot actions.
        
        Args:
            game_id: Game ID
            player_id: Player making the play
            pieces: Pieces to play
            user_id: User ID for tracking
            
        Returns:
            Turn completion result
        """
        # Make the play
        from application.dto.common import PieceInfo
        piece_infos = [PieceInfo(p["value"], p["kind"]) for p in pieces]
        
        play_request = PlayRequest(
            game_id=game_id,
            player_id=player_id,
            pieces=piece_infos,
            user_id=user_id
        )
        play_response = await self._play_use_case.execute(play_request)
        
        if play_response.success and not play_response.turn_complete:
            # Trigger bot plays if needed
            await self._trigger_bot_plays(game_id)
        
        return {
            "play_accepted": play_response.success,
            "turn_complete": play_response.turn_complete,
            "round_complete": play_response.round_complete,
            "game_complete": play_response.game_complete,
            "next_player_id": play_response.next_player_id,
            "scores": play_response.scores
        }
    
    async def handle_redeal_timeout(
        self,
        game_id: str,
        redeal_id: str
    ) -> Dict[str, Any]:
        """
        Handle redeal vote timeout.
        
        Args:
            game_id: Game ID
            redeal_id: Redeal session ID
            
        Returns:
            Timeout handling result
        """
        from application.dto.game import HandleRedealDecisionRequest
        
        request = HandleRedealDecisionRequest(
            game_id=game_id,
            redeal_id=redeal_id,
            force_decision=True
        )
        
        response = await self._handle_redeal_use_case.execute(request)
        
        # Handle bot actions after redeal decision
        if response.success and response.new_hands_dealt:
            await self._handle_bot_declarations(game_id)
        
        return {
            "decision": response.decision,
            "new_hands_dealt": response.new_hands_dealt,
            "starting_player_id": response.starting_player_id
        }
    
    async def get_game_statistics(
        self,
        game_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive game statistics.
        
        Args:
            game_id: Game ID
            
        Returns:
            Game statistics
        """
        async with self._uow:
            game = await self._uow.games.get_by_id(game_id)
            if not game:
                raise ApplicationException(
                    f"Game {game_id} not found",
                    code="GAME_NOT_FOUND"
                )
            
            # Calculate statistics
            total_turns = sum(getattr(p, 'turns_played', 0) for p in game.players)
            total_pieces_played = sum(getattr(p, 'pieces_played', 0) for p in game.players)
            
            stats = {
                "game_id": game_id,
                "round_number": game.round_number,
                "total_turns": total_turns,
                "total_pieces_played": total_pieces_played,
                "current_leader": self._get_current_leader(game),
                "player_stats": self._get_player_game_stats(game),
                "phase_durations": getattr(game, 'phase_durations', {}),
                "interesting_plays": self._get_interesting_plays(game)
            }
            
            return stats
    
    async def _handle_bot_redeal_responses(
        self,
        game_id: str,
        weak_hands: List[str]
    ) -> None:
        """Handle bot responses to redeal requests."""
        async with self._uow:
            game = await self._uow.games.get_by_id(game_id)
            if not game:
                return
            
            # Check if any bot has weak hand
            bot_weak_hands = []
            for player in game.players:
                if player.is_bot and player.id in weak_hands:
                    bot_weak_hands.append(player.id)
            
            # If bot has weak hand, it should request redeal
            if bot_weak_hands and hasattr(game, 'active_redeal_id'):
                for bot_id in bot_weak_hands:
                    # Bot logic would determine accept/decline
                    # For now, bots with weak hands always accept
                    pass
    
    async def _trigger_bot_plays(self, game_id: str) -> None:
        """Trigger bot players to make their plays."""
        async with self._uow:
            game = await self._uow.games.get_by_id(game_id)
            if not game:
                return
            
            # Check if current player is bot
            current_player = next(
                (p for p in game.players if p.id == game.current_player_id),
                None
            )
            
            if current_player and current_player.is_bot:
                # Get bot action
                game_state = self._create_game_state_for_bot(game)
                bot_action = await self._bot_service.get_bot_action(
                    game_state,
                    current_player.id
                )
                
                # Execute bot play
                if bot_action and bot_action.get("action") == "play":
                    await self.complete_game_turn(
                        game_id=game_id,
                        player_id=current_player.id,
                        pieces=bot_action.get("pieces", [])
                    )
    
    async def _handle_bot_declarations(self, game_id: str) -> None:
        """Handle bot pile declarations."""
        async with self._uow:
            game = await self._uow.games.get_by_id(game_id)
            if not game:
                return
            
            # Get all bot players who need to declare
            for player in game.players:
                if player.is_bot and not hasattr(player, 'declaration'):
                    # Simple bot strategy: declare based on hand strength
                    pile_count = self._calculate_bot_declaration(player)
                    
                    declare_request = DeclareRequest(
                        game_id=game_id,
                        player_id=player.id,
                        pile_count=pile_count
                    )
                    
                    await self._declare_use_case.execute(declare_request)
    
    def _get_current_leader(self, game) -> Dict[str, Any]:
        """Get current game leader."""
        if not game.players:
            return None
        
        leader = max(game.players, key=lambda p: p.score)
        return {
            "player_id": leader.id,
            "player_name": leader.name,
            "score": leader.score,
            "lead_margin": leader.score - sorted(
                [p.score for p in game.players],
                reverse=True
            )[1] if len(game.players) > 1 else 0
        }
    
    def _get_player_game_stats(self, game) -> Dict[str, Dict[str, Any]]:
        """Get per-player game statistics."""
        stats = {}
        
        for player in game.players:
            stats[player.id] = {
                "score": player.score,
                "rounds_won": getattr(player, 'rounds_won', 0),
                "turns_won": getattr(player, 'turns_won', 0),
                "pieces_captured": getattr(player, 'total_pieces_captured', 0),
                "declaration_accuracy": self._calculate_declaration_accuracy(player),
                "is_bot": player.is_bot
            }
        
        return stats
    
    def _get_interesting_plays(self, game) -> List[Dict[str, Any]]:
        """Get notable plays from the game."""
        # This would analyze game history for interesting moments
        return []
    
    def _calculate_declaration_accuracy(self, player) -> float:
        """Calculate how accurate player's declarations have been."""
        if not hasattr(player, 'declaration_history'):
            return 0.0
        
        if not player.declaration_history:
            return 0.0
        
        accurate = sum(
            1 for d in player.declaration_history
            if d['declared'] == d['actual']
        )
        
        return accurate / len(player.declaration_history)
    
    def _create_game_state_for_bot(self, game) -> Dict[str, Any]:
        """Create game state representation for bot decision making."""
        return {
            "phase": game.phase.value,
            "round_number": game.round_number,
            "turn_number": game.turn_number,
            "current_play": getattr(game, 'current_turn_plays', []),
            "player_hands": {
                p.id: len(p.hand) for p in game.players
            },
            "scores": {p.id: p.score for p in game.players}
        }
    
    def _calculate_bot_declaration(self, player) -> int:
        """Simple bot declaration strategy."""
        # Count high-value pieces
        high_pieces = sum(1 for p in player.hand if p.value >= 10)
        
        # Simple strategy: declare based on high pieces
        if high_pieces >= 3:
            return min(3, high_pieces)
        elif high_pieces >= 1:
            return 1
        else:
            return 0