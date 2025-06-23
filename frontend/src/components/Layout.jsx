// frontend/src/components/Layout.jsx

import React from 'react';
import ConnectionIndicator from './ConnectionIndicator';

const Layout = ({
  children,
  title = 'Liap TUI',
  showConnection = false,
  connectionProps = {},
  showHeader = true,
  headerContent = null,
  className = ''
}) => {
  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      {/* Header */}
      {showHeader && (
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              {/* Title/Logo */}
              <div className="flex items-center space-x-4">
                <h1 className="text-xl font-bold text-gray-900">
                  {title}
                </h1>
              </div>

              {/* Header content */}
              <div className="flex items-center space-x-4">
                {headerContent}
                
                {/* Connection indicator */}
                {showConnection && (
                  <ConnectionIndicator
                    showDetails={true}
                    {...connectionProps}
                  />
                )}
              </div>
            </div>
          </div>
        </header>
      )}

      {/* Main content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
};

export default Layout;