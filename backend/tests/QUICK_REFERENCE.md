# Backend Testing Quick Reference 🚀

## **Fast Commands** ⚡

```bash
# Unit tests (fast feedback)
pytest tests/unit/ -v

# Integration tests (thorough)
pytest tests/integration/ -v

# End-to-end tests (comprehensive)
pytest tests/e2e/ -v

# Specific category
pytest tests/unit/engine/ -v          # Engine unit tests
pytest tests/integration/bots/ -v     # Bot integration tests
pytest tests/e2e/game_flows/ -v       # Game flow E2E tests
```

## **Test Markers** 🏷️

```bash
# Run by marker
pytest -m unit              # All unit tests
pytest -m integration       # All integration tests
pytest -m e2e               # All end-to-end tests
pytest -m bots              # All bot-related tests
pytest -m websocket         # All WebSocket tests
pytest -m "not slow"        # Skip slow tests
```

## **Development Workflow** 🔄

### **Writing New Code**
1. **Write unit tests first** (`tests/unit/`)
2. **Run unit tests frequently** during development
3. **Add integration tests** for module interactions
4. **Add E2E tests** for complete features

### **Before Committing**
```bash
# Run affected tests
pytest tests/unit/engine/ -v          # If you changed engine code
pytest tests/integration/api/ -v      # If you changed API code

# Run full unit test suite
pytest tests/unit/ -v
```

### **Before Merging**
```bash
# Run comprehensive test suite
pytest tests/unit/ tests/integration/ -v

# Optional: Run E2E tests
pytest tests/e2e/ -v
```

## **File Organization** 📁

### **Where to Put New Tests**

| **Test Type** | **Location** | **When to Use** |
|---------------|--------------|-----------------|
| **Unit** | `tests/unit/engine/` | Testing game logic, state machine |
| **Unit** | `tests/unit/api/` | Testing API endpoints, validation |
| **Unit** | `tests/unit/infrastructure/` | Testing queues, events, storage |
| **Integration** | `tests/integration/api/` | Testing API request flows |
| **Integration** | `tests/integration/bots/` | Testing bot behavior |
| **Integration** | `tests/integration/websocket/` | Testing WebSocket flows |
| **E2E** | `tests/e2e/game_flows/` | Testing complete game scenarios |
| **E2E** | `tests/e2e/performance/` | Testing system performance |

### **Naming Convention**
```
test_[module]_[feature].py           # Unit: test_state_machine_transitions.py
test_[feature]_integration.py       # Integration: test_bot_timing_integration.py
test_[scenario]_e2e.py              # E2E: test_full_game_flow_e2e.py
```

## **Test Categories** 📊

| **Category** | **Count** | **Speed** | **Purpose** |
|--------------|-----------|-----------|-------------|
| **Unit** | 24 files | < 1s each | Fast feedback, isolated testing |
| **Integration** | 47 files | 1-10s each | Module interaction testing |
| **E2E** | 10 files | 10-60s each | Complete scenario testing |
| **Utilities** | 6 files | Variable | Test support and debugging |

## **Common Commands** 💻

### **Coverage Reports**
```bash
pytest --cov=backend tests/unit/
pytest --cov=backend tests/integration/
pytest --cov=backend tests/
```

### **Parallel Execution**
```bash
pytest -n auto tests/unit/              # Run unit tests in parallel
pytest -n 4 tests/integration/         # Run integration tests with 4 workers
```

### **Specific Test Types**
```bash
pytest tests/unit/engine/test_state_machine.py -v
pytest tests/integration/bots/ -k "timing" -v
pytest tests/e2e/game_flows/ -x -v     # Stop on first failure
```

### **Debugging**
```bash
pytest tests/unit/engine/ -v -s        # Show print statements
pytest tests/integration/bots/ --pdb   # Drop into debugger on failure
pytest tests/utilities/debugging/ -v   # Run debugging utilities
```

## **Test Performance** ⏱️

### **Expected Runtimes**
- **Unit tests**: < 30 seconds total
- **Integration tests**: 1-5 minutes total  
- **E2E tests**: 2-10 minutes total
- **Full suite**: 5-15 minutes total

### **Optimization Tips**
- Run unit tests during development (fastest feedback)
- Run integration tests before commits
- Run E2E tests before releases
- Use parallel execution for faster CI

## **Troubleshooting** 🔧

### **Common Issues**

**Import Errors**:
```bash
# Ensure you're in backend directory
cd backend
pytest tests/unit/

# Check Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

**Test Discovery**:
```bash
# Verify test discovery
pytest --collect-only tests/unit/

# Check specific directory
pytest --collect-only tests/integration/bots/
```

**Slow Tests**:
```bash
# Skip slow tests during development
pytest -m "not slow" tests/

# Run only fast unit tests
pytest tests/unit/ -x
```

### **Debugging Failed Tests**
```bash
# Run single test with verbose output
pytest tests/unit/engine/test_state_machine.py::test_specific_function -v -s

# Use debugging utilities
pytest tests/utilities/debugging/ -v

# Check test logs
pytest tests/integration/api/ --log-cli-level=DEBUG
```

## **CI/CD Integration** 🔄

### **Recommended Pipeline**
```yaml
# Stage 1: Unit Tests (fast)
- pytest tests/unit/ --cov=backend

# Stage 2: Integration Tests  
- pytest tests/integration/ --cov=backend

# Stage 3: E2E Tests (comprehensive)
- pytest tests/e2e/ --cov=backend

# Stage 4: Manual Verification
- Review tests/integration/manual/README.md
```

### **Branch Protection**
```bash
# Minimum requirements for merge
pytest tests/unit/ -x                  # All unit tests pass
pytest tests/integration/api/ -x       # Core integration tests pass
```

---

**Quick Start**: `pytest tests/unit/ -v` (fastest feedback)
**Full Test**: `pytest tests/ -v` (comprehensive coverage)
**Help**: See `tests/README.md` for detailed documentation