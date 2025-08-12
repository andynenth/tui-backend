# backend/services/play_history_v2.py

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.models.play_history import (
    PlayerInfo, InitialState, PieceInfo, DeclarationInfo,
    PlayData, TurnInfo, RoundSummary, RoundHistory, PlayHistoryResponse,
    StarterInfo, DeclarationData, TurnWinner, GameStateAfterTurn,
    CaptureInfo, ScoringInfo
)
from .event_store_v2 import EventStoreV2

logger = logging.getLogger(__name__)


class PlayHistoryV2Service:
    """
    Play History service using optimized schema.
    
    Phase 3 of database optimization - Uses pre-computed round snapshots
    for 10x faster query performance.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize with EventStore V2."""
        self.store = EventStoreV2(db_path)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def build_play_history(
        self,
        room_id: str,
        round_numbers: Optional[List[int]] = None,
        include_ai_analysis: bool = True,
        format: Optional[str] = None
    ) -> PlayHistoryResponse:
        """
        Build play history from optimized schema.
        
        Args:
            room_id: Room identifier
            round_numbers: Specific rounds to include
            include_ai_analysis: Whether to include AI analysis
            format: Response format ('compact' for minimal data)
            
        Returns:
            PlayHistoryResponse with game history
        """
        # Check cache
        cache_key = f"{room_id}:{round_numbers}:{format}:{include_ai_analysis}"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.info(f"Cache hit for room {room_id}")
                return cached_data
        
        logger.info(f"Building play history from V2 schema for room {room_id}")
        
        # Get game summary
        summary = await self.store.get_game_summary(room_id)
        if not summary:
            return PlayHistoryResponse(
                room_id=room_id,
                total_rounds=0,
                players={},
                rounds=[]
            )
        
        # Extract players from summary
        import json
        players_data = summary['players']
        if isinstance(players_data, str):
            players_data = json.loads(players_data)
        players = self._extract_players(players_data)
        
        # Get round snapshots
        snapshots = await self.store.get_round_snapshots(room_id, round_numbers)
        logger.info(f"Retrieved {len(snapshots)} snapshots for room {room_id}")
        
        # Convert snapshots to RoundHistory objects
        rounds = []
        for snapshot in snapshots:
            try:
                if format == 'compact':
                    round_history = self._build_compact_round(snapshot, players)
                else:
                    round_history = self._build_full_round(snapshot, players, include_ai_analysis)
                
                if round_history:
                    rounds.append(round_history)
                else:
                    logger.warning(f"Failed to build round history for snapshot: {snapshot.get('round_number', 'unknown')}")
            except Exception as e:
                logger.error(f"Error building round history: {e}", exc_info=True)
        
        # Build response
        response = PlayHistoryResponse(
            room_id=room_id,
            total_rounds=len(rounds),
            players=players,
            rounds=rounds
        )
        
        # Cache the result
        self._cache[cache_key] = (response, time.time())
        
        return response
    
    def _extract_players(self, players_data: List[Dict[str, Any]]) -> Dict[str, PlayerInfo]:
        """Extract player information from summary data."""
        players = {}
        
        for player_data in players_data:
            player_name = player_data.get('player_name', '')
            player_id = player_name.lower().replace(' ', '_')
            
            players[player_name] = PlayerInfo(
                player_id=player_id,
                player_name=player_name,
                player_type=player_data.get('player_type', 'ai'),
                ai_version='v2' if player_data.get('player_type') == 'ai' else None
            )
        
        return players
    
    def _build_full_round(
        self,
        snapshot: Dict[str, Any],
        players: Dict[str, PlayerInfo],
        include_ai_analysis: bool
    ) -> RoundHistory:
        """Build complete round history from snapshot."""
        round_num = snapshot['round_number']
        
        # Build initial state
        initial_state = InitialState(
            starter=StarterInfo(
                player_id=snapshot['starter_player'].lower().replace(' ', '_'),
                player_name=snapshot['starter_player'],
                reason=snapshot.get('starter_reason', 'default'),
                highest_card='GENERAL_RED(14)' if snapshot.get('starter_reason') == 'has_general_red' else None
            ),
            player_order=list(snapshot['initial_hands'].keys())
        )
        
        # Build hands dealt
        hands_dealt = {}
        for player_name, hand in snapshot['initial_hands'].items():
            hands_dealt[player_name] = [
                PieceInfo(kind=p['kind'], point=p['point'])
                for p in hand
            ]
        
        # Build declaration phase
        declaration_phase = self._build_declaration_info(
            snapshot['declarations'],
            players
        )
        
        # Build turn history
        turn_history = self._build_turn_history(
            snapshot['turn_sequence'],
            snapshot['declarations'],
            include_ai_analysis
        )
        
        # Build round summary
        round_summary = self._build_round_summary(
            snapshot,
            players
        )
        
        return RoundHistory(
            round_number=round_num,
            initial_state=initial_state,
            hands_dealt=hands_dealt,
            declaration_phase=declaration_phase,
            turn_history=turn_history,
            round_summary=round_summary
        )
    
    def _build_compact_round(
        self,
        snapshot: Dict[str, Any],
        players: Dict[str, PlayerInfo]
    ) -> RoundHistory:
        """Build compact round history (minimal data)."""
        round_num = snapshot['round_number']
        
        # Build initial state
        initial_state = InitialState(
            starter=StarterInfo(
                player_id=snapshot['starter_player'].lower().replace(' ', '_'),
                player_name=snapshot['starter_player'],
                reason=snapshot.get('starter_reason', 'default'),
                highest_card=None
            ),
            player_order=list(snapshot['initial_hands'].keys())
        )
        
        # Build declaration phase
        declaration_phase = self._build_declaration_info(
            snapshot['declarations'],
            players
        )
        
        # Build round summary
        round_summary = self._build_round_summary(
            snapshot,
            players
        )
        
        return RoundHistory(
            round_number=round_num,
            initial_state=initial_state,
            hands_dealt={},  # Empty for compact
            declaration_phase=declaration_phase,
            turn_history=[],  # Empty for compact
            round_summary=round_summary
        )
    
    def _build_declaration_info(
        self,
        declarations: Dict[str, int],
        players: Dict[str, PlayerInfo]
    ) -> DeclarationInfo:
        """Build declaration info from snapshot data."""
        declaration_list = []
        pile_room_calculation = {}
        total_declared = 0
        running_total = 0
        
        player_order = list(players.keys())
        
        for position, player_name in enumerate(player_order):
            declared = declarations.get(player_name, 0)
            
            # Pile room calculation
            if position == 0:
                pile_room = 8
            else:
                pile_room = max(0, 8 - running_total)
            
            pile_room_calculation[player_name] = pile_room
            
            # Strategy notes
            if position == 0:
                strategy_notes = "starter with full pile room"
            elif declared == 0:
                strategy_notes = "conservative play" if pile_room > 0 else "forced zero"
            else:
                strategy_notes = f"competing for {pile_room} pile room"
            
            declaration_list.append(DeclarationData(
                player_id=player_name.lower().replace(' ', '_'),
                declared=declared,
                position=position,
                strategy_notes=strategy_notes
            ))
            
            running_total += declared
            total_declared += declared
        
        return DeclarationInfo(
            declarations=declaration_list,
            total_declared=total_declared,
            pile_room_calculation=pile_room_calculation
        )
    
    def _build_turn_history(
        self,
        turn_sequence: List[Dict[str, Any]],
        declarations: Dict[str, int],
        include_ai_analysis: bool
    ) -> List[TurnInfo]:
        """Build turn history from snapshot data."""
        turns = []
        
        for turn_data in turn_sequence:
            turn_num = turn_data['turn_number']
            
            # Build plays
            plays = []
            for player_name, play_info in turn_data['plays'].items():
                pieces = [
                    PieceInfo(kind=p.get('kind', p), point=p.get('point', 0))
                    for p in play_info.get('pieces', [])
                ]
                
                play = PlayData(
                    player_id=player_name.lower().replace(' ', '_'),
                    player_name=player_name,
                    pieces_played=pieces,
                    play_type=self._get_play_type(pieces),
                    hand_before=[],  # Not stored in snapshot
                    hand_after=[],   # Not stored in snapshot
                    captured_count=0,  # Will be calculated
                    declared_count=declarations.get(player_name, 0),
                    ai_decision_analysis=None  # TODO: Add if needed
                )
                plays.append(play)
            
            # Build winner info
            winner_info = None
            if turn_data.get('winner'):
                winner_name = turn_data['winner']
                winner_play = next(
                    (p for p in plays if p.player_name == winner_name),
                    None
                )
                if winner_play:
                    winner_info = TurnWinner(
                        player_id=winner_name.lower().replace(' ', '_'),
                        player_name=winner_name,
                        winning_play=winner_play.pieces_played,
                        pieces_captured=turn_data.get('piles_won', 0)
                    )
            
            # Build game state after turn (simplified)
            game_state_after = {}
            
            turn = TurnInfo(
                turn_number=turn_num,
                plays=plays,
                winner=winner_info,
                next_starter=turn_data.get('winner', turn_data.get('starter', '')),
                game_state_after=game_state_after
            )
            turns.append(turn)
        
        return turns
    
    def _build_round_summary(
        self,
        snapshot: Dict[str, Any],
        players: Dict[str, PlayerInfo]
    ) -> RoundSummary:
        """Build round summary from snapshot data."""
        final_captures = {}
        scoring = {}
        
        round_scores = snapshot.get('round_scores', {})
        declarations = snapshot.get('declarations', {})
        
        # Calculate captures from scores
        for player_name in players:
            declared = declarations.get(player_name, 0)
            score = round_scores.get(player_name, 0)
            
            # Infer captured from score
            if score == 0 and declared > 0:
                # Exact match
                captured = declared
                difference = 0
                reason = "exact_match"
                multiplier = 0
            elif score > 0:
                # Exceeded (score = captured - declared)
                captured = declared + score
                difference = score
                reason = f"exceeded_by_{abs(difference)}"
                multiplier = 1
            else:
                # Missed (score = 2 * (captured - declared))
                difference = score // 2
                captured = declared + difference
                reason = f"missed_by_{abs(difference)}"
                multiplier = 2
            
            final_captures[player_name] = CaptureInfo(
                captured=captured,
                declared=declared,
                difference=difference
            )
            
            scoring[player_name] = ScoringInfo(
                points=score,
                multiplier=multiplier,
                reason=reason
            )
        
        return RoundSummary(
            total_turns=len(snapshot.get('turn_sequence', [])),
            final_captures=final_captures,
            scoring=scoring,
            cumulative_scores=snapshot.get('cumulative_scores', {})
        )
    
    def _get_play_type(self, pieces: List[PieceInfo]) -> str:
        """Determine play type from pieces."""
        if not pieces:
            return "UNKNOWN"
        
        count = len(pieces)
        if count == 1:
            return "SINGLE"
        elif count == 2:
            # Check if same kind
            if all(p.kind == pieces[0].kind for p in pieces):
                return "PAIR"
            else:
                return "DOUBLE"
        elif count == 3:
            if all(p.kind == pieces[0].kind for p in pieces):
                if "SOLDIER" in pieces[0].kind:
                    return "THREE_OF_A_KIND"
                else:
                    return "TRIPLE"
            else:
                return "TRIPLE"
        elif count == 4:
            return "QUADRUPLE"
        elif count == 5:
            return "QUINTUPLE"
        elif count == 6:
            return "SEXTUPLE"
        else:
            return "MULTIPLE"