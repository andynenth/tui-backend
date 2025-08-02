# Test Organization Guide

## Current Test Structure ✅

```
src/
├── components/
│   └── __tests__/           # Component tests (co-located)
│       └── WaitingUI.test.jsx
├── hooks/
│   └── __tests__/           # Hook tests (co-located)
├── services/
│   └── __tests__/           # Service tests (co-located)
│       ├── GameService.test.js
│       ├── NetworkService.test.js
│       └── ServiceIntegration.test.js
├── utils/
│   └── __tests__/           # Utility tests (co-located)
│       ├── roomHelpers.test.js
│       ├── sessionStorage.test.js
│       └── sessionStorage.simple.test.js
├── tests/                   # Integration & specialized tests
│   ├── components/          # Isolated component tests
│   ├── game/               # Game logic tests
│   ├── hooks/              # Isolated hook tests
│   ├── integration/        # Integration tests
│   │   ├── connection-state.test.js
│   │   └── test_frontend_connection.js
│   ├── pages/              # Page-level tests
│   ├── setup/              # Test configuration
│   │   └── test-setup.js
│   └── README.md           # This file
```

## Test Organization Principles ✅

### 1. Co-located Tests (Preferred)
- **Location**: Next to source files in `__tests__/` folders
- **Benefits**: Easy to find, maintain, and understand relationships
- **Pattern**: `src/[module]/__tests__/[file].test.js`

### 2. Centralized Tests (When Needed)
- **Location**: `src/tests/` directory
- **Use cases**: Integration tests, complex multi-module tests, specialized test utilities
- **Organization**: Grouped by functionality or test type

### 3. Configuration Files
- **Jest config**: `jest.config.js` (root level)
- **Jest setup**: `jest.setup.js` (root level)
- **Test utilities**: `src/tests/setup/` directory

## Test Coverage Status ✅

### ✅ Well-Tested Modules
- **Utils**: Complete coverage (72 tests)
  - `roomHelpers.js`: 30 tests covering all functions
  - `sessionStorage.js`: 42 tests including edge cases
- **Services**: Extensive coverage
  - `GameService.ts`: Comprehensive integration tests
  - `NetworkService.ts`: Connection and WebSocket tests
- **Components**: Growing coverage
  - `WaitingUI.jsx`: 41 tests covering all scenarios
- **Integration**: Cross-system tests
  - `connection-state.test.js`: GameService connection tracking
  - `test_frontend_connection.js`: Frontend-backend data flow simulation

### 📝 Modules Needing Tests
- Most React components in `src/components/`
- React hooks in `src/hooks/`
- Page components in `src/pages/`
- Context providers in `src/contexts/`

## Running Tests ✅

```bash
# All tests
npm test

# Specific pattern
npm test -- --testPathPattern="utils"
npm test -- --testPathPattern="WaitingUI"

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage

# Type checking
npm run type-check

# Linting
npm run lint

# Manual integration tests (from project root)
node frontend/src/tests/integration/test_frontend_connection.js
```

## Manual Testing Scripts ✅

Additional manual testing scripts are available:

```bash
# Backend integration tests (from project root)
cd backend && source venv/bin/activate
python tests/integration/manual/test_connection.py
python tests/integration/manual/test_websocket_debug.py

# API endpoint testing
./scripts/testing/test_endpoints_manual.sh
```

## Test Quality Standards ✅

### ✅ Implemented Standards
1. **Comprehensive Coverage**: Test happy path, edge cases, and error conditions
2. **Proper Mocking**: Isolate dependencies with Jest mocks
3. **Clear Test Names**: Descriptive test names explaining what is being tested
4. **Grouped Tests**: Related tests organized in `describe` blocks
5. **Setup/Cleanup**: Proper beforeEach/afterEach for test isolation

### 📋 Example Test Structure
```javascript
describe('ModuleName', () => {
  beforeEach(() => {
    // Setup mocks and test data
  });

  describe('functionName', () => {
    test('handles normal case correctly', () => {
      // Test implementation
    });

    test('handles edge case gracefully', () => {
      // Test implementation
    });

    test('throws error for invalid input', () => {
      // Test implementation
    });
  });
});
```

## Next Steps 📋

1. **Add TypeScript Support**: Configure Babel preset for TypeScript testing
2. **Expand Component Tests**: Test remaining React components
3. **Hook Testing**: Add comprehensive hook tests
4. **Page Testing**: Add page-level integration tests
5. **Context Testing**: Test React context providers
6. **E2E Tests**: Consider adding Playwright/Cypress for end-to-end testing

## Benefits of Current Organization ✅

1. **🔍 Easy Discovery**: Tests are next to the code they test
2. **🛠️ Easy Maintenance**: Changes to code immediately show related tests
3. **📊 Clear Coverage**: Easy to see what has tests and what doesn't
4. **🚀 Fast Development**: No need to navigate between distant directories
5. **🧹 Clean Structure**: Root directory is uncluttered
6. **⚖️ Flexible**: Supports both co-located and centralized test patterns