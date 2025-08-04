import React, { useState, useEffect } from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, motion, layout, shadows, gradients } from '../design-system/tokens.stylex';
import { useTheme } from '../contexts/ThemeContext';
import { themes } from '../utils/themeManager';

// Animations
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
    transform: 'translateY(20px)',
    opacity: 0,
  },
  '100%': {
    transform: 'translateY(0)',
    opacity: 1,
  },
});

// SettingsModal styles
const styles = stylex.create({
  overlay: {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    animation: `${fadeIn} 0.2s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  modal: {
    backgroundColor: '#ffffff',
    borderRadius: '1rem',
    width: '90%',
    maxWidth: '600px',
    maxHeight: '80vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    animation: `${slideUp} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1.5rem',
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    borderBottomColor: '#e9ecef',
  },
  
  title: {
    fontSize: '1.25rem',
    fontWeight: '700',
    color: '#343a40',
    margin: 0,
  },
  
  closeButton: {
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '0.375rem',
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    transition: `background-color '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    color: '#adb5bd',
    
    ':hover': {
      backgroundColor: '#f1f3f5',
      color: '#495057',
    },
  },
  
  closeIcon: {
    width: '20px',
    height: '20px',
  },
  
  body: {
    flex: 1,
    overflowY: 'auto',
    padding: '1.5rem',
  },
  
  section: {
    marginBottom: '2rem',
  },
  
  sectionTitle: {
    fontSize: '1.125rem',
    fontWeight: '600',
    color: '#495057',
    marginBottom: '1rem',
  },
  
  themeOptions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  
  themeOption: {
    display: 'flex',
    alignItems: 'center',
    padding: '1rem',
    borderRadius: '0.5rem',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#e9ecef',
    cursor: 'pointer',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    backgroundColor: '#ffffff',
    
    ':hover': {
      borderColor: '#0d6efd',
      backgroundColor: '#e7f1ff',
    },
  },
  
  themeOptionActive: {
    borderColor: '#0d6efd',
    backgroundColor: '#e7f1ff',
    boxShadow: `0 0 0 3px '#e7f1ff'`,
  },
  
  themePreview: {
    display: 'flex',
    gap: '0.5rem',
    marginRight: '1rem',
  },
  
  piecePreview: {
    width: '40px',
    height: '40px',
    objectFit: 'contain',
  },
  
  themeInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xxs,
  },
  
  themeName: {
    fontSize: '1rem',
    fontWeight: '500',
    color: '#343a40',
  },
  
  themeDesc: {
    fontSize: '0.875rem',
    color: '#6c757d',
  },
  
  themeCheck: {
    width: '24px',
    height: '24px',
    borderRadius: '9999px',
    backgroundColor: '#0d6efd',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#ffffff',
  },
  
  checkIcon: {
    width: '16px',
    height: '16px',
  },
  
  placeholder: {
    padding: '1.5rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '0.375rem',
    textAlign: 'center',
    color: '#adb5bd',
    fontSize: '0.875rem',
    lineHeight: 1.5,
  },
  
  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '1rem',
    padding: '1.5rem',
    borderTopWidth: '1px',
    borderTopStyle: 'solid',
    borderTopColor: '#e9ecef',
  },
  
  button: {
    padding: `'0.5rem' '1.5rem'`,
    borderRadius: '0.375rem',
    fontSize: '1rem',
    fontWeight: '500',
    border: 'none',
    cursor: 'pointer',
    transition: `all '300ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  cancelButton: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    
    ':hover': {
      backgroundColor: '#dee2e6',
    },
  },
  
  applyButton: {
    background: gradients.primary,
    color: '#ffffff',
    
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },
});

const SettingsModal = ({ isOpen, onClose }) => {
  const { currentTheme, changeTheme } = useTheme();
  const [selectedTheme, setSelectedTheme] = useState(currentTheme.id);

  // Show available themes (excluding modern)
  const availableThemes = [themes.classic, themes.medieval];

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
    <div {...stylex.props(styles.overlay)} onClick={handleOverlayClick}>
      <div {...stylex.props(styles.modal)}>
        <div {...stylex.props(styles.header)}>
          <h2 {...stylex.props(styles.title)}>Settings</h2>
          <button
            {...stylex.props(styles.closeButton)}
            onClick={handleCancel}
            aria-label="Close settings"
          >
            <svg
              {...stylex.props(styles.closeIcon)}
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

        <div {...stylex.props(styles.body)}>
          <div {...stylex.props(styles.section)}>
            <h3 {...stylex.props(styles.sectionTitle)}>Theme</h3>
            <div {...stylex.props(styles.themeOptions)}>
              {availableThemes.map((theme) => (
                <div
                  key={theme.id}
                  {...stylex.props(
                    styles.themeOption,
                    selectedTheme === theme.id && styles.themeOptionActive
                  )}
                  onClick={() => handleThemeSelect(theme.id)}
                >
                  <div {...stylex.props(styles.themePreview)}>
                    <img
                      src={theme.pieceAssets.GENERAL_RED}
                      alt="Red General"
                      {...stylex.props(styles.piecePreview)}
                    />
                    <img
                      src={theme.pieceAssets.GENERAL_BLACK}
                      alt="Black General"
                      {...stylex.props(styles.piecePreview)}
                    />
                  </div>
                  <div {...stylex.props(styles.themeInfo)}>
                    <div {...stylex.props(styles.themeName)}>{theme.name}</div>
                    <div {...stylex.props(styles.themeDesc)}>{theme.description}</div>
                  </div>
                  {selectedTheme === theme.id && (
                    <div {...stylex.props(styles.themeCheck)}>
                      <svg
                        {...stylex.props(styles.checkIcon)}
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

          <div {...stylex.props(styles.section)}>
            <h3 {...stylex.props(styles.sectionTitle)}>Other Settings</h3>
            <div {...stylex.props(styles.placeholder)}>
              More settings coming soon...
              <br />
              (Sound, Animations, etc.)
            </div>
          </div>
        </div>

        <div {...stylex.props(styles.footer)}>
          <button 
            {...stylex.props(styles.button, styles.cancelButton)}
            onClick={handleCancel}
          >
            Cancel
          </button>
          <button 
            {...stylex.props(styles.button, styles.applyButton)}
            onClick={handleApply}
          >
            Apply
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;