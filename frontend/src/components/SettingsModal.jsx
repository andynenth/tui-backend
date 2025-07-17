import React, { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { themes } from '../utils/themeManager';

const SettingsModal = ({ isOpen, onClose }) => {
  const { currentTheme, changeTheme } = useTheme();
  const [selectedTheme, setSelectedTheme] = useState(currentTheme.id);

  // Show all available themes
  const availableThemes = [themes.classic, themes.modern, themes.medieval];

  useEffect(() => {
    setSelectedTheme(currentTheme.id);
  }, [currentTheme]);

  const handleThemeSelect = (themeId) => {
    setSelectedTheme(themeId);
  };

  const handleApply = () => {
    if (selectedTheme !== currentTheme.id) {
      changeTheme(selectedTheme);
    }
    onClose();
  };

  const handleCancel = () => {
    setSelectedTheme(currentTheme.id);
    onClose();
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      handleCancel();
    }
  };

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        handleCancel();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="settings-modal-overlay" onClick={handleOverlayClick}>
      <div className="settings-modal">
        <div className="settings-modal-header">
          <h2 className="settings-modal-title">Settings</h2>
          <button
            className="settings-modal-close"
            onClick={handleCancel}
            aria-label="Close settings"
          >
            <svg
              className="modal-close-icon"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>

        <div className="settings-modal-body">
          <div className="settings-section">
            <h3 className="settings-section-title">Theme</h3>
            <div className="theme-options">
              {availableThemes.map((theme) => (
                <div
                  key={theme.id}
                  className={`theme-option ${selectedTheme === theme.id ? 'active' : ''}`}
                  onClick={() => handleThemeSelect(theme.id)}
                >
                  <div className="theme-option-preview">
                    <span
                      className="piece-char"
                      style={{ color: theme.pieceColors.red }}
                    >
                      帥
                    </span>
                    <span
                      className="piece-char"
                      style={{ color: theme.pieceColors.black }}
                    >
                      將
                    </span>
                  </div>
                  <div className="theme-option-info">
                    <div className="theme-option-name">{theme.name}</div>
                    <div className="theme-option-desc">{theme.description}</div>
                  </div>
                  {selectedTheme === theme.id && (
                    <div className="theme-option-check">
                      <svg
                        className="check-icon"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="settings-section">
            <h3 className="settings-section-title">Other Settings</h3>
            <div className="settings-placeholder">
              More settings coming soon...
              <br />
              (Sound, Animations, etc.)
            </div>
          </div>
        </div>

        <div className="settings-modal-footer">
          <button className="btn-modal btn-cancel" onClick={handleCancel}>
            Cancel
          </button>
          <button className="btn-modal btn-apply" onClick={handleApply}>
            Apply Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
