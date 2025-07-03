/**
 * 🎯 **ActionFeedback Component** - Phase 5.3 Clean State Flow UI
 * 
 * Provides user feedback for action states:
 * ✅ Loading indicators for pending actions
 * ✅ Success/failure notifications
 * ✅ Retry buttons for failed actions
 * ✅ Action progress tracking
 */

import React, { useState, useEffect } from 'react';
import { useActionManager } from '../../hooks/useActionManager';

const ActionFeedback = ({ 
  className = '',
  showPendingActions = true,
  showNotifications = true,
  autoHideNotifications = true,
  notificationDuration = 3000 
}) => {
  const { 
    pendingActions, 
    lastActionResult, 
    retryAction, 
    cancelAction 
  } = useActionManager();
  
  const [notifications, setNotifications] = useState([]);
  const [retryingActions, setRetryingActions] = useState(new Set());

  // Handle new action results
  useEffect(() => {
    if (!lastActionResult || !showNotifications) return;

    const notification = {
      id: `${lastActionResult.actionId}-${Date.now()}`,
      type: lastActionResult.success ? 'success' : 'error',
      message: lastActionResult.success 
        ? 'Action completed successfully'
        : `Action failed: ${lastActionResult.error}`,
      actionId: lastActionResult.actionId,
      timestamp: Date.now()
    };

    setNotifications(prev => [...prev, notification]);

    // Auto-hide notification
    if (autoHideNotifications) {
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== notification.id));
      }, notificationDuration);
    }
  }, [lastActionResult, showNotifications, autoHideNotifications, notificationDuration]);

  // Handle retry action
  const handleRetry = async (actionId) => {
    setRetryingActions(prev => new Set(prev).add(actionId));
    
    try {
      await retryAction(actionId);
    } finally {
      setRetryingActions(prev => {
        const newSet = new Set(prev);
        newSet.delete(actionId);
        return newSet;
      });
    }
  };

  // Handle cancel action
  const handleCancel = (actionId) => {
    cancelAction(actionId);
  };

  // Handle dismiss notification
  const handleDismissNotification = (notificationId) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId));
  };

  // Get action type display name
  const getActionDisplayName = (actionType) => {
    const names = {
      'play_pieces': 'Playing Cards',
      'declare': 'Making Declaration',
      'redeal_decision': 'Redeal Decision',
      'request_redeal': 'Requesting Redeal',
      'join_room': 'Joining Room',
      'leave_room': 'Leaving Room'
    };
    return names[actionType] || actionType;
  };

  // Get action status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'confirmed': return '✅';
      case 'failed': return '❌';
      case 'timeout': return '⏰';
      default: return '❓';
    }
  };

  return (
    <div className={`action-feedback ${className}`}>
      {/* Pending Actions */}
      {showPendingActions && pendingActions.length > 0 && (
        <div className="pending-actions">
          <h4>⏳ Actions in Progress</h4>
          {pendingActions.map(action => (
            <div key={action.id} className="pending-action">
              <div className="action-info">
                <span className="action-name">
                  {getActionDisplayName(action.action.type)}
                </span>
                <span className="action-status">
                  {getStatusIcon(action.status)} {action.status}
                </span>
                {action.retryCount > 0 && (
                  <span className="retry-count">
                    (Retry {action.retryCount})
                  </span>
                )}
              </div>
              
              <div className="action-controls">
                {action.status === 'failed' && (
                  <button
                    onClick={() => handleRetry(action.id)}
                    disabled={retryingActions.has(action.id)}
                    className="retry-button"
                  >
                    {retryingActions.has(action.id) ? '🔄 Retrying...' : '🔄 Retry'}
                  </button>
                )}
                
                {action.status === 'pending' && (
                  <button
                    onClick={() => handleCancel(action.id)}
                    className="cancel-button"
                  >
                    ❌ Cancel
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Notifications */}
      {showNotifications && notifications.length > 0 && (
        <div className="action-notifications">
          {notifications.map(notification => (
            <div 
              key={notification.id} 
              className={`notification ${notification.type}`}
            >
              <div className="notification-content">
                <span className="notification-icon">
                  {notification.type === 'success' ? '✅' : '❌'}
                </span>
                <span className="notification-message">
                  {notification.message}
                </span>
              </div>
              
              <button
                onClick={() => handleDismissNotification(notification.id)}
                className="dismiss-button"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      <style jsx>{`
        .action-feedback {
          position: fixed;
          top: 20px;
          right: 20px;
          z-index: 1000;
          max-width: 400px;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .pending-actions {
          background: rgba(255, 255, 255, 0.95);
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 16px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .pending-actions h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
          color: #333;
        }

        .pending-action {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #f0f0f0;
        }

        .pending-action:last-child {
          border-bottom: none;
        }

        .action-info {
          flex: 1;
        }

        .action-name {
          font-weight: 500;
          color: #333;
          display: block;
          font-size: 13px;
        }

        .action-status {
          font-size: 12px;
          color: #666;
          margin-left: 8px;
        }

        .retry-count {
          font-size: 11px;
          color: #ff6b35;
          margin-left: 4px;
        }

        .action-controls {
          display: flex;
          gap: 8px;
        }

        .retry-button, .cancel-button {
          padding: 4px 8px;
          border: none;
          border-radius: 4px;
          font-size: 11px;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .retry-button {
          background: #4CAF50;
          color: white;
        }

        .retry-button:hover:not(:disabled) {
          background: #45a049;
        }

        .retry-button:disabled {
          background: #cccccc;
          cursor: not-allowed;
        }

        .cancel-button {
          background: #f44336;
          color: white;
        }

        .cancel-button:hover {
          background: #da190b;
        }

        .action-notifications {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .notification {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-radius: 6px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          animation: slideIn 0.3s ease-out;
        }

        .notification.success {
          background: #d4edda;
          border: 1px solid #c3e6cb;
          color: #155724;
        }

        .notification.error {
          background: #f8d7da;
          border: 1px solid #f5c6cb;
          color: #721c24;
        }

        .notification-content {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
        }

        .notification-icon {
          font-size: 16px;
        }

        .notification-message {
          font-size: 13px;
          font-weight: 500;
        }

        .dismiss-button {
          background: none;
          border: none;
          color: currentColor;
          cursor: pointer;
          font-size: 14px;
          padding: 4px;
          opacity: 0.7;
          transition: opacity 0.2s;
        }

        .dismiss-button:hover {
          opacity: 1;
        }

        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        @media (max-width: 768px) {
          .action-feedback {
            top: 10px;
            right: 10px;
            left: 10px;
            max-width: none;
          }
        }
      `}</style>
    </div>
  );
};

export default ActionFeedback;