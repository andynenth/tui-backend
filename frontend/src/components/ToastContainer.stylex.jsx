// frontend/src/components/ToastContainer.stylex.jsx

import React from 'react';
import { createPortal } from 'react-dom';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { spacing, motion } from '../design-system/tokens.stylex';
import ToastNotification from './ToastNotification.stylex';
import useToastNotifications from '../hooks/useToastNotifications';

// Animations
const slideIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateX(100%)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateX(0)',
  },
});

const slideInLeft = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateX(-100%)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateX(0)',
  },
});

// ToastContainer styles
const styles = stylex.create({
  container: {
    position: 'fixed',
    zIndex: 9999,
    pointerEvents: 'none',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    padding: '1rem',
  },
  
  topLeft: {
    top: 0,
    left: 0,
    alignItems: 'flex-start',
  },
  
  topRight: {
    top: 0,
    right: 0,
    alignItems: 'flex-end',
  },
  
  bottomLeft: {
    bottom: 0,
    left: 0,
    alignItems: 'flex-start',
  },
  
  bottomRight: {
    bottom: 0,
    right: 0,
    alignItems: 'flex-end',
  },
  
  wrapper: {
    pointerEvents: 'auto',
  },
  
  wrapperRight: {
    animation: `${slideIn} '300ms' 'cubic-bezier(0, 0, 0.2, 1)' both`,
  },
  
  wrapperLeft: {
    animation: `${slideInLeft} '300ms' 'cubic-bezier(0, 0, 0.2, 1)' both`,
  },
});

/**
 * ToastContainer Component
 *
 * Container for displaying toast notifications
 * Uses React Portal to render toasts at the document body level
 */
const ToastContainer = ({ position = 'top-right', maxToasts = 5, className = '' }) => {
  const { toasts, removeToast } = useToastNotifications();

  // Get visible notifications (limit by maxToasts)
  const visibleNotifications = toasts.slice(-maxToasts);

  // Don't render if no notifications
  if (visibleNotifications.length === 0) return null;

  // Get position style
  const positionStyle = 
    position === 'top-left' ? styles.topLeft :
    position === 'bottom-left' ? styles.bottomLeft :
    position === 'bottom-right' ? styles.bottomRight :
    styles.topRight;

  // Get animation style based on position
  const isLeftSide = position.includes('left');
  const wrapperAnimation = isLeftSide ? styles.wrapperLeft : styles.wrapperRight;

  // Apply container styles
  const containerProps = stylex.props(styles.container, positionStyle);
  
  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;

  return createPortal(
    <div {...combinedContainerProps}>
      {visibleNotifications.map((notification, index) => (
        <div
          key={notification.id}
          {...stylex.props(styles.wrapper, wrapperAnimation)}
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
  className: PropTypes.string,
};

export default ToastContainer;