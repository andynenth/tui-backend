// frontend/src/pages/StartPage.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useApp } from '../contexts/AppContext';
import { useTheme } from '../contexts/ThemeContext';
import { Layout, LoadingOverlay } from '../components';
import SettingsButton from '../components/SettingsButton';
import SettingsModal from '../components/SettingsModal';
// CSS classes are imported globally

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
        <div
          className="min-h-screen flex items-center justify-center"
          style={{ background: 'var(--gradient-gray)' }}
        >
          <div className="sp-game-container">
            <SettingsButton onClick={() => setShowSettings(true)} />
            <div className="sp-content-wrapper">
              {/* Game Icon with rotating pieces - always using SVGs */}
              <div className="sp-game-icon">
                <div className="sp-icon-circle">
                  <img
                    src={currentTheme.uiElements.startIcon.main}
                    alt="Game icon"
                  />
                </div>
                <div className="sp-icon-pieces sp-icon-piece-1">
                  <img
                    src={currentTheme.uiElements.startIcon.piece1}
                    alt="Red piece"
                  />
                </div>
                <div className="sp-icon-pieces sp-icon-piece-2">
                  <img
                    src={currentTheme.uiElements.startIcon.piece2}
                    alt="Black piece"
                  />
                </div>
              </div>

              {/* Header */}
              <h1 className="sp-game-title">Welcome to Castellan</h1>
              <p className="sp-game-subtitle">
                Enter your player name to start playing
              </p>

              {/* Player name form */}
              <form
                onSubmit={handleSubmit(onSubmit)}
                className="sp-form-container"
              >
                <div className="sp-input-wrapper">
                  <label className="sp-input-label">Player Name</label>
                  <input
                    type="text"
                    className="sp-glowing-input"
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
                    <p className="sp-input-error">
                      ⚠️ {errors.playerName.message}
                    </p>
                  ) : (
                    <p className="sp-input-helper-text">
                      2-20 characters, letters and numbers only
                    </p>
                  )}
                </div>

                <div className="sp-button-group">
                  <button
                    type="submit"
                    className="btn btn-secondary btn-full"
                    disabled={!playerNameValue || isSubmitting}
                    style={{ background: '#495057', color: 'white' }}
                  >
                    {isSubmitting && <span className="sp-loading-spinner" />}
                    {isSubmitting ? 'Setting up...' : 'Enter Lobby'}
                  </button>

                  {/* Continue as previous player */}
                  {app.playerName && (
                    <button
                      type="button"
                      className="btn btn-secondary btn-full"
                      onClick={goToLobby}
                    >
                      Continue as {app.playerName}
                    </button>
                  )}

                  {/* Separator */}
                  <div
                    style={{
                      height: '1px',
                      background: 'rgba(173, 181, 189, 0.2)',
                      margin: '4px 0',
                    }}
                  ></div>

                  {/* How to play button */}
                  <button
                    type="button"
                    className="btn btn-danger btn-full"
                    onClick={() => navigate('/tutorial')}
                    style={{ background: '#dc3545', color: 'white' }}
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
