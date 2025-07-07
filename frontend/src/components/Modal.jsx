// frontend/src/components/Modal.jsx

import React, { useEffect, useRef } from 'react';
import Button from './Button';

const Modal = ({
  isOpen = false,
  onClose,
  title = '',
  children,
  size = 'md',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  className = ''
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

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4'
  };

  if (!isOpen) {
    return null;
  }


  return (
    <div
      ref={overlayRef}
      className="modal-overlay fixed inset-0 z-50 flex items-center justify-center"
      onClick={handleOverlayClick}
    >
      <div
        ref={modalRef}
        className={`
          relative bg-white rounded-lg shadow-xl max-h-[90vh] w-full overflow-hidden
          ${sizeClasses[size]} ${className}
        `}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            {title && (
              <h2 id="modal-title" className="text-lg font-semibold text-gray-900">
                {title}
              </h2>
            )}
            
            {showCloseButton && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="p-1 hover:bg-gray-100 rounded-full"
                aria-label="Close modal"
              >
                <span className="text-xl">×</span>
              </Button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-theme(spacing.16))]">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Modal;