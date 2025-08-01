# Phase Transition Workflows Design

## Overview

This document maps out how game phase transitions will be tracked and managed through the state persistence system.

## Current Phase Transitions

### Domain Phases (6 phases)
1. NOT_STARTED → PREPARATION
2. PREPARATION → DECLARATION  
3. DECLARATION → TURN
4. TURN → SCORING
5. SCORING → PREPARATION (new round) or GAME_OVER
6. GAME_OVER (terminal)

### State Machine Phases (11 phases)
Includes all domain phases plus:
- WAITING (before NOT_STARTED)
- ROUND_START (between rounds)
- TURN_END (after each turn)
- ROUND_END (after scoring)
- ERROR (error recovery state)

## Unified Phase Transition Model

### Core Transitions to Track

```python
CRITICAL_TRANSITIONS = {
    # Game lifecycle
    ("NOT_STARTED", "PREPARATION"): {
        "trigger": "start_game",
        "persist": True,
        "snapshot": True,
        "validation": ["has_players", "room_ready"]
    },
    
    # Round flow
    ("PREPARATION", "DECLARATION"): {
        "trigger": "pieces_dealt",
        "persist": True,
        "snapshot": False,
        "validation": ["all_players_have_pieces"]
    },
    
    ("DECLARATION", "TURN"): {
        "trigger": "declarations_complete",
        "persist": True,
        "snapshot": False,
        "validation": ["all_declared_or_timed_out"]
    },
    
    ("TURN", "TURN"): {
        "trigger": "play_pieces",
        "persist": False,  # Too frequent
        "snapshot": False,
        "validation": ["valid_play"]
    },
    
    ("TURN", "SCORING"): {
        "trigger": "round_complete",
        "persist": True,
        "snapshot": True,
        "validation": ["all_pieces_played_or_round_won"]
    },
    
    ("SCORING", "PREPARATION"): {
        "trigger": "new_round",
        "persist": True,
        "snapshot": True,
        "validation": ["scores_calculated", "not_game_over"]
    },
    
    ("SCORING", "GAME_OVER"): {
        "trigger": "game_complete",
        "persist": True,
        "snapshot": True,
        "validation": ["win_condition_met"]
    }
}
```

### Transition Context Requirements

```python
@dataclass
class PhaseTransitionContext:
    """Rich context for phase transitions."""
    
    # Basic info
    game_id: str
    room_id: str
    from_phase: UnifiedGamePhase
    to_phase: UnifiedGamePhase
    trigger: str
    
    # Game state
    round_number: int
    turn_number: int
    current_player_id: Optional[str]
    
    # Transition data
    actor_id: Optional[str]  # Who triggered it
    timestamp: datetime
    duration_ms: int  # Time in previous phase
    
    # Validation
    validations_passed: List[str]
    warnings: List[str]
    
    # Payload
    transition_data: Dict[str, Any]
```

### State Validation Rules

```python
class PhaseTransitionValidator:
    """Validates phase transitions are legal."""
    
    def validate_transition(
        self,
        context: PhaseTransitionContext,
        game_state: GameState
    ) -> ValidationResult:
        """Validate a phase transition is allowed."""
        
        # Check transition is defined
        key = (context.from_phase.value, context.to_phase.value)
        if key not in CRITICAL_TRANSITIONS:
            return ValidationResult(
                valid=False,
                reason=f"Undefined transition: {key}"
            )
        
        # Check phase sequence
        if context.to_phase not in context.from_phase.next_phases():
            return ValidationResult(
                valid=False,
                reason=f"Invalid sequence: {context.from_phase} → {context.to_phase}"
            )
        
        # Run specific validations
        config = CRITICAL_TRANSITIONS[key]
        for validation in config["validation"]:
            result = self._run_validation(validation, game_state)
            if not result.valid:
                return result
        
        return ValidationResult(valid=True)
    
    def _run_validation(
        self,
        validation_name: str,
        game_state: GameState
    ) -> ValidationResult:
        """Run specific validation check."""
        validators = {
            "has_players": lambda s: len(s.players) >= 2,
            "room_ready": lambda s: s.room_status == "READY",
            "all_players_have_pieces": lambda s: all(p.hand_size > 0 for p in s.players),
            "all_declared_or_timed_out": lambda s: s.declarations_complete,
            "valid_play": lambda s: s.last_play_valid,
            "scores_calculated": lambda s: s.round_scores_set,
            "win_condition_met": lambda s: any(p.score >= s.max_score for p in s.players)
        }
        
        validator = validators.get(validation_name)
        if not validator:
            return ValidationResult(valid=True)  # Unknown validation passes
            
        try:
            if validator(game_state):
                return ValidationResult(valid=True)
            else:
                return ValidationResult(
                    valid=False,
                    reason=f"Validation failed: {validation_name}"
                )
        except Exception as e:
            return ValidationResult(
                valid=False,
                reason=f"Validation error: {validation_name} - {str(e)}"
            )
```

## Integration with StateManagementAdapter

### Enhanced Phase Tracking

```python
class StateManagementAdapter:
    
    async def track_phase_change(
        self,
        context: StateTransitionContext,
        from_phase: DomainGamePhase,
        to_phase: DomainGamePhase,
        trigger: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Enhanced phase tracking with validation."""
        
        if not self.enabled or not self._state_manager:
            return True
            
        try:
            # Create rich context
            transition_context = PhaseTransitionContext(
                game_id=context.game_id,
                room_id=context.room_id,
                from_phase=UnifiedGamePhase.from_domain_phase(from_phase.value),
                to_phase=UnifiedGamePhase.from_domain_phase(to_phase.value),
                trigger=trigger,
                round_number=payload.get("round_number", 0),
                turn_number=payload.get("turn_number", 0),
                current_player_id=payload.get("current_player_id"),
                actor_id=context.actor_id,
                timestamp=datetime.utcnow(),
                duration_ms=self._calculate_phase_duration(context.game_id),
                validations_passed=[],
                warnings=[],
                transition_data=payload or {}
            )
            
            # Validate transition
            if self._validator:
                game_state = await self._load_game_state(context.game_id)
                validation = self._validator.validate_transition(
                    transition_context,
                    game_state
                )
                
                if not validation.valid:
                    logger.warning(
                        f"Invalid phase transition: {validation.reason}",
                        extra={"context": transition_context}
                    )
                    transition_context.warnings.append(validation.reason)
            
            # Check if we should persist
            key = (from_phase.value, to_phase.value)
            config = CRITICAL_TRANSITIONS.get(key, {})
            
            if config.get("persist", True):
                # Create state transition
                transition = StateTransition(
                    from_state=transition_context.from_phase.value,
                    to_state=transition_context.to_phase.value,
                    action=trigger,
                    payload=transition_context.transition_data,
                    actor_id=transition_context.actor_id,
                    metadata={
                        "round": transition_context.round_number,
                        "turn": transition_context.turn_number,
                        "duration_ms": transition_context.duration_ms,
                        "validations": transition_context.validations_passed,
                        "warnings": transition_context.warnings
                    }
                )
                
                # Determine persistence policy
                policy = AutoPersistencePolicy(
                    persist_on_transition=config.get("persist", True),
                    persist_on_phase_change=True,
                    persist_on_error=True,
                    create_snapshot=config.get("snapshot", False)
                )
                
                await self._state_manager.handle_transition(
                    state_machine_id=context.game_id,
                    transition=transition,
                    policy=policy
                )
                
                logger.info(
                    f"Phase transition tracked: {from_phase.value} → {to_phase.value}",
                    extra={
                        "game_id": context.game_id,
                        "trigger": trigger,
                        "duration_ms": transition_context.duration_ms
                    }
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track phase change: {e}")
            return False
```

### Automatic Snapshot Points

```python
SNAPSHOT_TRIGGERS = {
    "start_game": {
        "reason": "Game initialization",
        "include_hands": True
    },
    "round_complete": {
        "reason": "Round ended",
        "include_scores": True
    },
    "game_complete": {
        "reason": "Game finished",
        "include_full_history": True
    },
    "error_recovery": {
        "reason": "Error state entered",
        "include_debug": True
    }
}

async def should_create_snapshot(
    self,
    trigger: str,
    context: PhaseTransitionContext
) -> bool:
    """Determine if snapshot should be created."""
    
    # Check trigger-based snapshots
    if trigger in SNAPSHOT_TRIGGERS:
        return True
    
    # Check time-based snapshots (every 5 minutes)
    last_snapshot = await self._get_last_snapshot_time(context.game_id)
    if datetime.utcnow() - last_snapshot > timedelta(minutes=5):
        return True
    
    # Check transition-based snapshots
    key = (context.from_phase.value, context.to_phase.value)
    config = CRITICAL_TRANSITIONS.get(key, {})
    return config.get("snapshot", False)
```

## Recovery Workflows

### Phase Consistency Recovery

```python
class PhaseRecoveryService:
    """Handles recovery when phases get out of sync."""
    
    async def recover_phase_consistency(
        self,
        game_id: str,
        domain_phase: str,
        state_machine_phase: str
    ) -> RecoveryResult:
        """Recover when domain and state machine phases diverge."""
        
        # Load full state history
        history = await self._state_manager.get_transition_history(game_id)
        
        # Find last known good state
        last_good = self._find_last_consistent_state(history)
        
        # Determine recovery strategy
        if self._can_fast_forward(last_good, domain_phase):
            # Fast-forward state machine to match domain
            return await self._fast_forward_recovery(
                game_id,
                last_good,
                domain_phase
            )
        elif self._can_rollback(last_good, state_machine_phase):
            # Rollback domain to match state machine
            return await self._rollback_recovery(
                game_id,
                last_good,
                state_machine_phase
            )
        else:
            # Need manual intervention
            return RecoveryResult(
                success=False,
                reason="Manual intervention required",
                suggested_action="Contact support"
            )
```

## Metrics and Monitoring

### Phase Transition Metrics

```python
PHASE_METRICS = {
    "phase_transition.duration": {
        "type": "histogram",
        "unit": "milliseconds",
        "tags": ["from_phase", "to_phase", "trigger"]
    },
    "phase_transition.validation_failure": {
        "type": "counter",
        "tags": ["from_phase", "to_phase", "validation_type"]
    },
    "phase_transition.recovery_needed": {
        "type": "counter",
        "tags": ["game_id", "inconsistency_type"]
    },
    "phase_transition.snapshot_created": {
        "type": "counter",
        "tags": ["trigger", "phase"]
    }
}
```

### Phase Duration Tracking

```python
async def track_phase_duration(self, context: PhaseTransitionContext):
    """Track how long each phase lasts."""
    
    # Store phase entry time
    await self._cache.set(
        f"phase_start:{context.game_id}:{context.to_phase}",
        context.timestamp.timestamp(),
        ttl=3600  # 1 hour
    )
    
    # Calculate previous phase duration
    if context.from_phase:
        start_key = f"phase_start:{context.game_id}:{context.from_phase}"
        start_time = await self._cache.get(start_key)
        
        if start_time:
            duration = context.timestamp.timestamp() - float(start_time)
            
            # Track metric
            self._metrics.histogram(
                "game.phase_duration",
                duration * 1000,  # Convert to ms
                tags={
                    "phase": context.from_phase.value,
                    "game_id": context.game_id
                }
            )
            
            # Alert on unusual durations
            expected = EXPECTED_PHASE_DURATIONS.get(context.from_phase.value)
            if expected and duration > expected * 2:
                logger.warning(
                    f"Phase {context.from_phase} took {duration}s "
                    f"(expected ~{expected}s)",
                    extra={"game_id": context.game_id}
                )
```

## Summary

This phase transition workflow design provides:
- **Unified phase model** bridging domain and state machine
- **Rich transition context** with validation and metadata
- **Automatic snapshots** at critical points
- **Recovery mechanisms** for phase inconsistencies
- **Comprehensive metrics** for monitoring phase flow