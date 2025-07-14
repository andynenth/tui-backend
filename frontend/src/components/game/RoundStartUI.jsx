/**
 * 📋 **RoundStartUI Component** - Round Start Phase Interface
 *
 * Displays round information before declaration phase:
 * - Round number
 * - Starter name
 * - Reason for being starter
 *
 * Auto-transitions to Declaration after 5 seconds
 */

import React from 'react';
import PropTypes from 'prop-types';
import RoundStartContent from './content/RoundStartContent';

/**
 * Pure UI component for round start phase
 */
export function RoundStartUI({
  // Data props
  roundNumber = 1,
  starter = '',
  starterReason = 'default',
}) {
  // Pass props to content component
  return (
    <RoundStartContent
      roundNumber={roundNumber}
      starter={starter}
      starterReason={starterReason}
    />
  );
}

// PropTypes definition
RoundStartUI.propTypes = {
  roundNumber: PropTypes.number.isRequired,
  starter: PropTypes.string.isRequired,
  starterReason: PropTypes.oneOf([
    'has_general_red',
    'won_last_turn',
    'accepted_redeal',
    'default',
  ]).isRequired,
};

RoundStartUI.defaultProps = {
  roundNumber: 1,
  starter: '',
  starterReason: 'default',
};

export default RoundStartUI;
