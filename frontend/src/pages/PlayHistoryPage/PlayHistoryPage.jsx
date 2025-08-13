import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { usePlayHistory } from '../../hooks/usePlayHistory';
import './styles.css';

// Placeholder components - will be implemented later
const LoadingState = () => (
  <div className="min-h-screen bg-game-background flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-game-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-game-text text-lg">Loading game history...</p>
    </div>
  </div>
);

const ErrorState = ({ error, onRetry }) => (
  <div className="min-h-screen bg-game-background flex items-center justify-center">
    <div className="bg-game-surface rounded-lg shadow-game-lg p-8 max-w-md w-full mx-4">
      <div className="text-center">
        <div className="w-16 h-16 bg-game-danger/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-game-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-game-text mb-2">Failed to load game history</h2>
        <p className="text-game-text/60 mb-6">{error.message}</p>
        {error.canRetry && (
          <button 
            onClick={onRetry}
            className="bg-game-primary hover:bg-game-primary/80 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  </div>
);

const EmptyState = () => (
  <div className="min-h-screen bg-game-background flex items-center justify-center">
    <div className="text-center">
      <p className="text-game-text/60 text-lg">No game history found</p>
    </div>
  </div>
);

export const PlayHistoryPage = () => {
  const { roomId } = useParams();
  const { data, loading, error, retry } = usePlayHistory(roomId);
  const [selectedRound, setSelectedRound] = useState(1);
  
  // Add play-history-page and dark classes to body
  useEffect(() => {
    document.body.classList.add('play-history-page', 'dark');
    return () => {
      document.body.classList.remove('play-history-page', 'dark');
    };
  }, []);
  
  if (loading) {
    return <LoadingState />;
  }
  
  if (error) {
    return <ErrorState error={error} onRetry={retry} />;
  }
  
  if (!data) {
    return <EmptyState />;
  }
  
  // Check if there are no rounds
  if (!data.rounds || data.rounds.length === 0) {
    return (
      <div className="min-h-screen bg-game-background flex items-center justify-center">
        <div className="bg-game-surface rounded-lg shadow-game-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-game-text mb-2">No Game History</h2>
            <p className="text-game-text/60">This room was created but no rounds were played.</p>
            <div className="mt-4 text-sm text-game-text/40">
              <p>Room ID: {roomId}</p>
              <p>Players: {data.players.map(p => p.name).join(', ')}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  const currentRound = data.rounds[selectedRound - 1];
  
  // Basic implementation with mock data
  return (
    <div className="min-h-screen bg-game-background text-game-text" data-testid="play-history-page">
      <div className="max-w-7xl mx-auto p-6">
        <GameHeader 
          roomId={roomId}
          round={currentRound}
          totalRounds={data.rounds.length}
          selectedRound={selectedRound}
          onRoundSelect={setSelectedRound}
        />
        
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
          <PlayerOverview 
            players={data.players}
            roundData={currentRound}
          />
        </div>
        
        <div className="bg-game-surface rounded-lg shadow-game-lg p-8 mb-6">
          <DeclarationPhase 
            declarations={currentRound.declarations}
            players={data.players}
          />
        </div>
        
        <div className="bg-game-surface rounded-lg shadow-game-lg p-8 mb-6">
          <TurnTimeline 
            turns={currentRound.turns}
            players={data.players}
          />
        </div>
        
        <div className="bg-game-surface rounded-lg shadow-game-lg p-8">
          <RoundSummary 
            scoring={currentRound.scoring}
            winner={currentRound.winner}
          />
        </div>
      </div>
    </div>
  );
};

// Basic GameHeader component
const GameHeader = ({ roomId, round, totalRounds, selectedRound, onRoundSelect }) => {
  return (
    <div className="bg-game-surface rounded-lg shadow-game p-6 mb-8">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-3xl font-bold text-game-text">
          Room {roomId} - Round {selectedRound}
        </h1>
        
        <div className="flex items-center gap-2">
          <label className="text-sm text-game-text/80">Round:</label>
          <select 
            value={selectedRound}
            onChange={(e) => onRoundSelect(Number(e.target.value))}
            className="bg-game-background border border-game-text/20 rounded px-3 py-1 text-game-text focus:outline-none focus:border-game-primary"
          >
            {Array.from({ length: totalRounds }, (_, i) => (
              <option key={i + 1} value={i + 1}>Round {i + 1}</option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="text-sm text-game-text/60">
        <span>Total Turns: {round.turns.length}</span>
        <span className="mx-4">•</span>
        <span>Winner: <span className="text-game-success font-semibold">{round.winner}</span></span>
      </div>
    </div>
  );
};

// Basic PlayerOverview component
const PlayerOverview = ({ players, roundData }) => {
  return players.map((player) => {
    const isStarter = roundData.starter === player.name;
    const playerStats = roundData.scoring.players[player.name];
    
    return (
      <div 
        key={player.name}
        className={`
          bg-game-surface rounded-lg p-6 relative
          ${isStarter ? 'ring-2 ring-game-piece-gold' : ''}
        `}
      >
        {isStarter && (
          <span className="absolute top-2 right-2 text-xs bg-game-piece-gold text-game-background px-2 py-1 rounded">
            STARTER
          </span>
        )}
        
        <h3 className="text-xl font-semibold mb-4">{player.name}</h3>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-game-text/60">Declared:</span>
            <span className="font-mono">{playerStats.declared}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-game-text/60">Captured:</span>
            <span className="font-mono">{playerStats.captured}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-game-text/60">Score:</span>
            <span className={`font-mono font-bold ${
              playerStats.score > 0 ? 'text-game-success' : 
              playerStats.score < 0 ? 'text-game-danger' : ''
            }`}>
              {playerStats.score > 0 ? '+' : ''}{playerStats.score}
            </span>
          </div>
        </div>
      </div>
    );
  });
};

// DeclarationPhase component
const DeclarationPhase = ({ declarations, players }) => {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Declaration Phase</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {declarations.map((declaration) => {
          const player = players.find(p => p.name === declaration.player);
          return (
            <div key={declaration.player} className="bg-game-background rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium">{declaration.player}</h3>
                <span className="text-sm text-game-text/60">{player?.type}</span>
              </div>
              
              <div className="mb-3">
                <HandBeforePlay pieces={declaration.hand} />
              </div>
              
              <div className="text-center">
                <span className="text-sm text-game-text/60">Declared:</span>
                <p className="text-2xl font-bold text-game-primary">{declaration.declared}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// HandBeforePlay component
const HandBeforePlay = ({ pieces }) => {
  return (
    <div>
      <div className="text-xs text-game-text/60 mb-1">Hand</div>
      <div className="flex flex-wrap gap-1">
        {pieces.map((piece, index) => (
          <span 
            key={index}
            className={`
              px-2 py-1 rounded text-xs font-mono
              ${piece.color === 'red' 
                ? 'bg-game-piece-red/20 text-game-piece-red border border-game-piece-red/30' 
                : 'bg-game-piece-black/20 text-game-piece-black border border-game-piece-black/30'
              }
            `}
          >
            {piece.type}({piece.point})
          </span>
        ))}
      </div>
    </div>
  );
};

// TurnTimeline component
const TurnTimeline = ({ turns, players }) => {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Turn Timeline</h2>
      <div className="space-y-6">
        {turns.map((turn) => (
          <TurnSection 
            key={turn.turnNumber}
            turn={turn}
            turnNumber={turn.turnNumber}
            players={players}
          />
        ))}
      </div>
    </div>
  );
};

// TurnSection component
const TurnSection = ({ turn, turnNumber }) => {
  const isTriplePlay = turn.plays.every(p => p.pieces.length === 3);
  
  return (
    <div className="border-b border-game-text/10 pb-6 last:border-0">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">
          Turn {turnNumber} {isTriplePlay && '- Triple Play Showdown'}
        </h3>
        <div className="text-sm text-game-text/60">
          <span className="text-game-success font-semibold">{turn.winner} wins</span>
          <span className="ml-2">• {turn.winnerPieces} pieces</span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {turn.plays.map((play) => (
          <PlayCard 
            key={play.player}
            play={play}
            isWinner={play.player === turn.winner}
            isStarter={play.isStarter}
          />
        ))}
      </div>
    </div>
  );
};

// PlayCard component
const PlayCard = ({ play, isWinner, isStarter }) => {
  return (
    <div className={`
      bg-game-background rounded-lg p-4 relative
      ${isWinner ? 'ring-2 ring-game-success' : ''}
    `}>
      {isWinner && (
        <span className="absolute -top-2 -right-2 text-xs bg-game-success text-white px-2 py-1 rounded">
          WINNER
        </span>
      )}
      
      <div className="mb-3">
        <h4 className="font-medium flex items-center gap-2">
          {play.player}
          {isStarter && (
            <span className="text-xs text-game-piece-gold">(Starter)</span>
          )}
        </h4>
      </div>
      
      <div className="mb-3">
        <div className="text-xs text-game-text/60 mb-1">Hand Before Play</div>
        <div className="flex flex-wrap gap-1 mb-2">
          {play.handBefore.map((piece, index) => (
            <span 
              key={index}
              className={`
                px-1 py-0.5 rounded text-xs font-mono
                ${piece.color === 'red' 
                  ? 'bg-game-piece-red/20 text-game-piece-red' 
                  : 'bg-game-piece-black/20 text-game-piece-black'
                }
              `}
            >
              {piece.type[0]}{piece.point}
            </span>
          ))}
        </div>
      </div>
      
      <div className="mb-3">
        <div className="text-xs text-game-text/60 mb-1">Played</div>
        <div className="flex flex-wrap gap-1">
          {play.pieces.map((piece, index) => (
            <span 
              key={index}
              className={`
                px-2 py-1 rounded text-sm font-mono font-semibold
                ${piece.color === 'red' 
                  ? 'bg-game-piece-red text-white' 
                  : 'bg-game-piece-black text-white'
                }
              `}
            >
              {piece.type}({piece.point})
            </span>
          ))}
        </div>
      </div>
      
      <div className="border-t border-game-text/10 pt-2 mt-2">
        <div className="flex justify-between text-xs">
          <span className="text-game-text/60">Captured:</span>
          <span className="font-mono">0→{play.captured}</span>
        </div>
      </div>
    </div>
  );
};

// RoundSummary component
const RoundSummary = ({ scoring, winner }) => {
  // Convert players object to array for easier manipulation
  const playerScores = Object.entries(scoring.players).map(([name, score]) => ({
    name,
    ...score
  }));
  
  // Sort by score descending
  const sortedScores = [...playerScores].sort((a, b) => b.score - a.score);
  
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Round Summary</h2>
      
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-3">Final Scores</h3>
        <div className="space-y-2">
          {sortedScores.map((player, index) => (
            <div 
              key={player.name}
              className={`
                flex items-center justify-between p-3 rounded-lg
                ${player.name === winner ? 'bg-game-success/20 border border-game-success' : 'bg-game-background'}
              `}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold text-game-text/40">#{index + 1}</span>
                <span className="font-medium">{player.name}</span>
                {player.name === winner && (
                  <span className="text-xs bg-game-success text-white px-2 py-1 rounded">WINNER</span>
                )}
              </div>
              
              <div className="flex items-center gap-6 text-sm">
                <div className="text-right">
                  <div className="text-game-text/60">Declared</div>
                  <div className="font-mono">{player.declared}</div>
                </div>
                <div className="text-right">
                  <div className="text-game-text/60">Captured</div>
                  <div className="font-mono">{player.captured}</div>
                </div>
                <div className="text-right">
                  <div className="text-game-text/60">Base</div>
                  <div className="font-mono">{player.baseScore}</div>
                </div>
                <div className="text-right">
                  <div className="text-game-text/60">Multiplier</div>
                  <div className="font-mono">×{player.multiplier}</div>
                </div>
                <div className="text-right">
                  <div className="text-game-text/60">Score</div>
                  <div className={`font-mono font-bold text-lg ${
                    player.score > 0 ? 'text-game-success' : 
                    player.score < 0 ? 'text-game-danger' : ''
                  }`}>
                    {player.score > 0 ? '+' : ''}{player.score}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {scoring.bonuses && scoring.bonuses.length > 0 && (
        <div>
          <h3 className="text-lg font-medium mb-3">Bonuses</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {scoring.bonuses.map((bonus, index) => (
              <div key={index} className="bg-game-background rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{bonus.player}</div>
                    <div className="text-sm text-game-text/60">{bonus.description}</div>
                  </div>
                  <div className="text-game-success font-bold">+{bonus.points}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayHistoryPage;