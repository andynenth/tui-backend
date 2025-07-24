# Contract Testing Framework for Backend Refactoring

This framework ensures that refactored backend endpoints maintain 100% compatibility with the current implementation, guaranteeing that the frontend continues to work without any modifications.

## Overview

The contract testing framework provides:
1. **WebSocket Contract Definitions** - Formal contracts for all messages
2. **Golden Master Testing** - Capture current behavior as reference
3. **Parallel Test Execution** - Compare old vs new implementations
4. **Compatibility Reporting** - Clear pass/fail results

## Key Components

### 1. WebSocket Contracts (`websocket_contracts.py`)
Defines the exact message formats for all WebSocket communications:
- Request schemas (what frontend sends)
- Response schemas (what backend returns)
- Broadcast events (what backend broadcasts)
- Error cases and their exact formats
- State preconditions and postconditions

### 2. Golden Master Capture (`golden_master.py`)
Captures the current system's behavior as "golden masters":
- Records exact responses for given inputs
- Captures all broadcast events and their order
- Measures response timing
- Stores results for future comparison

### 3. Parallel Test Runner (`parallel_runner.py`)
Runs tests against both current and refactored systems:
- Executes same test on both systems
- Compares responses, broadcasts, and timing
- Generates compatibility reports
- Identifies any behavioral differences

### 4. Example Tests (`test_websocket_contracts.py`)
Demonstrates how to write contract tests for critical operations:
- Room creation and joining
- Game actions (declare, play)
- Error scenarios
- Performance comparisons

## Usage

### Step 1: Capture Golden Masters
Before refactoring, capture the current behavior:

```python
from tests.contracts.golden_master import GoldenMasterCapture

capture = GoldenMasterCapture()

# Capture behavior for a message
record = await capture.capture_message_behavior(
    current_handler,
    {"action": "create_room", "data": {"player_name": "Alice"}}
)

# Save for future comparison
capture.save_golden_master(record)
```

### Step 2: Define Contract Tests
Create tests for each WebSocket message:

```python
test_cases = [
    (
        CREATE_ROOM_CONTRACT,
        {"action": "create_room", "data": {"player_name": "Alice"}},
        None  # Initial state
    ),
    # Add more test cases...
]
```

### Step 3: Run Parallel Tests
Compare refactored implementation against golden masters:

```python
runner = ParallelContractRunner(
    current_system_handler=current_handler,
    new_system_handler=refactored_handler,
    comparator=GoldenMasterComparator()
)

suite = await runner.run_contract_suite(test_cases)
print(runner.generate_compatibility_report(suite))
```

### Step 4: Verify Compatibility
The test suite will report:
- ✅ **FULL COMPATIBILITY** - All tests passed, safe to deploy
- ⚠️  **HIGH COMPATIBILITY** - Minor differences, review needed
- ❌ **LOW COMPATIBILITY** - Breaking changes detected

## Example Output

```
============================================================
WebSocket Contract Compatibility Report
============================================================

Test Suite: WebSocket Contract Tests
Total Tests: 15
Passed: 15 (100.0%)
Failed: 0
Duration: 0.45s

Compatibility Assessment:
----------------------------------------
✅ FULL COMPATIBILITY - All tests passed!
   The refactored system behaves identically to the current system.
```

## Contract Testing Workflow

1. **Before Refactoring**:
   - Run `capture_golden_masters.py` to record current behavior
   - Review captured behaviors in `tests/contracts/golden_masters/`
   - Add any missing test cases

2. **During Refactoring**:
   - Run contract tests frequently: `pytest tests/contracts/`
   - Fix any compatibility issues immediately
   - Use test results to guide refactoring

3. **Before Deployment**:
   - Run full contract test suite
   - Achieve 100% compatibility
   - Review any timing degradations

## Writing New Contract Tests

For each WebSocket message type:

1. **Define the Contract**:
```python
MY_MESSAGE_CONTRACT = WebSocketContract(
    name="my_message",
    direction=MessageDirection.CLIENT_TO_SERVER,
    request_schema={...},
    response_schema={...},
    broadcast_schemas=[...],
    error_cases=[...]
)
```

2. **Create Test Cases**:
```python
test_cases = [
    # Happy path
    (MY_MESSAGE_CONTRACT, valid_message, initial_state),
    # Error cases
    (MY_MESSAGE_CONTRACT, invalid_message, initial_state),
]
```

3. **Run and Verify**:
```python
suite = await runner.run_contract_suite(test_cases)
assert suite.success_rate == 100.0
```

## Best Practices

1. **Test All Message Types**: Every WebSocket message needs contract tests
2. **Include Error Cases**: Test both success and failure scenarios
3. **Verify Broadcasts**: Check that all events are sent in correct order
4. **Monitor Performance**: Ensure refactored code isn't significantly slower
5. **Ignore Volatile Fields**: Timestamps, IDs may differ - configure comparator

## Troubleshooting

### Test Failures
If a contract test fails:
1. Check the comparison details in the report
2. Verify the exact field differences
3. Ensure response format matches exactly
4. Check broadcast event order

### Performance Issues
If timing tests fail:
1. Compare average response times
2. Profile the refactored code
3. Consider 20% overhead as acceptable
4. Optimize critical paths

## Continuous Integration

Add to your CI pipeline:

```yaml
- name: Run Contract Tests
  run: |
    pytest tests/contracts/ -v
    python tests/contracts/generate_report.py
```

This ensures every commit maintains frontend compatibility.