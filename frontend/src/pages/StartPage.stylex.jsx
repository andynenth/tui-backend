// frontend/src/pages/StartPage.stylex.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, motion, gradients } from '../design-system/tokens.stylex';
import { useApp } from '../contexts/AppContext';
import { useTheme } from '../contexts/ThemeContext';
import Layout from '../components/Layout.stylex';
import LoadingOverlay from '../components/LoadingOverlay.stylex';
import SettingsButton from '../components/SettingsButton.stylex';
import SettingsModal from '../components/SettingsModal.stylex';

// Animations
const rotate = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

const spin = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

const float = stylex.keyframes({
  '0%, 100%': {
    transform: 'translateY(0)',
  },
  '50%': {
    transform: 'translateY(-10px)',
  },
});

// StartPage styles
const styles = stylex.create({
  pageContainer: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundImage: gradients.gray,
  },
  
  gameContainer: {
    position: 'relative',
    width: '100%',
    maxWidth: '400px',
    padding: spacing.xl,
  },
  
  contentWrapper: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusLg,
    boxShadow: shadows.xl,
    padding: spacing.xl,
    textAlign: 'center',
  },
  
  gameIcon: {
    position: 'relative',
    width: '120px',
    height: '120px',
    margin: '0 auto',
    marginBottom: spacing.xl,
  },
  
  iconCircle: {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    animation: `${float} 3s ${motion.easeInOut} infinite`,
  },
  
  iconImage: {
    width: '80px',
    height: '80px',
  },
  
  iconPiece: {
    position: 'absolute',
    width: '30px',
    height: '30px',
  },
  
  iconPiece1: {
    top: '-10px',
    right: '-10px',
    animation: `${rotate} 8s linear infinite`,
  },
  
  iconPiece2: {
    bottom: '-10px',
    left: '-10px',
    animation: `${rotate} 10s linear infinite reverse`,
  },
  
  gameTitle: {
    fontSize: typography.text3xl,
    fontWeight: typography.weightBold,
    color: colors.gray900,
    marginBottom: spacing.sm,
  },
  
  gameSubtitle: {
    fontSize: typography.textBase,
    color: colors.gray600,
    marginBottom: spacing.xl,
  },
  
  formContainer: {
    marginTop: spacing.xl,
  },
  
  inputWrapper: {
    marginBottom: spacing.lg,
    textAlign: 'left',
  },
  
  inputLabel: {
    display: 'block',
    fontSize: typography.textSm,
    fontWeight: typography.weightMedium,
    color: colors.gray700,
    marginBottom: spacing.sm,
  },
  
  glowingInput: {
    width: '100%',
    padding: `${spacing.sm} ${spacing.md}`,
    fontSize: typography.textBase,
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: colors.gray300,
    borderRadius: layout.radiusMd,
    backgroundColor: colors.white,
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    ':focus': {
      outline: 'none',
      borderColor: colors.primary,
      boxShadow: `0 0 0 3px rgba(59, 130, 246, 0.1)`,
    },
    '::placeholder': {
      color: colors.gray400,
    },
  },
  
  inputError: {
    marginTop: spacing.xs,
    fontSize: typography.textXs,
    color: colors.danger,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.xs,
  },
  
  inputHelperText: {
    marginTop: spacing.xs,
    fontSize: typography.textXs,
    color: colors.gray500,
  },
  
  buttonGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.sm,
  },
  
  button: {
    width: '100%',
    padding: `${spacing.md} ${spacing.lg}`,
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    borderRadius: layout.radiusMd,
    border: 'none',
    cursor: 'pointer',
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  primaryButton: {
    backgroundColor: '#495057',
    color: colors.white,
    ':hover:not(:disabled)': {
      backgroundColor: '#343a40',
      transform: 'translateY(-2px)',
      boxShadow: shadows.md,
    },
  },
  
  secondaryButton: {
    backgroundColor: colors.gray200,
    color: colors.gray700,
    ':hover:not(:disabled)': {
      backgroundColor: colors.gray300,
      transform: 'translateY(-2px)',
      boxShadow: shadows.md,
    },
  },
  
  dangerButton: {
    backgroundColor: colors.danger,
    color: colors.white,
    ':hover:not(:disabled)': {
      backgroundColor: colors.dangerDark,
      transform: 'translateY(-2px)',
      boxShadow: shadows.md,
    },
  },
  
  loadingSpinner: {
    display: 'inline-block',
    width: '16px',
    height: '16px',
    border: '2px solid rgba(255, 255, 255, 0.3)',
    borderTopColor: colors.white,
    borderRadius: '50%',
    animation: `${spin} 0.6s linear infinite`,
  },
  
  separator: {
    height: '1px',
    backgroundColor: 'rgba(173, 181, 189, 0.2)',
    margin: `${spacing.xs} 0`,
  },
  
  settingsButtonPosition: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    zIndex: 10,
  },
});

const StartPage = () => {
  const navigate = useNavigate();
  const app = useApp();
  const { currentTheme } = useTheme();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm({
    defaultValues: {
      playerName: app.playerName || '',
    },
  });

  const playerNameValue = watch('playerName');

  // If player name already exists, suggest going to lobby
  useEffect(() => {
    if (app.playerName) {
      setValue('playerName', app.playerName);
    }
  }, [app.playerName, setValue]);

  const onSubmit = async (data) => {
    setIsSubmitting(true);

    try {
      // Update player name in app context
      app.updatePlayerName(data.playerName);

      // Navigate to lobby
      navigate('/lobby');
    } catch (error) {
      console.error('Failed to set player name:', error);
      // Error will be shown via form validation
    } finally {
      setIsSubmitting(false);
    }
  };

  const goToLobby = () => {
    if (app.playerName) {
      navigate('/lobby');
    }
  };

  return (
    <>
      <Layout
        title="Castellan - Welcome"
        showConnection={false}
        showHeader={false}
      >
        <div {...stylex.props(styles.pageContainer)}>
          <div {...stylex.props(styles.gameContainer)}>
            <div {...stylex.props(styles.settingsButtonPosition)}>
              <SettingsButton onClick={() => setShowSettings(true)} />
            </div>
            <div {...stylex.props(styles.contentWrapper)}>
              {/* Game Icon with rotating pieces - always using SVGs */}
              <div {...stylex.props(styles.gameIcon)}>
                <div {...stylex.props(styles.iconCircle)}>
                  <img
                    src={currentTheme.uiElements.startIcon.main}
                    alt="Game icon"
                    {...stylex.props(styles.iconImage)}
                  />
                </div>
                <div {...stylex.props(styles.iconPiece, styles.iconPiece1)}>
                  <img
                    src={currentTheme.uiElements.startIcon.piece1}
                    alt="Red piece"
                    style={{ width: '100%', height: '100%' }}
                  />
                </div>
                <div {...stylex.props(styles.iconPiece, styles.iconPiece2)}>
                  <img
                    src={currentTheme.uiElements.startIcon.piece2}
                    alt="Black piece"
                    style={{ width: '100%', height: '100%' }}
                  />
                </div>
              </div>

              {/* Header */}
              <h1 {...stylex.props(styles.gameTitle)}>Welcome to Castellan</h1>
              <p {...stylex.props(styles.gameSubtitle)}>
                Enter your player name to start playing
              </p>

              {/* Player name form */}
              <form
                onSubmit={handleSubmit(onSubmit)}
                {...stylex.props(styles.formContainer)}
              >
                <div {...stylex.props(styles.inputWrapper)}>
                  <label {...stylex.props(styles.inputLabel)}>Player Name</label>
                  <input
                    type="text"
                    {...stylex.props(styles.glowingInput)}
                    placeholder="Enter your name..."
                    {...register('playerName', {
                      required: 'Player name is required',
                      minLength: {
                        value: 2,
                        message: 'Name must be at least 2 characters',
                      },
                      maxLength: {
                        value: 20,
                        message: 'Name must be less than 20 characters',
                      },
                      pattern: {
                        value: /^[a-zA-Z0-9_-]+$/,
                        message:
                          'Only letters, numbers, underscore and dash allowed',
                      },
                    })}
                  />
                  {errors.playerName ? (
                    <p {...stylex.props(styles.inputError)}>
                      ⚠️ {errors.playerName.message}
                    </p>
                  ) : (
                    <p {...stylex.props(styles.inputHelperText)}>
                      2-20 characters, letters and numbers only
                    </p>
                  )}
                </div>

                <div {...stylex.props(styles.buttonGroup)}>
                  <button
                    type="submit"
                    {...stylex.props(styles.button, styles.primaryButton)}
                    disabled={!playerNameValue || isSubmitting}
                  >
                    {isSubmitting && <span {...stylex.props(styles.loadingSpinner)} />}
                    {isSubmitting ? 'Setting up...' : 'Enter Lobby'}
                  </button>

                  {/* Continue as previous player */}
                  {app.playerName && (
                    <button
                      type="button"
                      {...stylex.props(styles.button, styles.secondaryButton)}
                      onClick={goToLobby}
                    >
                      Continue as {app.playerName}
                    </button>
                  )}

                  {/* Separator */}
                  <div {...stylex.props(styles.separator)} />

                  {/* How to play button */}
                  <button
                    type="button"
                    {...stylex.props(styles.button, styles.dangerButton)}
                    onClick={() => navigate('/tutorial')}
                  >
                    How to Play
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </Layout>

      <LoadingOverlay
        isVisible={isSubmitting}
        message="Setting up your profile..."
        subtitle="Please wait while we prepare your game session"
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </>
  );
};

export default StartPage;