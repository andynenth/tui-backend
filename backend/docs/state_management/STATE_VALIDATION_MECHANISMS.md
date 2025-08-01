# State Validation Mechanisms Design

## Overview

This document outlines the validation mechanisms to ensure state consistency between the Clean Architecture domain model and the state persistence system.

## Validation Layers

### 1. Pre-Transition Validation
Validates state transitions before they occur.

```python
class PreTransitionValidator:
    """Validates transitions before execution."""
    
    def __init__(self):
        self.rules = self._load_validation_rules()
    
    async def validate(
        self,
        current_state: GameState,
        proposed_transition: StateTransition
    ) -> ValidationResult:
        """Validate a proposed state transition."""
        
        # 1. Structural validation
        structural = self._validate_structure(proposed_transition)
        if not structural.valid:
            return structural
        
        # 2. Business rule validation
        business = await self._validate_business_rules(
            current_state,
            proposed_transition
        )
        if not business.valid:
            return business
        
        # 3. Consistency validation
        consistency = self._validate_consistency(
            current_state,
            proposed_transition
        )
        if not consistency.valid:
            return consistency
        
        return ValidationResult(valid=True)
    
    def _validate_structure(self, transition: StateTransition) -> ValidationResult:
        """Validate transition structure."""
        errors = []
        
        # Required fields
        if not transition.from_state:
            errors.append("Missing from_state")
        if not transition.to_state:
            errors.append("Missing to_state")
        if not transition.action:
            errors.append("Missing action")
            
        # Valid phase values
        valid_phases = set(p.value for p in UnifiedGamePhase)
        if transition.from_state not in valid_phases:
            errors.append(f"Invalid from_state: {transition.from_state}")
        if transition.to_state not in valid_phases:
            errors.append(f"Invalid to_state: {transition.to_state}")
        
        if errors:
            return ValidationResult(
                valid=False,
                errors=errors,
                reason="Structural validation failed"
            )
        
        return ValidationResult(valid=True)
```

### 2. Post-Transition Validation
Validates state after transitions to ensure consistency.

```python
class PostTransitionValidator:
    """Validates state consistency after transitions."""
    
    async def validate(
        self,
        game_id: str,
        domain_state: Game,
        persisted_state: PersistedState
    ) -> ConsistencyReport:
        """Compare domain and persisted states."""
        
        report = ConsistencyReport(game_id=game_id)
        
        # 1. Phase consistency
        domain_phase = domain_state.current_phase.value
        persisted_phase = persisted_state.current_state
        
        if domain_phase != persisted_phase:
            # Check if it's a known mapping issue
            unified_domain = UnifiedGamePhase.from_domain_phase(domain_phase)
            unified_persisted = UnifiedGamePhase.from_state_machine_phase(persisted_phase)
            
            if unified_domain.to_domain_phase() == unified_persisted.to_domain_phase():
                # Phases are equivalent
                report.add_warning(
                    "phase_mapping",
                    f"Domain phase {domain_phase} maps to {persisted_phase}"
                )
            else:
                # Real inconsistency
                report.add_error(
                    "phase_mismatch",
                    f"Domain: {domain_phase}, Persisted: {persisted_phase}"
                )
        
        # 2. Player state consistency
        await self._validate_player_states(domain_state, persisted_state, report)
        
        # 3. Game progress consistency
        self._validate_game_progress(domain_state, persisted_state, report)
        
        # 4. Score consistency
        self._validate_scores(domain_state, persisted_state, report)
        
        return report
    
    async def _validate_player_states(
        self,
        domain_state: Game,
        persisted_state: PersistedState,
        report: ConsistencyReport
    ):
        """Validate player-specific state."""
        
        domain_players = {p.name: p for p in domain_state.players}
        persisted_players = persisted_state.context.get("players", {})
        
        # Check player count
        if len(domain_players) != len(persisted_players):
            report.add_error(
                "player_count",
                f"Domain: {len(domain_players)}, Persisted: {len(persisted_players)}"
            )
            return
        
        # Check each player
        for name, domain_player in domain_players.items():
            persisted_player = persisted_players.get(name)
            
            if not persisted_player:
                report.add_error("missing_player", f"Player {name} not in persisted state")
                continue
            
            # Validate player attributes
            if domain_player.score != persisted_player.get("score", 0):
                report.add_error(
                    "score_mismatch",
                    f"Player {name} - Domain: {domain_player.score}, "
                    f"Persisted: {persisted_player.get('score', 0)}"
                )
            
            if len(domain_player.hand) != persisted_player.get("hand_size", 0):
                report.add_warning(
                    "hand_size_mismatch",
                    f"Player {name} - Domain: {len(domain_player.hand)}, "
                    f"Persisted: {persisted_player.get('hand_size', 0)}"
                )
```

### 3. Invariant Validation
Ensures game invariants are maintained.

```python
class GameInvariantValidator:
    """Validates game invariants are maintained."""
    
    INVARIANTS = [
        "total_pieces_constant",
        "turn_order_maintained",
        "score_monotonic_increasing",
        "phase_progression_valid",
        "player_count_constant"
    ]
    
    async def validate_invariants(
        self,
        game_state: GameState,
        transition_history: List[StateTransition]
    ) -> InvariantReport:
        """Check all game invariants."""
        
        report = InvariantReport()
        
        for invariant_name in self.INVARIANTS:
            validator = getattr(self, f"_check_{invariant_name}", None)
            if validator:
                result = await validator(game_state, transition_history)
                report.add_result(invariant_name, result)
        
        return report
    
    async def _check_total_pieces_constant(
        self,
        game_state: GameState,
        history: List[StateTransition]
    ) -> InvariantResult:
        """Total pieces in game should remain constant."""
        
        expected_total = 28  # Domino set size
        
        # Count pieces in all locations
        pieces_in_hands = sum(p.hand_size for p in game_state.players)
        pieces_played = len(game_state.played_pieces)
        pieces_in_deck = game_state.deck_size
        
        actual_total = pieces_in_hands + pieces_played + pieces_in_deck
        
        if actual_total != expected_total:
            return InvariantResult(
                valid=False,
                message=f"Piece count mismatch. Expected: {expected_total}, "
                       f"Actual: {actual_total} "
                       f"(hands: {pieces_in_hands}, played: {pieces_played}, "
                       f"deck: {pieces_in_deck})"
            )
        
        return InvariantResult(valid=True)
    
    async def _check_score_monotonic_increasing(
        self,
        game_state: GameState,
        history: List[StateTransition]
    ) -> InvariantResult:
        """Scores should never decrease."""
        
        # Group transitions by player
        player_scores = {}
        
        for transition in history:
            if "score_update" in transition.action:
                player_id = transition.actor_id
                new_score = transition.payload.get("new_score", 0)
                
                if player_id in player_scores:
                    if new_score < player_scores[player_id]:
                        return InvariantResult(
                            valid=False,
                            message=f"Score decreased for player {player_id}: "
                                   f"{player_scores[player_id]} → {new_score}"
                        )
                
                player_scores[player_id] = new_score
        
        return InvariantResult(valid=True)
```

### 4. Cross-System Validation
Validates consistency across different system components.

```python
class CrossSystemValidator:
    """Validates consistency across system boundaries."""
    
    async def validate_cross_system(
        self,
        game_id: str,
        domain_game: Game,
        state_manager: StatePersistenceManager,
        event_store: EventStore
    ) -> CrossSystemReport:
        """Validate consistency across all systems."""
        
        report = CrossSystemReport(game_id=game_id)
        
        # 1. Domain vs State Machine
        persisted = await state_manager.get_current_state(game_id)
        if persisted:
            domain_vs_state = await self._validate_domain_vs_state(
                domain_game,
                persisted
            )
            report.add_validation("domain_vs_state", domain_vs_state)
        
        # 2. State Machine vs Event Store
        events = await event_store.get_events(game_id)
        state_vs_events = await self._validate_state_vs_events(
            persisted,
            events
        )
        report.add_validation("state_vs_events", state_vs_events)
        
        # 3. Domain vs Event Store
        domain_vs_events = self._validate_domain_vs_events(
            domain_game,
            events
        )
        report.add_validation("domain_vs_events", domain_vs_events)
        
        return report
    
    def _validate_domain_vs_events(
        self,
        domain_game: Game,
        events: List[DomainEvent]
    ) -> ValidationResult:
        """Ensure domain state matches event history."""
        
        # Replay events to build expected state
        replayed_game = Game(room_id=domain_game.room_id)
        
        for event in events:
            try:
                self._apply_event_to_game(replayed_game, event)
            except Exception as e:
                return ValidationResult(
                    valid=False,
                    reason=f"Event replay failed: {e}"
                )
        
        # Compare states
        if not self._games_equal(domain_game, replayed_game):
            return ValidationResult(
                valid=False,
                reason="Domain state doesn't match event replay"
            )
        
        return ValidationResult(valid=True)
```

## Validation Rules Configuration

```yaml
# validation_rules.yaml
phase_transitions:
  NOT_STARTED:
    allowed_next: [PREPARATION]
    validations:
      - has_minimum_players
      - room_is_ready
  
  PREPARATION:
    allowed_next: [DECLARATION]
    validations:
      - all_players_have_pieces
      - weak_hands_checked
  
  DECLARATION:
    allowed_next: [TURN]
    validations:
      - all_players_declared_or_timed_out
      - declaration_period_ended
  
  TURN:
    allowed_next: [TURN, SCORING]
    validations:
      - valid_piece_played
      - turn_order_correct
  
  SCORING:
    allowed_next: [PREPARATION, GAME_OVER]
    validations:
      - round_complete
      - scores_calculated

invariants:
  - name: total_pieces_constant
    description: Total domino pieces must always equal 28
    severity: critical
    
  - name: player_count_constant  
    description: Number of players cannot change during game
    severity: critical
    
  - name: score_monotonic
    description: Player scores can only increase
    severity: critical
    
  - name: turn_order_cyclic
    description: Turns must follow player order
    severity: high
```

## Validation Execution Strategy

### 1. Synchronous Validation (Critical Path)
```python
# In use case
if self._state_adapter:
    # Quick structural validation only
    validation = await self._state_adapter.validate_transition_quick(
        from_phase=old_phase,
        to_phase=new_phase,
        action="play_pieces"
    )
    
    if not validation.valid:
        logger.error(f"Invalid transition: {validation.reason}")
        # Could choose to block or just log
```

### 2. Asynchronous Validation (Background)
```python
# In background worker
async def validation_worker():
    """Background validation of game states."""
    
    while True:
        # Get games needing validation
        games = await get_games_for_validation()
        
        for game_id in games:
            try:
                # Full validation suite
                report = await full_game_validation(game_id)
                
                if not report.is_valid():
                    await handle_validation_failure(game_id, report)
                    
            except Exception as e:
                logger.error(f"Validation failed for {game_id}: {e}")
        
        await asyncio.sleep(30)  # Run every 30 seconds
```

## Recovery Actions

### Automatic Recovery
```python
RECOVERY_ACTIONS = {
    "phase_mismatch": {
        "auto_recover": True,
        "action": "sync_phases",
        "max_attempts": 3
    },
    "score_mismatch": {
        "auto_recover": False,  # Too risky
        "action": "log_and_alert",
        "requires_manual": True
    },
    "missing_player": {
        "auto_recover": False,
        "action": "halt_game",
        "severity": "critical"
    }
}
```

### Manual Recovery Interface
```python
class ManualRecoveryService:
    """Handles manual recovery operations."""
    
    async def get_recovery_options(
        self,
        game_id: str,
        validation_report: ValidationReport
    ) -> List[RecoveryOption]:
        """Get available recovery options."""
        
        options = []
        
        for error in validation_report.errors:
            recovery_config = RECOVERY_ACTIONS.get(error.type)
            
            if recovery_config and not recovery_config["auto_recover"]:
                options.append(
                    RecoveryOption(
                        error_type=error.type,
                        description=error.description,
                        actions=[
                            "rollback_to_snapshot",
                            "sync_from_domain",
                            "sync_from_state_machine",
                            "manual_edit"
                        ],
                        recommended=recovery_config["action"]
                    )
                )
        
        return options
```

## Monitoring and Alerts

### Validation Metrics
```python
VALIDATION_METRICS = {
    "validation.executed": Counter,
    "validation.passed": Counter,
    "validation.failed": Counter,
    "validation.duration": Histogram,
    "validation.error_type": Counter,  # Tagged by error type
    "validation.recovery_attempted": Counter,
    "validation.recovery_success": Counter
}
```

### Alert Conditions
1. **Critical**: Invariant violations (pieces missing, etc.)
2. **High**: Persistent phase mismatches
3. **Medium**: Score inconsistencies
4. **Low**: Warning-level validation issues

## Summary

This validation mechanism design provides:
- **Multi-layer validation** at different points in the flow
- **Configurable rules** via YAML configuration
- **Automatic recovery** for safe scenarios
- **Manual recovery options** for complex issues
- **Comprehensive monitoring** of validation health