# Testing Guide

## Quick Start

```bash
# Run all tests
cd backend && python -m pytest
cd frontend && npm test
```

## Backend Testing (78+ test suites)

The project includes comprehensive testing across all components.

### Running Backend Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all backend tests
cd backend
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=. --cov-report=html

# Test specific components
python test_full_game_flow.py          # Complete game integration
python test_reliable_messaging.py      # Message delivery system
python test_error_recovery.py          # Health monitoring & recovery
python test_event_sourcing.py          # Event store system

# Quick state machine validation
python run_tests.py
```

### Test Organization

```
backend/tests/
├── unit/                    # Unit tests for individual components
│   ├── test_game.py        # Game engine tests
│   ├── test_rules.py       # Rule validation tests
│   ├── test_scoring.py     # Scoring calculation tests
│   └── test_player.py      # Player management tests
│
├── integration/            # Integration tests
│   ├── test_state_machine.py    # State transitions
│   ├── test_websocket.py        # WebSocket communication
│   └── test_room_manager.py     # Room management
│
└── system/                 # System-wide tests
    ├── test_full_game_flow.py   # End-to-end game flow
    ├── test_reliable_messaging.py # Message delivery
    └── test_event_sourcing.py    # Event persistence
```

## Frontend Testing

### Running Frontend Tests

```bash
cd frontend

# Run all frontend tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# TypeScript validation
npm run type-check

# Code quality checks
npm run lint

# Auto-fix linting issues
npm run lint:fix
```

### Frontend Test Types

- **Component Tests**: Testing React components in isolation
- **Hook Tests**: Testing custom React hooks
- **Service Tests**: Testing TypeScript services (NetworkService, etc.)
- **Integration Tests**: Testing component interactions

## Quality Assurance

### Python Code Quality

```bash
# Run in virtual environment
source venv/bin/activate
cd backend

# Code formatting
black .

# Code analysis
pylint engine/ api/ tests/

# Type checking (if using type hints)
mypy engine/ api/
```

### JavaScript Code Quality

```bash
cd frontend

# Auto-fix linting issues
npm run lint:fix

# Format code
npm run format:fix

# Full quality check
npm run lint && npm run type-check && npm run format
```

## Test Coverage Requirements

### Backend Coverage Goals
- **Overall**: ≥80% coverage
- **Core Engine**: ≥90% coverage
- **State Machine**: ≥95% coverage
- **API Endpoints**: ≥85% coverage

### Frontend Coverage Goals
- **Overall**: ≥70% coverage
- **Components**: ≥80% coverage
- **Hooks**: ≥90% coverage
- **Services**: ≥85% coverage

## Continuous Integration

Tests run automatically on:
- Pull requests
- Commits to main branch
- Pre-deployment checks

### CI Test Pipeline
1. **Linting**: Code style and quality checks
2. **Type Checking**: TypeScript and Python type validation
3. **Unit Tests**: Fast, isolated component tests
4. **Integration Tests**: Component interaction tests
5. **System Tests**: Full end-to-end scenarios
6. **Coverage Report**: Ensure coverage thresholds met

## Writing New Tests

### Backend Test Example

```python
# test_new_feature.py
import pytest
from engine.game import Game

class TestNewFeature:
    @pytest.fixture
    def game(self):
        return Game()
    
    def test_feature_behavior(self, game):
        # Arrange
        initial_state = game.state
        
        # Act
        result = game.new_feature()
        
        # Assert
        assert result == expected_value
        assert game.state == expected_state
```

### Frontend Test Example

```javascript
// NewComponent.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { NewComponent } from './NewComponent';

describe('NewComponent', () => {
  it('should handle user interaction', () => {
    // Arrange
    render(<NewComponent />);
    
    // Act
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    // Assert
    expect(screen.getByText('Expected Result')).toBeInTheDocument();
  });
});
```

## Debugging Tests

### Backend Debugging
```bash
# Run specific test with debugging
python -m pytest tests/test_game.py::TestGame::test_specific -v -s

# Drop into debugger on failure
python -m pytest tests/ --pdb

# Show local variables on failure
python -m pytest tests/ -l
```

### Frontend Debugging
```bash
# Run single test file
npm test -- GameComponent.test.tsx

# Debug in VS Code
# Add breakpoint and use "Debug Test" option
```

## Performance Testing

### Load Testing WebSockets
```python
# Use the included performance test suite
python tests/performance/test_websocket_load.py

# Configurable parameters:
# - Number of concurrent connections
# - Messages per second
# - Test duration
```

### Frontend Performance
```bash
# Build with profiling
npm run build -- --profile

# Analyze bundle size
npm run build -- --metafile
npx esbuild-visualizer
```

## Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Isolation**: Each test should be independent and not rely on others
3. **Speed**: Keep unit tests fast (< 100ms per test)
4. **Deterministic**: Tests should always produce the same result
5. **Coverage**: Write tests for edge cases, not just happy paths
6. **Maintenance**: Update tests when requirements change

## Troubleshooting Common Test Issues

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Module Not Found
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Flaky Tests
- Check for timing issues (use proper waitFor methods)
- Ensure proper test isolation
- Mock external dependencies
- Use fixed timestamps/random seeds

For more testing patterns and examples, see the existing test files in the project.