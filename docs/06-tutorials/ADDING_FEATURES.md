# Adding Features Tutorial - Step-by-Step Guide

## Table of Contents
1. [Overview](#overview)
2. [Feature Planning](#feature-planning)
3. [Example 1: Adding New Game Rule](#example-1-adding-new-game-rule)
4. [Example 2: Creating UI Component](#example-2-creating-ui-component)
5. [Example 3: Adding API Endpoint](#example-3-adding-api-endpoint)
6. [Common Patterns](#common-patterns)
7. [Testing Your Feature](#testing-your-feature)
8. [Deployment Checklist](#deployment-checklist)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Overview

This tutorial guides you through adding new features to Liap Tui. We'll cover three common scenarios with complete, working examples you can adapt for your needs.

### Prerequisites

- Development environment set up (see LOCAL_DEVELOPMENT.md)
- Understanding of the architecture (see README.md)
- Familiarity with WebSocket flow (see WEBSOCKET_FLOW.md)

## Feature Planning

### Before You Start

1. **Define the Feature**
   - What problem does it solve?
   - Who will use it?
   - How does it fit into existing gameplay?

2. **Identify Components**
   - Backend changes needed?
   - Frontend UI required?
   - State machine modifications?
   - Database schema updates?

3. **Plan Implementation**
   - Break into small, testable pieces
   - Consider backward compatibility
   - Plan for error cases

## Example 1: Adding New Game Rule

Let's add a "Lucky Seven" bonus: players get 7 extra points when capturing exactly 7 pieces in one turn.

### Step 1: Update Game Constants

```python
# backend/engine/constants.py
class GameConstants:
    # Existing constants...
    
    # Lucky Seven bonus
    LUCKY_SEVEN_ENABLED = True
    LUCKY_SEVEN_PIECE_COUNT = 7
    LUCKY_SEVEN_BONUS_POINTS = 7
```

### Step 2: Modify Scoring Logic

```python
# backend/engine/scoring.py
from typing import Dict, List, Tuple
from .constants import GameConstants

class ScoringEngine:
    def calculate_turn_bonus(
        self, 
        pieces_captured: int, 
        player_name: str
    ) -> Tuple[int, str]:
        """Calculate bonus points for special captures."""
        bonus = 0
        bonus_reason = ""
        
        # Lucky Seven bonus
        if (GameConstants.LUCKY_SEVEN_ENABLED and 
            pieces_captured == GameConstants.LUCKY_SEVEN_PIECE_COUNT):
            bonus = GameConstants.LUCKY_SEVEN_BONUS_POINTS
            bonus_reason = "Lucky Seven!"
            
        return bonus, bonus_reason
    
    def calculate_round_scores(
        self, 
        players: List['Player'], 
        pile_counts: Dict[str, int]
    ) -> Dict[str, int]:
        """Calculate scores with bonuses."""
        scores = {}
        
        for player in players:
            base_score = self._calculate_base_score(player)
            
            # Check for Lucky Seven bonus
            if pile_counts.get(player.name, 0) == 7:
                bonus, reason = self.calculate_turn_bonus(7, player.name)
                scores[player.name] = base_score + bonus
                
                # Log bonus for UI notification
                player.bonuses_earned.append({
                    'type': 'lucky_seven',
                    'points': bonus,
                    'reason': reason
                })
            else:
                scores[player.name] = base_score
                
        return scores
```

### Step 3: Update State Machine

```python
# backend/engine/state_machine/states/turn_state.py
class TurnState(GameState):
    async def handle_play(self, action: GameAction) -> None:
        # Existing play logic...
        
        # After determining turn winner
        if self.phase_data['turn_winner']:
            pile_count = self.phase_data['current_pile_count']
            
            # Check for Lucky Seven
            bonus, reason = self.game.scoring_engine.calculate_turn_bonus(
                pile_count, 
                self.phase_data['turn_winner']
            )
            
            if bonus > 0:
                # Broadcast special bonus event
                await self.broadcast_custom_event(
                    'special_bonus',
                    {
                        'player': self.phase_data['turn_winner'],
                        'bonus_type': 'lucky_seven',
                        'bonus_points': bonus,
                        'message': reason,
                        'animation': 'fireworks'
                    },
                    f"{self.phase_data['turn_winner']} earned {reason}"
                )
                
                # Update player score immediately
                winner_player = self.game.get_player(self.phase_data['turn_winner'])
                winner_player.score += bonus
```

### Step 4: Add Frontend Animation

```tsx
// frontend/src/components/BonusAnimation.tsx
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './BonusAnimation.css';

interface BonusAnimationProps {
    player: string;
    bonusType: string;
    bonusPoints: number;
    message: string;
}

export const BonusAnimation: React.FC<BonusAnimationProps> = ({
    player,
    bonusType,
    bonusPoints,
    message
}) => {
    const [isVisible, setIsVisible] = useState(true);
    
    useEffect(() => {
        const timer = setTimeout(() => setIsVisible(false), 3000);
        return () => clearTimeout(timer);
    }, []);
    
    if (bonusType !== 'lucky_seven') return null;
    
    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    className="bonus-animation lucky-seven"
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    transition={{ duration: 0.5, type: "spring" }}
                >
                    <div className="bonus-content">
                        <div className="seven-icon">7️⃣</div>
                        <h2>{message}</h2>
                        <p>{player} gains +{bonusPoints} points!</p>
                        <div className="sparkles">
                            {[...Array(7)].map((_, i) => (
                                <motion.span
                                    key={i}
                                    className="sparkle"
                                    animate={{
                                        y: [-20, -100],
                                        opacity: [1, 0],
                                        scale: [1, 0]
                                    }}
                                    transition={{
                                        duration: 1,
                                        delay: i * 0.1,
                                        repeat: Infinity,
                                        repeatDelay: 2
                                    }}
                                >
                                    ✨
                                </motion.span>
                            ))}
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
```

### Step 5: Handle WebSocket Event

```tsx
// frontend/src/phases/TurnPhase.tsx
import { BonusAnimation } from '../components/BonusAnimation';

export const TurnPhase: React.FC = () => {
    const [bonusAnimation, setBonusAnimation] = useState(null);
    
    useEffect(() => {
        const handleSpecialBonus = (data) => {
            setBonusAnimation({
                player: data.player,
                bonusType: data.bonus_type,
                bonusPoints: data.bonus_points,
                message: data.message
            });
            
            // Play sound effect
            if (data.bonus_type === 'lucky_seven') {
                new Audio('/sounds/lucky-seven.mp3').play();
            }
        };
        
        NetworkService.on('special_bonus', handleSpecialBonus);
        
        return () => {
            NetworkService.off('special_bonus', handleSpecialBonus);
        };
    }, []);
    
    return (
        <div className="turn-phase">
            {/* Existing turn UI */}
            
            {bonusAnimation && (
                <BonusAnimation {...bonusAnimation} />
            )}
        </div>
    );
};
```

### Step 6: Add Feature Toggle

```python
# backend/config/features.py
from pydantic import BaseSettings

class FeatureFlags(BaseSettings):
    """Feature toggles for gradual rollout."""
    
    # Game features
    lucky_seven_enabled: bool = True
    lucky_seven_bonus_points: int = 7
    
    # UI features
    enable_animations: bool = True
    enable_sound_effects: bool = True
    
    class Config:
        env_prefix = "FEATURE_"
```

## Example 2: Creating UI Component

Let's add a player statistics popup showing game history.

### Step 1: Create Statistics Component

```tsx
// frontend/src/components/PlayerStats.tsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { NetworkService } from '../network/NetworkService';
import './PlayerStats.css';

interface PlayerStatsProps {
    playerName: string;
    onClose: () => void;
}

interface Stats {
    gamesPlayed: number;
    gamesWon: number;
    winRate: number;
    highestScore: number;
    perfectDeclarations: number;
    luckySevenCount: number;
}

export const PlayerStats: React.FC<PlayerStatsProps> = ({ 
    playerName, 
    onClose 
}) => {
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        fetchPlayerStats();
    }, [playerName]);
    
    const fetchPlayerStats = async () => {
        try {
            // Request stats via WebSocket
            NetworkService.send('get_player_stats', { 
                player_name: playerName 
            });
            
            // Listen for response
            const handleStats = (data) => {
                if (data.player_name === playerName) {
                    setStats(data.stats);
                    setLoading(false);
                }
            };
            
            NetworkService.on('player_stats', handleStats);
            
            return () => {
                NetworkService.off('player_stats', handleStats);
            };
        } catch (error) {
            console.error('Failed to fetch stats:', error);
            setLoading(false);
        }
    };
    
    return (
        <motion.div
            className="player-stats-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
        >
            <motion.div
                className="player-stats-modal"
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                onClick={(e) => e.stopPropagation()}
            >
                <div className="stats-header">
                    <h2>{playerName}'s Statistics</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>
                
                {loading ? (
                    <div className="loading">Loading...</div>
                ) : stats ? (
                    <div className="stats-content">
                        <div className="stat-group">
                            <h3>Overall Performance</h3>
                            <div className="stat-row">
                                <span>Games Played:</span>
                                <span>{stats.gamesPlayed}</span>
                            </div>
                            <div className="stat-row">
                                <span>Games Won:</span>
                                <span>{stats.gamesWon}</span>
                            </div>
                            <div className="stat-row">
                                <span>Win Rate:</span>
                                <span>{(stats.winRate * 100).toFixed(1)}%</span>
                            </div>
                            <div className="stat-row">
                                <span>Highest Score:</span>
                                <span>{stats.highestScore}</span>
                            </div>
                        </div>
                        
                        <div className="stat-group">
                            <h3>Achievements</h3>
                            <div className="achievement-list">
                                <div className="achievement">
                                    <span className="achievement-icon">🎯</span>
                                    <span>Perfect Declarations: {stats.perfectDeclarations}</span>
                                </div>
                                <div className="achievement">
                                    <span className="achievement-icon">7️⃣</span>
                                    <span>Lucky Sevens: {stats.luckySevenCount}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div className="win-rate-chart">
                            <h3>Win Rate Progress</h3>
                            <WinRateChart data={stats.winRateHistory} />
                        </div>
                    </div>
                ) : (
                    <div className="no-stats">No statistics available</div>
                )}
            </motion.div>
        </motion.div>
    );
};

// Sub-component for win rate visualization
const WinRateChart: React.FC<{ data: number[] }> = ({ data }) => {
    const maxValue = Math.max(...data, 1);
    
    return (
        <div className="chart">
            {data.map((value, index) => (
                <div
                    key={index}
                    className="chart-bar"
                    style={{
                        height: `${(value / maxValue) * 100}%`
                    }}
                    title={`Game ${index + 1}: ${(value * 100).toFixed(1)}%`}
                />
            ))}
        </div>
    );
};
```

### Step 2: Add Backend Handler

```python
# backend/api/websocket/handlers/stats_handler.py
from typing import Dict, Any
import json

async def handle_get_player_stats(
    websocket: WebSocket,
    data: Dict[str, Any],
    room_manager: RoomManager
) -> None:
    """Handle player statistics request."""
    player_name = data.get('player_name')
    
    if not player_name:
        await send_error(websocket, "MISSING_PLAYER_NAME", "Player name required")
        return
    
    # Get stats from cache or database
    stats = await get_player_statistics(player_name)
    
    # Send response
    await websocket.send_json({
        'event': 'player_stats',
        'data': {
            'player_name': player_name,
            'stats': {
                'gamesPlayed': stats.games_played,
                'gamesWon': stats.games_won,
                'winRate': stats.win_rate,
                'highestScore': stats.highest_score,
                'perfectDeclarations': stats.perfect_declarations,
                'luckySevenCount': stats.lucky_seven_count,
                'winRateHistory': stats.win_rate_history[-10:]  # Last 10 games
            }
        }
    })

async def get_player_statistics(player_name: str) -> PlayerStats:
    """Fetch player statistics from storage."""
    # Check cache first
    cache_key = f"player_stats:{player_name}"
    cached = await redis_client.get(cache_key)
    
    if cached:
        return PlayerStats.parse_raw(cached)
    
    # Calculate from game history
    stats = PlayerStats(player_name=player_name)
    
    # In production, this would query the database
    # For now, generate sample data
    import random
    stats.games_played = random.randint(10, 100)
    stats.games_won = random.randint(0, stats.games_played)
    stats.win_rate = stats.games_won / stats.games_played if stats.games_played > 0 else 0
    stats.highest_score = random.randint(50, 120)
    stats.perfect_declarations = random.randint(0, stats.games_won)
    stats.lucky_seven_count = random.randint(0, stats.games_played // 5)
    
    # Generate win rate history
    stats.win_rate_history = []
    wins = 0
    for i in range(1, min(stats.games_played + 1, 11)):
        if random.random() < stats.win_rate:
            wins += 1
        stats.win_rate_history.append(wins / i)
    
    # Cache for 5 minutes
    await redis_client.setex(
        cache_key,
        300,
        stats.json()
    )
    
    return stats
```

### Step 3: Register WebSocket Handler

```python
# backend/api/websocket/message_router.py
from .handlers import stats_handler

MESSAGE_HANDLERS = {
    # Existing handlers...
    
    # Statistics
    'get_player_stats': stats_handler.handle_get_player_stats,
}
```

### Step 4: Add to Player List UI

```tsx
// frontend/src/components/PlayerList.tsx
import { PlayerStats } from './PlayerStats';

export const PlayerList: React.FC = ({ players }) => {
    const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
    
    return (
        <div className="player-list">
            <h3>Players</h3>
            {players.map((player) => (
                <div key={player.name} className="player-item">
                    <span className="player-name">{player.name}</span>
                    <span className="player-score">{player.score}</span>
                    <button
                        className="stats-btn"
                        onClick={() => setSelectedPlayer(player.name)}
                        title="View statistics"
                    >
                        📊
                    </button>
                </div>
            ))}
            
            {selectedPlayer && (
                <PlayerStats
                    playerName={selectedPlayer}
                    onClose={() => setSelectedPlayer(null)}
                />
            )}
        </div>
    );
};
```

## Example 3: Adding API Endpoint

Let's add a REST endpoint for game replay data (useful for spectators or analysis).

### Step 1: Create Replay Model

```python
# backend/models/replay.py
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class GameReplay(BaseModel):
    """Complete game replay data."""
    game_id: str
    room_id: str
    started_at: datetime
    ended_at: datetime
    players: List[str]
    winner: str
    final_scores: Dict[str, int]
    rounds: List['RoundReplay']
    total_duration: float
    
class RoundReplay(BaseModel):
    """Single round replay data."""
    round_number: int
    multiplier: int
    initial_hands: Dict[str, List[Dict[str, Any]]]
    declarations: Dict[str, int]
    turns: List['TurnReplay']
    scores: Dict[str, int]
    
class TurnReplay(BaseModel):
    """Single turn replay data."""
    turn_number: int
    leading_player: str
    required_count: int
    plays: Dict[str, List[Dict[str, Any]]]
    winner: str
    pile_count: int
```

### Step 2: Create REST Endpoint

```python
# backend/api/routes/replay.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from ..auth import get_current_user
from ..models.replay import GameReplay

router = APIRouter(prefix="/api/replay", tags=["replay"])

@router.get("/{game_id}", response_model=GameReplay)
async def get_game_replay(
    game_id: str,
    user: Optional[str] = Depends(get_current_user)
) -> GameReplay:
    """Get complete replay data for a game."""
    # Check if replay exists
    replay_data = await fetch_game_replay(game_id)
    
    if not replay_data:
        raise HTTPException(status_code=404, detail="Game replay not found")
    
    # Check access permissions
    if not await user_can_access_replay(user, replay_data):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return replay_data

async def fetch_game_replay(game_id: str) -> Optional[GameReplay]:
    """Fetch replay data from storage."""
    # Try cache first
    cached = await redis_client.get(f"replay:{game_id}")
    if cached:
        return GameReplay.parse_raw(cached)
    
    # In production, fetch from database
    # For now, check if we have it in memory
    if game_id in replay_storage:
        replay = replay_storage[game_id]
        
        # Cache for future requests
        await redis_client.setex(
            f"replay:{game_id}",
            3600,  # 1 hour
            replay.json()
        )
        
        return replay
    
    return None

async def user_can_access_replay(
    user: Optional[str], 
    replay: GameReplay
) -> bool:
    """Check if user can access this replay."""
    # Public replays after game ends
    if replay.ended_at:
        return True
    
    # Players can always see their own games
    if user and user in replay.players:
        return True
    
    # Otherwise, requires special permission
    return False

@router.get("/{game_id}/turn/{round_number}/{turn_number}")
async def get_turn_replay(
    game_id: str,
    round_number: int,
    turn_number: int
) -> Dict[str, Any]:
    """Get specific turn data for detailed replay."""
    replay = await fetch_game_replay(game_id)
    
    if not replay:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Find specific turn
    try:
        round_data = replay.rounds[round_number - 1]
        turn_data = round_data.turns[turn_number - 1]
        
        return {
            'game_id': game_id,
            'round': round_number,
            'turn': turn_number,
            'data': turn_data.dict(),
            'context': {
                'multiplier': round_data.multiplier,
                'current_scores': calculate_scores_at_turn(replay, round_number, turn_number)
            }
        }
    except IndexError:
        raise HTTPException(status_code=404, detail="Turn not found")
```

### Step 3: Store Replay Data

```python
# backend/engine/replay_recorder.py
from typing import Dict, Any
import asyncio
from collections import defaultdict

class ReplayRecorder:
    """Records game events for replay functionality."""
    
    def __init__(self):
        self.active_recordings: Dict[str, GameReplay] = {}
        self.event_queue = asyncio.Queue()
        
    async def start_recording(self, game_id: str, room_id: str, players: List[str]):
        """Start recording a new game."""
        self.active_recordings[game_id] = GameReplay(
            game_id=game_id,
            room_id=room_id,
            started_at=datetime.utcnow(),
            players=[p.name for p in players],
            rounds=[]
        )
    
    async def record_round_start(self, game_id: str, round_number: int, hands: Dict[str, List[Piece]]):
        """Record the start of a round."""
        if game_id not in self.active_recordings:
            return
            
        round_replay = RoundReplay(
            round_number=round_number,
            initial_hands={
                player: [p.to_dict() for p in pieces]
                for player, pieces in hands.items()
            },
            declarations={},
            turns=[],
            scores={}
        )
        
        self.active_recordings[game_id].rounds.append(round_replay)
    
    async def record_turn(self, game_id: str, turn_data: Dict[str, Any]):
        """Record a turn."""
        if game_id not in self.active_recordings:
            return
            
        replay = self.active_recordings[game_id]
        current_round = replay.rounds[-1]
        
        turn_replay = TurnReplay(
            turn_number=len(current_round.turns) + 1,
            leading_player=turn_data['leading_player'],
            required_count=turn_data['required_count'],
            plays=turn_data['plays'],
            winner=turn_data['winner'],
            pile_count=turn_data['pile_count']
        )
        
        current_round.turns.append(turn_replay)
    
    async def finalize_recording(self, game_id: str, winner: str, final_scores: Dict[str, int]):
        """Finalize and store the replay."""
        if game_id not in self.active_recordings:
            return
            
        replay = self.active_recordings[game_id]
        replay.ended_at = datetime.utcnow()
        replay.winner = winner
        replay.final_scores = final_scores
        replay.total_duration = (replay.ended_at - replay.started_at).total_seconds()
        
        # Store replay
        await store_replay(replay)
        
        # Clean up
        del self.active_recordings[game_id]

# Global recorder instance
replay_recorder = ReplayRecorder()
```

### Step 4: Integrate with Game Engine

```python
# backend/engine/game.py
from .replay_recorder import replay_recorder

class Game:
    async def start_new_round(self) -> None:
        """Start a new round with replay recording."""
        # Existing logic...
        
        # Record for replay
        hands = {
            player.name: player.hand
            for player in self.players
        }
        await replay_recorder.record_round_start(
            self.game_id,
            self.round_number,
            hands
        )
```

### Step 5: Add Frontend Replay Viewer

```tsx
// frontend/src/components/ReplayViewer.tsx
import React, { useState, useEffect } from 'react';
import { fetchReplay } from '../api/replay';
import { GameBoard } from './GameBoard';
import './ReplayViewer.css';

interface ReplayViewerProps {
    gameId: string;
}

export const ReplayViewer: React.FC<ReplayViewerProps> = ({ gameId }) => {
    const [replay, setReplay] = useState(null);
    const [currentRound, setCurrentRound] = useState(0);
    const [currentTurn, setCurrentTurn] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [speed, setSpeed] = useState(1);
    
    useEffect(() => {
        loadReplay();
    }, [gameId]);
    
    useEffect(() => {
        if (playing && replay) {
            const timer = setTimeout(() => {
                advanceReplay();
            }, 2000 / speed);
            
            return () => clearTimeout(timer);
        }
    }, [playing, currentRound, currentTurn, speed]);
    
    const loadReplay = async () => {
        try {
            const data = await fetchReplay(gameId);
            setReplay(data);
        } catch (error) {
            console.error('Failed to load replay:', error);
        }
    };
    
    const advanceReplay = () => {
        if (!replay) return;
        
        const round = replay.rounds[currentRound];
        if (currentTurn < round.turns.length - 1) {
            setCurrentTurn(currentTurn + 1);
        } else if (currentRound < replay.rounds.length - 1) {
            setCurrentRound(currentRound + 1);
            setCurrentTurn(0);
        } else {
            setPlaying(false);
        }
    };
    
    const getCurrentState = () => {
        if (!replay) return null;
        
        const round = replay.rounds[currentRound];
        const turn = round.turns[currentTurn];
        
        return {
            round: round,
            turn: turn,
            scores: calculateScoresAtPoint(replay, currentRound, currentTurn)
        };
    };
    
    if (!replay) {
        return <div className="loading">Loading replay...</div>;
    }
    
    const currentState = getCurrentState();
    
    return (
        <div className="replay-viewer">
            <div className="replay-header">
                <h2>Game Replay: {gameId}</h2>
                <div className="replay-info">
                    <span>Winner: {replay.winner}</span>
                    <span>Duration: {formatDuration(replay.total_duration)}</span>
                </div>
            </div>
            
            <div className="replay-controls">
                <button onClick={() => setPlaying(!playing)}>
                    {playing ? '⏸️ Pause' : '▶️ Play'}
                </button>
                
                <button onClick={() => setCurrentTurn(Math.max(0, currentTurn - 1))}>
                    ⏮️ Previous
                </button>
                
                <button onClick={advanceReplay}>
                    ⏭️ Next
                </button>
                
                <div className="speed-control">
                    <label>Speed:</label>
                    <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
                        <option value={0.5}>0.5x</option>
                        <option value={1}>1x</option>
                        <option value={2}>2x</option>
                        <option value={4}>4x</option>
                    </select>
                </div>
                
                <div className="progress">
                    Round {currentRound + 1}/{replay.rounds.length}, 
                    Turn {currentTurn + 1}/{currentState.round.turns.length}
                </div>
            </div>
            
            <div className="replay-game-view">
                <GameBoard 
                    gameState={currentState}
                    isReplay={true}
                />
                
                <div className="replay-sidebar">
                    <h3>Current Scores</h3>
                    {Object.entries(currentState.scores).map(([player, score]) => (
                        <div key={player} className="score-item">
                            <span>{player}:</span>
                            <span>{score}</span>
                        </div>
                    ))}
                    
                    <h3>Turn Details</h3>
                    <div className="turn-details">
                        <p>Leader: {currentState.turn.leading_player}</p>
                        <p>Required: {currentState.turn.required_count} pieces</p>
                        <p>Winner: {currentState.turn.winner}</p>
                        <p>Pile: {currentState.turn.pile_count} pieces</p>
                    </div>
                </div>
            </div>
        </div>
    );
};
```

## Common Patterns

### Pattern 1: Adding to State Machine

When adding features that affect game flow:

1. Define new phase data fields
2. Update phase transition logic
3. Add validation rules
4. Broadcast appropriate events

```python
# Add to phase data
class TurnPhaseData(BaseModel):
    # Existing fields...
    special_rules_active: List[str] = []
    bonus_multiplier: int = 1

# Update state logic
async def apply_special_rules(self):
    if "double_points_hour" in self.phase_data["special_rules_active"]:
        self.phase_data["bonus_multiplier"] = 2
```

### Pattern 2: WebSocket Event Flow

For real-time features:

1. Define event type and payload
2. Add backend handler
3. Register in message router
4. Add frontend listener
5. Update UI accordingly

### Pattern 3: Feature Flags

For gradual rollout:

```python
# Check feature flag
if await feature_flags.is_enabled("new_feature", user_id):
    # New behavior
else:
    # Original behavior
```

## Testing Your Feature

### Unit Tests

```python
# backend/tests/test_lucky_seven.py
import pytest
from engine.scoring import ScoringEngine

def test_lucky_seven_bonus():
    engine = ScoringEngine()
    bonus, reason = engine.calculate_turn_bonus(7, "TestPlayer")
    
    assert bonus == 7
    assert "Lucky Seven" in reason

def test_no_bonus_for_other_counts():
    engine = ScoringEngine()
    
    for count in [1, 2, 3, 4, 5, 6, 8, 9, 10]:
        bonus, reason = engine.calculate_turn_bonus(count, "TestPlayer")
        assert bonus == 0
```

### Integration Tests

```python
# backend/tests/test_integration.py
async def test_lucky_seven_in_game():
    # Set up game
    game = Game(["Alice", "Bob", "Carol", "David"])
    game.start_new_round()
    
    # Simulate capturing 7 pieces
    # ... game play logic ...
    
    # Verify bonus applied
    assert "lucky_seven" in alice.bonuses_earned
    assert alice.score == expected_score + 7
```

### Frontend Tests

```tsx
// frontend/src/components/__tests__/BonusAnimation.test.tsx
import { render, screen } from '@testing-library/react';
import { BonusAnimation } from '../BonusAnimation';

test('renders lucky seven animation', () => {
    render(
        <BonusAnimation
            player="Alice"
            bonusType="lucky_seven"
            bonusPoints={7}
            message="Lucky Seven!"
        />
    );
    
    expect(screen.getByText('Lucky Seven!')).toBeInTheDocument();
    expect(screen.getByText('Alice gains +7 points!')).toBeInTheDocument();
});
```

## Deployment Checklist

Before deploying your feature:

### Backend Checklist
- [ ] All tests pass
- [ ] Linting passes (`black . && pylint`)
- [ ] Type hints added
- [ ] Error handling complete
- [ ] Logging added for debugging
- [ ] Feature flag configured

### Frontend Checklist
- [ ] TypeScript compilation successful
- [ ] ESLint passes (`npm run lint`)
- [ ] Component tests written
- [ ] Responsive design verified
- [ ] Accessibility checked
- [ ] Browser compatibility tested

### Integration Checklist
- [ ] WebSocket events documented
- [ ] API contracts updated
- [ ] State synchronization verified
- [ ] Error states handled
- [ ] Performance impact assessed
- [ ] Backward compatibility maintained

### Deployment Steps
1. Deploy backend with feature flag OFF
2. Deploy frontend
3. Test in staging environment
4. Gradually enable feature flag
5. Monitor metrics and errors
6. Full rollout when stable

## Troubleshooting

### Common Issues

1. **WebSocket Event Not Received**
   - Check event name matches exactly
   - Verify handler registered in router
   - Check browser console for errors
   - Use Chrome DevTools WebSocket inspector

2. **State Out of Sync**
   - Ensure using enterprise architecture methods
   - Check sequence numbers
   - Verify no manual state updates
   - Look for race conditions

3. **Feature Not Working**
   - Check feature flag enabled
   - Verify all code deployed
   - Check browser cache cleared
   - Look for JavaScript errors

### Debug Tools

```python
# Add debug logging
import logging
logger = logging.getLogger(__name__)

async def debug_feature():
    logger.debug(f"Feature state: {feature_enabled}")
    logger.debug(f"Game state: {game.get_debug_info()}")
```

```tsx
// Frontend debugging
console.log('[LuckySeaven] Bonus triggered:', bonusData);
window.debugGameState = () => {
    console.log('Current state:', gameContext.state);
    console.log('Network queue:', NetworkService.getQueueStatus());
};
```

## Best Practices

### Do's
✅ Plan the feature completely before coding
✅ Break into small, testable pieces
✅ Use feature flags for gradual rollout
✅ Add comprehensive error handling
✅ Write tests as you go
✅ Document WebSocket events
✅ Consider mobile users
✅ Add telemetry for monitoring

### Don'ts
❌ Skip the planning phase
❌ Make breaking changes to APIs
❌ Forget about error cases
❌ Ignore performance impact
❌ Deploy without testing
❌ Hardcode values
❌ Bypass the state machine
❌ Forget accessibility

### Code Quality
- Follow existing patterns
- Use type hints (Python) and TypeScript
- Add meaningful comments
- Keep functions small and focused
- Handle edge cases
- Make code testable

## Summary

Adding features to Liap Tui involves:

1. **Planning**: Define the feature and affected components
2. **Implementation**: Follow existing patterns and architecture
3. **Testing**: Unit, integration, and E2E tests
4. **Deployment**: Use feature flags and gradual rollout
5. **Monitoring**: Track metrics and user feedback

Remember to:
- Use the enterprise architecture for state changes
- Maintain WebSocket-only communication for game operations
- Follow the established patterns
- Test thoroughly before deployment

Happy coding! 🎮