# AI Declaration Logic Revision Plan

## Overview

This document outlines the implementation plan for revising the AI declaration logic in the LIAP-TUI game. The new logic introduces different strategies for starters (first players) versus non-starters, with explicit play tracking and pile room management.

## Key Concepts

### Strong Combos
- **Definition**: Combos where the average piece value is greater than HORSE_RED (6 points)
- **Purpose**: Identify combos that are likely to win piles reliably

### Play List
- **Definition**: Explicit list of planned plays (combos and individual pieces)
- **Purpose**: Track exactly what the AI plans to play, avoiding double-counting pieces

### Pile Room
- **For Starters**: 8 minus the number of pieces in play list
- **For Non-Starters**: 8 minus the sum of previous declarations

## Implementation Structure

### 1. Constants to Add

```python
# backend/engine/ai.py - Add at module level

# Strong combo threshold - combos with average piece value > HORSE_RED
STRONG_COMBO_MIN_AVG = 6  # HORSE_RED point value

# Note: Individual piece thresholds are managed by get_piece_threshold() function
# This provides cleaner handling of all pile room values (1-8+)

# All combo types for reference
ALL_COMBO_TYPES = {
    "PAIR",
    "THREE_OF_A_KIND",
    "STRAIGHT", 
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT"
}
```

### 2. Helper Functions to Implement

```python
def is_strong_combo(combo_type: str, pieces: List[Piece]) -> bool:
    """
    Check if a combo qualifies as a strong combo.
    
    Args:
        combo_type: Type of combo (e.g., "PAIR", "STRAIGHT")
        pieces: List of pieces in the combo
        
    Returns:
        True if average piece value > STRONG_COMBO_MIN_AVG
    """
    avg_value = sum(p.point for p in pieces) / len(pieces)
    return avg_value > STRONG_COMBO_MIN_AVG


def remove_pieces_from_hand(hand: List[Piece], pieces_to_remove: List[Piece]) -> List[Piece]:
    """
    Remove specific pieces from hand to avoid overlap in play planning.
    
    Args:
        hand: Current hand
        pieces_to_remove: Pieces to remove
        
    Returns:
        New hand with pieces removed
    """
    hand_copy = hand.copy()
    for piece in pieces_to_remove:
        if piece in hand_copy:
            hand_copy.remove(piece)
    return hand_copy


def get_piece_threshold(pile_room: int) -> int:
    """
    Get minimum piece value needed for given pile room.
    More restrictive with less room, more flexible with more room.
    
    Args:
        pile_room: Available pile slots
        
    Returns:
        Minimum piece value threshold
    """
    if pile_room <= 0:
        return float('inf')  # Impossible threshold
    elif pile_room == 1:
        return 13  # >13 (only GENERAL_RED qualifies)
    elif pile_room == 2:
        return 13  # >=13 (GENERAL_BLACK/RED)
    elif pile_room == 3:
        return 12  # >=12 (ADVISOR_RED and up)
    elif pile_room == 4:
        return 12  # >=12 (ADVISOR_RED and up)
    elif pile_room == 5:
        return 11  # >=11 (ADVISOR_BLACK and up)
    else:
        return 11  # >=11 for pile room > 5 (default to standard opener threshold)


def get_individual_strong_pieces(hand: List[Piece], pile_room: int) -> List[Piece]:
    """
    Find individual pieces that meet the threshold for given pile room.
    
    Args:
        hand: Current hand
        pile_room: Available pile room
        
    Returns:
        List of qualifying pieces
    """
    threshold = get_piece_threshold(pile_room)
    
    if pile_room == 1:
        # Special case: pile room 1 requires > 13 (not >=)
        return [p for p in hand if p.point > threshold]
    else:
        return [p for p in hand if p.point >= threshold]


def fit_plays_to_pile_room(play_list: List[Dict], pile_room: int) -> List[Dict]:
    """
    Adjust play list to fit within pile room constraints.
    
    Strategy: Remove lowest value combos first, keep openers if possible.
    
    Args:
        play_list: List of planned plays
        pile_room: Maximum pieces allowed
        
    Returns:
        Adjusted play list that fits pile room
    """
    total_pieces = sum(len(play['pieces']) for play in play_list)
    
    if total_pieces <= pile_room:
        return play_list
    
    # Separate openers and combos
    openers = [p for p in play_list if p['type'] == 'opener']
    combos = [p for p in play_list if p['type'] == 'combo']
    
    # Sort combos by total value (ascending) to remove weakest first
    combos.sort(key=lambda x: sum(p.point for p in x['pieces']))
    
    # Remove combos until we fit
    while total_pieces > pile_room and combos:
        removed = combos.pop(0)  # Remove weakest combo
        total_pieces -= len(removed['pieces'])
    
    # Rebuild play list
    return openers + combos
```

### 3. Main Declaration Function

```python
def choose_declare_strategic_v2(
    hand,
    is_first_player: bool,
    position_in_order: int,
    previous_declarations: list[int],
    must_declare_nonzero: bool,
    verbose: bool = True
) -> int:
    """
    New declaration logic with separate starter/non-starter strategies.
    
    Starter Strategy:
    1. Find all strong combos first
    2. Find individual strong pieces
    3. Declaration = total pieces in play list
    
    Non-Starter Strategy:
    1. Find ONE opener first for control
    2. Find strong combos from remaining pieces
    3. Find additional individual pieces
    4. Fit to pile room by removing combos if needed
    5. If no opener found, declare 0
    """
    
    play_list = []
    hand_copy = hand.copy()
    
    if verbose:
        print(f"\n📢 DECLARATION DECISION V2 for position {position_in_order}")
        print(f"  Hand: {[f'{p.name}({p.point})' for p in hand]}")
        print(f"  Previous declarations: {previous_declarations}")
        print(f"  Starter: {is_first_player}")
    
    if is_first_player:
        # =====================================================
        # STARTER LOGIC
        # =====================================================
        if verbose:
            print("\n🎯 STARTER STRATEGY:")
        
        # Step 1: Find all strong combos
        all_combos = find_all_valid_combos(hand_copy)
        strong_combos = []
        
        for combo_type, pieces in all_combos:
            if is_strong_combo(combo_type, pieces):
                strong_combos.append({
                    'type': 'combo',
                    'combo_type': combo_type,
                    'pieces': pieces
                })
        
        if verbose:
            print(f"  Found {len(strong_combos)} strong combos")
        
        # Add combos to play list and remove from hand
        for combo in strong_combos:
            play_list.append(combo)
            hand_copy = remove_pieces_from_hand(hand_copy, combo['pieces'])
        
        # Step 2: Calculate pile room
        total_pieces_planned = sum(len(play['pieces']) for play in play_list)
        pile_room_left = 8 - total_pieces_planned
        
        if verbose:
            print(f"  After combos: {total_pieces_planned} pieces planned, {pile_room_left} room left")
        
        # Step 3: Find individual strong pieces
        for room in range(min(5, pile_room_left), 0, -1):
            strong_pieces = get_individual_strong_pieces(hand_copy, room)
            for piece in strong_pieces:
                if pile_room_left > 0:
                    play_list.append({
                        'type': 'opener',
                        'pieces': [piece]
                    })
                    hand_copy = remove_pieces_from_hand(hand_copy, [piece])
                    pile_room_left -= 1
        
        # Calculate declaration
        declaration = sum(len(play['pieces']) for play in play_list)
        
    else:
        # =====================================================
        # NON-STARTER LOGIC
        # =====================================================
        if verbose:
            print("\n🎯 NON-STARTER STRATEGY:")
        
        # Step 1: Calculate pile room from previous declarations
        pile_room = 8 - sum(previous_declarations)
        if verbose:
            print(f"  Pile room available: {pile_room}")
        
        # Step 2: Find ONE opener first
        opener = None
        for threshold in [13, 12, 11]:  # Try highest first
            candidates = [p for p in hand_copy if p.point >= threshold]
            if candidates:
                opener = max(candidates, key=lambda p: p.point)
                play_list.append({
                    'type': 'opener',
                    'pieces': [opener]
                })
                hand_copy = remove_pieces_from_hand(hand_copy, [opener])
                if verbose:
                    print(f"  Found opener: {opener.name}({opener.point})")
                break
        
        if not opener:
            if verbose:
                print("  No opener found - declaring 0")
            return 0
        
        # Step 3: Find all strong combos from remaining pieces
        all_combos = find_all_valid_combos(hand_copy)
        for combo_type, pieces in all_combos:
            if is_strong_combo(combo_type, pieces):
                play_list.append({
                    'type': 'combo',
                    'combo_type': combo_type,
                    'pieces': pieces
                })
                hand_copy = remove_pieces_from_hand(hand_copy, pieces)
        
        # Step 4: Find additional individual strong pieces
        current_pieces = sum(len(play['pieces']) for play in play_list)
        room_left = pile_room - current_pieces
        
        for room in range(min(5, room_left), 0, -1):
            strong_pieces = get_individual_strong_pieces(hand_copy, room)
            for piece in strong_pieces:
                if room_left > 0:
                    play_list.append({
                        'type': 'opener',
                        'pieces': [piece]
                    })
                    hand_copy = remove_pieces_from_hand(hand_copy, [piece])
                    room_left -= 1
        
        # Step 5: Fit to pile room if needed
        play_list = fit_plays_to_pile_room(play_list, pile_room)
        
        # Calculate declaration
        declaration = sum(len(play['pieces']) for play in play_list)
    
    # =====================================================
    # HANDLE FORBIDDEN VALUES (same for both)
    # =====================================================
    forbidden_declares = set()
    
    # Last player can't make sum = 8
    if position_in_order == 3:
        total_so_far = sum(previous_declarations)
        forbidden = 8 - total_so_far
        if 0 <= forbidden <= 8:
            forbidden_declares.add(forbidden)
    
    # Must declare non-zero rule
    if must_declare_nonzero:
        forbidden_declares.add(0)
    
    # Adjust if needed
    if declaration in forbidden_declares:
        valid_options = [d for d in range(0, 9) if d not in forbidden_declares]
        if valid_options:
            # Pick closest valid option
            declaration = min(valid_options, key=lambda x: abs(x - declaration))
    
    if verbose:
        print(f"\n🎯 FINAL DECLARATION: {declaration}")
        print(f"  Play list has {len(play_list)} plays:")
        for play in play_list:
            if play['type'] == 'combo':
                print(f"    - {play['combo_type']}: {[f'{p.name}({p.point})' for p in play['pieces']]}")
            else:
                print(f"    - Opener: {play['pieces'][0].name}({play['pieces'][0].point})")
    
    return declaration
```

## Implementation Phases

### Phase 1: Foundation (Day 1)
1. Add constants to `backend/engine/ai.py`
2. Implement helper functions
3. Write unit tests for each helper function

### Phase 2: Core Logic (Day 2)
1. Implement `choose_declare_strategic_v2`
2. Test starter logic with existing test cases
3. Test non-starter logic with existing test cases

### Phase 3: Integration (Day 3)
1. Add parallel testing mode to compare v1 vs v2
2. Run comprehensive test suite
3. Fix edge cases and bugs

### Phase 4: Migration (Day 4)
1. Add feature flag for gradual rollout
2. Monitor performance differences
3. Complete migration when stable

## Testing Strategy

### Unit Tests
- Test `is_strong_combo` with various combo types
- Test `remove_pieces_from_hand` for correctness
- Test `get_individual_strong_pieces` for each pile room
- Test `fit_plays_to_pile_room` with various scenarios

### Integration Tests
- Test starter declarations with strong hands
- Test non-starter declarations with limited pile room
- Test forbidden value handling
- Test edge cases (no openers, all combos, etc.)

### Regression Tests
- Compare v2 output with v1 for consistency
- Ensure no degradation in bot performance
- Validate against historical game data

## Success Criteria

1. **Correctness**: All existing tests pass
2. **Performance**: Declaration speed within 100ms
3. **Strategy**: Bots make sensible declarations
4. **Maintainability**: Code is clear and well-documented

## Risk Mitigation

1. **Backward Compatibility**: Keep v1 function until v2 is stable
2. **Gradual Rollout**: Use feature flags for testing
3. **Comprehensive Logging**: Add detailed debug output
4. **Fallback Logic**: If v2 fails, fall back to v1

## Timeline

- **Week 1**: Implementation and unit testing
- **Week 2**: Integration testing and bug fixes
- **Week 3**: Performance testing and optimization
- **Week 4**: Production rollout and monitoring