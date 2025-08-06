# AI Declaration Implementation - Executive Summary

## Current State
- AI uses simple hand evaluation: counts combos + opener + starter bonus
- Ignores context like pile room, opponent strength, and playability
- Systematically under-declares due to fixed bugs

## Proposed Changes
Transform the simple AI into a sophisticated strategic system that considers:

### 1. **Pile Room Constraint** (CRITICAL)
- Maximum piles = 8 - sum(previous_declarations)
- Hard ceiling that overrides all other factors
- Example: Perfect hand but room=0 → must declare 0

### 2. **Declaration Pattern Analysis**
- Read what opponents reveal through declarations
- [0,1] = weak hands with no combos
- [4+] = strong hands with multiple combos
- Determines if your combos are playable

### 3. **GENERAL_RED Game Changer**
- Strongest piece (14 points) acts like being starter
- In weak fields, enables dramatic declarations
- Can turn 2-pile hand into 5-pile hand

### 4. **Combo Playability Analysis**
- Without starter/opener, combos often unplayable
- Need opponents to create opportunities
- Weak combos (like 18pt STRAIGHT) rarely win

### 5. **Context-Aware Adjustments**
- Opener reliability varies by field strength
- Last player can't declare sum=8 value
- Position dramatically affects declaration

## Implementation Approach

### Phase Structure (7 phases, ~16 hours)
1. **Fix Bugs** - Remove starter bonus, fix range
2. **Infrastructure** - Context class, helper functions
3. **Analysis Functions** - Pattern reading, field assessment
4. **Core Algorithm** - Rewrite declaration logic
5. **Advanced Features** - Strategic adjustments
6. **Testing** - Comprehensive validation
7. **Final Validation** - User acceptance testing

### Key Technical Details
- Maintain backward compatibility (same function signature)
- Target <100ms decision time
- Extensive debug logging for transparency
- Defensive programming for edge cases

## Expected Outcomes

### Before
- Same hand → same declaration always
- Ignores game context completely
- Often declares impossibly high values

### After  
- Same hand → different declarations based on:
  - Available pile room
  - Opponent strength
  - Position (starter vs not)
  - GENERAL_RED presence
- Respects hard constraints
- Makes contextually appropriate decisions

## Risk Mitigation
- Maintain exact API compatibility
- Comprehensive testing suite
- Phased implementation option
- Extensive logging for debugging

## Quick Wins Available
If full implementation is too complex:
1. **Just add pile room check** - Biggest single improvement
2. **Add GENERAL_RED handling** - Enables dramatic plays
3. **Implement incrementally** - Phase by phase

## Validation
- 18 detailed test examples ready
- Each example shows expected behavior
- Covers all strategic scenarios