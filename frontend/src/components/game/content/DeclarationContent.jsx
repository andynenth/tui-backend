import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { PlayerAvatar, PieceTray } from '../shared';

/**
 * DeclarationContent Component
 *
 * Displays the declaration phase with:
 * - Players list showing declaration status
 * - Declaration panel with number selection (0-8)
 * - Validation for total sum and consecutive zeros
 * - Player's hand display at bottom
 */
const DeclarationContent = ({
  myHand = [],
  players = [],
  currentPlayer = '',
  myName = '',
  declarations = {},
  totalDeclared = 0,
  consecutiveZeros = 0,
  redealMultiplier = 1,
  onDeclare,
}) => {
  const [selectedValue, setSelectedValue] = useState(null);
  const [showPanel, setShowPanel] = useState(false);

  // Check if it's my turn
  const isMyTurn = currentPlayer === myName;

  // Show panel when it's my turn
  useEffect(() => {
    if (isMyTurn) {
      setShowPanel(true);
    } else {
      setShowPanel(false);
      setSelectedValue(null);
    }
  }, [isMyTurn]);

  // Calculate restrictions
  const getRestrictions = () => {
    const restrictions = {
      message: 'Declare your target pile count',
      disabledValues: [],
    };

    // Check if player is last to declare
    const declaredCount = Object.keys(declarations).length;
    const isLastPlayer = declaredCount === players.length - 1;

    if (isLastPlayer) {
      // Total cannot equal 8
      const remainingForEight = 8 - totalDeclared;
      if (remainingForEight >= 0 && remainingForEight <= 8) {
        restrictions.disabledValues.push(remainingForEight);
        restrictions.message = 'The total number cannot be 8';
      }
    }

    // Check consecutive zeros (player declared 0 twice in a row)
    if (consecutiveZeros >= 2) {
      restrictions.disabledValues.push(0);
      restrictions.message = 'No third consecutive 0';
    }

    return restrictions;
  };

  const restrictions = getRestrictions();

  // Get player status
  const getPlayerStatus = (player) => {
    // Players are now always objects
    const playerName = player.name;

    if (declarations[playerName] !== undefined) {
      return {
        type: 'declared',
        value: declarations[playerName],
      };
    } else if (playerName === currentPlayer) {
      return {
        type: 'current',
        text: 'Declaring',
      };
    } else {
      // Check if this player will declare after current player
      const currentIndex = players.findIndex((p) => p.name === currentPlayer);
      const playerIndex = players.findIndex((p) => p.name === playerName);

      if (
        currentIndex !== -1 &&
        playerIndex !== -1 &&
        playerIndex === currentIndex + 1
      ) {
        return {
          type: 'pending',
          text: 'Next',
        };
      }

      return {
        type: 'waiting',
        text: 'Waiting',
      };
    }
  };

  // Handle declaration selection
  const handleSelectValue = (value) => {
    if (!restrictions.disabledValues.includes(value)) {
      setSelectedValue(value);
    }
  };

  // Handle confirm
  const handleConfirm = () => {
    if (selectedValue !== null && onDeclare) {
      onDeclare(selectedValue);
    }
  };

  // Handle clear
  const handleClear = () => {
    setSelectedValue(null);
  };

  return (
    <>
      {/* Game status section */}
      <div className="dec-game-status-section">
        {/* Declaration requirement - removed */}

        {/* Players list */}
        <div className="dec-players-list">
          {players.map((player) => {
            // Debug logging to understand data structure
            console.log(
              'Declaration player data:',
              player,
              'Type:',
              typeof player
            );

            // Players should now always be objects with is_bot property
            const playerName = player.name;
            const displayName = playerName;

            const status = getPlayerStatus(player);
            const isCurrentTurn = playerName === currentPlayer;
            const isDeclared = status.type === 'declared';

            return (
              <div
                key={playerName}
                className={`dec-player-row ${isCurrentTurn ? 'current-turn' : ''} ${isDeclared ? 'declared' : ''}`}
              >
                <PlayerAvatar
                  name={displayName}
                  isBot={player.is_bot}
                  isThinking={isCurrentTurn && player.is_bot}
                  size="large"
                />
                <div className="dec-player-info">
                  <div className="dec-player-name">
                    {displayName}
                    {playerName === myName ? ' (You)' : ''}
                  </div>
                </div>
                <div className="dec-player-status">
                  {status.type === 'declared' ? (
                    <div className="dec-declared-value">{status.value}</div>
                  ) : (
                    <div className={`dec-status-badge ${status.type}`}>
                      {status.text}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Declaration panel - sliding tray */}
      <div className={`dec-panel ${showPanel ? 'show' : ''}`}>
        <div className="dec-options">
          {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((value) => {
            const isDisabled = restrictions.disabledValues.includes(value);
            const isSelected = selectedValue === value;

            return (
              <button
                key={value}
                className={`dec-option ${isSelected ? 'selected' : ''} ${isDisabled ? 'disabled' : ''}`}
                onClick={() => handleSelectValue(value)}
                disabled={isDisabled}
              >
                {value}
              </button>
            );
          })}
        </div>

        <div className="dec-actions">
          <button
            className="dec-action-btn"
            onClick={handleConfirm}
            disabled={selectedValue === null}
          >
            Confirm
          </button>
          <button className="dec-action-btn secondary" onClick={handleClear}>
            Clear
          </button>
        </div>
      </div>

      {/* Hand section - always visible at bottom */}
      <PieceTray pieces={myHand} showValues />
    </>
  );
};

DeclarationContent.propTypes = {
  myHand: PropTypes.array,
  players: PropTypes.array,
  currentPlayer: PropTypes.string,
  myName: PropTypes.string,
  declarations: PropTypes.object,
  totalDeclared: PropTypes.number,
  consecutiveZeros: PropTypes.number,
  redealMultiplier: PropTypes.number,
  onDeclare: PropTypes.func,
};

export default DeclarationContent;
