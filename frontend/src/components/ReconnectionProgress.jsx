// frontend/src/components/ReconnectionProgress.jsx

import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * ReconnectionProgress Component
 *
 * Shows a progress bar and status during reconnection attempts
 * Includes smooth animations and success/failure states
 */
const ReconnectionProgress = ({
  isReconnecting,
  attemptNumber = 1,
  maxAttempts = 5,
  onCancel,
  className = '',
}) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle'); // idle, connecting, success, failed
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (isReconnecting) {
      setStatus('connecting');
      setProgress(0);
      setShowSuccess(false);

      // Simulate progress
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      return () => clearInterval(interval);
    } else if (status === 'connecting') {
      // Connection completed
      setProgress(100);
      setStatus('success');
      setShowSuccess(true);

      // Hide after animation
      const timer = setTimeout(() => {
        setStatus('idle');
        setShowSuccess(false);
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [isReconnecting, status]);

  if (status === 'idle' && !showSuccess) {
    return null;
  }

  const progressPercentage = Math.min(progress, 100);
  const attemptPercentage = (attemptNumber / maxAttempts) * 100;

  return (
    <div
      className={`fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 min-w-[300px] transition-all duration-300 ${
        showSuccess ? 'scale-105' : 'scale-100'
      } ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800">
          {status === 'success' ? 'Reconnected!' : 'Reconnecting...'}
        </h3>
        {status === 'connecting' && onCancel && (
          <button
            onClick={onCancel}
            className="text-gray-500 hover:text-gray-700 transition-colors"
            aria-label="Cancel reconnection"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Progress Bar */}
      <div className="relative mb-2">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ease-out ${
              status === 'success' ? 'bg-green-500' : 'bg-blue-500'
            }`}
            style={{ width: `${progressPercentage}%` }}
          />
        </div>

        {/* Attempt indicator */}
        {status === 'connecting' && maxAttempts > 1 && (
          <div className="absolute top-0 left-0 h-full pointer-events-none">
            <div
              className="h-full border-r-2 border-gray-400 border-dashed opacity-50"
              style={{ width: `${attemptPercentage}%` }}
            />
          </div>
        )}
      </div>

      {/* Status Text */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-600">
          {status === 'success' ? (
            <span className="text-green-600 font-medium">
              Connection restored
            </span>
          ) : (
            <>
              Attempt {attemptNumber} of {maxAttempts}
            </>
          )}
        </span>

        {/* Success Animation */}
        {showSuccess && (
          <div className="flex items-center text-green-600 animate-fadeIn">
            <svg
              className="w-5 h-5 mr-1"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span className="font-medium">Success!</span>
          </div>
        )}
      </div>

      {/* Additional Info */}
      {status === 'connecting' && (
        <div className="mt-3 text-xs text-gray-500">
          <div className="animate-pulse">Establishing secure connection...</div>
        </div>
      )}
    </div>
  );
};

ReconnectionProgress.propTypes = {
  isReconnecting: PropTypes.bool.isRequired,
  attemptNumber: PropTypes.number,
  maxAttempts: PropTypes.number,
  onCancel: PropTypes.func,
  className: PropTypes.string,
};

export default ReconnectionProgress;
