# Lobby Real-time Updates Testing Guide

This document describes the comprehensive test suite for the lobby real-time update functionality.

## Test Coverage

### 1. Backend Unit Tests (`test_lobby_realtime_updates.py`)

Tests the core lobby functionality at the use case level:

#### Room Creation Visibility
- ✅ New rooms appear immediately in room list
- ✅ Multiple lobby users see the same rooms
- ✅ Room creation events are properly mapped

#### Player Count Updates
- ✅ Player count increases when users join
- ✅ Player count decreases when users leave
- ✅ Concurrent player updates are handled correctly

#### Room State Changes
- ✅ Room status changes (waiting/in-game) are reflected
- ✅ Full rooms can be filtered from the list
- ✅ Deleted rooms are removed from lobby

#### Edge Cases
- ✅ Network delays are handled gracefully
- ✅ Empty lobby state is handled properly
- ✅ Pagination works with many rooms

### 2. Frontend Tests (`LobbyPage.test.jsx`)

Tests the React component's handling of WebSocket events:

#### UI Updates
- ✅ Room list updates when `room_list_update` event is received
- ✅ Player counts update in real-time
- ✅ Room status badges (FULL, In Game) display correctly

#### User Interactions
- ✅ Create room button triggers correct WebSocket message
- ✅ Join room sends proper request
- ✅ Refresh button requests updated room list

#### Error Handling
- ✅ Network delays show loading state
- ✅ Empty lobby shows appropriate message
- ✅ Concurrent updates don't cause UI issues

### 3. Integration Tests (`test_lobby_websocket_integration.py`)

Tests the complete WebSocket flow:

#### WebSocket Communication
- ✅ Room creation broadcasts to all lobby connections
- ✅ Player join/leave updates are broadcasted
- ✅ Room-specific broadcasts don't leak to lobby

#### Multi-client Scenarios
- ✅ Multiple clients see consistent room state
- ✅ Concurrent operations are handled correctly
- ✅ Connection isolation is maintained

### 4. Dispatcher Tests (`test_lobby_dispatcher.py`)

Tests the WebSocket event dispatcher specifically:

#### Event Naming
- ✅ `get_rooms` returns `room_list_update` event (not `room_list`)
- ✅ Both `get_rooms` and `request_room_list` work identically
- ✅ Event data structure matches frontend expectations

#### Request Handling
- ✅ Filters (include_private, include_full) are passed correctly
- ✅ Pagination parameters work properly
- ✅ Sorting options are handled

## Running the Tests

### Run All Lobby Tests
```bash
cd backend
python tests/test_lobby_suite.py
```

### Run Individual Test Files
```bash
# Backend unit tests
pytest tests/application/test_lobby_realtime_updates.py -v

# Frontend tests (from frontend directory)
cd frontend
npm test src/pages/__tests__/LobbyPage.test.jsx

# Integration tests
cd backend
pytest tests/integration/test_lobby_websocket_integration.py -v

# Dispatcher tests
pytest tests/application/websocket/test_lobby_dispatcher.py -v
```

### Run with Coverage
```bash
pytest tests/application/test_lobby_realtime_updates.py --cov=application.use_cases.lobby --cov-report=html
```

## Key Test Patterns

### 1. Mocking WebSocket Connections
```python
class MockWebSocket:
    def __init__(self, room_id: str = "lobby"):
        self.room_id = room_id
        self.sent_messages = []
        
    async def send_json(self, data: dict):
        self.sent_messages.append(data)
```

### 2. Testing Real-time Updates
```python
# Simulate room creation
response = await dispatcher.dispatch("create_room", {...}, context)

# Verify update is visible to other clients
list_response = await dispatcher.dispatch("get_rooms", {}, other_context)
assert new_room in list_response["data"]["rooms"]
```

### 3. Frontend Event Testing
```javascript
// Emit WebSocket event
act(() => {
  emitEvent('room_list_update', {
    rooms: [/* room data */],
    total_count: 1
  });
});

// Verify UI update
await waitFor(() => {
  expect(screen.getByText("Room Name")).toBeInTheDocument();
});
```

## Common Issues and Solutions

### Issue: Frontend not updating when rooms change
**Solution**: Ensure backend sends `room_list_update` event (not `room_list`)

### Issue: Player counts not accurate
**Solution**: Use proper room state calculation in `list_active` method

### Issue: Concurrent updates cause race conditions
**Solution**: Use proper async/await and transaction handling in use cases

### Issue: Tests fail intermittently
**Solution**: Add proper cleanup in test fixtures, clear WebSocket connections

## Future Enhancements

1. **Performance Testing**: Add tests for handling 100+ concurrent lobby users
2. **Stress Testing**: Test rapid room creation/deletion cycles
3. **Network Failure**: Test recovery from WebSocket disconnections
4. **Security**: Test that private rooms are properly filtered
5. **Analytics**: Add metrics collection for lobby usage patterns