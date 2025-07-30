"""
Integration example showing how to use event sourcing with the game system.

This demonstrates how the existing game engine can be enhanced with
event sourcing for audit trails, replay, and analytics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from backend.engine.game import Game
from backend.engine.state_machine.game_state_machine import GameStateMachine, GamePhase
from .hybrid_event_store import HybridEventStore, Event, EventType
from .event_sourcing import DomainEvent, EventSourcedAggregate


# Domain events specific to Liap game


class WeakHandRequestedEvent(DomainEvent):
    """Event when a player requests weak hand redeal."""

    event_type = EventType.PLAYER_ACTION

    def __init__(self, player_name: str, hand_value: int):
        super().__init__(
            {
                "action_type": "weak_hand_request",
                "player_name": player_name,
                "hand_value": hand_value,
            }
        )


class RedealAcceptedEvent(DomainEvent):
    """Event when a player accepts redeal."""

    event_type = EventType.PLAYER_ACTION

    def __init__(self, player_name: str):
        super().__init__({"action_type": "redeal_accepted", "player_name": player_name})


class RedealDeclinedEvent(DomainEvent):
    """Event when a player declines redeal."""

    event_type = EventType.PLAYER_ACTION

    def __init__(self, player_name: str, becomes_starter: bool):
        super().__init__(
            {
                "action_type": "redeal_declined",
                "player_name": player_name,
                "becomes_starter": becomes_starter,
            }
        )


class DeclarationMadeEvent(DomainEvent):
    """Event when a player makes a pile declaration."""

    event_type = EventType.PLAYER_ACTION

    def __init__(self, player_name: str, pile_count: int):
        super().__init__(
            {
                "action_type": "declaration_made",
                "player_name": player_name,
                "pile_count": pile_count,
            }
        )


class PiecesPlayedEvent(DomainEvent):
    """Event when pieces are played in a turn."""

    event_type = EventType.PLAYER_ACTION

    def __init__(
        self, player_name: str, pieces: List[Dict[str, Any]], pile_winner: Optional[str]
    ):
        super().__init__(
            {
                "action_type": "pieces_played",
                "player_name": player_name,
                "pieces": pieces,
                "pile_winner": pile_winner,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


class GameEventRecorder:
    """
    Records game events to the event store.

    This can be integrated with the existing game engine to capture
    all game actions without modifying core game logic.
    """

    def __init__(self, event_store: HybridEventStore):
        self._event_store = event_store

    async def record_game_created(self, game: Game, room_id: str) -> None:
        """Record game creation."""
        event = Event(
            id=f"evt_{game.game_id}_{datetime.utcnow().timestamp()}",
            type=EventType.GAME_CREATED,
            aggregate_id=game.game_id,
            aggregate_type="game",
            data={
                "room_id": room_id,
                "players": [p.name for p in game.players],
                "config": {
                    "starting_player": game.starting_player,
                    "round_number": game.round_number,
                    "max_rounds": 20,
                },
            },
            metadata={"source": "game_engine"},
            timestamp=datetime.utcnow(),
            sequence_number=0,
        )

        await self._event_store.append_event(event)

    async def record_phase_change(
        self,
        game: Game,
        from_phase: GamePhase,
        to_phase: GamePhase,
        phase_data: Dict[str, Any],
    ) -> None:
        """Record phase transitions."""
        event = Event(
            id=f"evt_{game.game_id}_{datetime.utcnow().timestamp()}",
            type=EventType.PHASE_CHANGED,
            aggregate_id=game.game_id,
            aggregate_type="game",
            data={
                "from_phase": from_phase.value,
                "to_phase": to_phase.value,
                "phase_data": phase_data,
                "round_number": game.round_number,
                "turn_number": game.turn_number,
            },
            metadata={"source": "state_machine"},
            timestamp=datetime.utcnow(),
            sequence_number=0,
        )

        await self._event_store.append_event(event)

    async def record_player_action(
        self,
        game: Game,
        player_name: str,
        action_type: str,
        action_data: Dict[str, Any],
    ) -> None:
        """Record generic player action."""
        event = Event(
            id=f"evt_{game.game_id}_{datetime.utcnow().timestamp()}",
            type=EventType.PLAYER_ACTION,
            aggregate_id=game.game_id,
            aggregate_type="game",
            data={
                "player_name": player_name,
                "action_type": action_type,
                "action_data": action_data,
                "game_state": {
                    "phase": game.current_phase,
                    "round": game.round_number,
                    "turn": game.turn_number,
                },
            },
            metadata={"source": "player_input"},
            timestamp=datetime.utcnow(),
            sequence_number=0,
        )

        await self._event_store.append_event(event)

    async def record_game_completed(
        self, game: Game, final_scores: Dict[str, int], winner: Optional[str]
    ) -> None:
        """Record game completion."""
        event = Event(
            id=f"evt_{game.game_id}_{datetime.utcnow().timestamp()}",
            type=EventType.GAME_COMPLETED,
            aggregate_id=game.game_id,
            aggregate_type="game",
            data={
                "final_scores": final_scores,
                "winner": winner,
                "total_rounds": game.round_number,
                "completion_reason": "score_limit" if winner else "max_rounds",
                "duration_seconds": (
                    (datetime.utcnow() - game.created_at).total_seconds()
                    if hasattr(game, "created_at")
                    else None
                ),
            },
            metadata={"source": "game_engine"},
            timestamp=datetime.utcnow(),
            sequence_number=0,
        )

        await self._event_store.append_event(event)

        # Mark the stream as completed for archival
        stream = await self._event_store.get_stream(game.game_id)
        if stream:
            stream.is_completed = True


class GameReplayService:
    """
    Service for replaying games from event history.

    This allows viewing historical games, debugging, and analysis.
    """

    def __init__(self, event_store: HybridEventStore):
        self._event_store = event_store

    async def replay_game(self, game_id: str) -> Dict[str, Any]:
        """
        Replay a game and return its history.

        Returns:
            Dictionary with game timeline and key events
        """
        events = await self._event_store.get_events(game_id)

        if not events:
            return {"error": "Game not found"}

        timeline = []
        game_info = {}

        for event in events:
            if event.type == EventType.GAME_CREATED:
                game_info = {
                    "game_id": game_id,
                    "room_id": event.data["room_id"],
                    "players": event.data["players"],
                    "started_at": event.timestamp.isoformat(),
                }

            timeline.append(
                {
                    "timestamp": event.timestamp.isoformat(),
                    "type": event.type.value,
                    "data": event.data,
                    "sequence": event.sequence_number,
                }
            )

        return {
            "game_info": game_info,
            "timeline": timeline,
            "total_events": len(events),
        }

    async def get_player_history(self, player_name: str) -> List[Dict[str, Any]]:
        """Get all games and actions for a player."""
        # Get all game created events
        created_events = await self._event_store.get_all_events(
            event_type=EventType.GAME_CREATED
        )

        player_games = []

        for event in created_events:
            if player_name in event.data.get("players", []):
                # Get all events for this game
                game_events = await self._event_store.get_events(event.aggregate_id)

                # Find player actions
                player_actions = [
                    e
                    for e in game_events
                    if e.type == EventType.PLAYER_ACTION
                    and e.data.get("player_name") == player_name
                ]

                # Check if game completed
                completed = any(e.type == EventType.GAME_COMPLETED for e in game_events)

                player_games.append(
                    {
                        "game_id": event.aggregate_id,
                        "started_at": event.timestamp.isoformat(),
                        "total_actions": len(player_actions),
                        "completed": completed,
                    }
                )

        return player_games


class GameAnalyticsService:
    """
    Analytics service that uses event data for insights.

    This demonstrates the power of event sourcing for analytics.
    """

    def __init__(self, event_store: HybridEventStore):
        self._event_store = event_store

    async def get_game_statistics(self) -> Dict[str, Any]:
        """Get overall game statistics."""
        all_events = await self._event_store.get_all_events()

        stats = {
            "total_games": 0,
            "completed_games": 0,
            "total_rounds": 0,
            "average_game_duration": 0,
            "most_active_players": {},
            "phase_statistics": {},
            "action_counts": {},
        }

        game_durations = []

        for event in all_events:
            if event.type == EventType.GAME_CREATED:
                stats["total_games"] += 1

            elif event.type == EventType.GAME_COMPLETED:
                stats["completed_games"] += 1
                if "duration_seconds" in event.data:
                    game_durations.append(event.data["duration_seconds"])

            elif event.type == EventType.PHASE_CHANGED:
                phase = event.data.get("to_phase", "unknown")
                stats["phase_statistics"][phase] = (
                    stats["phase_statistics"].get(phase, 0) + 1
                )

            elif event.type == EventType.PLAYER_ACTION:
                action = event.data.get("action_type", "unknown")
                stats["action_counts"][action] = (
                    stats["action_counts"].get(action, 0) + 1
                )

                player = event.data.get("player_name")
                if player:
                    stats["most_active_players"][player] = (
                        stats["most_active_players"].get(player, 0) + 1
                    )

        if game_durations:
            stats["average_game_duration"] = sum(game_durations) / len(game_durations)

        # Sort most active players
        stats["most_active_players"] = dict(
            sorted(
                stats["most_active_players"].items(), key=lambda x: x[1], reverse=True
            )[:10]
        )

        return stats

    async def analyze_weak_hand_patterns(self) -> Dict[str, Any]:
        """Analyze weak hand redeal patterns."""
        action_events = await self._event_store.get_all_events(
            event_type=EventType.PLAYER_ACTION
        )

        weak_hand_stats = {
            "total_requests": 0,
            "accepted_redeals": 0,
            "declined_redeals": 0,
            "became_starter": 0,
            "by_player": {},
        }

        for event in action_events:
            action_type = event.data.get("action_type")
            player = event.data.get("player_name", "unknown")

            if action_type == "weak_hand_request":
                weak_hand_stats["total_requests"] += 1

                if player not in weak_hand_stats["by_player"]:
                    weak_hand_stats["by_player"][player] = {
                        "requests": 0,
                        "accepted": 0,
                        "declined": 0,
                    }
                weak_hand_stats["by_player"][player]["requests"] += 1

            elif action_type == "redeal_accepted":
                weak_hand_stats["accepted_redeals"] += 1
                if player in weak_hand_stats["by_player"]:
                    weak_hand_stats["by_player"][player]["accepted"] += 1

            elif action_type == "redeal_declined":
                weak_hand_stats["declined_redeals"] += 1
                if event.data.get("becomes_starter"):
                    weak_hand_stats["became_starter"] += 1
                if player in weak_hand_stats["by_player"]:
                    weak_hand_stats["by_player"][player]["declined"] += 1

        return weak_hand_stats


# Example integration with existing game system


async def integrate_event_store_with_game():
    """
    Example of how to integrate event store with existing game system.

    This would be added to the game initialization and state machine.
    """
    # Create event store
    event_store = HybridEventStore(
        memory_capacity=50000, archive_completed_games=True, archive_after_hours=24
    )
    await event_store.start()

    # Create services
    recorder = GameEventRecorder(event_store)
    replay_service = GameReplayService(event_store)
    analytics = GameAnalyticsService(event_store)

    # In the game creation flow:
    # game = Game(players=players)
    # await recorder.record_game_created(game, room_id)

    # In the state machine transitions:
    # await recorder.record_phase_change(game, old_phase, new_phase, phase_data)

    # In player action handlers:
    # await recorder.record_player_action(game, player_name, action_type, action_data)

    # When game completes:
    # await recorder.record_game_completed(game, scores, winner)

    return event_store, recorder, replay_service, analytics
