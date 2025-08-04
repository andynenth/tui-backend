// frontend/src/App.stylex.jsx

import React, { useEffect, useState } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
  useParams,
} from 'react-router-dom';
import { AppProvider, useApp } from './contexts/AppContext';
import { GameProvider } from './contexts/GameContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ErrorBoundary } from './components';
import { hasValidSession, getSession } from './utils/sessionStorage';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, animations } from './design-system/tokens.stylex';

// Import scene components
import StartPage from './pages/StartPage.stylex';
import LobbyPage from './pages/LobbyPage.stylex';
import RoomPage from './pages/RoomPage.stylex';
import GamePage from './pages/GamePage.stylex';
import TutorialPage from './pages/TutorialPage.stylex';
import { LoadingOverlay } from './components';

// Service initialization
import { initializeServices, cleanupServices } from './services';

// Initialize theme on app load
import { initializeTheme } from './utils/themeManager';

const styles = stylex.create({
  serviceInitOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: colors.background,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
  },
  
  serviceInitContainer: {
    backgroundColor: colors.surface,
    borderRadius: '1rem',
    padding: '2rem',
    maxWidth: '400px',
    width: '90%',
    textAlign: 'center',
    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
  },
  
  serviceErrorTitle: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.error,
    marginTop: 0,
    marginBottom: '1rem',
  },
  
  serviceErrorMessage: {
    fontSize: typography.fontSize.base,
    color: colors.textSecondary,
    marginBottom: '1.5rem',
    lineHeight: 1.5,
  },
  
  serviceRetryButton: {
    backgroundColor: '#0d6efd',
    color: '#ffffff',
    border: 'none',
    borderRadius: '0.5rem',
    padding: `'0.5rem' '1.5rem'`,
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.semibold,
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
    ':hover': {
      backgroundColor: '#0056b3',
    },
    ':active': {
      transform: 'scale(0.98)',
    },
  },
  
  serviceLoadingSpinner: {
    width: '48px',
    height: '48px',
    borderWidth: '4px',
    borderStyle: 'solid',
    borderColor: '#dee2e6',
    borderTopColor: '#0d6efd',
    borderRadius: '50%',
    margin: '0 auto',
    marginBottom: '1rem',
    animationName: animations.spin,
    animationDuration: '1s',
    animationTimingFunction: 'linear',
    animationIterationCount: 'infinite',
  },
  
  serviceLoadingText: {
    fontSize: typography.fontSize.base,
    color: colors.textSecondary,
    margin: 0,
  },
});

// Protected Route component
const ProtectedRoute = ({ children, requiredData = [] }) => {
  const app = useApp();

  // Check if required data is available
  const hasRequiredData = requiredData.every((key) => {
    switch (key) {
      case 'playerName':
        return !!app.playerName;
      case 'roomId':
        return !!app.currentRoomId;
      default:
        return true;
    }
  });

  if (!hasRequiredData) {
    // Redirect to appropriate scene based on what's missing
    if (!app.playerName) {
      return <Navigate to="/" replace />;
    }
    if (!app.currentRoomId) {
      return <Navigate to="/lobby" replace />;
    }
  }

  return children;
};

// Game Route wrapper that provides GameContext
const GameRoute = ({ children }) => {
  const app = useApp();
  const { roomId } = useParams();
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    // Check if we need to recover from session
    if (!app.playerName || !app.currentRoomId) {
      const session = getSession();
      if (session && session.roomId === roomId) {
        console.log('🎮 GameRoute: Recovering session data');
        app.setPlayerName(session.playerName);
        app.setCurrentRoomId(session.roomId);
      }
    }
    setIsCheckingSession(false);
  }, [app, roomId]);

  if (isCheckingSession) {
    return (
      <LoadingOverlay
        isVisible={true}
        message="Checking session..."
        subtitle="Please wait while we verify your game session"
      />
    );
  }

  if (!app.playerName || !app.currentRoomId) {
    return <Navigate to="/" replace />;
  }

  return (
    <GameProvider roomId={app.currentRoomId} playerName={app.playerName}>
      {children}
    </GameProvider>
  );
};

// App Router component
const AppRouter = ({ sessionToRecover }) => {
  return (
    <Router>
      <AppRouterContent sessionToRecover={sessionToRecover} />
    </Router>
  );
};

// Router content with session recovery
const AppRouterContent = ({ sessionToRecover }) => {
  const navigate = useNavigate();
  const app = useApp();

  useEffect(() => {
    if (sessionToRecover) {
      // Restore app context
      app.updatePlayerName(sessionToRecover.playerName);
      // Note: currentRoomId will be set automatically by navigation

      // Navigate to game
      console.log(
        '🎮 Recovering session, navigating to game:',
        sessionToRecover.roomId
      );
      navigate(`/game/${sessionToRecover.roomId}`);
    }
  }, [sessionToRecover, navigate, app]);

  return (
    <Routes>
      {/* Start page - no requirements */}
      <Route path="/" element={<StartPage />} />
      
      {/* Tutorial page - no requirements */}
      <Route path="/tutorial" element={<TutorialPage />} />

      {/* Lobby - requires player name */}
      <Route
        path="/lobby"
        element={
          <ProtectedRoute requiredData={['playerName']}>
            <LobbyPage />
          </ProtectedRoute>
        }
      />

      {/* Room - requires player name and room ID */}
      <Route
        path="/room/:roomId"
        element={
          <ProtectedRoute requiredData={['playerName', 'roomId']}>
            <RoomPage />
          </ProtectedRoute>
        }
      />

      {/* Game - requires player name and room ID, provides GameContext */}
      <Route
        path="/game/:roomId"
        element={
          <GameRoute>
            <GamePage />
          </GameRoute>
        }
      />

      {/* Catch all - redirect to start */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

// Service-aware App component with session recovery
const AppWithServices = ({ className }) => {
  const [servicesInitialized, setServicesInitialized] = useState(false);
  const [initializationError, setInitializationError] = useState(null);
  const [sessionToRecover, setSessionToRecover] = useState(null);

  useEffect(() => {
    const initServices = async () => {
      try {
        // Initialize theme first
        initializeTheme();

        await initializeServices();

        // Check for stored session
        if (hasValidSession()) {
          const session = getSession();
          console.log('🎮 Found stored session:', session);
          setSessionToRecover(session);
        }

        setServicesInitialized(true);
        console.log('🎮 Global services initialized');
      } catch (error) {
        console.error('Failed to initialize global services:', error);
        setInitializationError(error.message);
      }
    };

    initServices();

    // Cleanup on unmount
    return () => {
      cleanupServices();
      console.log('🎮 Global services cleaned up');
    };
  }, []);

  if (initializationError) {
    return (
      <div {...stylex.props(styles.serviceInitOverlay, className)}>
        <div {...stylex.props(styles.serviceInitContainer)}>
          <h1 {...stylex.props(styles.serviceErrorTitle)}>Service Initialization Failed</h1>
          <p {...stylex.props(styles.serviceErrorMessage)}>{initializationError}</p>
          <button
            onClick={() => window.location.reload()}
            {...stylex.props(styles.serviceRetryButton)}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!servicesInitialized) {
    return (
      <div {...stylex.props(styles.serviceInitOverlay, className)}>
        <div {...stylex.props(styles.serviceInitContainer)}>
          <div {...stylex.props(styles.serviceLoadingSpinner)}></div>
          <p {...stylex.props(styles.serviceLoadingText)}>Initializing game services...</p>
        </div>
      </div>
    );
  }

  return <AppRouter sessionToRecover={sessionToRecover} />;
};

// Main App component
const App = ({ className }) => {
  return (
    <ErrorBoundary className={className}>
      <ThemeProvider>
        <AppProvider>
          <AppWithServices className={className} />
        </AppProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;