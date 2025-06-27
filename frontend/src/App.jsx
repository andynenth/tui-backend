// frontend/src/App.jsx

import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider, useApp } from './contexts/AppContext';
import { GameProvider } from './contexts/GameContext';
import { ErrorBoundary } from './components';

// Import scene components (to be created)
import StartPage from './pages/StartPage';
import LobbyPage from './pages/LobbyPage';
import RoomPage from './pages/RoomPage';
import GamePage from './pages/GamePage';
import DemoPage from './pages/DemoPage';

// Service initialization
import { initializeServices, cleanupServices } from './services';

// Protected Route component
const ProtectedRoute = ({ children, requiredData = [] }) => {
  const app = useApp();
  
  // Check if required data is available
  const hasRequiredData = requiredData.every(key => {
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
const AppRouter = () => {
  return (
    <Router>
      <Routes>
        {/* Start page - no requirements */}
        <Route path="/" element={<StartPage />} />
        
        {/* Demo page - standalone UI demonstration */}
        <Route path="/demo" element={<DemoPage />} />
        
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
    </Router>
  );
};

// Service-aware App component
const AppWithServices = () => {
  const [servicesInitialized, setServicesInitialized] = useState(false);
  const [initializationError, setInitializationError] = useState(null);

  useEffect(() => {
    const initServices = async () => {
      try {
        await initializeServices();
        setServicesInitialized(true);
        console.log('🎮 Phase 1-4 Enterprise Architecture - Global services initialized');
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
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Service Initialization Failed</h1>
          <p className="text-gray-600 mb-4">{initializationError}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!servicesInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="text-center bg-white p-8 rounded-lg shadow-lg">
          <div className="mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg mb-2">
              <span className="font-semibold">🚀 Phase 1-4 Enterprise Architecture</span>
            </div>
            <p className="text-gray-600">Initializing advanced services...</p>
          </div>
          <div className="text-xs text-gray-500 space-y-1">
            <div>• State Machine Engine</div>
            <div>• TypeScript Service Layer</div>
            <div>• Enterprise Monitoring</div>
            <div>• Auto-Recovery Systems</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <AppRouter />
    </div>
  );
};

// Main App component
const App = () => {
  return (
    <ErrorBoundary>
      <AppProvider>
        <AppWithServices />
      </AppProvider>
    </ErrorBoundary>
  );
};

export default App;