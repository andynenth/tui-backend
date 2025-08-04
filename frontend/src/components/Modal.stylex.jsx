import React, { useEffect, useRef } from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, shadows, layout } from '../design-system/tokens.stylex';
import { animations } from '../design-system/utils.stylex';
import Button from './Button.stylex';

// Modal styles
const styles = stylex.create({
  overlay: {
    position: 'fixed',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    zIndex: 50,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    backdropFilter: 'blur(4px)',
    animation: `${animations.fadeIn} '300ms' 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  modal: {
    position: 'relative',
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    maxHeight: '90vh',
    width: '100%',
    overflow: 'hidden',
    animation: `${animations.scaleIn} '300ms' 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  // Size variants
  sm: {
    maxWidth: '28rem', // max-w-md
  },
  
  md: {
    maxWidth: '32rem', // max-w-lg
  },
  
  lg: {
    maxWidth: '42rem', // max-w-2xl
  },
  
  xl: {
    maxWidth: '56rem', // max-w-4xl
  },
  
  full: {
    maxWidth: '100%',
    margin: '1.5rem',
  },
  
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1.5rem',
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    borderBottomColor: '#e9ecef',
  },
  
  title: {
    fontSize: '1.125rem',
    fontWeight: '600',
    color: '#343a40',
    margin: 0,
  },
  
  closeButton: {
    padding: '0.25rem',
    borderRadius: '9999px',
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1.25rem',
    color: '#adb5bd',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    lineHeight: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '32px',
    height: '32px',
    
    ':hover': {
      backgroundColor: '#f1f3f5',
      color: '#495057',
    },
  },
  
  content: {
    padding: '1.5rem',
    overflowY: 'auto',
    maxHeight: 'calc(90vh - 64px)',
  },
});

const Modal = ({
  isOpen = false,
  onClose,
  title = ',
  children,
  size = 'md',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  className = '',
}) => {
  const modalRef = useRef(null);
  const overlayRef = useRef(null);

  // Handle escape key
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, closeOnEscape, onClose]);

  // Focus management
  useEffect(() => {
    if (isOpen && modalRef.current) {
      modalRef.current.focus();
    }
  }, [isOpen]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const handleOverlayClick = (event) => {
    if (closeOnOverlayClick && event.target === overlayRef.current) {
      onClose?.();
    }
  };

  if (!isOpen) {
    return null;
  }

  // Apply modal styles
  const modalProps = stylex.props(
    styles.modal,
    styles[size]
  );

  // During migration, allow combining with existing CSS classes
  const combinedModalProps = className 
    ? { ...modalProps, className: `${modalProps.className || ''} ${className}`.trim() }
    : modalProps;

  return (
    <div
      ref={overlayRef}
      {...stylex.props(styles.overlay)}
      onClick={handleOverlayClick}
    >
      <div
        ref={modalRef}
        {...combinedModalProps}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div {...stylex.props(styles.header)}>
            {title && (
              <h2
                id="modal-title"
                {...stylex.props(styles.title)}
              >
                {title}
              </h2>
            )}

            {showCloseButton && (
              <button
                {...stylex.props(styles.closeButton)}
                onClick={onClose}
                aria-label="Close modal"
              >
                ×
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div {...stylex.props(styles.content)}>
          {children}
        </div>
      </div>
    </div>
  );
};

export default Modal;