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
    animation: `${fadeIn} 0.2s ${motion.easeOut}`,
  },
  
  modal: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusXl,
    width: '90%',
    maxWidth: '600px',
    maxHeight: '80vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: shadows.xl,
    animation: `${slideUp} 0.3s ${motion.easeOut}`,
  },
  
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    borderBottom: `1px solid ${colors.gray200}`,
  },
  
  title: {
    fontSize: typography.textXl,
    fontWeight: typography.weightBold,
    color: colors.gray800,
    margin: 0,
  },
  
  closeButton: {
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: layout.radiusMd,
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    transition: `background-color ${motion.durationBase} ${motion.easeInOut}`,
    color: colors.gray500,
    
    ':hover': {
      backgroundColor: colors.gray100,
      color: colors.gray700,
    },
  },
  
  closeIcon: {
    width: '20px',
    height: '20px',
  },
  
  body: {
    flex: 1,
    overflowY: 'auto',
    padding: spacing.lg,
  },
  
  section: {
    marginBottom: spacing.xl,
  },
  
  sectionTitle: {
    fontSize: typography.textLg,
    fontWeight: typography.weightSemibold,
    color: colors.gray700,
    marginBottom: spacing.md,
  },
  
  themeOptions: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.md,
  },
  
  themeOption: {
    display: 'flex',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: layout.radiusLg,
    border: `2px solid ${colors.gray200}`,
    cursor: 'pointer',
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
    backgroundColor: colors.white,
    
    ':hover': {
      borderColor: colors.primary,
      backgroundColor: colors.primaryLight,
    },
  },
  
  themeOptionActive: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryLight,
    boxShadow: `0 0 0 3px ${colors.primaryLight}`,
  },
  
  themePreview: {
    display: 'flex',
    gap: spacing.sm,
    marginRight: spacing.md,
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
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    color: colors.gray800,
  },
  
  themeDesc: {
    fontSize: typography.textSm,
    color: colors.gray600,
  },
  
  themeCheck: {
    width: '24px',
    height: '24px',
    borderRadius: layout.radiusFull,
    backgroundColor: colors.primary,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: colors.white,
  },
  
  checkIcon: {
    width: '16px',
    height: '16px',
  },
  
  placeholder: {
    padding: spacing.lg,
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusMd,
    textAlign: 'center',
    color: colors.gray500,
    fontSize: typography.textSm,
    lineHeight: 1.5,
  },
  
  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: spacing.md,
    padding: spacing.lg,
    borderTop: `1px solid ${colors.gray200}`,
  },
  
  button: {
    padding: `${spacing.sm} ${spacing.lg}`,
    borderRadius: layout.radiusMd,
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    border: 'none',
    cursor: 'pointer',
    transition: `all ${motion.durationBase} ${motion.easeInOut}`,
  },
  
  cancelButton: {
    backgroundColor: colors.gray200,
    color: colors.gray700,
    
    ':hover': {
      backgroundColor: colors.gray300,
    },
  },
  
  applyButton: {
    background: gradients.primary,
    color: colors.white,
    
    ':hover': {
      transform: 'translateY(-2px)',
      boxShadow: shadows.md,
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