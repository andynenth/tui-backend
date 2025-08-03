// frontend/src/components/ToastNotification.jsx

import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import '../styles/toast-notifications.css';

const ToastNotification = ({
  id,
  type = 'info',
  title,
  message,
  duration = 5000,
  onClose,
  _position = 'top-right',
}) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose(id);
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case 'disconnect':
        return '🔌';
      case 'reconnect':
        return '🔗';
      case 'ai-activated':
        return '🤖';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'success':
        return '✅';
      default:
        return 'ℹ️';
    }
  };

  const getTypeClass = () => {
    switch (type) {
      case 'disconnect':
        return 'toast--disconnect';
      case 'reconnect':
        return 'toast--reconnect';
      case 'ai-activated':
        return 'toast--ai';
      case 'error':
        return 'toast--error';
      case 'warning':
        return 'toast--warning';
      case 'success':
        return 'toast--success';
      default:
        return 'toast--info';
    }
  };

  return (
    <div className={`toast-notification ${getTypeClass()}`}>
      <div className="toast-icon">{getIcon()}</div>
      <div className="toast-content">
        {title && <div className="toast-title">{title}</div>}
        <div className="toast-message">{message}</div>
      </div>
      <button
        className="toast-close"
        onClick={() => onClose(id)}
        aria-label="Close notification"
      >
        ×
      </button>
      {duration > 0 && (
        <div
          className="toast-progress"
          style={{ animationDuration: `${duration}ms` }}
        />
      )}
    </div>
  );
};

ToastNotification.propTypes = {
  id: PropTypes.string.isRequired,
  type: PropTypes.oneOf([
    'info',
    'success',
    'warning',
    'error',
    'disconnect',
    'reconnect',
    'ai-activated',
  ]),
  title: PropTypes.string,
  message: PropTypes.string.isRequired,
  duration: PropTypes.number,
  onClose: PropTypes.func.isRequired,
  position: PropTypes.oneOf([
    'top-left',
    'top-right',
    'bottom-left',
    'bottom-right',
  ]),
};

export default ToastNotification;
