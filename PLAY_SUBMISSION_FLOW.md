# Complete Play Submission Flow Documentation

This document traces the complete data flow from when a player submits a play until the end of the round, based solely on the actual code implementation.

## 1. Frontend Play Submission

### 1.1 Player Action (GameService.ts:178-208)
```javascript
playPieces(indices: number[]): void {
    // Frontend validation
    - Validates indices are valid
    - Checks if it's player's turn
    - Validates piece count matches required (if set)
    
    // Sends WebSocket message
    this.sendAction('play', { 
        piece_indices: indices,  // [0, 2, 4]
        player_name: this.state.playerName,
        play_value: totalValue  // Sum of piece points
    });
}
```

## 2. Backend WebSocket Reception

### 2.1 WebSocket Handler (ws.py:564-623)
```python
elif event_name == "play":
    # Extract data
    player_name = event_data.get("player_name")
    indices = event_data.get("piece_indices", [])
    
    # Convert indices to actual pieces
    player = find_player(player_name)
    pieces = []
    for idx in indices:
        if 0 <= idx < len(player.hand):
            pieces.append(player.hand[idx])  # Gets actual Piece objects
    
    # Create GameAction (NO play type determination!)
    action = GameAction(
        player_name=player_name,
        action_type=ActionType.PLAY_PIECES,
        payload={"pieces": pieces}  # Only pieces, no play_type!
    )
    
    # Queue for state machine
    result = await room.game_state_machine.handle_action(action)
```

**CRITICAL ISSUE**: The WebSocket handler does NOT determine play type or validate pieces.

## 3. State Machine Processing

### 3.1 Turn State Validation (turn_state.py:229-275)
```python
async def _validate_play_pieces(self, action: GameAction) -> bool:
    # ✅ Validates turn order
    if action.player_name != current_player:
        return False
    
    # ✅ Validates hasn't already played
    if action.player_name in self.turn_plays:
        return False
    
    # ✅ Validates piece count
    if self.required_piece_count is None:
        if not (1 <= piece_count <= 6):  # Starter: 1-6 pieces
            return False
    else:
        if piece_count != self.required_piece_count:  # Others match starter
            return False
    
    # ❌ TODO: Add piece validity checks (line 272-273)
    # For now, assume pieces are valid
    
    return True
```

**CRITICAL ISSUES**:
- No validation that pieces form valid combinations
- No validation that player actually has these pieces
- No validation that play can beat previous plays

### 3.2 Play Processing (turn_state.py:277-385)
```python
async def _handle_play_pieces(self, action: GameAction) -> Dict[str, Any]:
    pieces = payload["pieces"]
    
    # If starter, set required count
    if self.required_piece_count is None:
        self.required_piece_count = piece_count
    
    # Store the play (with default values!)
    play_data = {
        "pieces": pieces.copy(),
        "piece_count": piece_count,
        "play_type": payload.get("play_type", "unknown"),  # Always "unknown"!
        "play_value": payload.get("play_value", 0),  # Always 0!
        "is_valid": payload.get("is_valid", True),  # Always True!
        "timestamp": action.timestamp,
    }
    
    self.turn_plays[action.player_name] = play_data
    
    # Move to next player
    self.current_player_index += 1
    
    # Check if turn is complete
    if self.current_player_index >= len(self.turn_order):
        await self._complete_turn()
    
    # Broadcast update
    await self.update_phase_data({
        "current_player": next_player,
        "required_piece_count": self.required_piece_count,
        "turn_plays": self.turn_plays.copy(),
        "turn_complete": self.turn_complete,
        "current_turn_number": current_turn_number,
    })
```

**CRITICAL**: Pieces are NOT removed from player's hand at this point!

## 4. Turn Completion

### 4.1 Determine Winner (turn_state.py:433-526)
```python
def _determine_turn_winner(self) -> Optional[str]:
    # Convert to TurnPlay objects
    turn_play_objects = []
    for player_name in self.turn_order:
        if player_name in self.turn_plays:
            play_data = self.turn_plays[player_name]
            turn_play = TurnPlay(
                player=player_obj,
                pieces=pieces,
                is_valid=is_valid  # Always True!
            )
            turn_play_objects.append(turn_play)
    
    # Use turn_resolution.py
    turn_result = resolve_turn(turn_play_objects)
    return winner_name
```

### 4.2 Turn Resolution (turn_resolution.py:28-51)
```python
def resolve_turn(turn_plays: List[TurnPlay]) -> TurnResult:
    winner: Optional[TurnPlay] = None
    winning_pieces: Optional[List[Piece]] = None
    
    for play in turn_plays:
        if not play.is_valid:  # Never happens - always True!
            continue
        
        if not winner:
            winner = play
            winning_pieces = play.pieces
        else:
            result = compare_plays(winning_pieces, play.pieces)
            if result == 2:  # play beats winner
                winner = play
                winning_pieces = play.pieces
    
    return TurnResult(plays=turn_plays, winner=winner)
```

### 4.3 Award Piles (turn_state.py:528-551)
```python
async def _award_piles(self, winner: str, pile_count: int) -> None:
    # Update game state
    if winner not in game.player_piles:
        game.player_piles[winner] = 0
    game.player_piles[winner] += pile_count
    
    # Update player object
    for player in game.players:
        if player.name == winner:
            player.captured_piles += pile_count
            break
```

## 5. Turn Completion Processing

### 5.1 Remove Pieces from Hands (turn_state.py:552-597)
```python
async def _process_turn_completion(self) -> None:
    # STEP 1: Remove played pieces from player hands FIRST
    for player in game.players:
        if player.name in self.turn_plays:
            pieces_to_remove = self.turn_plays[player.name]["pieces"]
            
            # Remove each piece from player's hand
            for piece in pieces_to_remove:
                if piece in player.hand:
                    player.hand.remove(piece)
    
    # STEP 2: Check if all hands empty
    all_hands_empty = True
    for player in game.players:
        if len(player.hand) > 0:
            all_hands_empty = False
    
    # STEP 3: Broadcast turn completion
    await self._broadcast_turn_completion_enterprise()
    
    # STEP 4: Decide next action
    if all_hands_empty:
        # Round complete - will transition to scoring
        game.last_turn_winner = self.winner
    else:
        # Start next turn after 7 second delay
        await asyncio.sleep(7.0)
        await self.start_next_turn_if_needed()
```

**CRITICAL**: Pieces are removed ONLY AFTER turn completion, not when played!

## 6. Round End - Scoring Phase

### 6.1 Scoring Calculation (scoring_state.py:276-334)
```python
async def _calculate_round_scores(self) -> None:
    for player in game.players:
        # Get declared vs actual
        declared = game.player_declarations.get(player.name, 0)
        actual = getattr(player, "captured_piles", 0)
        
        # Calculate score
        base_score = calculate_score(declared, actual)
        multiplier = getattr(game, "redeal_multiplier", 1)
        final_score = base_score * multiplier
        
        # Update total
        player.score = current_score + final_score
        
        self.round_scores[player.name] = {
            "declared": declared,
            "actual": actual,
            "base_score": base_score,
            "multiplier": multiplier,
            "final_score": final_score,
            "total_score": player.score,
        }
```

### 6.2 Check Game Winner (scoring_state.py:335-367)
```python
async def _check_game_winner(self) -> None:
    WIN_THRESHOLD = 50
    
    for player in game.players:
        if player.score >= WIN_THRESHOLD:
            winning_players.append(player.name)
    
    if winning_players:
        self.game_complete = True
        self.winners = [highest_scorer]
```

### 6.3 Prepare Next Round (scoring_state.py:369-401)
```python
def _prepare_next_round(self) -> None:
    # Increment round number
    game.round_number += 1
    
    # Clear all hands (already empty)
    for player in game.players:
        player.hand = []
    
    # Reset redeal multiplier
    game.redeal_multiplier = 1
    
    # Set next round starter
    if hasattr(game, "last_turn_winner") and game.last_turn_winner:
        game.round_starter = game.last_turn_winner
    
    # Clear turn data
    game.turn_number = 0
```

## 7. Data Flow Summary

1. **Frontend → Backend**: Piece indices only
2. **Backend → State Machine**: Piece objects (no validation)
3. **State Machine**: 
   - Validates turn order and count only
   - Stores play with defaults (play_type="unknown", is_valid=True)
   - Does NOT remove pieces from hand
4. **Turn Completion**:
   - Determines winner using piece comparison
   - Awards piles to winner
   - THEN removes pieces from all hands
5. **Round End**:
   - Calculates scores (declared vs captured piles)
   - Checks for game winner (≥50 points)
   - Prepares next round or ends game

## Critical Issues Found

1. **No Play Type Determination**: Backend receives pieces but never determines what type of play it is (PAIR, STRAIGHT, etc.)
2. **No Combination Validation**: No check if pieces form valid combinations
3. **No Ownership Validation**: No verification player has the pieces they're playing
4. **Delayed Piece Removal**: Pieces removed only after turn completes, not when played
5. **Always Valid**: All plays marked as valid by default
6. **No Play Value**: Play values not calculated or used properly

These issues mean the game relies entirely on frontend validation and honest players.