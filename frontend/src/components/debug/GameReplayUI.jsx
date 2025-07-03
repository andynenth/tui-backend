/**
 * 🎮 **GameReplayUI Component** - Phase 6.1 Replay Interface
 * 
 * Visual interface for game replay functionality:
 * ✅ Recording controls with status indicators
 * ✅ Playback controls (play/pause/step/jump)
 * ✅ Interactive timeline with event markers
 * ✅ Event filtering and search
 * ✅ Session management (save/load/export/import)
 */

import React, { useState, useRef } from 'react';
import { useGameReplay } from '../../hooks/useGameReplay';

const GameReplayUI = ({ 
  roomId, 
  playerName, 
  className = '',
  isVisible = true,
  onClose = null 
}) => {
  const {
    // Recording
    startRecording,
    stopRecording,
    isRecording,

    // Playback
    startReplay,
    stopReplay,
    togglePause,
    stepForward,
    stepBackward,
    jumpToEvent,
    setPlaybackSpeed,

    // State
    replayState,
    currentSession,
    filteredEvents,

    // Timeline
    currentEventIndex,
    totalEvents,
    currentEvent,
    timelineProgress,

    // Filters
    setEventFilters,
    eventFilters,

    // Import/Export
    exportSession,
    importSession,

    // Session management
    sessions,
    saveSession,
    loadSession,
    deleteSession
  } = useGameReplay();

  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [showEventDetails, setShowEventDetails] = useState(false);
  const [exportData, setExportData] = useState('');
  const [importData, setImportData] = useState('');
  const fileInputRef = useRef(null);

  if (!isVisible) return null;

  // Handle session selection
  const handleLoadSession = (sessionId) => {
    const session = loadSession(sessionId);
    if (session) {
      startReplay(session);
      setSelectedSessionId(sessionId);
    }
  };

  // Handle export
  const handleExport = (session) => {
    const data = exportSession(session);
    setExportData(data);
    
    // Download as file
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `replay_${session.roomId}_${new Date(session.startTime).toISOString().slice(0, 19)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Handle import
  const handleImport = () => {
    if (importData.trim()) {
      try {
        const session = importSession(importData);
        setImportData('');
        alert(`Imported session: ${session.roomId} (${session.events.length} events)`);
      } catch (error) {
        alert(`Import failed: ${error.message}`);
      }
    }
  };

  // Handle file import
  const handleFileImport = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImportData(e.target.result);
      };
      reader.readAsText(file);
    }
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Format duration
  const formatDuration = (startTime, endTime) => {
    const duration = (endTime || Date.now()) - startTime;
    return `${(duration / 1000).toFixed(1)}s`;
  };

  // Get event type icon
  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'network_message': return '📡';
      case 'state_change': return '🔄';
      case 'user_action': return '👤';
      case 'system_event': return '⚙️';
      default: return '❓';
    }
  };

  // Get event type color
  const getEventColor = (eventType) => {
    switch (eventType) {
      case 'network_message': return '#3498db';
      case 'state_change': return '#2ecc71';
      case 'user_action': return '#e74c3c';
      case 'system_event': return '#f39c12';
      default: return '#95a5a6';
    }
  };

  return (
    <div className={`game-replay-ui ${className}`}>
      {/* Header */}
      <div className="replay-header">
        <h3>🎮 Game Replay Tool</h3>
        {onClose && (
          <button onClick={onClose} className="close-button">✕</button>
        )}
      </div>

      {/* Recording Controls */}
      <div className="recording-section">
        <h4>📹 Recording</h4>
        <div className="recording-controls">
          {!isRecording ? (
            <button
              onClick={() => startRecording(roomId, playerName)}
              disabled={!roomId || !playerName}
              className="record-button"
            >
              🔴 Start Recording
            </button>
          ) : (
            <button
              onClick={stopRecording}
              className="stop-button"
            >
              ⏹️ Stop Recording
            </button>
          )}
          
          {isRecording && (
            <div className="recording-status">
              <span className="recording-indicator">🔴 REC</span>
              <span>Events: {currentSession?.events.length || 0}</span>
            </div>
          )}
        </div>
      </div>

      {/* Session Management */}
      <div className="session-section">
        <h4>💾 Sessions</h4>
        
        {/* Session List */}
        <div className="session-list">
          {sessions.length === 0 ? (
            <p className="no-sessions">No replay sessions available</p>
          ) : (
            sessions.map(session => (
              <div key={session.id} className="session-item">
                <div className="session-info">
                  <div className="session-title">
                    {session.roomId} - {session.playerName}
                  </div>
                  <div className="session-meta">
                    {formatTime(session.startTime)} • 
                    {formatDuration(session.startTime, session.endTime)} • 
                    {session.events.length} events
                  </div>
                </div>
                
                <div className="session-actions">
                  <button
                    onClick={() => handleLoadSession(session.id)}
                    className="load-button"
                    disabled={replayState.isRecording}
                  >
                    ▶️ Play
                  </button>
                  <button
                    onClick={() => handleExport(session)}
                    className="export-button"
                  >
                    💾 Export
                  </button>
                  <button
                    onClick={() => deleteSession(session.id)}
                    className="delete-button"
                    title="Delete session"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Import/Export */}
        <div className="import-export">
          <div className="import-section">
            <h5>📥 Import Session</h5>
            <div className="import-controls">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="file-import-button"
              >
                📁 Choose File
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                onChange={handleFileImport}
                style={{ display: 'none' }}
              />
              <button
                onClick={handleImport}
                disabled={!importData.trim()}
                className="import-button"
              >
                📥 Import
              </button>
            </div>
            <textarea
              value={importData}
              onChange={(e) => setImportData(e.target.value)}
              placeholder="Paste JSON data here..."
              className="import-textarea"
              rows={3}
            />
          </div>
        </div>
      </div>

      {/* Playback Controls */}
      {replayState.isReplaying && currentSession && (
        <div className="playback-section">
          <h4>⏯️ Playback</h4>
          
          {/* Timeline */}
          <div className="timeline-container">
            <div className="timeline">
              <div 
                className="timeline-progress"
                style={{ width: `${timelineProgress * 100}%` }}
              />
              <div className="timeline-events">
                {filteredEvents.map((event, index) => (
                  <div
                    key={event.id}
                    className={`timeline-event ${index === currentEventIndex ? 'current' : ''}`}
                    style={{
                      left: `${(event.sequence / totalEvents) * 100}%`,
                      backgroundColor: getEventColor(event.type)
                    }}
                    title={`${event.type}: ${event.data?.event || event.data?.type || 'Unknown'}`}
                    onClick={() => jumpToEvent(index)}
                  >
                    {getEventIcon(event.type)}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="timeline-info">
              Event {currentEventIndex + 1} of {totalEvents}
              {currentEvent && (
                <span className="current-event-info">
                  - {currentEvent.type}: {currentEvent.data?.event || currentEvent.data?.type}
                </span>
              )}
            </div>
          </div>

          {/* Playback Controls */}
          <div className="playback-controls">
            <button onClick={stepBackward} title="Step Back">⏮️</button>
            <button onClick={togglePause}>
              {replayState.isPaused ? '▶️' : '⏸️'}
            </button>
            <button onClick={stepForward} title="Step Forward">⏭️</button>
            <button onClick={stopReplay} title="Stop">⏹️</button>
            
            <div className="speed-control">
              <label>Speed:</label>
              <select
                value={replayState.playbackSpeed}
                onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
              >
                <option value={0.25}>0.25x</option>
                <option value={0.5}>0.5x</option>
                <option value={1}>1x</option>
                <option value={2}>2x</option>
                <option value={4}>4x</option>
              </select>
            </div>
          </div>

          {/* Event Filters */}
          <div className="filters-section">
            <h5>🔍 Event Filters</h5>
            <div className="filter-checkboxes">
              <label>
                <input
                  type="checkbox"
                  checked={eventFilters.showNetworkMessages}
                  onChange={(e) => setEventFilters({ showNetworkMessages: e.target.checked })}
                />
                📡 Network Messages
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={eventFilters.showStateChanges}
                  onChange={(e) => setEventFilters({ showStateChanges: e.target.checked })}
                />
                🔄 State Changes
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={eventFilters.showUserActions}
                  onChange={(e) => setEventFilters({ showUserActions: e.target.checked })}
                />
                👤 User Actions
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={eventFilters.showSystemEvents}
                  onChange={(e) => setEventFilters({ showSystemEvents: e.target.checked })}
                />
                ⚙️ System Events
              </label>
            </div>
          </div>

          {/* Current Event Details */}
          {currentEvent && (
            <div className="event-details">
              <h5>
                📋 Current Event
                <button
                  onClick={() => setShowEventDetails(!showEventDetails)}
                  className="toggle-details"
                >
                  {showEventDetails ? '▼' : '▶'}
                </button>
              </h5>
              
              {showEventDetails && (
                <pre className="event-data">
                  {JSON.stringify(currentEvent, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      <style jsx>{`
        .game-replay-ui {
          position: fixed;
          top: 20px;
          right: 20px;
          width: 400px;
          max-height: 90vh;
          background: rgba(255, 255, 255, 0.98);
          border: 1px solid #ddd;
          border-radius: 8px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
          z-index: 2000;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          overflow-y: auto;
        }

        .replay-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          border-bottom: 1px solid #eee;
          background: #f8f9fa;
          border-radius: 8px 8px 0 0;
        }

        .replay-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .close-button {
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: #666;
          padding: 4px;
        }

        .close-button:hover {
          color: #000;
        }

        .recording-section,
        .session-section,
        .playback-section {
          padding: 16px;
          border-bottom: 1px solid #eee;
        }

        .recording-section h4,
        .session-section h4,
        .playback-section h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
        }

        .recording-controls {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .record-button,
        .stop-button {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .record-button {
          background: #e74c3c;
          color: white;
        }

        .record-button:hover:not(:disabled) {
          background: #c0392b;
        }

        .record-button:disabled {
          background: #bdc3c7;
          cursor: not-allowed;
        }

        .stop-button {
          background: #34495e;
          color: white;
        }

        .stop-button:hover {
          background: #2c3e50;
        }

        .recording-status {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
        }

        .recording-indicator {
          color: #e74c3c;
          font-weight: bold;
          animation: blink 1s infinite;
        }

        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }

        .session-list {
          max-height: 200px;
          overflow-y: auto;
          margin-bottom: 12px;
        }

        .no-sessions {
          text-align: center;
          color: #666;
          font-style: italic;
          margin: 20px 0;
        }

        .session-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px;
          border: 1px solid #eee;
          border-radius: 4px;
          margin-bottom: 8px;
          background: #fafafa;
        }

        .session-info {
          flex: 1;
        }

        .session-title {
          font-weight: 500;
          font-size: 13px;
          margin-bottom: 2px;
        }

        .session-meta {
          font-size: 11px;
          color: #666;
        }

        .session-actions {
          display: flex;
          gap: 4px;
        }

        .load-button,
        .export-button,
        .delete-button {
          padding: 4px 8px;
          border: none;
          border-radius: 3px;
          font-size: 11px;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .load-button {
          background: #27ae60;
          color: white;
        }

        .load-button:hover:not(:disabled) {
          background: #229954;
        }

        .load-button:disabled {
          background: #bdc3c7;
          cursor: not-allowed;
        }

        .export-button {
          background: #3498db;
          color: white;
        }

        .export-button:hover {
          background: #2980b9;
        }

        .delete-button {
          background: #e74c3c;
          color: white;
        }

        .delete-button:hover {
          background: #c0392b;
        }

        .import-export {
          border-top: 1px solid #eee;
          padding-top: 12px;
        }

        .import-section h5 {
          margin: 0 0 8px 0;
          font-size: 12px;
          font-weight: 600;
        }

        .import-controls {
          display: flex;
          gap: 8px;
          margin-bottom: 8px;
        }

        .file-import-button,
        .import-button {
          padding: 6px 12px;
          border: 1px solid #ddd;
          border-radius: 3px;
          font-size: 12px;
          cursor: pointer;
          background: white;
        }

        .file-import-button:hover,
        .import-button:hover:not(:disabled) {
          background: #f8f9fa;
        }

        .import-button:disabled {
          background: #f8f9fa;
          color: #999;
          cursor: not-allowed;
        }

        .import-textarea {
          width: 100%;
          padding: 8px;
          border: 1px solid #ddd;
          border-radius: 3px;
          font-size: 11px;
          font-family: monospace;
          resize: vertical;
        }

        .timeline-container {
          margin-bottom: 16px;
        }

        .timeline {
          position: relative;
          height: 40px;
          background: #f0f0f0;
          border-radius: 4px;
          margin-bottom: 8px;
          cursor: pointer;
        }

        .timeline-progress {
          height: 100%;
          background: linear-gradient(90deg, #3498db, #2ecc71);
          border-radius: 4px;
          transition: width 0.1s ease;
        }

        .timeline-events {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
        }

        .timeline-event {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          width: 20px;
          height: 20px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          cursor: pointer;
          border: 2px solid white;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        }

        .timeline-event.current {
          border-color: #f39c12;
          box-shadow: 0 0 8px rgba(243, 156, 18, 0.6);
        }

        .timeline-info {
          font-size: 12px;
          color: #666;
        }

        .current-event-info {
          color: #333;
          font-weight: 500;
        }

        .playback-controls {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 16px;
        }

        .playback-controls button {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          font-size: 14px;
        }

        .playback-controls button:hover {
          background: #f8f9fa;
        }

        .speed-control {
          display: flex;
          align-items: center;
          gap: 4px;
          margin-left: auto;
          font-size: 12px;
        }

        .speed-control select {
          padding: 4px;
          border: 1px solid #ddd;
          border-radius: 3px;
          font-size: 12px;
        }

        .filters-section h5 {
          margin: 0 0 8px 0;
          font-size: 12px;
          font-weight: 600;
        }

        .filter-checkboxes {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .filter-checkboxes label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          cursor: pointer;
        }

        .event-details {
          margin-top: 16px;
          border-top: 1px solid #eee;
          padding-top: 12px;
        }

        .event-details h5 {
          margin: 0 0 8px 0;
          font-size: 12px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .toggle-details {
          background: none;
          border: none;
          cursor: pointer;
          font-size: 12px;
          color: #666;
        }

        .event-data {
          background: #f8f9fa;
          border: 1px solid #e9ecef;
          border-radius: 4px;
          padding: 8px;
          font-size: 11px;
          max-height: 200px;
          overflow-y: auto;
          white-space: pre-wrap;
          word-break: break-all;
        }

        @media (max-width: 768px) {
          .game-replay-ui {
            top: 10px;
            right: 10px;
            left: 10px;
            width: auto;
          }
        }
      `}</style>
    </div>
  );
};

export default GameReplayUI;