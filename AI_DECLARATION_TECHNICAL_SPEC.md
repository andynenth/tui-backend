# AI Declaration Technical Specification

## Detailed Function Specifications

### 1. DeclarationContext Class

```python
@dataclass
class DeclarationContext:
    """Holds all context needed for strategic declaration decisions."""
    position_in_order: int  # 0-3
    previous_declarations: List[int]  # Length 0-3
    is_starter: bool
    pile_room: int  # Calculated: 8 - sum(previous_declarations)
    field_strength: str  # "weak", "normal", "strong"
    has_general_red: bool
    opponent_patterns: Dict[str, Any]  # Analysis results
```

### 2. Strategic Analysis Functions

```python
def calculate_pile_room(previous_declarations: List[int]) -> int:
    """
    Calculate maximum piles available in this round.
    
    Returns:
        int: Available pile room (0-8)
    """
    total_declared = sum(previous_declarations)
    # Handle edge case where sum > 8 (shouldn't happen but defensive)
    return max(0, 8 - total_declared)


def assess_field_strength(previous_declarations: List[int]) -> str:
    """
    Categorize the overall field strength based on declarations.
    
    Returns:
        str: "weak", "normal", or "strong"
    """
    if not previous_declarations:
        return "normal"  # No info yet
        
    avg = sum(previous_declarations) / len(previous_declarations)
    
    if avg <= 1.0:
        return "weak"  # Opponents have poor hands
    elif avg >= 3.5:
        return "strong"  # Opponents have excellent hands
    else:
        return "normal"


def analyze_opponent_patterns(previous_declarations: List[int]) -> Dict:
    """
    Analyze what opponent declarations reveal about their hands.
    
    Returns:
        Dict with:
        - low_declarers: int (count of 0-1 declarations)
        - high_declarers: int (count of 4+ declarations)  
        - combo_opportunity: bool (might opponents play 3+ pieces?)
        - likely_singles_only: bool (all opponents playing singles?)
    """
    low_count = sum(1 for d in previous_declarations if d <= 1)
    high_count = sum(1 for d in previous_declarations if d >= 4)
    
    # If all previous players declared 0-1, they have NO combos
    likely_singles_only = (low_count == len(previous_declarations))
    
    # Combo opportunity exists if someone might play combos
    combo_opportunity = high_count > 0 or any(d >= 3 for d in previous_declarations)
    
    return {
        'low_declarers': low_count,
        'high_declarers': high_count,
        'combo_opportunity': combo_opportunity,
        'likely_singles_only': likely_singles_only
    }


def evaluate_opener_reliability(piece, field_strength: str) -> float:
    """
    Evaluate how reliable an opener is given field strength.
    
    Returns:
        float: Reliability score (0.0 - 1.0)
    """
    if piece.point >= 13:  # GENERAL
        return 1.0  # Always reliable
    elif piece.point >= 11:  # ADVISOR
        if field_strength == "weak":
            return 1.0  # Very reliable vs weak opponents
        elif field_strength == "normal":
            return 0.85  # Usually reliable
        else:  # strong
            return 0.7  # Might lose to GENERALs
    else:
        return 0.0  # Not an opener


def filter_viable_combos(combos: List[Tuple], context: DeclarationContext, 
                        has_reliable_opener: bool) -> List[Tuple]:
    """
    Filter combos to only those that are actually playable.
    
    Args:
        combos: List of (combo_type, pieces) tuples
        context: Declaration context
        has_reliable_opener: Whether hand has 11+ point piece
        
    Returns:
        List of viable combos
    """
    viable = []
    
    for combo_type, pieces in combos:
        combo_size = len(pieces)
        
        # Check 1: Pile room constraint
        if combo_size > context.pile_room:
            continue  # Can't play if not enough room
            
        # Check 2: Playability without control
        if context.is_starter or has_reliable_opener or context.has_general_red:
            # Have control or can get it
            viable.append((combo_type, pieces))
        else:
            # Need opportunity from opponents
            if context.opponent_patterns['combo_opportunity'] and combo_size >= 3:
                # Opponents might create opportunity
                # But check combo strength
                total_points = sum(p.point for p in pieces)
                
                if combo_type == "STRAIGHT" and total_points < 21:
                    # Weak straight, unlikely to win even with opportunity
                    continue
                    
                viable.append((combo_type, pieces))
    
    return viable
```

### 3. Enhanced Main Declaration Function

```python
def choose_declare_strategic(
    hand,
    is_first_player: bool,
    position_in_order: int,
    previous_declarations: list[int],
    must_declare_nonzero: bool,
    verbose: bool = True,
) -> int:
    """
    Strategic declaration logic implementing all principles from strategy guide.
    """
    # Phase 1: Build context
    context = DeclarationContext(
        position_in_order=position_in_order,
        previous_declarations=previous_declarations,
        is_starter=is_first_player,
        pile_room=calculate_pile_room(previous_declarations),
        field_strength=assess_field_strength(previous_declarations),
        has_general_red=any(p.name == "GENERAL" and p.point == 14 for p in hand),
        opponent_patterns=analyze_opponent_patterns(previous_declarations)
    )
    
    # Phase 2: Find and filter combos
    all_combos = find_all_valid_combos(hand)
    strong_combos = [c for c in all_combos if c[0] in {
        "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND", 
        "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"
    }]
    
    # Phase 3: Evaluate openers
    opener_score = 0
    has_reliable_opener = False
    for piece in hand:
        if piece.point >= 11:
            reliability = evaluate_opener_reliability(piece, context.field_strength)
            if reliability > 0:
                has_reliable_opener = True
                opener_score += reliability
    
    # Phase 4: Filter viable combos
    viable_combos = filter_viable_combos(
        strong_combos, context, has_reliable_opener
    )
    
    # Phase 5: Calculate base score
    score = 0
    
    # Add piles from viable combos
    for combo_type, pieces in viable_combos:
        if combo_type in ["THREE_OF_A_KIND", "STRAIGHT"]:
            score += 3
        elif combo_type in ["FOUR_OF_A_KIND", "EXTENDED_STRAIGHT"]:
            score += 4
        elif combo_type in ["FIVE_OF_A_KIND", "EXTENDED_STRAIGHT_5"]:
            score += 5
        elif combo_type == "DOUBLE_STRAIGHT":
            score += 6
    
    # Add opener piles
    score += int(opener_score)
    
    # Phase 6: Apply GENERAL_RED game changer
    if context.has_general_red and context.field_strength == "weak":
        # Recalculate with all combos viable
        all_combo_piles = sum(
            len(pieces) for _, pieces in strong_combos
        )
        # Take maximum of current score or GENERAL_RED enabled score
        score = max(score, min(all_combo_piles + 1, context.pile_room))
    
    # Phase 7: Apply constraints
    # Pile room is absolute ceiling
    score = min(score, context.pile_room)
    
    # Valid range
    score = max(0, min(score, 8))
    
    # Phase 8: Handle forbidden values
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
    
    # Find best valid alternative if needed
    if score in forbidden_declares:
        valid_options = [d for d in range(0, 9) if d not in forbidden_declares]
        
        # Strategy: Pick closest valid option
        if valid_options:
            # Find closest to our ideal score
            score = min(valid_options, key=lambda x: abs(x - score))
        else:
            # Shouldn't happen, but defensive
            score = 1
    
    # Phase 9: Debug output
    if verbose:
        print(f"\\n🎯 STRATEGIC DECLARATION ANALYSIS")
        print(f"Position: {position_in_order} (Starter: {context.is_starter})")
        print(f"Previous declarations: {previous_declarations}")
        print(f"Pile room: {context.pile_room}")
        print(f"Field strength: {context.field_strength}")
        print(f"Has GENERAL_RED: {context.has_general_red}")
        print(f"Combo opportunity: {context.opponent_patterns['combo_opportunity']}")
        print(f"Found {len(strong_combos)} combos, {len(viable_combos)} viable")
        print(f"Opener score: {opener_score}")
        print(f"Final declaration: {score}")
    
    return score
```

### 4. Integration Notes

The new strategic system should:

1. **Replace** the existing `choose_declare()` function
2. **Preserve** the existing `find_all_valid_combos()` function
3. **Add** all new helper functions to the module
4. **Maintain** backward compatibility with the function signature

### 5. Edge Cases to Handle

1. **Empty previous_declarations** (first player)
2. **Sum already exceeds 8** (defensive programming)
3. **All combos filtered out** (fall back to singles)
4. **No valid declaration options** (shouldn't happen)
5. **Multiple openers in hand** (count each)
6. **Overlapping combos** (existing issue, track separately)

### 6. Testing Strategy

Create test cases for:
- Each of the 18 examples
- Edge cases listed above
- Performance benchmarks
- Integration with game flow