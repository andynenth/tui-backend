/**
 * 🔄 **SyncCheckerUI Component** - Phase 6.3 Visual Interface
 * 
 * Visual interface for sync checking functionality:
 * ✅ Real-time sync status monitoring
 * ✅ Desync event tracking and alerts
 * ✅ Historical sync data visualization
 * ✅ Recovery action suggestions
 * ✅ Alert configuration and management
 */

import React, { useState } from 'react';
import { useSyncChecker } from '../../hooks/useSyncChecker';

const SyncCheckerUI = ({ roomId, playerName, isVisible, onClose }) => {
  const {
    startChecking,
    stopChecking,
    checkSync,
    updateSettings,
    syncState,
    isActive,
    syncHistory,
    activeDesyncs,
    resolvedDesyncs,
    currentSyncStatus,
    lastCheckTime,
    totalChecks,
    totalDesyncs,
    averageResolutionTime,
    successRate,
    resolveDesync,
    clearHistory,
    exportData,
    activeAlerts,
    dismissAlert
  } = useSyncChecker();

  const [activeTab, setActiveTab] = useState('status');

  if (!isVisible) return null;

  const handleStartChecking = () => {
    if (roomId && playerName) {
      startChecking(roomId, playerName);
    }
  };

  const handleSettingsChange = (key, value) => {
    updateSettings({
      [key]: value
    });
  };

  const handleAlertSettingsChange = (key, value) => {
    updateSettings({
      alertSettings: {
        ...syncState.alertSettings,
        [key]: value
      }
    });
  };

  const handleExport = () => {
    const data = exportData();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sync-check-${roomId}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getStatusColor = (status) => {
    const colors = {
      synced: 'text-green-600 bg-green-50',
      warning: 'text-yellow-600 bg-yellow-50',
      desync: 'text-orange-600 bg-orange-50',
      critical: 'text-red-600 bg-red-50'
    };
    return colors[status] || 'text-gray-600 bg-gray-50';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: 'text-blue-600 bg-blue-50',
      medium: 'text-yellow-600 bg-yellow-50',
      high: 'text-orange-600 bg-orange-50',
      critical: 'text-red-600 bg-red-50'
    };
    return colors[severity] || 'text-gray-600 bg-gray-50';
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatDuration = (ms) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">
              🔄 Sync Checker
            </h2>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(currentSyncStatus)}`}>
              {currentSyncStatus.toUpperCase()}
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${isActive ? 'bg-green-500' : 'bg-gray-400'}`}></span>
              <span className="text-sm text-gray-600">
                {isActive ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Active Alerts */}
        {activeAlerts.length > 0 && (
          <div className="p-4 border-b border-gray-200 bg-yellow-50">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-yellow-800">Active Alerts</h3>
              <span className="text-xs text-yellow-600">{activeAlerts.length} active</span>
            </div>
            <div className="space-y-2 max-h-20 overflow-y-auto">
              {activeAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`flex items-center justify-between p-2 rounded text-sm ${getSeverityColor(alert.severity)}`}
                >
                  <span>{alert.message}</span>
                  <button
                    onClick={() => dismissAlert(alert.id)}
                    className="text-xs underline hover:no-underline ml-2"
                  >
                    Dismiss
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {!isActive ? (
                <button
                  onClick={handleStartChecking}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  🔄 Start Checking
                </button>
              ) : (
                <button
                  onClick={stopChecking}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  ⏹️ Stop Checking
                </button>
              )}
              
              <button
                onClick={checkSync}
                disabled={!isActive}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                🔍 Check Now
              </button>
              
              <button
                onClick={clearHistory}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                🗑️ Clear History
              </button>
              
              <button
                onClick={handleExport}
                disabled={totalChecks === 0}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                💾 Export Data
              </button>
            </div>

            {/* Statistics */}
            <div className="flex items-center space-x-6 text-sm text-gray-600">
              <div>Checks: <span className="font-medium">{totalChecks}</span></div>
              <div>Desyncs: <span className="font-medium text-red-600">{totalDesyncs}</span></div>
              <div>Success: <span className="font-medium text-green-600">{successRate.toFixed(1)}%</span></div>
              <div>Avg Resolution: <span className="font-medium">{formatDuration(averageResolutionTime)}</span></div>
              {lastCheckTime > 0 && (
                <div>Last Check: <span className="font-medium">{formatTime(lastCheckTime)}</span></div>
              )}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-4">
            {[
              { id: 'status', label: 'Status', count: activeDesyncs.length },
              { id: 'history', label: 'History', count: syncHistory.length },
              { id: 'desyncs', label: 'Desyncs', count: activeDesyncs.length + resolvedDesyncs.length },
              { id: 'settings', label: 'Settings', count: null }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
                {tab.count !== null && (
                  <span className="ml-2 bg-gray-200 text-gray-600 px-2 py-1 rounded-full text-xs">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Status Tab */}
          {activeTab === 'status' && (
            <div className="space-y-6">
              {/* Current Status */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Current Status</h3>
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{totalChecks}</div>
                    <div className="text-sm text-gray-600">Total Checks</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">{activeDesyncs.length}</div>
                    <div className="text-sm text-gray-600">Active Desyncs</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{successRate.toFixed(1)}%</div>
                    <div className="text-sm text-gray-600">Success Rate</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">{formatDuration(averageResolutionTime)}</div>
                    <div className="text-sm text-gray-600">Avg Resolution</div>
                  </div>
                </div>
              </div>

              {/* Active Desyncs */}
              {activeDesyncs.length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Active Desyncs</h3>
                  <div className="space-y-3">
                    {activeDesyncs.map((desync) => (
                      <div
                        key={desync.id}
                        className={`p-4 rounded-lg border ${getSeverityColor(desync.severity)}`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">Desync #{desync.id.slice(-8)}</span>
                            <span className="text-xs px-2 py-1 rounded bg-white bg-opacity-50">
                              {desync.severity}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600">
                            {formatTime(desync.startTime)} • Duration: {formatDuration(Date.now() - desync.startTime)}
                          </div>
                        </div>
                        <div className="text-sm mb-2">
                          <strong>Affected Fields:</strong> {desync.affectedFields.join(', ')}
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="text-xs text-gray-600">
                            Impact: {desync.impact.userExperienceImpact} • 
                            Blocking: {desync.impact.gameplayBlocking ? 'Yes' : 'No'} • 
                            Data: {desync.impact.dataIntegrity}
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => resolveDesync(desync.id, 'manual_fix', 'Manually resolved by user')}
                              className="text-xs bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700"
                            >
                              Resolve
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Sync History</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {syncHistory.slice(-50).reverse().map((point) => (
                  <div
                    key={point.id}
                    className={`p-3 rounded border ${point.isSync ? 'bg-green-50 border-green-200' : getSeverityColor(point.severity)}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        <span className={`w-2 h-2 rounded-full ${point.isSync ? 'bg-green-500' : 'bg-red-500'}`}></span>
                        <span className="font-medium text-sm">{point.fieldPath}</span>
                        <span className="text-xs text-gray-500">{point.context.phase}</span>
                      </div>
                      <span className="text-xs text-gray-500">{formatTime(point.timestamp)}</span>
                    </div>
                    {!point.isSync && (
                      <div className="grid grid-cols-2 gap-4 text-xs mt-2">
                        <div>
                          <div className="font-medium text-green-700">Frontend:</div>
                          <pre className="bg-white bg-opacity-50 p-1 rounded mt-1 overflow-auto max-h-16">
                            {JSON.stringify(point.frontendValue, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <div className="font-medium text-blue-700">Backend:</div>
                          <pre className="bg-white bg-opacity-50 p-1 rounded mt-1 overflow-auto max-h-16">
                            {JSON.stringify(point.backendValue, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Desyncs Tab */}
          {activeTab === 'desyncs' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Desync Events</h3>
              <div className="space-y-4">
                {/* Active Desyncs */}
                {activeDesyncs.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-red-600 mb-2">Active ({activeDesyncs.length})</h4>
                    <div className="space-y-2">
                      {activeDesyncs.map((desync) => (
                        <div key={desync.id} className={`p-3 rounded border ${getSeverityColor(desync.severity)}`}>
                          <div className="flex items-center justify-between">
                            <span className="font-medium">#{desync.id.slice(-8)}</span>
                            <span className="text-sm">{formatTime(desync.startTime)}</span>
                          </div>
                          <div className="text-sm mt-1">{desync.affectedFields.join(', ')}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Resolved Desyncs */}
                {resolvedDesyncs.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-green-600 mb-2">Resolved ({resolvedDesyncs.length})</h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {resolvedDesyncs.slice(-20).reverse().map((desync) => (
                        <div key={desync.id} className="p-3 rounded border border-green-200 bg-green-50">
                          <div className="flex items-center justify-between">
                            <span className="font-medium">#{desync.id.slice(-8)}</span>
                            <span className="text-sm">{formatDuration((desync.endTime || Date.now()) - desync.startTime)}</span>
                          </div>
                          <div className="text-sm mt-1">{desync.affectedFields.join(', ')}</div>
                          {desync.resolution && (
                            <div className="text-xs text-green-700 mt-1">
                              {desync.resolution.method}: {desync.resolution.description}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Settings Tab */}
          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Check Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Check Interval (ms)</label>
                    <input
                      type="number"
                      value={syncState.checkInterval}
                      onChange={(e) => handleSettingsChange('checkInterval', parseInt(e.target.value))}
                      min="500"
                      max="10000"
                      step="500"
                      className="mt-1 block w-32 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Tolerance (ms)</label>
                    <input
                      type="number"
                      value={syncState.toleranceMs}
                      onChange={(e) => handleSettingsChange('toleranceMs', parseInt(e.target.value))}
                      min="0"
                      max="1000"
                      step="10"
                      className="mt-1 block w-32 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Alert Settings</h3>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={syncState.alertSettings.enableVisualAlerts}
                      onChange={(e) => handleAlertSettingsChange('enableVisualAlerts', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Enable Visual Alerts</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={syncState.alertSettings.enableAudioAlerts}
                      onChange={(e) => handleAlertSettingsChange('enableAudioAlerts', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Enable Audio Alerts</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={syncState.alertSettings.enableAutoRecovery}
                      onChange={(e) => handleAlertSettingsChange('enableAutoRecovery', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Enable Auto Recovery</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={syncState.alertSettings.criticalOnly}
                      onChange={(e) => handleAlertSettingsChange('criticalOnly', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Critical Alerts Only</span>
                  </label>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .space-x-2 > * + * {
          margin-left: 0.5rem;
        }
        .space-x-3 > * + * {
          margin-left: 0.75rem;
        }
        .space-x-4 > * + * {
          margin-left: 1rem;
        }
        .space-x-6 > * + * {
          margin-left: 1.5rem;
        }
        .space-x-8 > * + * {
          margin-left: 2rem;
        }
        .space-y-2 > * + * {
          margin-top: 0.5rem;
        }
        .space-y-3 > * + * {
          margin-top: 0.75rem;
        }
        .space-y-4 > * + * {
          margin-top: 1rem;
        }
        .space-y-6 > * + * {
          margin-top: 1.5rem;
        }
      `}</style>
    </div>
  );
};

export default SyncCheckerUI;