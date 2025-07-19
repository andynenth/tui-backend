// frontend/src/components/ToastContainer.jsx

import React from 'react';
import { createPortal } from 'react-dom';
import PropTypes from 'prop-types';
import ToastNotification from './ToastNotification';
import useToastNotifications from '../hooks/useToastNotifications';
import '../styles/toast-notifications.css';

const ToastContainer = ({ position = 'top-right', maxToasts = 5 }) => {
  const { toasts, removeToast } = useToastNotifications();

  // Get visible notifications (limit by maxToasts)
  const visibleNotifications = toasts.slice(-maxToasts);

  // Don't render if no notifications
  if (visibleNotifications.length === 0) return null;

  return createPortal(
    <div className={`toast-container toast-container--${position}`}>
      {visibleNotifications.map((notification, index) => (
        <div
          key={notification.id}
          className="toast-wrapper"
          style={{
            animationDelay: `${index * 50}ms`,
          }}
        >
          <ToastNotification {...notification} onClose={removeToast} />
        </div>
      ))}
    </div>,
    document.body
  );
};

ToastContainer.propTypes = {
  position: PropTypes.oneOf([
    'top-left',
    'top-right',
    'bottom-left',
    'bottom-right',
  ]),
  maxToasts: PropTypes.number,
};

export default ToastContainer;
