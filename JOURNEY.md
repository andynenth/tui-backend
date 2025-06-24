The Issue: The "Create Room" button appeared to do nothing when clicked.

  Root Causes:
  1. Frontend Modal State Bug: Debug console.log statements in the Modal component were causing continuous
  re-rendering loops, making the modal flicker between open/closed states
  2. Backend-Frontend Mismatch: The frontend was sending WebSocket events (create_room, get_rooms) but the
  backend only had REST API endpoints - missing WebSocket event handlers

  How I Fixed It

  Phase 1: Frontend Modal Issues

  1. Identified re-rendering loop caused by debug logs in Modal.jsx lines 69 and 73
  2. Removed debug console.log statements that were triggering continuous component re-renders
  3. Applied useMemo optimization to useSocket hook to prevent unnecessary object recreation

  Phase 2: Simplified UX

  1. Removed modal complexity - you suggested directly creating rooms instead of showing a modal
  2. Streamlined button behavior: Click → Create room → Navigate (no modal popup)
  3. Added loading state: Button shows "Creating..." while processing

  Phase 3: Backend WebSocket Handlers

  1. Discovered missing handlers: Backend had REST API (POST /create-room) but no WebSocket event handlers
  2. Added WebSocket event handlers in /backend/api/routes/ws.py:
    - create_room: Creates room and responds with room_created event
    - get_rooms: Returns current room list as room_list event
  3. Integrated with existing room creation logic and lobby notifications

  Key Insight

  The problem wasn't the button itself - it was a communication protocol mismatch. Frontend expected WebSocket
   bidirectional communication, but backend only provided REST API endpoints. Adding the missing WebSocket
  handlers bridged this gap.

---

  The Issue: The "Create Room" button appeared to do nothing - rooms were created on the backend but the frontend
  couldn't display them properly.

  Root Cause Analysis

  There were actually 3 cascading issues:

  1. Missing WebSocket Handlers: Frontend sent create_room and get_room_state WebSocket events, but backend
  only had REST API endpoints
  2. Navigation Logic Bug: Two room_created events (direct response + lobby broadcast) caused navigation to
  wrong room ID
  3. Missing Host Information: Backend didn't include is_host field in player data, so frontend couldn't
  detect host status

  The Fix

  Phase 1: Added Missing WebSocket Handlers
  # backend/api/routes/ws.py
  elif event_name == "create_room":
      room_id = room_manager.create_room(player_name)
      await registered_ws.send_json({
          "event": "room_created",
          "data": {"room_id": room_id, "success": true}
      })

  elif event_name == "get_room_state":
      room = room_manager.get_room(room_id)
      await registered_ws.send_json({
          "event": "room_update",
          "data": room.summary()
      })

  Phase 2: Fixed Navigation Logic
  // frontend/src/pages/LobbyPage.jsx
  const unsubRoomCreated = socket.on('room_created', (data) => {
    // Only navigate if this is direct response, not lobby broadcast
    if (data.success === true) {
      navigate(`/room/${data.room_id}`);
    }
  });

  Phase 3: Added Host Information
  # backend/engine/room.py
  def slot_info(player, slot_index):
      return {
          "name": player.name,
          "is_bot": player.is_bot,
          "is_host": slot_index == 0  # Host is always in slot P1
      }

  Result

  ✅ Before: Button click → Nothing visible happens✅ After: Button click → Room created → Navigate to room →
  Display host in P1 + bots in P2-P4 → Start Game button enabled

  The key insight was that frontend and backend were using different communication protocols (WebSocket vs
  REST), which required bridging the gap with proper event handlers.
  ---
  ⏺ Summary of Room Management Bugs and Fixes

  1. JavaScript WebSocket Connection Error

  Bug: Cannot read properties of null (reading 'close') error in SocketConnection.js:31
  Root Cause: Timeout handler tried to call this.socket.close() when this.socket was null
  Fix: Added null check before calling close method
  // Before
  this.socket.close();

  // After  
  if (this.socket) {
      this.socket.close();
  }

  2. Missing "Remove Bot" Backend Handler

  Bug: Remove bot button did nothing - no backend response
  Root Cause: Backend WebSocket handler missing remove_player event processor
  Fix: Added complete remove_player event handler in backend/api/routes/ws.py
  elif event_name == "remove_player":
      slot_id = event_data.get("slot_id")
      # Convert frontend slot IDs (1-4) to backend indices (0-3)
      slot_index = int(slot_id) - 1
      result = await room.assign_slot_safe(slot_index, None)
      # Broadcast room update to all clients

  3. Missing "Add Bot" Backend Handler

  Bug: Add bot button didn't work - same issue as remove bot
  Root Cause: Backend missing add_bot event processorFix: Added add_bot event handler that generates bot names
   and assigns to slots
  elif event_name == "add_bot":
      slot_id = event_data.get("slot_id")
      bot_name = f"Bot {slot_id}"
      result = await room.assign_slot_safe(slot_index, bot_name)
      # Broadcast room update to all clients

  4. Wrong Broadcast Function Call

  Bug: name 'broadcast_to_room' is not defined error when removing players
  Root Cause: Used non-existent function name instead of the actual broadcast function
  Fix: Changed broadcast_to_room() calls to use existing broadcast() function
  # Before
  await broadcast_to_room(room_id, {...})

  # After
  await broadcast(room_id, "room_update", {...})

  5. Missing "Leave Room" Backend Handler

  Bug: Leave room button did nothing - no backend processing
  Root Cause: Backend missing leave_room event processor
  Fix: Added comprehensive leave room handler that:
  - Distinguishes between host leaving (closes room) vs regular player leaving
  - Broadcasts appropriate events (room_closed or room_update)
  - Updates lobby room list when rooms are closed
  - Handles both scenarios correctly

  6. Frontend Leave Room Data Missing

  Bug: Backend expected player_name in leave room event but frontend didn't send it
  Root Cause: Frontend called socket.send('leave_room') without player data
  Fix: Updated frontend to include player name
  // Before
  socket.send('leave_room');

  // After  
  socket.send('leave_room', { player_name: app.playerName });

  Key Patterns in the Fixes

  1. Consistent Event Handling: All WebSocket events now follow the same pattern:
    - Validate input data
    - Use assign_slot_safe() for thread-safe operations
    - Broadcast updates to all room clients
    - Handle errors gracefully
  2. Frontend-Backend Data Sync: Fixed slot numbering mismatches (frontend 1-4 → backend 0-3)
  3. Real-time Updates: All operations now broadcast room state changes immediately to connected clients
  4. Error Prevention: Added null checks and proper error handling throughout

  The end result is a fully functional room management system where all buttons work correctly with real-time
  UI updates and proper WebSocket communication.