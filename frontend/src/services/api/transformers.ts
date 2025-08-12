import { PlayHistory, Round, Turn, Play, Piece, Player } from '../../types/playHistory';

/**
 * Transform API response from snake_case to camelCase format
 */
export function transformPlayHistoryResponse(apiData: any): PlayHistory {
  return {
    roomId: apiData.room_id,
    totalRounds: apiData.total_rounds || apiData.rounds?.length || 0,
    startTime: apiData.start_time || new Date().toISOString(),
    endTime: apiData.end_time || null,
    players: transformPlayers(apiData.players),
    rounds: apiData.rounds.map(transformRound),
    gameStatus: {
      completed: apiData.game_status?.completed || apiData.rounds?.length > 0,
      winner: apiData.game_status?.winner || null,
      finalScores: apiData.game_status?.final_scores || {}
    }
  };
}

function transformPlayers(playersData: any): Player[] {
  if (Array.isArray(playersData)) {
    return playersData;
  }
  
  // Handle object format from API
  return Object.entries(playersData).map(([name, data]: [string, any], index) => ({
    name: data.player_name || name,
    type: data.player_type === 'ai' ? 'bot' : 'human',
    position: index
  }));
}

function transformRound(roundData: any): Round {
  return {
    roundNumber: roundData.round_number,
    starter: roundData.initial_state?.starter?.player_name || 'Unknown',
    timestamp: roundData.timestamp || new Date().toISOString(),
    winner: roundData.round_summary?.winner || findRoundWinner(roundData),
    declarations: transformDeclarations(roundData),
    turns: transformTurns(roundData.turn_history || []),
    scoring: transformScoring(roundData.round_summary)
  };
}

function findRoundWinner(roundData: any): string {
  // Try to find winner from scoring data
  if (roundData.round_summary?.scoring) {
    const scores = roundData.round_summary.scoring;
    let maxScore = -Infinity;
    let winner = 'Unknown';
    
    Object.entries(scores).forEach(([player, data]: [string, any]) => {
      if (data.points > maxScore) {
        maxScore = data.points;
        winner = player;
      }
    });
    
    return winner;
  }
  
  return 'Unknown';
}

function transformDeclarations(roundData: any): any[] {
  const declarations = roundData.declaration_phase?.declarations || [];
  const handsDealt = roundData.hands_dealt || {};
  
  return declarations.map((decl: any) => {
    const playerName = decl.player_name || findPlayerName(decl.player_id, roundData);
    const hand = handsDealt[playerName] || [];
    
    return {
      player: playerName,
      declared: decl.declared,
      hand: hand.map(transformPiece),
      timestamp: decl.timestamp || new Date().toISOString()
    };
  });
}

function transformTurns(turns: any[]): Turn[] {
  return turns.map((turn, index) => ({
    turnNumber: turn.turn_number || index + 1,
    plays: transformPlays(turn.plays || []),
    winner: turn.winner?.player_name || turn.winner || 'Unknown',
    winnerPieces: turn.winner?.pieces_captured || turn.winnerPieces || 0,
    timestamp: turn.timestamp || new Date().toISOString()
  }));
}

function transformPlays(plays: any[]): Play[] {
  return plays.map(play => ({
    player: play.player_name || play.player || 'Unknown',
    pieces: (play.pieces_played || play.pieces || []).map(transformPiece),
    isStarter: play.is_starter || play.isStarter || false,
    handBefore: (play.hand_before || []).map(transformPiece),
    handAfter: (play.hand_after || []).map(transformPiece),
    captured: play.captured_count || play.captured || 0
  }));
}

function transformPiece(piece: any): Piece {
  // Handle different piece formats from API
  if (piece.kind) {
    // Format: { kind: "GENERAL_RED", point: 14 }
    const [type, color] = piece.kind.split('_');
    return {
      type: type,
      point: piece.point,
      color: color.toLowerCase() as 'red' | 'black'
    };
  }
  
  // Already in correct format
  return {
    type: piece.type,
    point: piece.point,
    color: piece.color
  };
}

function transformScoring(summary: any): any {
  if (!summary) {
    return {
      players: {},
      bonuses: []
    };
  }
  
  const players: Record<string, any> = {};
  
  if (summary.scoring) {
    Object.entries(summary.scoring).forEach(([playerName, score]: [string, any]) => {
      players[playerName] = {
        declared: summary.final_captures?.[playerName]?.declared || score.declared || 0,
        captured: summary.final_captures?.[playerName]?.captured || score.captured || 0,
        score: score.points || 0,
        multiplier: score.multiplier || 0,
        baseScore: score.points || 0
      };
    });
  }
  
  return {
    players,
    bonuses: []
  };
}

function findPlayerName(playerId: string, roundData: any): string {
  // Try to find player name from various sources
  const players = roundData.players || {};
  
  for (const [name, data] of Object.entries(players)) {
    if (data.player_id === playerId) {
      return name;
    }
  }
  
  // Fallback to player ID
  return playerId;
}