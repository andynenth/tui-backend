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
    padding: '2rem',
  },
  
  contentWrapper: {
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    padding: '2rem',
    textAlign: 'center',
  },
  
  gameIcon: {
    position: 'relative',
    width: '120px',
    height: '120px',
    margin: '0 auto',
    marginBottom: '2rem',
  },
  
  iconCircle: {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    animation: `${float} 3s 'cubic-bezier(0.4, 0, 0.2, 1)' infinite`,
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
    fontSize: '1.875rem',
    fontWeight: '700',
    color: '#212529',
    marginBottom: '0.5rem',
  },
  
  gameSubtitle: {
    fontSize: '1rem',
    color: '#6c757d',
    marginBottom: '2rem',
  },
  
  formContainer: {
    marginTop: '2rem',
  },
  
  inputWrapper: {
    marginBottom: '1.5rem',
    textAlign: 'left',
  },
  
  inputLabel: {
    display: 'block',
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#495057',
    marginBottom: '0.5rem',
  },
  
  glowingInput: {
    width: '100%',
    padding: `'0.5rem' '1rem'`,
    fontSize: '1rem',
    borderWidth: '2px',
    borderStyle: 'solid',
    borderColor: '#dee2e6',
    borderRadius: '0.375rem',
    backgroundColor: '#ffffff',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    ':focus': {
      outline: 'none',
      borderColor: '#0d6efd',
      boxShadow: `0 0 0 3px rgba(59, 130, 246, 0.1)`,
    },
    '::placeholder': {
      color: '#ced4da',
    },
  },
  
  inputError: {
    marginTop: '0.25rem',
    fontSize: '0.75rem',
    color: '#dc3545',
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
  },
  
  inputHelperText: {
    marginTop: '0.25rem',
    fontSize: '0.75rem',
    color: '#adb5bd',
  },
  
  buttonGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  
  button: {
    width: '100%',
    padding: `'1rem' '1.5rem'`,
    fontSize: '1rem',
    fontWeight: '500',
    borderRadius: '0.375rem',
    border: 'none',
    cursor: 'pointer',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  primaryButton: {
    backgroundColor: '#495057',
    color: '#ffffff',
    ':hover:not(:disabled)': {
      backgroundColor: '#343a40',
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },
  
  secondaryButton: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    ':hover:not(:disabled)': {
      backgroundColor: '#dee2e6',
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },
  
  dangerButton: {
    backgroundColor: '#dc3545',
    color: '#ffffff',
    ':hover:not(:disabled)': {
      backgroundColor: '#a71e2a',
      transform: 'translateY(-2px)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  },
  
  loadingSpinner: {
    display: 'inline-block',
    width: '16px',
    height: '16px',
    border: '2px solid rgba(255, 255, 255, 0.3)',
    borderTopColor: '#ffffff',
    borderRadius: '50%',
    animation: `${spin} 0.6s linear infinite`,
  },
  
  separator: {
    height: '1px',
    backgroundColor: 'rgba(173, 181, 189, 0.2)',
    margin: `'0.25rem' 0`,
  },
  
  settingsButtonPosition: {
    position: 'absolute',
    top: '1rem',
    right: '1rem',
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
      playerName: app.playerName || ',
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