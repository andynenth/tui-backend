/**
 * 🎮 **WaitingUI Component** - Pure Waiting State Interface
 *
 * Phase 2, Task 2.2: Pure UI Components
 *
 * Features:
 * ✅ Pure functional component (props in, JSX out)
 * ✅ No hooks except local UI state
 * ✅ Comprehensive prop interfaces
 * ✅ Accessible and semantic HTML
 * ✅ Tailwind CSS styling
 */

import React from 'react';
import PropTypes from 'prop-types';
import LoadingOverlay from '../LoadingOverlay';
import ConnectionIndicator from '../ConnectionIndicator';

/**
 * Pure UI component for waiting states
 */
export function WaitingUI({
  // Connection props
  isConnected,
  isConnecting,
  isReconnecting,
  connectionError,

  // Status props
  message = 'Waiting...',
  phase = 'waiting',

  // Action props
  onRetry,
  onCancel,
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center p-4">
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 max-w-md w-full text-center">
        {/* Connection Status */}
        <div className="mb-6">
          <ConnectionIndicator
            isConnected={isConnected}
            isConnecting={isConnecting}
            isReconnecting={isReconnecting}
            error={connectionError}
          />
        </div>

        {/* Main Status */}
        <div className="mb-8">
          <div className="text-6xl mb-4">{getPhaseIcon(phase)}</div>

          <h1 className="text-2xl font-bold text-white mb-2">
            {getPhaseTitle(phase)}
          </h1>

          <p className="text-blue-200 text-lg">{message}</p>
        </div>

        {/* Loading Animation */}
        {(isConnecting || isReconnecting) && (
          <div className="mb-6">
            <LoadingOverlay
              message={isReconnecting ? 'Reconnecting...' : 'Connecting...'}
            />
          </div>
        )}

        {/* Error State */}
        {connectionError && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
            <div className="text-red-200 text-sm mb-3">
              Connection Error: {connectionError}
            </div>

            {onRetry && (
              <button
                onClick={onRetry}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                aria-label="Retry connection"
              >
                Retry Connection
              </button>
            )}
          </div>
        )}

        {/* Waiting Animation */}
        {!connectionError && !isConnecting && !isReconnecting && (
          <div className="mb-6">
            <div className="waiting-dots">
              {[0, 1, 2].map((i) => (
                <div key={i} className="waiting-dot" />
              ))}
            </div>
          </div>
        )}

        {/* Phase Information */}
        <div className="text-blue-300 text-sm space-y-1">
          <div>
            Phase: <span className="font-medium text-blue-200">{phase}</span>
          </div>
          <div>
            Status:{' '}
            <span className="font-medium text-blue-200">
              {getConnectionStatus(
                isConnected,
                isConnecting,
                isReconnecting,
                connectionError
              )}
            </span>
          </div>
        </div>

        {/* Cancel Button */}
        {onCancel && (
          <div className="mt-6">
            <button
              onClick={onCancel}
              className="text-gray-300 hover:text-white text-sm underline transition-colors"
              aria-label="Cancel and return"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper functions
function getPhaseIcon(phase) {
  switch (phase) {
    case 'waiting':
      return '⏳';
    case 'preparation':
      return '🃏';
    case 'declaration':
      return '🎯';
    case 'turn':
      return '🎮';
    case 'scoring':
      return '🏆';
    default:
      return '⏳';
  }
}

function getPhaseTitle(phase) {
  switch (phase) {
    case 'waiting':
      return 'Waiting for Game';
    case 'preparation':
      return 'Preparing Cards';
    case 'declaration':
      return 'Making Declarations';
    case 'turn':
      return 'Playing Turn';
    case 'scoring':
      return 'Calculating Scores';
    default:
      return 'Waiting';
  }
}

function getConnectionStatus(isConnected, isConnecting, isReconnecting, error) {
  if (error) return 'Error';
  if (isReconnecting) return 'Reconnecting';
  if (isConnecting) return 'Connecting';
  if (isConnected) return 'Connected';
  return 'Disconnected';
}

// PropTypes definition
WaitingUI.propTypes = {
  // Connection props
  isConnected: PropTypes.bool.isRequired,
  isConnecting: PropTypes.bool,
  isReconnecting: PropTypes.bool,
  connectionError: PropTypes.string,

  // Status props
  message: PropTypes.string,
  phase: PropTypes.oneOf([
    'waiting',
    'preparation',
    'declaration',
    'turn',
    'scoring',
  ]),

  // Action props
  onRetry: PropTypes.func,
  onCancel: PropTypes.func,
};

WaitingUI.defaultProps = {
  isConnecting: false,
  isReconnecting: false,
  connectionError: null,
  message: 'Waiting...',
  phase: 'waiting',
  onRetry: null,
  onCancel: null,
};

export default WaitingUI;
