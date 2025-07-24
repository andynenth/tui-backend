# Next Steps: Begin Phase 1 - Clean API Layer

## 🎯 Current Status (Updated 2025-07-24)
✅ **Contract Testing Infrastructure**: COMPLETE
✅ **Behavioral Test Suite**: COMPLETE  
✅ **Shadow Mode System**: COMPLETE (not enabled)
✅ **CI/CD Integration**: COMPLETE
✅ **Documentation**: COMPLETE
✅ **Golden Masters**: CAPTURED (22 scenarios)
🚧 **Phase 1 Implementation**: IN PROGRESS (4/23 adapters)

## 🚀 Immediate Next Steps

### 1. Capture Golden Masters (Required First!)
```bash
cd backend

# Option A: Automated capture (simulated responses)
python3 start_golden_master_capture.py

# Option B: Live server capture (more accurate)
# First start your server, then:
python3 capture_from_live_server.py
```

### 2. Verify Baseline
```bash
# Check golden masters were created
ls tests/contracts/golden_masters/

# Run behavioral tests
python3 tests/behavioral/run_behavioral_tests.py

# Generate compatibility report
python3 tests/contracts/monitor_compatibility.py --report
```

### 3. Commit Baseline
```bash
git add tests/contracts/golden_masters/
git add tests/behavioral/results/
git commit -m "Add golden masters baseline for refactoring

- Captured 23 WebSocket message behaviors
- Established behavioral test baseline
- Ready for Phase 1 refactoring

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## 📝 Phase 1 Implementation Plan

### Start Branch
```bash
git checkout -b phase-1-clean-api-layer
```

### First Adapter: CreateRoomAdapter

1. **Create the adapter structure**:
```python
# backend/api/adapters/room_adapters.py
class CreateRoomAdapter:
    """Adapter to bridge WebSocket messages to clean architecture"""
    
    def __init__(self, room_use_case):
        self.room_use_case = room_use_case
    
    async def handle(self, websocket, message: Dict[str, Any]):
        # Extract data
        player_name = message["data"]["player_name"]
        
        # Call use case
        result = await self.room_use_case.create_room(player_name)
        
        # Map to WebSocket response
        return {
            "event": "room_created",
            "data": {
                "room_id": result.room_id,
                "host_name": player_name,
                "success": True
            }
        }
```

2. **Test with contracts**:
```bash
pytest backend/tests/contracts/ -k "create_room" -v
```

3. **Enable shadow mode for testing**:
```python
# In your WebSocket handler
from api.shadow_mode_integration import ShadowModeWebSocketAdapter

adapter = ShadowModeWebSocketAdapter(current_handler)
adapter.set_shadow_handler(new_adapter_handler)
adapter.enable_shadow_mode(sample_rate=0.1)
```

### Adapter Implementation Order

Based on complexity and dependencies:

1. **Connection/Utility Messages** (Simple) ✅ COMPLETE
   - [x] ping → PingAdapter ✅
   - [x] client_ready → ClientReadyAdapter ✅
   - [x] ack → AckAdapter ✅
   - [x] sync_request → SyncRequestAdapter ✅
   
2. **Room Management** (Medium)
   - [ ] create_room → CreateRoomAdapter
   - [ ] join_room → JoinRoomAdapter  
   - [ ] leave_room → LeaveRoomAdapter
   - [ ] add_bot → AddBotAdapter
   - [ ] remove_player → RemovePlayerAdapter
   
3. **Game Flow** (Complex)
   - [ ] start_game → StartGameAdapter
   - [ ] declare → DeclareAdapter
   - [ ] play → PlayAdapter
   - [ ] request_redeal → RedealAdapter

### Testing Each Adapter

After implementing each adapter:

1. **Unit test the adapter**:
```python
async def test_create_room_adapter():
    # Test adapter logic in isolation
    adapter = CreateRoomAdapter(mock_use_case)
    result = await adapter.handle(mock_ws, test_message)
    assert result["event"] == "room_created"
```

2. **Contract test**:
```bash
pytest backend/tests/contracts/test_websocket_contracts.py::test_create_room_contract
```

3. **Shadow mode verification**:
```python
# Monitor shadow mode results
from api.shadow_mode_manager import ShadowModeManager
manager = ShadowModeManager()
print(manager.analyze_mismatches())
```

## 📊 Progress Tracking

### Current Progress (2025-07-24)

#### Adapters Completed
- [x] ping (all tests passing) ✅
- [x] client_ready (all tests passing) ✅
- [x] ack (all tests passing) ✅
- [x] sync_request (implemented) ✅
- [ ] create_room (0/5 tests passing) ⏭️ Next
- [ ] join_room (0/6 tests passing)
...

#### Metrics
- Contract Test Pass Rate: 100% (for implemented adapters)
- Shadow Mode Compatibility: Not tested yet
- Performance Overhead: ⚠️ 71% (needs optimization)
- Adapter Coverage: 4/23 (17.4%)

## 🔧 Development Workflow

1. **Pick an adapter** from the list
2. **Create adapter class** following the pattern
3. **Write unit tests** for the adapter
4. **Run contract tests** to verify compatibility
5. **Enable shadow mode** for that message type
6. **Monitor results** for 10-20 requests
7. **Commit** when tests pass

## ⚡ Quick Commands

```bash
# Run specific contract test
pytest backend/tests/contracts/ -k "message_name" -v

# Check shadow mode status
python3 -c "from api.shadow_mode_manager import *; print(ShadowModeManager().get_current_status())"

# Monitor compatibility live
python3 tests/contracts/monitor_compatibility.py --monitor

# Run pre-commit checks
pre-commit run --all-files
```

## 🎯 Success Criteria for Phase 1

- [ ] All 23 message types have adapters (4/23 = 17.4%)
- [x] 100% contract tests passing (for implemented adapters) ✅
- [ ] Shadow mode shows 100% compatibility (not enabled)
- [ ] Performance overhead < 20% (❌ currently 71%)
- [x] Clean separation between API and business logic ✅
- [x] No changes to frontend code ✅

## 🔧 Current Issues

1. **Performance Overhead**: 71% vs 20% target
   - Need to profile and optimize adapter layer
   - Consider caching or reducing abstraction levels

2. **Integration**: ws.py not yet updated
   - Created integration layer but not connected
   - Need to test with real WebSocket connections

## 📚 Resources

- **Adapter Pattern Guide**: PHASE_1_CLEAN_API_LAYER.md
- **Contract Definitions**: backend/tests/contracts/websocket_contracts.py
- **Quick Reference**: CONTRACT_TESTING_QUICK_REFERENCE.md
- **Troubleshooting**: CONTRACT_TESTING_README.md

---

**Ready to start Phase 1!** Remember: The contract tests are your safety net. Trust them and refactor with confidence! 🚀