# AI Debug Mode - Flow Diagram

## Complete Game Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        START AI DEBUG MODE                        │
│                   python ai_debug_simple.py                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INITIALIZATION PHASE                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Parse command line arguments (--games, --log-level)           │
│ 2. Create AILogger with output path                              │
│ 3. Initialize bug detector                                        │
│ 4. Set game counter to 0                                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         GAME LOOP START                           │
│                    (Repeat for N games)                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         GAME SETUP                                │
├─────────────────────────────────────────────────────────────────┤
│ 1. Create game ID: "AI_123456"                                   │
│ 2. Create 4 Player objects (all bots)                            │
│ 3. Initialize Game object                                         │
│ 4. Log game_start event                                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ROUND LOOP                                │
│                  (Max 10 rounds per game)                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PREPARATION PHASE                            │
├─────────────────────────────────────────────────────────────────┤
│ 1. game.deal_pieces() - Each player gets 8 pieces                │
│ 2. Check for weak hands (no piece > 9 points)                    │
│ 3. Handle redeals if needed                                      │
│ 4. Assign pieces to player.hand                                  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DECLARATION PHASE                             │
├─────────────────────────────────────────────────────────────────┤
│ For each player in order:                                        │
│ 1. Call choose_declare_strategic_v2()                            │
│    ├─> Analyze hand strength (openers, combos, weak)             │
│    ├─> Consider position (starter, pile room)                    │
│    └─> Return declaration value (0-6)                            │
│ 2. Validate declaration (sum ≠ 8)                                │
│ 3. Log declaration event with:                                   │
│    ├─> Hand analysis                                              │
│    ├─> Decision reasoning                                         │
│    └─> Bug detection results                                      │
│ 4. Update game.declarations                                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        TURN PHASE                                 │
│                     (8 turns per round)                           │
├─────────────────────────────────────────────────────────────────┤
│ For each turn (1-8):                                             │
│   For each player in turn order:                                 │
│     1. Call choose_turn_play_strategic_v3()                      │
│        ├─> Calculate urgency (piles needed vs turns left)        │
│        ├─> Find valid plays                                       │
│        └─> Select best play based on strategy                    │
│     2. Create TurnPlay object                                     │
│     3. Validate play (piece count, availability)                 │
│                                                                   │
│   4. Resolve turn winner (highest point total)                   │
│   5. Update captured_piles for winner                            │
│   6. Remove played pieces from hands                             │
│   7. Log turn_play events                                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SCORING PHASE                               │
├─────────────────────────────────────────────────────────────────┤
│ For each player:                                                  │
│ 1. Compare declared vs captured piles                            │
│ 2. Calculate score:                                               │
│    ├─> Perfect (declared = captured): +10 base + multiplier      │
│    ├─> Off by 1: -2 points                                       │
│    ├─> Off by 2: -4 points                                       │
│    └─> Off by 3+: -6 to -10 points                              │
│ 3. Update total scores                                            │
│ 4. Log round_end event                                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      WIN CHECK                                    │
├─────────────────────────────────────────────────────────────────┤
│ IF any player.score >= 50:                                       │
│    └─> Game Over                                                 │
│ ELSE IF rounds_played >= 10:                                     │
│    └─> Game Over                                                 │
│ ELSE:                                                             │
│    └─> Continue to next round                                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        GAME END                                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. Determine winner(s) - highest score                           │
│ 2. Log game_end event with:                                      │
│    ├─> Final scores                                              │
│    ├─> Winner(s)                                                 │
│    ├─> Rounds played                                             │
│    └─> Game duration                                             │
│ 3. Save complete log to JSON file                                │
│ 4. Add results to statistics                                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STATISTICS OUTPUT                              │
├─────────────────────────────────────────────────────────────────┤
│ After all games complete:                                        │
│ 1. Calculate win rates by player position                        │
│ 2. Average scores per player                                     │
│ 3. Average rounds per game                                       │
│ 4. Total execution time                                          │
│ 5. Games per second throughput                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Through Components

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   User       │────▶│  CLI Args    │────▶│  ai_debug    │
│              │     │              │     │  _simple.py  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                     ┌────────────────────────────┼────────────────────────────┐
                     ▼                            ▼                            ▼
            ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
            │ SimpleAIGame │            │   AILogger   │            │ BugDetector  │
            │              │            │              │            │              │
            │ Orchestrates │            │ Logs events  │            │ Finds bugs   │
            │ game flow    │            │ to JSON      │            │ in AI logic  │
            └──────┬───────┘            └──────┬───────┘            └──────┬───────┘
                   │                           │                           │
                   ▼                           ▼                           ▼
            ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
            │ Game Engine  │            │  Log Files   │            │ Bug Reports  │
            │              │            │              │            │              │
            │ Core game    │            │ logs/ai_     │            │ Embedded in  │
            │ mechanics    │            │ debug/*.json │            │ log events   │
            └──────┬───────┘            └──────────────┘            └──────────────┘
                   │
                   ▼
            ┌──────────────┐
            │  AI Engine   │
            │              │
            │ Decision     │
            │ making       │
            └──────────────┘
```

## Bug Detection Flow

```
AI Makes Decision
       │
       ▼
┌─────────────────┐
│ Decision Data   │
│ - Declaration   │
│ - Hand info     │
│ - Game state    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Bug Detector   │
│                 │
│ Checks for:     │
│ - Zero w/strong │
│ - Over-aggress  │
│ - Pile ignored  │
│ - Wasted opener │
│ - Not to win    │
└────────┬────────┘
         │
         ▼
    Bugs Found?
    ┌────┴────┐
    │         │
   YES       NO
    │         │
    ▼         ▼
Log Bug    Continue
Event      Normal Log
```

## Performance Flow

```
Start Time
    │
    ▼
Game 1 ──────► ~140ms ─────┐
Game 2 ──────► ~140ms ─────┤
Game 3 ──────► ~140ms ─────┤
  ...                      ├─► Total: N × 140ms
Game N ──────► ~140ms ─────┤   = ~7 games/second
    │                      │
    ▼                      │
End Time ◄─────────────────┘
    │
    ▼
Calculate Stats
    │
    ▼
Print Summary
```
