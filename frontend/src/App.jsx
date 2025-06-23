// frontend/src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider, useApp } from './contexts/AppContext';
import { GameProvider } from './contexts/GameContext';

// Import scene components (to be created)
import StartPage from './pages/StartPage';
import LobbyPage from './pages/LobbyPage';
import RoomPage from './pages/RoomPage';
import GamePage from './pages/GamePage';

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

// Main App component
const App = () => {
  return (
    <AppProvider>
      <div className="App">
        <AppRouter />
      </div>
    </AppProvider>
  );
};

export default App;