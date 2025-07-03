# 🛠️ Debugging Tools Guide

**Liap Tui Game - Complete Debugging Suite Documentation**

This guide covers the comprehensive debugging tools implemented in Phases 6.1-6.3, providing developers with production-ready capabilities for identifying, analyzing, and resolving synchronization issues.

---

## 📋 Table of Contents

1. [Quick Access](#-quick-access)
2. [🎮 Game Replay Tool](#-game-replay-tool---session-recording--playback)
3. [🔍 State Debug Tool](#-state-debug-tool---live-state-inspection)
4. [🔄 Sync Checker Tool](#-sync-checker-tool---proactive-desync-detection)
5. [🎯 Tool Selection Guide](#-tool-selection-guide)
6. [🚨 Alert Interpretation](#-alert-interpretation-guide)
7. [📊 Export Data Formats](#-export-data-formats)
8. [🔧 Development Tips](#-development-tips)

---

## 🚀 Quick Access

All debugging tools are accessible from the game page header:

```
Game Header: [🎮 Replay] [🔍 Debug] [🔄 Sync] [Leave Game]
```

- **🎮 Replay** - Game Replay Tool (Phase 6.1)
- **🔍 Debug** - State Debug Tool (Phase 6.2)  
- **🔄 Sync** - Sync Checker Tool (Phase 6.3)

Each tool opens in a modal overlay and can be used simultaneously for comprehensive debugging.

---

## 🎮 Game Replay Tool - Session Recording & Playback

### Purpose
Record exact game sessions for bug reproduction and team collaboration. Essential for investigating player-reported issues and understanding complex interaction sequences.

### When to Use
- **Bug Reports**: Player reports "something weird happened"
- **Issue Reproduction**: Need to see exact sequence of events
- **Team Collaboration**: Share problematic sessions with developers
- **Regression Testing**: Verify fixes don't break existing functionality

### Features Overview
- ✅ Records all game events (actions, state changes, WebSocket messages)
- ✅ Step-by-step replay with pause/rewind/fast-forward controls
- ✅ Visual timeline with event filtering
- ✅ Export/import replay files for team sharing
- ✅ Integration with existing event system

---

### Step-by-Step Usage

#### 1. Starting a Recording Session
```
1. Click [🎮 Replay] button in game header
2. In the Game Replay Tool modal:
   - Room ID and Player Name are auto-populated
   - Click [🎬 Start Recording] button
3. Play the game normally
4. When issue occurs or session complete:
   - Click [⏹️ Stop Recording]
   - Session automatically saved to localStorage
```

**Recording Indicators:**
- 🔴 Red recording dot when active
- Event counter shows captured events in real-time
- Recording duration timer

#### 2. Session Management
```
Sessions Panel (bottom section):
┌─ Saved Sessions ─────────────────────────────┐
│ Session #abc123 - Room: game456 - 2m 30s    │
│ 📅 2024-01-15 14:30  👤 PlayerA  📊 247 events │
│ [▶️ Load] [📄 Details] [🗑️ Delete]           │
├──────────────────────────────────────────────┤
│ Session #def789 - Room: game123 - 1m 45s    │
│ 📅 2024-01-15 13:15  👤 PlayerB  📊 189 events │
│ [▶️ Load] [📄 Details] [🗑️ Delete]           │
└──────────────────────────────────────────────┘

- Sessions auto-saved with metadata
- Click session name to load for playback
- Details show event breakdown and game phases
- Delete to clean up old sessions
```

#### 3. Playback Controls
```
Timeline Controls:
[⏮️] [⏪] [▶️/⏸️] [⏩] [⏭️]  Speed: [0.25x] [0.5x] [1x] [2x] [4x]

Event: 47/247  Time: 00:01:23/00:02:30
████████████████████████░░░░░░░░░░ 67%

Controls:
- ⏮️ Jump to start
- ⏪ Step backward (previous event)
- ▶️/⏸️ Play/Pause automated playback
- ⏩ Step forward (next event)
- ⏭️ Jump to end
- Speed: 0.25x to 4x for slow-motion or fast analysis
```

**Visual Timeline:**
- Progress bar shows current position
- Event markers indicate important events
- Click timeline to jump to specific time
- Hover for event details

#### 4. Event Filtering
```
Filter Controls:
┌─ Event Types ────────────────────┐
│ ☑️ Network Messages (127 events) │
│ ☑️ State Changes (89 events)     │
│ ☑️ User Actions (31 events)      │
│ ☑️ System Events (15 events)     │
└───────────────────────────────────┘

Additional Filters:
Player Filter: [All Players ▼] [PlayerA] [PlayerB] [PlayerC]
Phase Filter:  [All Phases ▼]  [Preparation] [Declaration] [Turn] [Scoring]

Search: [text field] - Search event data content
```

**Filter Effects:**
- Unchecked types hidden from timeline
- Player filter shows only events from selected player
- Phase filter shows events from specific game phases
- Search finds events containing specific text

#### 5. Event Details Viewer
```
Current Event Details:
┌─ Event #47: User Action ─────────────────────┐
│ Timestamp: 14:32:15.234                      │
│ Type: user_action                            │
│ Player: PlayerA                              │
│ Action: play_pieces                          │
│ Data:                                        │
│ {                                            │
│   "pieces": ["A♠", "K♠"],                   │
│   "count": 2,                               │
│   "position": "attack"                      │
│ }                                            │
│ Metadata:                                    │
│   Phase: turn                               │
│   Sequence: 47                              │
└──────────────────────────────────────────────┘
```

#### 6. Export/Import Sessions
```
Export Options:
1. Click [💾 Export Session] button
2. Choose format:
   - Full Session (all events, largest file)
   - Summary Only (key events, smaller file)
   - Custom Range (specify start/end events)
3. Downloads JSON file: "replay-room123-20240115.json"

Import Process:
1. Click [📁 Import Session] button
2. Select JSON file from file picker
3. Session loaded and available for playback
4. Validates file format and shows import status

Use Cases:
- Share problematic sessions with development team
- Archive important game sessions for testing
- Import sessions from other environments
```

---

### Real-World Example: Bug Investigation

**Scenario**: Player reports "My cards disappeared during my turn"

```
Investigation Process:

1. Start Recording:
   - Player contacts support about missing cards
   - Ask player to continue playing while recording
   - Click [🎬 Start Recording] before they make next move

2. Reproduce Issue:
   - Player plays normally
   - Issue occurs: cards disappear from hand
   - Stop recording immediately: [⏹️ Stop Recording]

3. Playback Analysis:
   - Load the session for replay
   - Set speed to 0.5x for detailed analysis
   - Filter to show only "State Changes" and "Network Messages"
   
4. Find the Problem:
   - Step through events leading to card disappearance
   - Event #89: User plays cards ["A♠", "K♠"]  
   - Event #90: Network message "play_pieces" sent
   - Event #91: State change removes cards from myHand
   - Event #92: Network response "invalid_play" (missed!)
   - Event #93: No state rollback occurs ← BUG FOUND!

5. Export and Report:
   - Export session: "card-disappear-bug-20240115.json"
   - Attach to bug report with timeline analysis
   - Development team can import and reproduce exactly
```

---

## 🔍 State Debug Tool - Live State Inspection

### Purpose
Real-time monitoring and comparison of frontend vs backend game state. Essential for identifying state synchronization issues and performance bottlenecks during active gameplay.

### When to Use
- **State Mismatches**: Frontend shows different data than backend
- **Performance Issues**: Slow state updates or lag
- **Development**: Understanding state flow during development
- **Sync Verification**: Ensuring changes propagate correctly

### Features Overview
- ✅ Live monitoring of frontend vs backend state differences
- ✅ Real-time state synchronization tracking
- ✅ Interactive state inspector with expandable object trees
- ✅ WebSocket message viewer with filtering
- ✅ State comparison with diff highlighting
- ✅ Performance metrics and timing analysis

---

### Step-by-Step Usage

#### 1. Start Debugging Session
```
1. Click [🔍 Debug] button in game header
2. In the State Debug Tool modal:
   - Room ID and Player Name auto-populated
   - Click [🔍 Start Debugging] button
3. Tool automatically captures state changes
4. Real-time monitoring begins immediately

Status Indicators:
🟢 Active - Tool is monitoring and capturing state
📊 Statistics - Shows capture rate and data volume
⏱️ Last Update - Timestamp of most recent state capture
```

#### 2. View Options Panel (Left Side)
```
┌─ View Options ───────────────────┐
│ ☑️ Show State Comparison          │
│ ☑️ Show Messages                  │
│ ☑️ Show Performance               │
│ ☑️ Auto Update                    │
│                                   │
│ Update Interval: [1000] ms        │
│ Max History: [1000] entries       │
└───────────────────────────────────┘

┌─ Message Filters ────────────────┐
│ ☑️ Incoming Messages              │
│ ☑️ Outgoing Messages              │
│                                   │
│ Event Filter: [text field]       │
│ Example: "phase_change"           │
│                                   │
│ Max Messages: [100] entries       │
└───────────────────────────────────┘

Options Explained:
- State Comparison: Shows frontend vs backend side-by-side
- Messages: WebSocket message viewer with full payloads
- Performance: Real-time latency and timing metrics
- Auto Update: Continuous vs manual refresh
```

#### 3. State Comparison View
```
Two-Panel State Comparison:
┌─ Frontend State ─────────┐  ┌─ Backend State ──────────┐
│ {                        │  │ {                        │
│   "phase": "turn",       │  │   "phase": "turn",       │
│   "currentPlayer": "A",  │  │   "currentPlayer": "B",  │ ← 🔴 DIFFERENCE!
│   "turnNumber": 5,       │  │   "turnNumber": 5,       │
│   "myHand": [            │  │   "myHand": [            │
│     "A♠", "K♣", "Q♦"     │  │     "A♠", "K♣", "J♦"     │ ← 🔴 DIFFERENCE!
│   ],                     │  │   ],                     │
│   "scores": {            │  │   "scores": {            │
│     "PlayerA": 15        │  │     "PlayerA": 15        │
│   }                      │  │   }                      │
│ }                        │  │ }                        │
└──────────────────────────┘  └──────────────────────────┘

Difference Highlighting:
🔴 Critical - phase, currentPlayer, gameOver (game-breaking)
🟠 High     - myHand, scores, turnNumber (affects gameplay)  
🟡 Medium   - players, declarations (affects UX)
🔵 Low      - UI state, timestamps (cosmetic)
```

#### 4. State Differences Panel
```
State Differences Detected (3):

🔴 Critical: currentPlayer
Path: currentPlayer
Frontend: "PlayerA"  Backend: "PlayerB"
Impact: Game turn logic broken

🟠 High: myHand[2]  
Path: myHand[2]
Frontend: "Q♦"  Backend: "J♦"  
Impact: Player sees wrong cards

🟡 Medium: declarations.PlayerC
Path: declarations.PlayerC
Frontend: 3  Backend: 4
Impact: Score calculation may be wrong

[🔄 Force Sync] [📋 Copy Details] [🚨 Create Alert]
```

#### 5. Performance Metrics Dashboard
```
┌─ Performance Metrics ────────────────────────┐
│                                              │
│ State Update Latency:                        │
│ ██████████████████░░ 25ms avg (12-45ms)      │
│                                              │
│ WebSocket Latency:                           │
│ ██████████████████████ 15ms avg (8-30ms)    │
│                                              │
│ Render Latency:                              │
│ ███████████████████████████ 8ms avg (5-15ms)│
│                                              │
│ Event Processing:                            │
│ ████████████████████████ 12ms avg (6-25ms)  │
│                                              │
└──────────────────────────────────────────────┘

Alert Thresholds:
🟢 Green: <50ms (excellent performance)
🟡 Yellow: 50-100ms (acceptable performance)  
🟠 Orange: 100-200ms (slow, investigate)
🔴 Red: >200ms (critical, immediate action)

Recent Measurements (last 10):
15ms, 18ms, 12ms, 25ms, 19ms, 16ms, 14ms, 22ms, 17ms, 20ms
```

#### 6. WebSocket Message Viewer
```
Message Stream (filtered: phase_change):
┌─ WebSocket Messages ─────────────────────────┐
│ 🔵 14:32:15.234 ⬇️ incoming  phase_change     │
│ {                                            │
│   "phase": "turn",                           │
│   "currentPlayer": "PlayerB",                │
│   "turnNumber": 5,                           │
│   "sequence": 127                            │
│ }                                            │
├──────────────────────────────────────────────┤
│ 🟢 14:32:14.891 ⬆️ outgoing  play_pieces      │
│ {                                            │
│   "pieces": ["A♠", "K♠"],                    │
│   "count": 2                                │
│ }                                            │
├──────────────────────────────────────────────┤
│ 🔵 14:32:14.156 ⬇️ incoming  turn_complete    │
│ {                                            │
│   "winner": "PlayerA",                       │
│   "piecesWon": 8                             │
│ }                                            │
└──────────────────────────────────────────────┘

Message Details:
- 🔵 Blue: Incoming from server
- 🟢 Green: Outgoing to server  
- Timestamp with millisecond precision
- Full JSON payload expandable
- Filter by event type or content search
```

#### 7. Manual State Capture
```
Manual Controls:
[📸 Capture State] - Force immediate state snapshot
[🗑️ Clear Data] - Reset all captured data
[💾 Export Session] - Download debugging session
[⚙️ Settings] - Configure capture options

Automatic Triggers:
- State changes detected
- WebSocket messages received
- Performance threshold exceeded
- User-defined intervals (configurable)
```

---

### Real-World Example: Card Mismatch Investigation

**Scenario**: Player reports "My hand shows cards I don't actually have"

```
Investigation Process:

1. Start State Debugging:
   - Player reports card display issue
   - Click [🔍 Debug] and [🔍 Start Debugging]
   - Enable "Show State Comparison" view

2. Identify the Problem:
   - Look at State Comparison panel
   - Check myHand field differences:
     Frontend myHand: ["A♠", "K♣", "Q♦"]
     Backend myHand:  ["A♠", "K♣", "J♦"]
   - Difference in third card: Q♦ vs J♦

3. Trace the Root Cause:
   - Switch to Messages tab
   - Filter for recent hand updates
   - Find message sequence:
     Event 1: play_pieces sent Q♦
     Event 2: turn_complete received  
     Event 3: hand_update with J♦ (not applied to frontend!)

4. Verify Performance Impact:
   - Check Performance tab
   - State update latency: 150ms (high)
   - Possible cause: slow frontend processing

5. Document and Fix:
   - Export debugging session
   - [💾 Export Session] → "card-mismatch-debug.json"
   - Share with team for frontend state update optimization
```

---

## 🔄 Sync Checker Tool - Proactive Desync Detection

### Purpose
Continuous monitoring of critical game state fields to detect synchronization issues before they impact gameplay. Provides automated alerts and recovery suggestions.

### When to Use
- **Proactive Monitoring**: Detect desyncs before users notice
- **Production Environment**: Continuous sync health monitoring
- **Alert Management**: Get notified of sync issues immediately
- **Quality Assurance**: Automated testing for sync reliability

### Features Overview
- ✅ Continuous monitoring of critical game state fields
- ✅ Automatic desync alerts with severity levels
- ✅ Historical desync tracking with timestamps
- ✅ Recovery suggestions and automated fixes
- ✅ Integration with existing debugging tools

---

### Step-by-Step Usage

#### 1. Start Sync Monitoring
```
1. Click [🔄 Sync] button in game header
2. In the Sync Checker Tool modal:
   - Room ID and Player Name auto-populated
   - Current status shows: INACTIVE
   - Click [🔄 Start Checking] button
3. Tool immediately begins monitoring critical fields
4. Status changes to SYNCED (green) or shows issues

Initial Configuration:
- Check Interval: 2000ms (every 2 seconds)
- Tolerance: 100ms (for timing differences)
- Critical Fields: phase, currentPlayer, currentRound, etc.
- Auto Recovery: Enabled by default
```

#### 2. Status Dashboard Overview
```
┌─ Sync Status Dashboard ──────────────────────┐
│                                              │
│ Current Status: [🟢 SYNCED]                  │
│ Active Since: 14:30:15 (5m 23s)             │
│                                              │
│ ┌─ Statistics ─┐  ┌─ Health ──┐  ┌─ Alerts ─┐ │
│ │ Checks: 1,247│  │ 99.2% ✅  │  │ 0 Active │ │
│ │ Desyncs: 3   │  │ 2.3s Avg  │  │ 3 Total  │ │
│ │ Last: 14:35:42│  │ <50ms ⚡   │  │ All Res. │ │
│ └──────────────┘  └───────────┘  └──────────┘ │
│                                              │
│ Last Check: 14:35:42  Next: 14:35:44         │
└──────────────────────────────────────────────┘

Status Indicators:
🟢 SYNCED - All fields synchronized (success rate >95%)
🟡 WARNING - Minor desyncs in non-critical fields (90-95%)
🟠 DESYNC - Important field desyncs requiring attention (80-90%)
🔴 CRITICAL - Critical field desyncs, game likely broken (<80%)
```

#### 3. Active Desync Alert System
```
🚨 Active Alerts Panel (appears when desyncs detected):
┌─ CRITICAL ALERT ─────────────────────────────┐
│ 🔴 Desync Detected in Critical Fields        │
│                                              │
│ Desync ID: #abc123                           │
│ Started: 14:35:30 (15 seconds ago)           │
│ Duration: 00:15 (ongoing)                    │
│                                              │
│ Affected Fields:                             │
│ • phase (frontend: "turn", backend: "scoring")│
│ • currentPlayer (frontend: "A", backend: "B")│
│                                              │
│ Impact Assessment:                           │
│ • Gameplay Blocking: YES                     │
│ • User Experience: SEVERE                    │
│ • Data Integrity: CORRUPTED                  │
│                                              │
│ Suggested Actions:                           │
│ 1. Request game state refresh from server    │
│ 2. Check network connection stability        │
│ 3. Consider reconnecting to the game         │
│                                              │
│ [🔧 Auto Recover] [✅ Mark Resolved] [📤 Export]│
└──────────────────────────────────────────────┘

Auto-Dismiss Timer: Alerts auto-dismiss after 30s if resolved
Audio Alerts: Configurable beep/sound for critical issues
Visual Alerts: Color-coded severity levels
```

#### 4. Tab Navigation System

##### Status Tab - Real-time Overview
```
Current Sync Health:
┌─ Field Status ───────────────────────────────┐
│ phase          🟢 SYNCED   Last: 14:35:42    │
│ currentPlayer  🟢 SYNCED   Last: 14:35:42    │  
│ currentRound   🟢 SYNCED   Last: 14:35:41    │
│ turnNumber     🟡 WARNING  Last: 14:35:30    │ ← Minor delay
│ myHand         🟢 SYNCED   Last: 14:35:42    │
│ players        🟢 SYNCED   Last: 14:35:41    │
│ declarations   🟢 SYNCED   Last: 14:35:42    │
│ scores         🟢 SYNCED   Last: 14:35:42    │
│ totalScores    🟢 SYNCED   Last: 14:35:42    │
│ gameOver       🟢 SYNCED   Last: 14:35:42    │
└──────────────────────────────────────────────┘

Quick Actions:
[🔍 Check Now] [📊 View Details] [⚙️ Configure]
```

##### History Tab - Timeline View
```
Sync Check History (last 50 checks):
┌─ Timeline ───────────────────────────────────┐
│ 14:35:42 🟢 All fields synced (Check #1247) │
│ 14:35:40 🟢 All fields synced (Check #1246) │
│ 14:35:38 🟡 turnNumber delayed (Check #1245) │
│ 14:35:36 🟢 All fields synced (Check #1244) │
│ 14:35:34 🟢 All fields synced (Check #1243) │
│ 14:35:32 🔴 DESYNC in phase (Check #1242)   │ ← Click to expand
│ 14:35:30 🔴 DESYNC started (Check #1241)    │
│ 14:35:28 🟢 All fields synced (Check #1240) │
└──────────────────────────────────────────────┘

Expandable Details (click any entry):
┌─ Check #1242 Details ────────────────────────┐
│ Timestamp: 14:35:32.456                      │
│ Total Fields Checked: 10                     │
│ Fields in Sync: 8                            │
│ Desynced Fields: 2                           │
│                                              │
│ Desync Details:                              │
│ • phase: frontend="turn", backend="scoring"  │
│ • currentPlayer: frontend="A", backend="B"   │
│                                              │
│ Resolution: Auto-recovered after 8 seconds   │
└──────────────────────────────────────────────┘
```

##### Desyncs Tab - Event Management
```
Active Desyncs (requiring attention):
┌─ ACTIVE DESYNCS ─────────────────────────────┐
│ Currently: 0 active desyncs                  │
│ System Status: 🟢 All systems synchronized   │
└──────────────────────────────────────────────┘

Resolved Desyncs (historical record):
┌─ RESOLVED DESYNCS ───────────────────────────┐
│ Desync #abc123 - Resolved 2m ago             │
│ Duration: 00:15  Severity: Critical          │
│ Fields: phase, currentPlayer                 │
│ Resolution: auto_recovered                   │
│ ─────────────────────────────────────────────│
│ Desync #def456 - Resolved 15m ago            │
│ Duration: 00:08  Severity: High              │
│ Fields: myHand                               │
│ Resolution: manual_fix "User refreshed page" │
│ ─────────────────────────────────────────────│
│ Desync #ghi789 - Resolved 1h ago             │
│ Duration: 00:03  Severity: Medium            │
│ Fields: scores                               │
│ Resolution: auto_recovered                   │
└──────────────────────────────────────────────┘

Resolution Methods:
• auto_recovered: System automatically fixed the issue
• manual_fix: User or developer manually resolved
• reconnect_required: Required full reconnection
• unsolved: Issue remains unresolved
```

##### Settings Tab - Configuration
```
┌─ Check Settings ─────────────────────────────┐
│ Check Interval: [2000] ms                   │
│ (How often to compare frontend vs backend)   │
│                                              │
│ Tolerance: [100] ms                          │
│ (Acceptable timing difference for timestamps)│
│                                              │
│ Critical Fields: [Edit List]                 │
│ ☑️ phase            ☑️ currentPlayer         │
│ ☑️ currentRound     ☑️ turnNumber            │
│ ☑️ gameOver         ☑️ myHand                │
│ ☑️ players          ☑️ declarations          │
│ ☑️ scores           ☑️ totalScores           │
└──────────────────────────────────────────────┘

┌─ Alert Settings ─────────────────────────────┐
│ ☑️ Enable Visual Alerts                      │
│ (Show popup notifications for desyncs)       │
│                                              │
│ ☑️ Enable Audio Alerts                       │
│ (Play sound for critical desyncs)            │
│                                              │
│ ☑️ Enable Auto Recovery                       │
│ (Attempt automatic fixes when possible)      │
│                                              │
│ ☑️ Critical Alerts Only                      │
│ (Only alert for critical/high severity)      │
│                                              │
│ Alert Duration: [30] seconds                 │
│ (How long to show visual alerts)             │
└──────────────────────────────────────────────┘

[💾 Save Settings] [↩️ Reset to Defaults]
```

#### 5. Desync Resolution System

##### Automatic Resolution
```
Auto-Recovery Process:
1. Desync detected in monitored field
2. System waits for configurable grace period (5s default)
3. Checks if field values converge naturally
4. If resolved, marks as "auto_recovered"
5. If persists, escalates to manual resolution

Example Auto-Recovery:
14:35:30 - Desync detected: currentPlayer mismatch
14:35:32 - Grace period active, monitoring...
14:35:35 - Values still mismatched, continuing monitoring
14:35:38 - Values converged: both show "PlayerB"
14:35:38 - Auto-resolution successful ✅
```

##### Manual Resolution
```
Manual Resolution Interface:
┌─ Resolve Desync #abc123 ─────────────────────┐
│ Current Status: Active (45 seconds)          │
│ Severity: Critical                           │
│ Fields: phase, currentPlayer                 │
│                                              │
│ Resolution Options:                          │
│ ○ Manual Fix Applied                         │
│   Description: [Text field for notes]       │
│                                              │
│ ○ Reconnection Required                      │
│   Description: [Connection reset performed]  │
│                                              │
│ ○ Mark as Resolved                           │
│   Description: [Issue resolved externally]   │
│                                              │
│ [✅ Resolve] [❌ Cancel]                      │
└──────────────────────────────────────────────┘

Resolution Tracking:
- All resolutions logged with timestamp
- Resolution method and description recorded
- Used for pattern analysis and statistics
- Helps identify recurring issues
```

#### 6. Export and Data Analysis
```
Export Options:
┌─ Export Sync Data ───────────────────────────┐
│ Export Type:                                 │
│ ○ Full Session (all sync checks and events) │
│ ○ Desyncs Only (just desync events)         │
│ ○ Statistics Summary (aggregated data)       │
│                                              │
│ Time Range:                                  │
│ From: [14:30:00] To: [14:35:42]             │
│ ○ All Data  ○ Last Hour  ○ Custom Range     │
│                                              │
│ Format:                                      │
│ ○ JSON (for technical analysis)              │
│ ○ CSV (for spreadsheet analysis)             │
│                                              │
│ [📥 Export] [❌ Cancel]                       │
└──────────────────────────────────────────────┘

Example Export Content:
{
  "sessionInfo": {
    "roomId": "room123",
    "playerName": "PlayerA",
    "startTime": 1640995200000,
    "endTime": 1640995500000,
    "totalChecks": 1247,
    "totalDesyncs": 3
  },
  "statistics": {
    "successRate": 99.2,
    "averageResolutionTime": 2300,
    "criticalDesyncs": 1,
    "autoResolutions": 2
  },
  "desyncEvents": [...],
  "syncHistory": [...]
}
```

---

### Real-World Example: Production Monitoring

**Scenario**: Continuous monitoring during peak gaming hours

```
Production Monitoring Workflow:

1. Session Start:
   - Game moderator starts sync checker at beginning of session
   - Configure for production environment:
     - Check interval: 5000ms (less aggressive)
     - Critical alerts only: Enabled
     - Auto recovery: Enabled
   - Monitor runs continuously in background

2. Early Warning Detection:
   - 15:42:30 - Minor desync detected in turnNumber field
   - Severity: Medium (no immediate action needed)
   - System logs event and continues monitoring
   - Auto-recovery successful after 3 seconds

3. Critical Issue Detection:
   - 15:58:15 - Critical desync alert triggered
   - Fields affected: phase, currentPlayer
   - Impact: Gameplay blocking for all players
   - Alert notification sent to moderator

4. Immediate Response:
   - Moderator receives visual and audio alert
   - Quick assessment shows network connectivity issue
   - Manual resolution: "Requesting game state refresh"
   - Issue resolved in 12 seconds

5. Post-Incident Analysis:
   - Export sync data for time period 15:50-16:00
   - Analyze pattern: network issues at 15:58:10-15:58:25
   - Update monitoring thresholds based on findings
   - Document incident for infrastructure team

6. Session Summary:
   - Total runtime: 2 hours 30 minutes
   - Total sync checks: 1,800
   - Desyncs detected: 4 (3 auto-resolved, 1 manual)
   - Overall success rate: 99.8%
   - Average resolution time: 4.2 seconds
```

---

## 🎯 Tool Selection Guide

### Choose the Right Tool for Your Situation

| Situation | Primary Tool | Secondary Tool | Why |
|-----------|--------------|----------------|-----|
| **"Something weird happened"** | 🎮 **Replay** | 🔍 **Debug** | Record exact sequence to reproduce issue |
| **"Cards show wrong values"** | 🔍 **Debug** | 🔄 **Sync** | Compare frontend vs backend state |
| **"Game feels laggy/desynced"** | 🔄 **Sync** | 🔍 **Debug** | Monitor sync health and performance |
| **Bug investigation** | 🎮 **Replay** | 🔍 **Debug** | Step-by-step analysis with state inspection |
| **Performance issues** | 🔍 **Debug** | 🔄 **Sync** | Check latency metrics and sync timing |
| **Production monitoring** | 🔄 **Sync** | - | Continuous health monitoring |
| **Development testing** | 🔍 **Debug** | 🎮 **Replay** | Understanding state flow during development |
| **User experience issues** | 🎮 **Replay** | 🔄 **Sync** | See user's perspective and check sync |

### Severity-Based Tool Selection

#### 🟢 Minor Issues (User reports cosmetic problems)
```
Primary: 🔍 Debug Tool
- Check for minor state differences
- Verify performance metrics are normal
- Look for UI-only issues

Secondary: 🔄 Sync Checker  
- Ensure no underlying sync problems
- Monitor for pattern of minor desyncs
```

#### 🟡 Moderate Issues (Functionality affected but playable)
```
Primary: 🔄 Sync Checker
- Identify specific fields causing problems
- Monitor desync frequency and resolution
- Check for recurring patterns

Secondary: 🔍 Debug Tool
- Detailed state comparison
- Performance impact analysis
- Network message inspection
```

#### 🔴 Critical Issues (Game broken, unplayable)
```
Primary: 🎮 Replay Tool
- Capture exact reproduction steps
- Record all events leading to failure
- Create shareable incident report

Secondary: 🔍 Debug Tool + 🔄 Sync Checker
- Real-time state analysis
- Critical field monitoring
- Immediate alerting system
```

---

### Combining Tools for Comprehensive Analysis

#### Standard Investigation Workflow
```
1. Start with 🔄 Sync Checker for continuous monitoring
2. When desync detected, activate 🔍 State Debugger
3. If issue persists or is complex, start 🎮 Replay recording
4. Use all three tools' exported data for complete analysis
```

#### Team Collaboration Workflow
```
1. Support agent uses 🎮 Replay to record user issue
2. Developer imports replay and uses 🔍 Debug for analysis
3. QA uses 🔄 Sync Checker to verify fix doesn't cause new desyncs
4. All data shared via exported JSON files
```

#### Production Monitoring Setup
```
Always Running: 🔄 Sync Checker
- Continuous background monitoring
- Critical alerts only to reduce noise
- Auto-recovery enabled for minor issues

On-Demand: 🔍 Debug Tool
- Activated when sync checker detects issues
- Deep-dive analysis of performance problems
- Network message inspection

Emergency: 🎮 Replay Tool  
- Started when critical issues occur
- Records exact incident for later analysis
- Provides reproduction steps for developers
```

---

## 🚨 Alert Interpretation Guide

Understanding the different types of alerts and their appropriate responses is crucial for effective debugging.

### Sync Checker Alert Levels

#### 🟢 SYNCED (Healthy State)
```
Characteristics:
- All critical fields match between frontend/backend
- Success rate >95%
- No active desyncs
- Response times <50ms average

What it means:
- Game is functioning normally
- Synchronization is working correctly
- No immediate action required

Recommended action:
- Continue normal monitoring
- Check periodically for performance trends
```

#### 🟡 WARNING (Monitor Closely)
```
Characteristics:
- Minor desyncs in non-critical fields
- Success rate 90-95%
- No gameplay impact
- Occasional timing mismatches

What it means:
- Minor synchronization delays
- Possible network latency issues
- No immediate user impact

Recommended actions:
1. Monitor for pattern development
2. Check network connection quality
3. Verify performance metrics are stable
4. Log for trend analysis
```

#### 🟠 DESYNC (Action Needed)
```
Characteristics:
- Desyncs in important fields (scores, player data)
- Success rate 80-90%
- May affect user experience
- User might notice discrepancies

What it means:
- Synchronization issues affecting gameplay
- User experience degradation likely
- Potential data consistency problems

Recommended actions:
1. Investigate root cause immediately
2. Use State Debug Tool for detailed analysis
3. Consider manual state refresh
4. Monitor user reports for related issues
5. Document issue for pattern analysis
```

#### 🔴 CRITICAL (Immediate Action Required)
```
Characteristics:
- Desyncs in critical fields (phase, currentPlayer)
- Success rate <80%
- Game likely broken for user
- Multiple field mismatches

What it means:
- Game is unplayable or severely broken
- Core game logic synchronization failed
- Immediate intervention required

Emergency response procedure:
1. Alert on-call developer immediately
2. Start Replay Tool to capture incident
3. Use State Debug Tool for real-time analysis
4. Consider forcing game reconnection
5. Escalate to infrastructure team if needed
6. Document thoroughly for post-incident review
```

---

### Recovery Actions by Severity Level

#### Low/Medium Desyncs (🟡 🟠)
```
Automatic Actions:
- System monitors for auto-recovery
- Logs events for pattern analysis
- Continues normal operation

Manual Actions (if needed):
- Refresh browser tab
- Clear browser cache
- Check network connection
- Wait for auto-recovery (usually 5-30 seconds)

Developer Actions:
- Review logs for recurring patterns
- Check server performance metrics
- Analyze network latency trends
- Update monitoring thresholds if needed
```

#### High Desyncs (🟠 Critical fields)
```
Immediate Actions:
- Check network connection stability
- Force refresh of game state
- Restart game session if necessary
- Monitor other players for similar issues

Developer Actions:
- Investigate state synchronization code
- Check server-side game logic
- Review recent deployments for issues
- Increase monitoring frequency temporarily

System Actions:
- Alert development team
- Increase logging verbosity
- Trigger automatic health checks
- Prepare for possible rollback
```

#### Critical Desyncs (🔴)
```
Emergency Response (immediate):
1. Alert on-call engineer
2. Force game reconnection for affected users
3. Check server status and load
4. Verify database connectivity
5. Consider temporary game pause if widespread

Investigation Actions:
1. Start comprehensive logging
2. Capture memory dumps if needed
3. Review recent configuration changes
4. Check for DDoS or security issues
5. Coordinate with infrastructure team

Communication Actions:
1. Notify game moderators
2. Prepare user communication if needed
3. Update status page if applicable
4. Document incident timeline
```

---

### Alert Escalation Matrix

| Alert Level | Initial Response | Escalation Time | Escalation Target |
|-------------|------------------|-----------------|-------------------|
| 🟢 SYNCED | Monitor | N/A | N/A |
| 🟡 WARNING | Log & Monitor | 15 minutes | Development Team |
| 🟠 DESYNC | Investigate | 5 minutes | Senior Developer |
| 🔴 CRITICAL | Emergency Response | Immediate | On-call Engineer + Manager |

---

## 📊 Export Data Formats

All debugging tools export data in JSON format for programmatic analysis and team collaboration.

### Game Replay Export Format

```json
{
  "sessionInfo": {
    "id": "replay-abc123",
    "roomId": "room456", 
    "playerName": "PlayerA",
    "startTime": 1640995200000,
    "endTime": 1640995380000,
    "duration": 180000,
    "totalEvents": 247
  },
  "gameMetadata": {
    "totalPlayers": 4,
    "gamePhases": ["preparation", "declaration", "turn", "scoring"],
    "totalRounds": 3,
    "finalScores": {
      "PlayerA": 25,
      "PlayerB": 18,
      "PlayerC": 22,
      "PlayerD": 15
    }
  },
  "events": [
    {
      "id": "event-001",
      "timestamp": 1640995205000,
      "sequence": 1,
      "type": "system_event",
      "source": "frontend",
      "roomId": "room456",
      "data": {
        "type": "recording_started",
        "initialGameState": { ... }
      },
      "metadata": {
        "playerName": "PlayerA"
      }
    },
    {
      "id": "event-002", 
      "timestamp": 1640995210000,
      "sequence": 2,
      "type": "user_action",
      "source": "user",
      "roomId": "room456",
      "data": {
        "event": "play_pieces",
        "data": {
          "pieces": ["A♠", "K♠"],
          "count": 2
        }
      },
      "metadata": {
        "playerName": "PlayerA",
        "actionType": "play_pieces"
      }
    }
  ],
  "version": "1.0.0"
}
```

**Usage Examples:**
```javascript
// Load and analyze replay data
const replayData = JSON.parse(exportedJson);

// Find all user actions
const userActions = replayData.events.filter(e => e.type === 'user_action');

// Calculate session duration
const duration = replayData.sessionInfo.duration;

// Find events by player
const playerAEvents = replayData.events.filter(e => 
  e.metadata?.playerName === 'PlayerA'
);
```

---

### State Debug Export Format

```json
{
  "sessionInfo": {
    "id": "debug-def789",
    "roomId": "room456",
    "playerName": "PlayerA", 
    "startTime": 1640995200000,
    "endTime": 1640995500000,
    "duration": 300000,
    "totalSnapshots": 150
  },
  "stateHistory": [
    {
      "id": "snapshot-001",
      "timestamp": 1640995205000,
      "source": "frontend",
      "roomId": "room456",
      "gameState": {
        "phase": "turn",
        "currentPlayer": "PlayerA",
        "myHand": ["A♠", "K♣", "Q♦"]
      },
      "metadata": {
        "phase": "turn",
        "playerName": "PlayerA",
        "checksum": "abc123"
      }
    }
  ],
  "messages": [
    {
      "id": "msg-001",
      "timestamp": 1640995210000,
      "direction": "incoming",
      "event": "phase_change",
      "data": {
        "phase": "turn",
        "currentPlayer": "PlayerB"
      },
      "roomId": "room456",
      "metadata": {
        "size": 156,
        "latency": 25
      }
    }
  ],
  "differences": [
    {
      "path": "currentPlayer",
      "frontendValue": "PlayerA", 
      "backendValue": "PlayerB",
      "type": "different",
      "severity": "critical"
    }
  ],
  "performanceMetrics": {
    "stateUpdateLatency": {
      "average": 25.4,
      "min": 12,
      "max": 45,
      "recent": [23, 27, 19, 31, 24]
    },
    "websocketLatency": {
      "average": 15.2,
      "min": 8,
      "max": 28,
      "recent": [14, 16, 12, 18, 15]
    }
  },
  "version": "1.0.0"
}
```

**Usage Examples:**
```javascript
// Analyze performance trends
const avgLatency = debugData.performanceMetrics.stateUpdateLatency.average;

// Find critical differences
const criticalDiffs = debugData.differences.filter(d => 
  d.severity === 'critical'
);

// Network message analysis
const phaseChangeMessages = debugData.messages.filter(m => 
  m.event === 'phase_change'
);
```

---

### Sync Checker Export Format

```json
{
  "sessionInfo": {
    "id": "sync-ghi012",
    "roomId": "room456",
    "playerName": "PlayerA",
    "startTime": 1640995200000,
    "endTime": 1640995800000,
    "totalChecks": 1247,
    "totalDesyncs": 3
  },
  "syncHistory": [
    {
      "id": "sync-001",
      "timestamp": 1640995205000,
      "fieldPath": "phase",
      "frontendValue": "turn",
      "backendValue": "turn", 
      "isSync": true,
      "severity": "info",
      "context": {
        "phase": "turn",
        "playerName": "PlayerA",
        "sequence": 127,
        "roomId": "room456"
      }
    },
    {
      "id": "sync-002",
      "timestamp": 1640995210000,
      "fieldPath": "currentPlayer",
      "frontendValue": "PlayerA",
      "backendValue": "PlayerB",
      "isSync": false,
      "severity": "critical",
      "context": {
        "phase": "turn",
        "playerName": "PlayerA",
        "sequence": 128,
        "roomId": "room456"
      }
    }
  ],
  "desyncEvents": [
    {
      "id": "desync-001",
      "timestamp": 1640995210000,
      "startTime": 1640995210000,
      "endTime": 1640995218000,
      "affectedFields": ["currentPlayer", "turnNumber"],
      "severity": "critical",
      "impact": {
        "gameplayBlocking": true,
        "userExperienceImpact": "severe",
        "dataIntegrity": "corrupted"
      },
      "resolution": {
        "method": "auto_recovered",
        "timestamp": 1640995218000,
        "description": "All affected fields returned to sync state"
      }
    }
  ],
  "statistics": {
    "totalChecks": 1247,
    "totalDesyncs": 3,
    "averageResolutionTime": 2300,
    "successRate": 99.2,
    "criticalDesyncs": 1,
    "autoResolutions": 2,
    "manualResolutions": 1
  },
  "settings": {
    "checkInterval": 2000,
    "toleranceMs": 100,
    "enableVisualAlerts": true,
    "enableAudioAlerts": true,
    "enableAutoRecovery": true,
    "criticalOnly": false
  },
  "version": "1.0.0"
}
```

**Usage Examples:**
```javascript
// Calculate success rate
const successRate = (syncData.statistics.totalChecks - 
  syncData.statistics.totalDesyncs) / syncData.statistics.totalChecks * 100;

// Find longest desync
const longestDesync = syncData.desyncEvents.reduce((longest, current) => 
  (current.endTime - current.startTime) > (longest.endTime - longest.startTime) 
    ? current : longest
);

// Analyze field-specific issues
const fieldIssues = syncData.syncHistory.filter(s => !s.isSync)
  .reduce((acc, curr) => {
    acc[curr.fieldPath] = (acc[curr.fieldPath] || 0) + 1;
    return acc;
  }, {});
```

---

## 🔧 Development Tips

### Best Practices for Production Use

#### 1. Performance Considerations
```
Tool Usage Guidelines:
✅ Sync Checker: Always safe for production (low overhead)
⚠️  State Debugger: Use judiciously (moderate overhead)
❌ Replay Tool: Development/staging only (high overhead)

Resource Impact:
- Sync Checker: ~1-2% CPU, minimal memory
- State Debugger: ~3-5% CPU, moderate memory usage
- Replay Tool: ~5-10% CPU, high memory usage (stores all events)

Production Recommendations:
- Enable Sync Checker by default with 5-10s intervals
- Use State Debugger only for investigation (not continuously)
- Reserve Replay Tool for critical issue reproduction
```

#### 2. Alert Configuration for Different Environments

##### Development Environment
```
Sync Checker Settings:
- Check Interval: 1000ms (frequent checking)
- All alert types enabled
- Auto-recovery disabled (want to see all issues)
- Tolerance: 50ms (strict)

State Debugger:
- Auto-update enabled
- Show all message types
- Performance monitoring active
- Export enabled for all sessions
```

##### Staging/QA Environment  
```
Sync Checker Settings:
- Check Interval: 2000ms (balanced)
- Visual alerts enabled, audio optional
- Auto-recovery enabled for low/medium severity
- Tolerance: 100ms (realistic)

Focus Areas:
- Load testing with multiple concurrent users
- Network latency simulation
- Recovery time measurement
- Pattern detection across user sessions
```

##### Production Environment
```
Sync Checker Settings:
- Check Interval: 5000ms (conservative)
- Critical alerts only
- Auto-recovery enabled
- Tolerance: 200ms (accommodate network variations)

Monitoring Strategy:
- Continuous sync health monitoring
- Automated alerting to on-call team
- Daily/weekly trend analysis
- Escalation procedures documented
```

---

### Common Troubleshooting Workflows

#### Workflow 1: User Reports "Game is Broken"
```
Step 1: Immediate Assessment (30 seconds)
- Start Sync Checker to check current sync status
- Look for active critical desyncs
- Check if issue affects multiple players

Step 2: Detailed Investigation (2-5 minutes)
- If desyncs found: Use State Debugger for field analysis
- If no desyncs: Start Replay Tool to capture user actions
- Check performance metrics for bottlenecks

Step 3: Resolution (varies)
- Auto-recovery: Wait and monitor
- Manual fix: Apply appropriate resolution
- Escalation: Alert development team with exported data

Step 4: Documentation
- Export all relevant debugging data
- Document resolution method and timeline
- Update knowledge base if new issue type
```

#### Workflow 2: Performance Degradation Investigation
```
Step 1: Baseline Measurement
- Use State Debugger to capture current performance metrics
- Note: state update latency, WebSocket latency, render times
- Compare to historical baselines

Step 2: Load Analysis
- Check if degradation correlates with user count
- Monitor performance across multiple sessions
- Identify specific operations causing delays

Step 3: Root Cause Analysis
- Use Replay Tool to capture slow operations
- Analyze network message timing and size
- Check for JavaScript execution bottlenecks

Step 4: Optimization
- Implement targeted fixes based on findings
- Re-measure with debugging tools
- Document performance improvements
```

#### Workflow 3: Recurring Desync Pattern Analysis
```
Step 1: Data Collection (1-2 days)
- Enable continuous Sync Checker monitoring
- Export sync data at regular intervals
- Collect multiple instances of the pattern

Step 2: Pattern Analysis
- Aggregate exported data across sessions
- Identify common factors:
  - Time of day patterns
  - User action sequences
  - Network conditions
  - Specific game phases

Step 3: Reproduction
- Use Replay Tool to attempt reproduction
- Test under controlled conditions
- Verify fix effectiveness with Sync Checker

Step 4: Prevention
- Update monitoring thresholds
- Implement proactive detection
- Document pattern for future reference
```

---

### Integration with External Tools

#### Log Aggregation Integration
```javascript
// Export debugging data to logging system
const exportAllDebuggingData = () => {
  const replayData = gameReplayManager.exportData();
  const debugData = stateDebugger.exportData();
  const syncData = syncChecker.exportData();
  
  // Send to log aggregation service
  logService.send({
    type: 'debugging_session',
    timestamp: Date.now(),
    roomId: currentRoomId,
    data: {
      replay: JSON.parse(replayData),
      debug: JSON.parse(debugData), 
      sync: JSON.parse(syncData)
    }
  });
};
```

#### Monitoring Dashboard Integration
```javascript
// Real-time sync metrics for dashboards
const getSyncMetrics = () => {
  const syncState = syncChecker.getState();
  
  return {
    successRate: ((syncState.totalChecks - syncState.totalDesyncs) / 
                 syncState.totalChecks * 100).toFixed(1),
    averageResolutionTime: syncState.averageResolutionTime,
    activeDesyncs: syncChecker.getActiveDesyncs().length,
    lastCheckTime: syncState.lastSyncCheck,
    status: getCurrentSyncStatus()
  };
};

// Send metrics every 30 seconds
setInterval(() => {
  dashboardAPI.updateMetrics('sync_health', getSyncMetrics());
}, 30000);
```

#### Automated Testing Integration
```javascript
// Automated sync health testing
const runSyncHealthTest = async () => {
  // Start monitoring
  syncChecker.startChecking(testRoomId, 'TestBot');
  
  // Run test scenario
  await runGameplayScenario();
  
  // Collect results
  const results = {
    totalChecks: syncChecker.getState().totalChecks,
    desyncsDetected: syncChecker.getActiveDesyncs().length,
    successRate: calculateSuccessRate(),
    averageLatency: getAverageLatency()
  };
  
  // Stop monitoring
  syncChecker.stopChecking();
  
  return results;
};
```

---

### Advanced Usage Patterns

#### Multi-Tool Correlation Analysis
```javascript
// Correlate events across all debugging tools
const correlateDebuggingEvents = (timeWindow = 5000) => {
  const syncEvents = syncChecker.getSyncHistory();
  const debugEvents = stateDebugger.getStateHistory();
  const replayEvents = gameReplayManager.getFilteredEvents();
  
  const correlatedEvents = [];
  
  syncEvents.forEach(syncEvent => {
    if (!syncEvent.isSync) {
      // Find related events within time window
      const relatedDebugEvents = debugEvents.filter(debugEvent => 
        Math.abs(debugEvent.timestamp - syncEvent.timestamp) < timeWindow
      );
      
      const relatedReplayEvents = replayEvents.filter(replayEvent =>
        Math.abs(replayEvent.timestamp - syncEvent.timestamp) < timeWindow
      );
      
      correlatedEvents.push({
        syncEvent,
        relatedDebugEvents,
        relatedReplayEvents,
        correlation: 'desync_pattern'
      });
    }
  });
  
  return correlatedEvents;
};
```

#### Predictive Issue Detection
```javascript
// Analyze patterns to predict potential issues
const predictPotentialIssues = () => {
  const syncHistory = syncChecker.getSyncHistory(100); // Last 100 checks
  const performanceMetrics = stateDebugger.getState().performanceMetrics;
  
  const predictions = [];
  
  // Check for increasing latency trend
  const recentLatencies = performanceMetrics.stateUpdateLatency.recent;
  const trend = calculateTrend(recentLatencies);
  if (trend > 0.1) { // 10% increase trend
    predictions.push({
      type: 'performance_degradation',
      confidence: 0.8,
      suggestedAction: 'Monitor performance closely'
    });
  }
  
  // Check for frequent minor desyncs (may indicate major desync coming)
  const recentDesyncs = syncHistory.filter(s => 
    !s.isSync && Date.now() - s.timestamp < 60000 // Last minute
  );
  if (recentDesyncs.length > 5) {
    predictions.push({
      type: 'potential_major_desync',
      confidence: 0.7,
      suggestedAction: 'Investigate sync stability'
    });
  }
  
  return predictions;
};
```

---

This comprehensive debugging suite provides developers with enterprise-grade tools for maintaining synchronization health and quickly resolving issues in production environments. The combination of proactive monitoring, detailed analysis, and comprehensive data export capabilities ensures robust debugging capabilities for complex multiplayer game scenarios.

**Tool Summary:**
- **🎮 Replay Tool**: Perfect reproduction and investigation
- **🔍 Debug Tool**: Real-time analysis and performance monitoring  
- **🔄 Sync Checker**: Proactive detection and automated recovery

Together, these tools provide complete visibility into game state synchronization and enable rapid issue resolution with minimal user impact.