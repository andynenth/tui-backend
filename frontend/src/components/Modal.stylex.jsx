// Modal component with StyleX
import React, { useEffect, useRef } from 'react';
import * as stylex from '@stylexjs/stylex';
import Button from './Button.stylex';
import { colors, spacing, shadows, layout, motion, typography } from '../design-system/tokens.stylex';

// Animation keyframes
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
  },
  '100%': {
    opacity: 1,
  },
});

const slideUp = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(20px) scale(0.95)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0) scale(1)',
  },
});

// Modal styles
const styles = stylex.create({
  overlay: {
    position: 'fixed',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    zIndex: layout.zModal,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    backdropFilter: 'blur(4px)',
    animation: `${fadeIn} ${motion.durationFast} ${motion.easeOut}`,
    padding: spacing.md,
  },
  
  modal: {
    position: 'relative',
    backgroundColor: colors.textLight,
    borderRadius: layout.radiusLg,
    boxShadow: shadows.xl,
    maxHeight: '90vh',
    width: '100%',
    overflow: 'hidden',
    animation: `${slideUp} ${motion.durationNormal} ${motion.easeOut}`,
    display: 'flex',
    flexDirection: 'column',
  },
  
  // Size variants
  sizeSmall: {
    maxWidth: '28rem', // 448px
  },
  
  sizeMedium: {
    maxWidth: '32rem', // 512px
  },
  
  sizeLarge: {
    maxWidth: '42rem', // 672px
  },
  
  sizeXLarge: {
    maxWidth: '56rem', // 896px
  },
  
  sizeFull: {
    maxWidth: 'calc(100% - 2rem)',
    margin: spacing.md,
  },
  
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.md,
    borderBottom: `1px solid ${colors.gray200}`,
    flexShrink: 0,
  },
  
  title: {
    fontSize: typography.textLg,
    fontWeight: typography.weightSemibold,
    color: colors.gray900,
    margin: 0,
  },
  
  closeButton: {
    padding: spacing.xs,
    marginLeft: spacing.md,
    background: 'transparent',
    border: 'none',
    borderRadius: layout.radiusFull,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '28px',
    height: '28px',
    transition: motion.transitionFast,
    color: colors.gray500,
    fontSize: '24px',
    lineHeight: '1',
    
    ':hover': {
      backgroundColor: colors.gray100,
      color: colors.gray700,
    },
    
    ':focus-visible': {
      outline: `2px solid ${colors.primary}`,
      outlineOffset: '2px',
    },
  },
  
  content: {
    padding: spacing.md,
    overflowY: 'auto',
    flexGrow: 1,
    // Custom scrollbar styling
    scrollbarWidth: 'thin',
    scrollbarColor: `${colors.gray300} transparent`,
    
    '::-webkit-scrollbar': {
      width: '8px',
    },
    
    '::-webkit-scrollbar-track': {
      background: 'transparent',
    },
    
    '::-webkit-scrollbar-thumb': {
      backgroundColor: colors.gray300,
      borderRadius: layout.radiusFull,
      
      ':hover': {
        backgroundColor: colors.gray400,
      },
    },
  },
  
  // For empty header when only close button is needed
  emptyHeader: {
    justifyContent: 'flex-end',
  },
});

const Modal = ({
  isOpen = false,
  onClose,
  title = '',
  children,
  size = 'medium',
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

  // Map size prop to style
  const sizeStyle = {
    sm: styles.sizeSmall,
    small: styles.sizeSmall,
    md: styles.sizeMedium,
    medium: styles.sizeMedium,
    lg: styles.sizeLarge,
    large: styles.sizeLarge,
    xl: styles.sizeXLarge,
    xlarge: styles.sizeXLarge,
    full: styles.sizeFull,
  }[size] || styles.sizeMedium;

  if (!isOpen) {
    return null;
  }

  return (
    <div
      ref={overlayRef}
      {...stylex.props(styles.overlay)}
      onClick={handleOverlayClick}
    >
      <div
        ref={modalRef}
        {...stylex.props(
          styles.modal,
          sizeStyle,
          // Allow className for migration period
          className && { className }
        )}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div {...stylex.props(
            styles.header,
            !title && showCloseButton && styles.emptyHeader
          )}>
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