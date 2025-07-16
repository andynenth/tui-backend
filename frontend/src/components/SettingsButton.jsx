import React from 'react';

const SettingsButton = ({ onClick }) => {
  return (
    <button className="settings-button" onClick={onClick} aria-label="Settings">
      <svg
        className="settings-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3m16.36-6.36l-4.24 4.24M7.88 7.88L3.64 3.64m16.72 16.72l-4.24-4.24m-8.24 0l-4.24 4.24"></path>
      </svg>
    </button>
  );
};

export default SettingsButton;
