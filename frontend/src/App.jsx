// frontend/src/App.jsx

import React, { useEffect, useState, Suspense } from 'react';
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

// Import critical pages directly (immediately needed)
import StartPage from './pages/StartPage';
import GamePage from './pages/GamePage';

// Lazy load secondary pages for better initial bundle size
const LobbyPage = React.lazy(() => import('./pages/LobbyPage'));
const RoomPage = React.lazy(() => import('./pages/RoomPage'));
const TutorialPage = React.lazy(() => import('./pages/TutorialPage'));
const PlayHistoryPage = React.lazy(() => import('./pages/PlayHistoryPage'));
import { LoadingOverlay } from './components';

// Service initialization
import { initializeServices, cleanupServices } from './services';

// Initialize theme on app load
import { initializeTheme } from './utils/themeManager';

// Performance monitoring
import './utils/performanceMonitor';

// Enhanced telemetry service
import { telemetryService } from './utils/telemetryService';
import TelemetryErrorBoundary from './components/TelemetryErrorBoundary';

// Loading component for code-split pages
const PageLoader = ({ message = "Loading page..." }) => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
      <p className="text-indigo-600 font-medium">{message}</p>
    </div>
  </div>
);

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

      {/* Tutorial page - no requirements - Lazy loaded */}
      <Route
        path="/tutorial"
        element={
          <Suspense fallback={<PageLoader message="Loading tutorial..." />}>
            <TutorialPage />
          </Suspense>
        }
      />

      {/* Lobby - requires player name - Lazy loaded */}
      <Route
        path="/lobby"
        element={
          <ProtectedRoute requiredData={['playerName']}>
            <Suspense fallback={<PageLoader message="Loading lobby..." />}>
              <LobbyPage />
            </Suspense>
          </ProtectedRoute>
        }
      />

      {/* Room - requires player name and room ID - Lazy loaded */}
      <Route
        path="/room/:roomId"
        element={
          <ProtectedRoute requiredData={['playerName', 'roomId']}>
            <Suspense fallback={<PageLoader message="Loading room..." />}>
              <RoomPage />
            </Suspense>
          </ProtectedRoute>
        }
      />

      {/* Game - requires player name and room ID, provides GameContext - Critical page, not lazy loaded */}
      <Route
        path="/game/:roomId"
        element={
          <GameRoute>
            <GamePage />
          </GameRoute>
        }
      />

      {/* Admin-only Play History - direct URL access only - Lazy loaded */}
      <Route
        path="/history/:roomId"
        element={
          <Suspense fallback={<PageLoader message="Loading play history..." />}>
            <PlayHistoryPage />
          </Suspense>
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

        // Initialize telemetry service
        telemetryService.track('react_app_init', {
          timestamp: Date.now(),
          userAgent: navigator.userAgent,
          viewport: {
            width: window.innerWidth,
            height: window.innerHeight
          }
        });

        // Check for stored session
        if (hasValidSession()) {
          const session = getSession();
          console.log('🎮 Found stored session:', session);
          telemetryService.track('session_recovery', {
            hasSession: true,
            roomId: session?.roomId
          });
          setSessionToRecover(session);
        } else {
          telemetryService.track('session_recovery', {
            hasSession: false
          });
        }

        setServicesInitialized(true);
        console.log('🎮 Global services initialized');
      } catch (error) {
        console.error('Failed to initialize global services:', error);
        telemetryService.trackError(error, {
          context: 'service_initialization',
          phase: 'startup'
        });
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
    <TelemetryErrorBoundary componentName="App">
      <ErrorBoundary>
        <ThemeProvider>
          <TelemetryErrorBoundary componentName="ThemeProvider">
            <AppProvider>
              <TelemetryErrorBoundary componentName="AppProvider">
                <AppWithServices />
              </TelemetryErrorBoundary>
            </AppProvider>
          </TelemetryErrorBoundary>
        </ThemeProvider>
      </ErrorBoundary>
    </TelemetryErrorBoundary>
  );
};

export default App;
