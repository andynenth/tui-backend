// frontend/src/pages/RoomPage.jsx
// Simplified to use Phase 1-4 Enterprise Architecture

import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { Layout, Button } from '../components';

const RoomPage = () => {
  const navigate = useNavigate();
  const { roomId } = useParams();
  const app = useApp();

  // Auto-redirect to game page since Phase 1-4 handles room logic there
  useEffect(() => {
    if (roomId && app.playerName) {
      console.log('🚀 ROOM_PAGE: Redirecting to Phase 1-4 game architecture');
      navigate(`/game/${roomId}`);
    }
  }, [roomId, app.playerName, navigate]);

  if (!app.playerName) {
    return (
      <Layout title="Room Access">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Player Name Required
          </h2>
          <p className="text-gray-600 mb-6">
            Please set your player name first.
          </p>
          <Button onClick={() => navigate('/')}>
            Go to Start Page
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Room ${roomId}`}>
      <div className="text-center py-12">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-2">
            🚀 Phase 1-4 Enterprise Architecture
          </h2>
          <p className="text-blue-100">
            Redirecting to advanced game interface...
          </p>
        </div>
        
        <div className="text-gray-600">
          <p>Room ID: {roomId}</p>
          <p>Player: {app.playerName}</p>
        </div>
        
        <div className="mt-6">
          <Button onClick={() => navigate(`/game/${roomId}`)}>
            Enter Game
          </Button>
        </div>
      </div>
    </Layout>
  );
};

export default RoomPage;