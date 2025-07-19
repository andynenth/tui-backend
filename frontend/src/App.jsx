// frontend/src/App.jsx

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

// Import scene components (to be created)
import StartPage from './pages/StartPage';
import LobbyPage from './pages/LobbyPage';
import RoomPage from './pages/RoomPage';
import GamePage from './pages/GamePage';
import { LoadingOverlay } from './components';

// Service initialization
import { initializeServices, cleanupServices } from './services';

// Initialize theme on app load
import { initializeTheme } from './utils/themeManager';

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
        console.log(
          '🎮 GameRoute: Found session, redirecting to reconnection URL'
        );
        // Redirect to reconnection URL instead of trying to recover here
        window.location.href =
          session.reconnectionUrl ||
          `/?rejoin=${roomId}&player=${session.playerName}`;
        return;
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
    // No session found, go to home page
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
      app.setPlayerName(sessionToRecover.playerName);
      app.setCurrentRoomId(sessionToRecover.roomId);

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
const AppWithServices = () => {
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
      <div className="service-init-overlay">
        <div className="service-init-container">
          <h1 className="service-error-title">Service Initialization Failed</h1>
          <p className="service-error-message">{initializationError}</p>
          <button
            onClick={() => window.location.reload()}
            className="service-retry-button"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!servicesInitialized) {
    return (
      <div className="service-init-overlay">
        <div className="service-init-container">
          <div className="service-loading-spinner"></div>
          <p className="service-loading-text">Initializing game services...</p>
        </div>
      </div>
    );
  }

  return <AppRouter sessionToRecover={sessionToRecover} />;
};

// Main App component
const App = () => {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AppProvider>
          <AppWithServices />
        </AppProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
