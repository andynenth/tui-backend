import React from 'react';
import PropTypes from 'prop-types';
import { FooterTimer } from '../shared';

/**
 * RoundStartContent Component
 * 
 * Displays round start information:
 * - Large round number
 * - Starter name with reason
 * - 5-second countdown timer
 */
const RoundStartContent = ({ roundNumber, starter, starterReason }) => {
  
  // Get human-readable reason text
  const getReasonText = () => {
    switch(starterReason) {
      case 'has_general_red':
        return 'has the General Red piece';
      case 'won_last_turn':
        return 'won the last turn';
      case 'accepted_redeal':
        return 'accepted the redeal';
      default:
        return 'starts this round';
    }
  };
  
  return (
    <div className="rs-content">
      {/* Round number display */}
      <div className="rs-round-section">
        <div className="rs-round-label">Round</div>
        <div className="rs-round-number">{roundNumber}</div>
      </div>
      
      {/* Starter information */}
      <div className="rs-starter-section">
        <div className="rs-starter-name">{starter}</div>
        <div className="rs-starter-reason">{getReasonText()}</div>
      </div>
      
      {/* Auto-advance timer */}
      <div className="rs-timer-section">
        <FooterTimer
          duration={5}
          prefix="Starting in"
          onComplete={() => {}}
          variant="inline"
        />
      </div>
    </div>
  );
};

RoundStartContent.propTypes = {
  roundNumber: PropTypes.number.isRequired,
  starter: PropTypes.string.isRequired,
  starterReason: PropTypes.string.isRequired
};

export default RoundStartContent;