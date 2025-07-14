// frontend/src/components/LoadingOverlay.jsx

import React from 'react';

const LoadingOverlay = ({
  isVisible = false,
  message = 'Loading...',
  subtitle = '',
  showSpinner = true,
  overlay = true,
  className = '',
}) => {
  if (!isVisible) return null;

  const overlayClasses = overlay
    ? 'fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-50'
    : 'absolute inset-0 bg-white bg-opacity-90 z-10';

  return (
    <div
      className={`${overlayClasses} flex items-center justify-center ${className} animate-in fade-in duration-300`}
    >
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-sm w-full mx-4 transform-gpu animate-in zoom-in-95 duration-300 delay-100">
        <div className="flex flex-col items-center space-y-4">
          {/* Enhanced Spinner */}
          {showSpinner && (
            <div className="relative">
              <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
              <div className="absolute inset-0 w-12 h-12 border-4 border-transparent border-l-blue-400 rounded-full animate-spin animate-reverse"></div>
            </div>
          )}

          {/* Message */}
          <div className="text-center animate-in slide-in-from-bottom-4 duration-500 delay-200">
            <h3 className="text-lg font-medium text-gray-900 mb-1">
              {message}
            </h3>

            {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingOverlay;
