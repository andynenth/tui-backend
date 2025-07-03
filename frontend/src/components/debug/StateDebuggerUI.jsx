/**
 * 🔍 **StateDebuggerUI Component** - Phase 6.2 Visual Interface
 * 
 * Visual interface for state debugging functionality:
 * ✅ Live state monitoring controls
 * ✅ State comparison viewer with diff highlighting
 * ✅ WebSocket message filtering and viewer
 * ✅ Performance metrics dashboard
 * ✅ Export functionality for debugging sessions
 */

import React from 'react';
import { useStateDebugger } from '../../hooks/useStateDebugger';

const StateDebuggerUI = ({ roomId, playerName, isVisible, onClose }) => {
  const {
    startDebugging,
    stopDebugging,
    captureState,
    clearData,
    debuggerState,
    isActive,
    stateHistory,
    currentFrontendState,
    currentBackendState,
    stateDifferences,
    recentMessages,
    filteredMessages,
    setMessageFilters,
    performanceMetrics,
    viewOptions,
    setViewOptions,
    exportData,
    totalSnapshots,
    totalMessages,
    criticalDifferences,
    averageLatency
  } = useStateDebugger();

  if (!isVisible) return null;

  const handleStartDebugging = () => {
    if (roomId && playerName) {
      startDebugging(roomId, playerName);
    }
  };

  const handleFilterChange = (filterName, value) => {
    setMessageFilters({ [filterName]: value });
  };

  const handleViewOptionChange = (optionName, value) => {
    setViewOptions({ [optionName]: value });
  };

  const handleExport = () => {
    const data = exportData();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `state-debug-${roomId}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatLatency = (latency) => {
    return latency ? `${latency.toFixed(1)}ms` : 'N/A';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'text-red-600 bg-red-50',
      high: 'text-orange-600 bg-orange-50',
      medium: 'text-yellow-600 bg-yellow-50',
      low: 'text-blue-600 bg-blue-50'
    };
    return colors[severity] || 'text-gray-600 bg-gray-50';
  };

  const formatValue = (value) => {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">
              🔍 State Debugger
            </h2>
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

        {/* Controls */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {!isActive ? (
                <button
                  onClick={handleStartDebugging}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  🔍 Start Debugging
                </button>
              ) : (
                <button
                  onClick={stopDebugging}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  ⏹️ Stop Debugging
                </button>
              )}
              
              <button
                onClick={captureState}
                disabled={!isActive}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                📸 Capture State
              </button>
              
              <button
                onClick={clearData}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                🗑️ Clear Data
              </button>
              
              <button
                onClick={handleExport}
                disabled={totalSnapshots === 0}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                💾 Export Session
              </button>
            </div>

            {/* Statistics */}
            <div className="flex items-center space-x-6 text-sm text-gray-600">
              <div>Snapshots: <span className="font-medium">{totalSnapshots}</span></div>
              <div>Messages: <span className="font-medium">{totalMessages}</span></div>
              <div>Critical Diffs: <span className="font-medium text-red-600">{criticalDifferences}</span></div>
              <div>Avg Latency: <span className="font-medium">{formatLatency(averageLatency)}</span></div>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden flex">
          {/* Left Panel - View Options & Filters */}
          <div className="w-80 border-r border-gray-200 p-4 overflow-y-auto">
            <div className="space-y-6">
              {/* View Options */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">View Options</h3>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={viewOptions.showStateComparison}
                      onChange={(e) => handleViewOptionChange('showStateComparison', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Show State Comparison</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={viewOptions.showMessages}
                      onChange={(e) => handleViewOptionChange('showMessages', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Show Messages</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={viewOptions.showPerformance}
                      onChange={(e) => handleViewOptionChange('showPerformance', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Show Performance</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={viewOptions.autoUpdate}
                      onChange={(e) => handleViewOptionChange('autoUpdate', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Auto Update</span>
                  </label>
                </div>
              </div>

              {/* Message Filters */}
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">Message Filters</h3>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={debuggerState.messageFilters.showIncoming}
                      onChange={(e) => handleFilterChange('showIncoming', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Incoming</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={debuggerState.messageFilters.showOutgoing}
                      onChange={(e) => handleFilterChange('showOutgoing', e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Outgoing</span>
                  </label>
                  <div>
                    <label className="text-sm text-gray-700">Event Filter:</label>
                    <input
                      type="text"
                      value={debuggerState.messageFilters.eventFilter}
                      onChange={(e) => handleFilterChange('eventFilter', e.target.value)}
                      placeholder="e.g. phase_change"
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              {viewOptions.showPerformance && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-3">Performance</h3>
                  <div className="space-y-2 text-xs">
                    <div className="bg-gray-50 p-2 rounded">
                      <div className="font-medium">State Update</div>
                      <div>Avg: {formatLatency(performanceMetrics.stateUpdateLatency.average)}</div>
                      <div>Min: {formatLatency(performanceMetrics.stateUpdateLatency.min)}</div>
                      <div>Max: {formatLatency(performanceMetrics.stateUpdateLatency.max)}</div>
                    </div>
                    <div className="bg-gray-50 p-2 rounded">
                      <div className="font-medium">WebSocket</div>
                      <div>Avg: {formatLatency(performanceMetrics.websocketLatency.average)}</div>
                      <div>Min: {formatLatency(performanceMetrics.websocketLatency.min)}</div>
                      <div>Max: {formatLatency(performanceMetrics.websocketLatency.max)}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Data Viewer */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Tab Navigation */}
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-4">
                {viewOptions.showStateComparison && (
                  <button className="py-3 px-1 border-b-2 border-blue-500 text-blue-600 font-medium text-sm">
                    State Comparison
                  </button>
                )}
                {viewOptions.showMessages && (
                  <button className="py-3 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm">
                    Messages ({filteredMessages.length})
                  </button>
                )}
              </nav>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {/* State Comparison View */}
              {viewOptions.showStateComparison && (
                <div className="space-y-4">
                  {/* State Differences */}
                  {stateDifferences.length > 0 && (
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 mb-3">
                        State Differences ({stateDifferences.length})
                      </h4>
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {stateDifferences.map((diff, index) => (
                          <div
                            key={index}
                            className={`p-3 rounded-lg border ${getSeverityColor(diff.severity)}`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium text-sm">{diff.path}</span>
                              <span className="text-xs px-2 py-1 rounded bg-white bg-opacity-50">
                                {diff.severity} • {diff.type}
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-xs">
                              <div>
                                <div className="font-medium text-green-700">Frontend:</div>
                                <pre className="bg-white bg-opacity-50 p-2 rounded mt-1 overflow-auto max-h-20">
                                  {formatValue(diff.frontendValue)}
                                </pre>
                              </div>
                              <div>
                                <div className="font-medium text-blue-700">Backend:</div>
                                <pre className="bg-white bg-opacity-50 p-2 rounded mt-1 overflow-auto max-h-20">
                                  {formatValue(diff.backendValue)}
                                </pre>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Current States */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 mb-3">Frontend State</h4>
                      <pre className="bg-gray-50 p-4 rounded-lg text-xs overflow-auto max-h-96 border">
                        {formatValue(currentFrontendState)}
                      </pre>
                    </div>
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 mb-3">Backend State</h4>
                      <pre className="bg-gray-50 p-4 rounded-lg text-xs overflow-auto max-h-96 border">
                        {formatValue(currentBackendState)}
                      </pre>
                    </div>
                  </div>
                </div>
              )}

              {/* Messages View */}
              {viewOptions.showMessages && !viewOptions.showStateComparison && (
                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">
                    WebSocket Messages ({filteredMessages.length})
                  </h4>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {filteredMessages.map((message) => (
                      <div
                        key={message.id}
                        className={`p-3 rounded-lg border ${
                          message.direction === 'incoming' 
                            ? 'bg-blue-50 border-blue-200' 
                            : 'bg-green-50 border-green-200'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className={`w-2 h-2 rounded-full ${
                              message.direction === 'incoming' ? 'bg-blue-500' : 'bg-green-500'
                            }`}></span>
                            <span className="font-medium text-sm">{message.event}</span>
                            <span className="text-xs text-gray-500">
                              {message.direction}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <pre className="bg-white bg-opacity-50 p-2 rounded text-xs overflow-auto max-h-32">
                          {formatValue(message.data)}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
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

export default StateDebuggerUI;