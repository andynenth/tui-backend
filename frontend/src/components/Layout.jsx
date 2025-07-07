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
    <div className={`${className}`}>
      {/* Header */}
      {showHeader && (
        <header>
          <div>
            <div>
              {/* Title/Logo */}
              <div>
                <h1>
                  {title}
                </h1>
              </div>

              {/* Header content */}
              <div>
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
      <main>
        {children}
      </main>
    </div>
  );
};

export default Layout;