import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { usePlayHistory } from '../../hooks/usePlayHistory';
import './styles.css';

// Placeholder components - will be implemented later
const LoadingState = () => (
  <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-[#3498db] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-white text-lg">Loading game history...</p>
    </div>
  </div>
);

const ErrorState = ({ error, onRetry }) => (
  <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
    <div className="bg-[#1a1a1a] rounded-lg shadow-[0_4px_20px_rgba(0,0,0,0.5)] p-8 max-w-md w-full mx-4">
      <div className="text-center">
        <div className="w-16 h-16 bg-[#e74c3c]/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-[#e74c3c]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">Failed to load game history</h2>
        <p className="text-[#999] mb-6">{error.message}</p>
        {error.canRetry && (
          <button 
            onClick={onRetry}
            className="bg-[#3498db] hover:bg-[#3498db]/80 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  </div>
);

const EmptyState = () => (
  <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
    <div className="text-center">
      <p className="text-[#999] text-lg">No game history found</p>
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
  
  const currentRound = data.rounds[selectedRound - 1];
  
  // Basic implementation with mock data
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="play-history-page">
      <div className="max-w-[1400px] mx-auto p-5">
        <GameHeader 
          roomId={roomId}
          round={currentRound}
          totalRounds={data.rounds.length}
          selectedRound={selectedRound}
          onRoundSelect={setSelectedRound}
        />
        
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-[15px] mb-[30px]">
          <PlayerOverview 
            players={data.players}
            roundData={currentRound}
          />
        </div>
        
        <div className="bg-[#1a1a1a] rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.5)] p-[25px] mb-[30px]">
          <DeclarationPhase 
            declarations={currentRound.declarations || []}
            handsDealt={currentRound.handsDealt}
            players={data.players}
          />
        </div>
        
        <div className="bg-[#1a1a1a] rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.5)] p-[25px] mb-[30px]">
          <TurnTimeline 
            turns={currentRound.turns || []}
            players={data.players}
          />
        </div>
        
        <div className="bg-gradient-to-br from-[#2a2a2a] to-[#1a1a1a] rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.5)] p-[30px]">
          <RoundSummary 
            scoring={currentRound.scoring}
            winner={currentRound.winner}
            finalCaptures={currentRound.finalCaptures}
          />
        </div>
      </div>
    </div>
  );
};

// Basic GameHeader component
const GameHeader = ({ roomId, round, totalRounds, selectedRound, onRoundSelect }) => {
  return (
    <div className="bg-gradient-to-br from-[#1a1a1a] to-[#2a2a2a] rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.5)] p-5 px-[30px] mb-[30px]">
      <div className="flex items-center justify-between mb-[15px]">
        <h1 className="text-2xl font-bold text-white">
          Room {roomId} - Round {selectedRound}
        </h1>
        
        <div className="flex items-center gap-[10px] bg-white/10 px-[15px] py-[5px] rounded-[20px]">
          <label className="text-sm text-[#999]">Round:</label>
          <select 
            value={selectedRound}
            onChange={(e) => onRoundSelect(Number(e.target.value))}
            className="bg-transparent border-none text-base font-semibold text-white focus:outline-none cursor-pointer"
          >
            {Array.from({ length: totalRounds }, (_, i) => (
              <option key={i + 1} value={i + 1} className="bg-[#2a2a2a]">Round {i + 1}</option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="text-sm text-[#999] flex gap-[30px]">
        <span>Total Turns: {round.turns?.length || 0}</span>
        <span>Winner: <span className="text-[#27ae60] font-semibold">{round.winner || 'Unknown'}</span></span>
      </div>
    </div>
  );
};

// Basic PlayerOverview component
const PlayerOverview = ({ players, roundData }) => {
  return players.map((player) => {
    const isStarter = roundData.starter === player.name;
    const playerStats = roundData.scoring?.players?.[player.name] || {};
    const isAI = player.type === 'bot';
    
    return (
      <div 
        key={player.name}
        className={`
          bg-[#1a1a1a] rounded-[10px] p-5 relative border-2 transition-all
          ${isStarter ? 'border-[#f39c12] shadow-[0_0_20px_rgba(243,156,18,0.3)]' : 'border-[#333]'}
        `}
      >
        {isStarter && (
          <span className="absolute top-2 right-2 text-[11px] bg-[#f39c12] text-white px-2 py-1 rounded font-semibold">
            STARTER
          </span>
        )}
        
        <div className="flex items-center gap-[10px] mb-[5px]">
          <h3 className="text-lg font-semibold text-[#f0f0f0]">{player.name}</h3>
          {isAI && (
            <span className="text-[11px] px-2 py-[2px] rounded bg-[#8b5cf6] text-white">
              AI
            </span>
          )}
        </div>
        
        <div className="grid grid-cols-3 gap-[10px] mt-[10px]">
          <div className="text-center">
            <div className="text-xl font-bold text-[#3498db]">{playerStats.declared || 0}</div>
            <div className="text-[11px] text-[#666] uppercase">Declared</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-[#3498db]">{playerStats.captured || 0}</div>
            <div className="text-[11px] text-[#666] uppercase">Captured</div>
          </div>
          <div className="text-center">
            <div className={`text-xl font-bold ${
              playerStats.score > 0 ? 'text-[#27ae60]' : 
              playerStats.score < 0 ? 'text-[#e74c3c]' : 'text-[#3498db]'
            }`}>
              {playerStats.score > 0 ? '+' : ''}{playerStats.score || 0}
            </div>
            <div className="text-[11px] text-[#666] uppercase">Score</div>
          </div>
        </div>
      </div>
    );
  });
};

// DeclarationPhase component
const DeclarationPhase = ({ declarations, handsDealt, players }) => {
  return (
    <div>
      <h2 className="text-xl mb-5 text-[#f0f0f0] flex items-center gap-[10px]">
        <div className="w-[30px] h-[30px] bg-[#3498db] rounded-full flex items-center justify-center text-base">
          📢
        </div>
        Declaration Phase
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-[15px]">
        {declarations.map((declaration, index) => {
          const player = players.find(p => p.name === declaration.player);
          // Use hand from declaration or fall back to handsDealt
          const hand = declaration.hand || handsDealt?.[declaration.player] || [];
          const isForced = declaration.declared === 0 && index === declarations.length - 1;
          return (
            <div key={declaration.player} className="bg-[#2a2a2a] rounded-lg p-[15px] text-center">
              <div className="text-sm text-[#999] mb-2">
                {declaration.player} (Position {index + 1})
              </div>
              
              <div className="text-[32px] font-bold text-[#e74c3c] mb-[5px]">
                {declaration.declared}
              </div>
              
              <div className="text-xs text-[#666]">
                {isForced ? (
                  <span className="text-[#e74c3c] italic">Forced zero</span>
                ) : (
                  <span>Room: {8 - declaration.declared} piles</span>
                )}
              </div>
              
              <div className="mt-3">
                <HandBeforePlay pieces={hand} />
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
      <div className="text-[11px] text-[#999] uppercase mb-[5px]">Hand</div>
      <div className="flex flex-wrap gap-1 justify-center">
        {pieces.map((piece, index) => {
          const isGeneral = piece.type === 'GENERAL' && piece.color === 'red' && piece.point === 14;
          return (
            <span 
              key={index}
              className={`
                px-2 py-1 rounded text-[11px] font-medium
                ${piece.color === 'red' 
                  ? isGeneral 
                    ? 'bg-[#e74c3c] text-white' 
                    : 'bg-[#e74c3c]/20 text-[#e74c3c] border border-[#e74c3c]' 
                  : 'bg-[#34495e]/20 text-[#95a5a6] border border-[#34495e]'
                }
              `}
            >
              {piece.type}({piece.point})
            </span>
          );
        })}
      </div>
    </div>
  );
};

// TurnTimeline component
const TurnTimeline = ({ turns, players }) => {
  return (
    <div>
      <h2 className="text-xl mb-5 text-[#f0f0f0] flex items-center gap-[10px]">
        <div className="w-[30px] h-[30px] bg-[#3498db] rounded-full flex items-center justify-center text-base">
          🎴
        </div>
        Turn Timeline
      </h2>
      <div className="space-y-5">
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
    <div className="bg-[#1a1a1a] p-[25px] rounded-xl mb-5">
      <div className="flex items-center justify-between mb-5 pb-[15px] border-b border-[#333]">
        <h3 className="text-lg text-[#f0f0f0]">
          Turn {turnNumber} {isTriplePlay && '- Triple Play Showdown'}
        </h3>
        <div className="flex items-center gap-[10px]">
          <span className="font-semibold text-[#27ae60]">{turn.winner} wins</span>
          <span className="bg-[#27ae60] text-white px-3 py-1 rounded-[20px] text-xs font-semibold">
            {turn.winnerPieces} pieces
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-[15px]">
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
  const isTriplePlay = play.pieces.length === 3;
  const totalPoints = play.pieces.reduce((sum, p) => sum + p.point, 0);
  
  return (
    <div className={`
      bg-[#2a2a2a] rounded-lg p-[15px] relative border-2 transition-all
      ${isWinner ? 'border-[#27ae60] bg-[#27ae60]/10' : 'border-transparent'}
    `}>
      {isWinner && (
        <span className="absolute -top-2 -right-2 text-xs bg-[#27ae60] text-white px-2 py-1 rounded">
          WINNER
        </span>
      )}
      
      <div className="text-sm font-medium text-[#ccc] mb-[10px]">
        {play.player} {isStarter && '(Starter)'}
      </div>
      
      <div className="bg-white/5 p-[10px] rounded-md mb-[15px]">
        <div className="text-[11px] text-[#999] uppercase mb-[5px]">Hand Before Play</div>
        <div className="flex flex-wrap gap-1">
          {play.handBefore.map((piece, index) => (
            <span 
              key={index}
              className={`
                text-[10px] px-[6px] py-[3px] rounded
                ${piece.color === 'red' 
                  ? 'bg-[#e74c3c]/20 text-[#e74c3c]' 
                  : 'bg-[#34495e]/20 text-[#95a5a6]'
                }
              `}
            >
              {piece.type?.charAt(0)}{piece.point}
            </span>
          ))}
        </div>
      </div>
      
      <div className="flex flex-wrap gap-2 mb-[10px]">
        {play.pieces.map((piece, index) => (
          <span 
            key={index}
            className={`
              px-3 py-2 rounded-md text-xs font-semibold flex items-center gap-[5px]
              ${piece.color === 'red' 
                ? 'bg-[#e74c3c] text-white' 
                : 'bg-[#34495e] text-white'
              }
            `}
          >
            <span className="text-[11px]">{piece.type}</span>
            <span className="font-bold">{piece.point}</span>
          </span>
        ))}
      </div>
      
      {isTriplePlay && (
        <div className="text-[11px] text-[#666] uppercase mb-[10px]">
          Triple Play ({totalPoints} pts)
        </div>
      )}
      
      <div className="flex justify-between mt-[10px] pt-[10px] border-t border-[#444] text-xs text-[#999]">
        <span>Captured: 0→{play.captured}</span>
        <span>Declared: {play.declared || 'N/A'}</span>
      </div>
    </div>
  );
};

// RoundSummary component
const RoundSummary = ({ scoring, winner, finalCaptures }) => {
  if (!scoring) return null;
  
  // Convert players object to array for easier manipulation
  const playerScores = Object.entries(scoring.players || {}).map(([name, score]) => ({
    name,
    ...score
  }));
  
  // Sort by score descending
  const sortedScores = [...playerScores].sort((a, b) => b.score - a.score);
  
  return (
    <div>
      <h2 className="text-xl mb-5 text-[#f0f0f0] flex items-center gap-[10px]">
        <div className="w-[30px] h-[30px] bg-[#3498db] rounded-full flex items-center justify-center text-base">
          🏆
        </div>
        Round Summary
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-[30px]">
        {sortedScores.map((player, index) => {
          const diff = player.captured - player.declared;
          const isExactMatch = diff === 0;
          const isForced = player.declared === 0 && player.captured === 0;
          
          return (
            <div key={player.name} className="bg-black/30 p-5 rounded-[10px] text-center">
              <div className="text-base font-semibold mb-[15px] text-[#f0f0f0]">
                {player.name}
              </div>
              
              <div className="grid gap-[10px]">
                <div className="flex justify-between p-[5px] text-sm">
                  <span className="text-[#999]">Declared</span>
                  <span className="font-semibold">{player.declared}</span>
                </div>
                <div className="flex justify-between p-[5px] text-sm">
                  <span className="text-[#999]">Captured</span>
                  <span className="font-semibold">{player.captured}</span>
                </div>
                <div className="flex justify-between p-[5px] text-sm">
                  <span className="text-[#999]">Difference</span>
                  <span className={`font-semibold ${
                    diff === 0 ? 'text-[#3498db]' : 
                    diff > 0 ? 'text-[#27ae60]' : 'text-[#e74c3c]'
                  }`}>
                    {diff > 0 ? '+' : ''}{diff}
                  </span>
                </div>
                <div className="flex justify-between p-[5px] text-sm">
                  <span className="text-[#999]">Score</span>
                  <span className={`font-semibold ${
                    player.score > 0 ? 'text-[#27ae60]' : 
                    player.score < 0 ? 'text-[#e74c3c]' : 'text-[#3498db]'
                  }`}>
                    {player.score > 0 ? '+' : ''}{player.score} pts
                  </span>
                </div>
                <div className="flex justify-between p-[5px] text-sm">
                  <span className="text-[#999]">Reason</span>
                  <span className="font-medium text-xs">
                    {isForced ? 'Forced zero bonus' : 
                     isExactMatch ? 'Exact match!' : 
                     diff > 0 ? `Exceeded by ${diff}` : `Missed by ${Math.abs(diff)}`}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {scoring.bonuses && scoring.bonuses.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-3 text-[#f0f0f0]">Bonuses</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {scoring.bonuses.map((bonus, index) => (
              <div key={index} className="bg-[#2a2a2a] rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-white">{bonus.player}</div>
                    <div className="text-sm text-[#999]">{bonus.description}</div>
                  </div>
                  <div className="text-[#27ae60] font-bold">+{bonus.points || bonus.value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {finalCaptures && (
        <div>
          <h3 className="text-lg font-medium mb-3 text-[#f0f0f0]">Final Captures</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(finalCaptures).map(([player, captures]) => (
              <div key={player} className="bg-[#2a2a2a] rounded-lg p-3 text-center">
                <div className="font-medium mb-1 text-white">{player}</div>
                <div className="text-2xl font-bold text-[#3498db]">{captures}</div>
                <div className="text-xs text-[#999]">piles</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayHistoryPage;