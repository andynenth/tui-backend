// frontend/src/components/VersionDisplay.jsx

import React from 'react';

/**
 * VersionDisplay Component
 * 
 * Displays the application version number.
 * Version is injected at build time from package.json
 */
const VersionDisplay = ({ className = '' }) => {
  // __APP_VERSION__ is defined at build time by esbuild
  // Falls back to 'dev' if not defined (e.g., during development)
  const version = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : 'dev';

  return (
    <div className={`sp-version-display ${className}`}>
      v{version}
    </div>
  );
};

export default VersionDisplay;