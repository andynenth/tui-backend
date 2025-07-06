/**
 * 🎮 **UnifiedGameUI** - Single container for all game phases
 * 
 * This component maintains the common structure across all phases
 * and only updates the content that changes, providing smooth transitions.
 */

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import EnhancedGamePiece from '../shared/EnhancedGamePiece';
import TableTurnUI from './TableTurnUI';

export function UnifiedGameUI({
  // Current phase
  phase = 'PREPARATION', // PREPARATION, DECLARATION, TURN, SCORING
  
  // Common data
  myHand = [],
  players = [],
  roundNumber = 1,
  
  // Preparation phase data
  weakHands = [],
  redealMultiplier = 1,
  isMyHandWeak = false,
  isMyDecision = false,
  
  // Declaration phase data
  declarations = {},
  currentTotal = 0,
  isMyTurnToDeclare = false,
  validOptions = [],
  isLastPlayer = false,
  
  // Turn phase data
  currentTurnPlays = [],
  requiredPieceCount = null,
  turnNumber = 1,
  isMyTurn = false,
  canPlayAnyCount = false,
  currentPlayer = '',
  
  // Actions
  onAcceptRedeal,
  onDeclineRedeal,
  onDeclare,
  onPlayPieces
}) {
  // Phase-specific states
  const [showDealing, setShowDealing] = useState(phase === 'PREPARATION');
  const [showWeakAlert, setShowWeakAlert] = useState(false);
  const [showMultiplier, setShowMultiplier] = useState(false);
  const [selectedDeclaration, setSelectedDeclaration] = useState(null);
  const [selectedPieces, setSelectedPieces] = useState([]);
  const [showConfirmPanel, setShowConfirmPanel] = useState(false);
  
  // Reset states when phase changes
  useEffect(() => {
    setSelectedDeclaration(null);
    setSelectedPieces([]);
    setShowConfirmPanel(false);
    
    if (phase === 'PREPARATION') {
      setShowDealing(true);
      setShowWeakAlert(false);
      
      // Simulate dealing animation
      const timer = setTimeout(() => {
        setShowDealing(false);
        // Check for weak hands
        const hasWeakHand = weakHands.length > 0 || isMyHandWeak || 
          (myHand.length > 0 && myHand.every(p => (p.point || p.value || 0) <= 9));
        if (hasWeakHand) {
          setShowWeakAlert(true);
        }
      }, 3500);
      
      return () => clearTimeout(timer);
    }
  }, [phase, weakHands, isMyHandWeak, myHand]);
  
  // Get phase-specific content
  const getPhaseTitle = () => {
    switch (phase) {
      case 'PREPARATION': return 'Preparation Phase';
      case 'DECLARATION': return 'Declaration Phase';
      case 'TURN': return 'Turn Phase';
      case 'SCORING': return 'Scoring Phase';
      default: return 'Game Phase';
    }
  };
  
  const getPhaseSubtitle = () => {
    switch (phase) {
      case 'PREPARATION': 
        return showDealing ? 'Dealing cards to all players' : 'Check your hand';
      case 'DECLARATION':
        return `Round ${roundNumber} • Declare your target pile count`;
      case 'TURN':
        return isMyTurn ? 'Your turn to play pieces' : `Waiting for ${currentPlayer}`;
      case 'SCORING':
        return 'Round complete';
      default:
        return '';
    }
  };
  
  // Handle piece selection for turn phase
  const handlePieceSelect = (index) => {
    if (!isMyTurn || phase !== 'TURN') return;
    
    setSelectedPieces(prev => {
      if (prev.includes(index)) {
        return prev.filter(i => i !== index);
      } else {
        const newSelection = [...prev, index];
        if (requiredPieceCount && newSelection.length > requiredPieceCount) {
          return [index];
        }
        if (canPlayAnyCount && newSelection.length > 6) {
          return prev;
        }
        return newSelection;
      }
    });
    
    if (!selectedPieces.includes(index) && selectedPieces.length === 0) {
      setTimeout(() => setShowConfirmPanel(true), 300);
    }
  };
  
  const handleConfirmPlay = () => {
    if (onPlayPieces && selectedPieces.length > 0) {
      onPlayPieces(selectedPieces);
      setSelectedPieces([]);
      setShowConfirmPanel(false);
    }
  };

  // For Turn phase, use the table UI which has its own container
  if (phase === 'TURN') {
    return (
      <>
        <TableTurnUI
          players={players}
          currentPlayer={currentPlayer}
          isMyTurn={isMyTurn}
          currentTurnPlays={currentTurnPlays}
          requiredPieceCount={requiredPieceCount}
          canPlayAnyCount={canPlayAnyCount}
          turnNumber={turnNumber}
          myHand={myHand}
          selectedPieces={selectedPieces}
          showConfirmPanel={showConfirmPanel}
          onPieceSelect={handlePieceSelect}
          onConfirmPlay={handleConfirmPlay}
          onCancelSelection={() => {
            setSelectedPieces([]);
            setShowConfirmPanel(false);
          }}
        />
      </>
    );
  }

  // For other phases, use the standard container
  return (
    <div className="game-container">
      {/* Fixed badges */}
      <div className="round-indicator">Round {roundNumber}</div>
      
      {redealMultiplier > 1 && (
        <div className="multiplier-indicator">{redealMultiplier}x</div>
      )}
      
      {/* Phase header - content changes but structure stays */}
      <div className="phase-header">
        <div className="phase-title">{getPhaseTitle()}</div>
        <div className="phase-subtitle">{getPhaseSubtitle()}</div>
      </div>
      
      {/* Dynamic content section */}
      <div className="content-section">
        {/* PREPARATION PHASE CONTENT */}
        {phase === 'PREPARATION' && (
          <>
            {showDealing ? (
              <div className="dealing-container">
                <div className="dealing-icon">
                  <div className="card-stack"></div>
                  <div className="card-stack"></div>
                  <div className="card-stack"></div>
                </div>
                <div className="dealing-message">Dealing Cards</div>
                <div className="dealing-status">Please wait while cards are being dealt...</div>
                <div className="progress-container">
                  <div className="progress-bar">
                    <div className="progress-fill"></div>
                  </div>
                </div>
              </div>
            ) : (
              showWeakAlert && (
                <div className="weak-hand-alert show">
                  <div className="alert-title">⚠️ Weak Hand Detected</div>
                  <div className="alert-message">
                    No piece greater than 9 points. Would you like to request a redeal?
                  </div>
                  <div className="alert-buttons">
                    <button className="alert-button primary" onClick={() => {
                      setShowMultiplier(true);
                      setShowWeakAlert(false);
                      onAcceptRedeal();
                    }}>
                      Request Redeal
                    </button>
                    <button className="alert-button secondary" onClick={() => {
                      setShowWeakAlert(false);
                      onDeclineRedeal();
                    }}>
                      Keep Hand
                    </button>
                  </div>
                </div>
              )
            )}
          </>
        )}
        
        {/* DECLARATION PHASE CONTENT */}
        {phase === 'DECLARATION' && (
          <div className="game-status-section">
            <div className="declaration-requirement">Declare your target pile count</div>
            
            <div className="players-list">
              {players.map((player) => {
                const hasDeclared = declarations.hasOwnProperty(player.name);
                const isCurrentPlayer = isMyTurnToDeclare && player.isMe;
                const status = isCurrentPlayer ? 'current-turn' : 
                              hasDeclared ? 'declared' : '';
                
                return (
                  <div key={player.name} className={`player-row ${status}`}>
                    <div className="player-avatar">{player.name.charAt(0)}</div>
                    <div className="player-info">
                      <div className="player-name">
                        {player.name}{player.isMe ? ' (You)' : ''}
                      </div>
                    </div>
                    <div className="player-status">
                      {hasDeclared ? (
                        <div className="declared-value">{declarations[player.name]}</div>
                      ) : isCurrentPlayer ? (
                        <div className="status-badge current">Your Turn</div>
                      ) : (
                        <div className="status-badge waiting">Waiting</div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
      
      {/* Hand section - always visible after dealing */}
      {(!showDealing || phase !== 'PREPARATION') && myHand.length > 0 && (
        <div className="hand-section">
          <div className="pieces-tray">
            {myHand.map((piece, index) => (
              <EnhancedGamePiece
                key={index}
                piece={piece}
                size="large"
                isSelected={selectedPieces.includes(index)}
                onClick={() => handlePieceSelect(index)}
                disabled={phase !== 'TURN' || !isMyTurn}
                animationDelay={`${index * 0.1}s`}
              />
            ))}
          </div>
        </div>
      )}
      
      {/* Declaration Popup - shown when it's player's turn */}
      {phase === 'DECLARATION' && isMyTurnToDeclare && validOptions.length > 0 && (
      <div className="declaration-popup">
        <div className="popup-content">
          <div className="popup-title">Make Your Declaration</div>
          <div className="popup-subtitle">How many piles do you plan to win this round?</div>
          
          <div className="declaration-options">
            {validOptions.map(value => (
              <div
                key={value}
                className={`declaration-option ${selectedDeclaration === value ? 'selected' : ''}`}
                onClick={() => setSelectedDeclaration(value)}
              >
                {value}
              </div>
            ))}
          </div>
          
          <button 
            className="confirm-button"
            onClick={() => {
              if (selectedDeclaration !== null) {
                onDeclare(selectedDeclaration);
                setSelectedDeclaration(null);
              }
            }}
            disabled={selectedDeclaration === null}
          >
            Confirm Declaration
          </button>
        </div>
        </div>
      )}
    </div>
  );
}

UnifiedGameUI.propTypes = {
  phase: PropTypes.oneOf(['PREPARATION', 'DECLARATION', 'TURN', 'SCORING']),
  myHand: PropTypes.array,
  players: PropTypes.array,
  roundNumber: PropTypes.number,
  weakHands: PropTypes.array,
  redealMultiplier: PropTypes.number,
  isMyHandWeak: PropTypes.bool,
  isMyDecision: PropTypes.bool,
  declarations: PropTypes.object,
  currentTotal: PropTypes.number,
  isMyTurnToDeclare: PropTypes.bool,
  validOptions: PropTypes.array,
  isLastPlayer: PropTypes.bool,
  currentTurnPlays: PropTypes.array,
  requiredPieceCount: PropTypes.number,
  turnNumber: PropTypes.number,
  isMyTurn: PropTypes.bool,
  canPlayAnyCount: PropTypes.bool,
  currentPlayer: PropTypes.string,
  onAcceptRedeal: PropTypes.func,
  onDeclineRedeal: PropTypes.func,
  onDeclare: PropTypes.func,
  onPlayPieces: PropTypes.func
};

export default UnifiedGameUI;