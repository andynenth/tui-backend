// frontend/src/pages/StartPage.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useApp } from '../contexts/AppContext';
import { Layout, Button, Input, LoadingOverlay } from '../components';

const StartPage = () => {
  const navigate = useNavigate();
  const app = useApp();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch
  } = useForm({
    defaultValues: {
      playerName: app.playerName || ''
    }
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
        title="Liap TUI - Welcome"
        showConnection={false}
        showHeader={false}
      >
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
          <div className="max-w-md w-full mx-4">
            <div className="bg-white rounded-lg shadow-xl p-8">
              {/* Header */}
              <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  Welcome to Liap TUI
                </h1>
                <p className="text-gray-600">
                  Enter your player name to start playing
                </p>
              </div>

              {/* Player name form */}
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <Input
                  label="Player Name"
                  placeholder="Enter your name..."
                  fullWidth
                  {...register('playerName', {
                    required: 'Player name is required',
                    minLength: {
                      value: 2,
                      message: 'Name must be at least 2 characters'
                    },
                    maxLength: {
                      value: 20,
                      message: 'Name must be less than 20 characters'
                    },
                    pattern: {
                      value: /^[a-zA-Z0-9_-]+$/,
                      message: 'Only letters, numbers, underscore and dash allowed'
                    }
                  })}
                  error={errors.playerName?.message}
                  helperText="2-20 characters, letters and numbers only"
                />

                <div className="space-y-3">
                  <Button
                    type="submit"
                    fullWidth
                    loading={isSubmitting}
                    disabled={!playerNameValue || isSubmitting}
                    loadingText="Setting up..."
                  >
                    Enter Lobby
                  </Button>

                  {/* Quick access if player name already exists */}
                  {app.playerName && app.playerName !== playerNameValue && (
                    <Button
                      type="button"
                      variant="outline"
                      fullWidth
                      onClick={goToLobby}
                    >
                      Continue as {app.playerName}
                    </Button>
                  )}
                </div>
              </form>

              {/* Game info */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <div className="text-center text-sm text-gray-500">
                  <p className="mb-2">
                    🎮 A real-time multiplayer strategy game
                  </p>
                  <p>
                    4 players • Card-based gameplay • Strategic planning
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Layout>

      <LoadingOverlay
        isVisible={isSubmitting}
        message="Setting up your profile..."
        subtitle="Please wait while we prepare your game session"
      />
    </>
  );
};

export default StartPage;