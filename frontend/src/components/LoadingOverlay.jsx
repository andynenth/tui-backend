// frontend/src/components/LoadingOverlay.jsx

import React from 'react';

const LoadingOverlay = ({
  isVisible = false,
  message = 'Loading...',
  subtitle = '',
  showSpinner = true,
  overlay = true,
  className = ''
}) => {
  if (!isVisible) return null;

  const overlayClasses = overlay 
    ? 'fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-50'
    : 'absolute inset-0 bg-white bg-opacity-90 z-10';

  return (
    <div className={`${overlayClasses} flex items-center justify-center ${className}`}>
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-sm w-full mx-4">
        <div className="flex flex-col items-center space-y-4">
          {/* Spinner */}
          {showSpinner && (
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
          )}

          {/* Message */}
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900">
              {message}
            </h3>
            
            {subtitle && (
              <p className="mt-2 text-sm text-gray-500">
                {subtitle}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingOverlay;