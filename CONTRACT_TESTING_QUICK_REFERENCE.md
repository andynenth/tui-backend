# Contract Testing Quick Reference 🚀

## Essential Commands

### 🏃 Quick Test Commands
```bash
# Run all contract tests
cd backend && pytest tests/contracts/ -v

# Run specific contract test
pytest tests/contracts/ -k "create_room"

# Run behavioral tests
python tests/behavioral/run_behavioral_tests.py

# Check compatibility status
python tests/contracts/monitor_compatibility.py --report
```

### 🔍 Debugging Failed Tests
```bash
# See detailed test output
pytest tests/contracts/test_websocket_contracts.py::TestWebSocketContracts::test_create_room_contract -vv

# Compare with golden master
cat tests/contracts/golden_masters/create_room_*.json | jq .

# Run with debugging
pytest tests/contracts/ --pdb
```

### 🛡️ Shadow Mode Commands
```bash
# Start shadow mode (in Python)
from api.shadow_mode_manager import ShadowModeManager
manager = ShadowModeManager()
manager.start_shadow_mode(sample_rate=0.1)

# Check shadow mode status
manager.get_current_status()

# Analyze mismatches
manager.analyze_mismatches(time_window_minutes=60)
```

## 📍 Key File Locations

### Test Files
- **Contracts**: `backend/tests/contracts/websocket_contracts.py`
- **Golden Masters**: `backend/tests/contracts/golden_masters/`
- **Behavioral Tests**: `backend/tests/behavioral/`
- **Test Results**: `backend/tests/contracts/test_results/`

### Shadow Mode
- **Core**: `backend/api/shadow_mode.py`
- **Manager**: `backend/api/shadow_mode_manager.py`
- **Integration**: `backend/api/shadow_mode_integration.py`

### CI/CD
- **GitHub Actions**: `.github/workflows/contract-tests.yml`
- **Pre-commit**: `.pre-commit-config.yaml`

## 🔧 Common Scenarios

### Adding a New WebSocket Message Type
1. Add contract to `websocket_contracts.py`:
```python
NEW_MESSAGE_CONTRACT = WebSocketContract(
    name="new_message",
    direction=MessageDirection.CLIENT_TO_SERVER,
    description="Description here",
    request_schema={...},
    response_schema={...}
)
```

2. Add to contract registry:
```python
WEBSOCKET_CONTRACTS = {
    # ... existing contracts
    "new_message": NEW_MESSAGE_CONTRACT,
}
```

3. Capture golden master:
```bash
python tests/contracts/capture_golden_masters.py
```

### Updating Contract After Agreed Change
1. Update the contract definition
2. Re-capture golden master for that message
3. Update behavioral tests if needed
4. Commit both contract and golden master changes

### Investigating Contract Test Failure
1. Check test output for exact differences
2. Compare actual vs expected:
```bash
# In test output, look for:
# Expected: {"event": "room_created", ...}
# Actual: {"event": "roomCreated", ...}
```
3. Verify field names, types, and structure match exactly

## ⚡ Performance Testing

### Check Response Times
```python
# In contract test
assert result.current_behavior.timing["duration_ms"] < 100  # For ping
assert result.current_behavior.timing["duration_ms"] < 200  # For declare
```

### Monitor Shadow Mode Performance
```python
report = manager.get_shadow_report()
print(f"Performance degradations: {report['metrics']['performance_degradations']}")
```

## 🚨 Emergency Procedures

### Rollback If Tests Fail in Production
```bash
# 1. Disable shadow mode immediately
manager.change_state(ShadowModeState.DISABLED)

# 2. Switch back to current implementation
# (This happens automatically when shadow mode is disabled)

# 3. Investigate using shadow mode logs
manager.export_session_data()
```

### Contract Test Suddenly Failing
1. Check if golden masters exist:
   ```bash
   ls backend/tests/contracts/golden_masters/
   ```
2. Re-run capture if missing:
   ```bash
   python backend/tests/contracts/capture_golden_masters.py
   ```
3. Check for environment differences

## 📊 Monitoring Dashboard

### Start Live Monitor
```bash
python backend/tests/contracts/monitor_compatibility.py --monitor
```

### Dashboard Shows:
- Overall compatibility score
- Golden master coverage
- Recent test failures
- Problem areas

## 🎯 Best Practices

1. **Run Tests Frequently**: After every change
2. **Check Shadow Mode**: Before merging PRs
3. **Update Golden Masters**: Only for agreed changes
4. **Monitor Performance**: Keep < 20% overhead
5. **Document Changes**: Update contracts when needed

## 📞 Getting Help

- **Contract Test Failures**: Check exact diff in test output
- **Shadow Mode Issues**: Review shadow mode logs
- **Performance Problems**: Use profiler on new code
- **Missing Golden Masters**: Run capture script

Remember: The tests are your safety net - trust them! 🛡️