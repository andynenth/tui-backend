# Manual Integration Tests

This directory contains manual integration tests for the Liap Tui backend system. These tests are designed to be run manually during development and debugging to verify system behavior.

## Test Files

### **Bot Management Tests**
- **`test_bot_replacement_flow.py`** - Comprehensive test of bot replacement system
  - Tests bot assignment, replacement logic, and state transitions
  - Verifies proper cleanup when bots are replaced with human players

### **Connection Tests**
- **`test_connection.py`** - Backend-frontend data connection verification
  - Tests data format and flow between backend and frontend services
  - Validates JSON serialization and WebSocket communication
- **`test_connection_tracking.py`** - Connection state tracking tests
  - Verifies player connection/disconnection tracking
  - Tests reconnection handling and state persistence

### **API Tests**
- **`test_rest_endpoints.py`** - Python REST endpoint tests
  - Tests all REST API endpoints for proper responses
  - Validates error handling and data formats

### **Room Management Tests**
- **`test_room_not_found.py`** - Room error handling tests
  - Tests behavior when accessing non-existent rooms
  - Validates proper error responses and cleanup
- **`test_websocket_room_management.py`** - WebSocket room management tests
  - Tests room creation, joining, and leaving via WebSocket
  - Verifies proper state synchronization across room operations

### **State Management Tests**
- **`test_state_sync.py`** - State synchronization tests
  - Tests game state synchronization between frontend and backend
  - Verifies proper handling of state changes and broadcasts

### **Debug Tools**
- **`test_websocket_debug.py`** - WebSocket debugging utilities
  - Debug tools for WebSocket data flow analysis
  - Useful for troubleshooting connection issues

## Running Manual Tests

### Prerequisites
```bash
# From project root
cd backend
source venv/bin/activate  # Activate Python virtual environment
```

### Running Individual Tests
```bash
# Run a specific test
python tests/integration/manual/test_connection.py

# Run with verbose output
python -v tests/integration/manual/test_bot_replacement_flow.py
```

### Running All Manual Tests
```bash
# Run all manual integration tests
for test in tests/integration/manual/test_*.py; do
    echo "Running $test..."
    python "$test"
    echo "---"
done
```

## Test Environment Setup

These tests require:
1. **Backend server running** - Start with `./start.sh` from project root
2. **Database access** - Tests may interact with the game database
3. **Network connectivity** - For WebSocket and REST API tests

## Expected Output

Each test provides:
- ✅ Success indicators for passing tests
- ❌ Failure indicators with detailed error messages
- 📊 Summary reports with test statistics
- 🔍 Debug information for troubleshooting

## Integration with Automated Testing

While these are manual tests, they can be integrated into CI/CD pipelines:
```bash
# Example CI integration
npm run backend:start &
sleep 5  # Wait for backend to start
python tests/integration/manual/test_connection.py
```

## Adding New Manual Tests

When creating new manual tests:
1. Follow the existing naming pattern: `test_[feature]_[type].py`
2. Include proper docstrings explaining the test purpose
3. Add success/failure indicators for clear output
4. Update this README with the new test description

## Troubleshooting

Common issues:
- **Connection errors**: Ensure backend server is running
- **Import errors**: Verify Python virtual environment is activated
- **Database errors**: Check database connectivity and permissions
- **Port conflicts**: Ensure no other services are using required ports