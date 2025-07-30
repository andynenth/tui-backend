# Contributing Guide

## Welcome Contributors! 🎉

We're excited that you're interested in contributing to Liap Tui! This guide will help you understand our development process, coding standards, and how to make meaningful contributions to the project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Code Standards](#code-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Pull Request Process](#pull-request-process)
6. [Issue Guidelines](#issue-guidelines)
7. [Documentation Standards](#documentation-standards)
8. [Release Process](#release-process)
9. [Community Guidelines](#community-guidelines)

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:
- **Python 3.9+** for backend development
- **Node.js 16+** for frontend development
- **Git** for version control
- **Docker** (optional, for containerized development)

### Initial Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/liap-tui.git
   cd liap-tui
   ```

2. **Set Up Development Environment**
   ```bash
   # Quick setup using our script
   ./start.sh
   
   # Or manual setup (see Developer Onboarding Guide)
   ```

3. **Verify Setup**
   ```bash
   # Check that both frontend and backend are running
   curl http://localhost:8000/health  # Backend health check
   # Open http://localhost:3000 in browser  # Frontend
   ```

4. **Run Tests**
   ```bash
   # Backend tests
   cd backend && python -m pytest tests/
   
   # Frontend tests
   cd frontend && npm test
   ```

### First Contribution

For your first contribution, look for issues labeled:
- `good first issue` - Simple changes perfect for new contributors
- `documentation` - Documentation improvements
- `frontend` or `backend` - Based on your expertise

---

## Development Workflow

### Branch Strategy

We use a **GitHub Flow** model with the following branches:

- **`main`** - Production-ready code, all tests pass
- **Feature branches** - `feature/description` or `fix/description`
- **Release branches** - `release/v1.2.0` (when preparing releases)

### Working on Features

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow coding standards (see below)
   - Write tests for new functionality
   - Update documentation if needed

3. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new game phase UI component
   
   - Implement TurnResultsUI with winner display
   - Add animation for pile score updates
   - Update GameContainer to handle new phase
   
   Fixes #123"
   ```

4. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Then create PR on GitHub
   ```

### Commit Message Format

We use **Conventional Commits** format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Build process, dependency updates

**Examples**:
```
feat(frontend): add declaration phase UI validation

fix(backend): resolve state machine transition bug

docs: update API reference with new endpoints

test(backend): add comprehensive scoring tests
```

---

## Code Standards

### Python (Backend) Standards

#### Code Style
```python
# Use Black for formatting
black backend/

# Use type hints everywhere
def calculate_score(declared: int, actual: int) -> int:
    """Calculate round score based on declared vs actual piles."""
    if declared == 0 and actual == 0:
        return 3  # Perfect zero bonus
    elif declared == 0:
        return -actual  # Failed zero penalty
    elif declared == actual:
        return declared + 5  # Perfect match bonus
    else:
        return -abs(declared - actual)  # Miss penalty
```

#### Enterprise Architecture Patterns
```python
# ✅ ALWAYS use enterprise patterns for state changes
await self.update_phase_data({
    'current_player': next_player,
    'turn_number': game.turn_number
}, "Player completed turn, advancing to next player")

# ❌ NEVER use manual state updates
self.phase_data['current_player'] = next_player  # This bypasses broadcasting!
```

#### Error Handling
```python
# Comprehensive error handling with context
try:
    result = await self.process_game_action(action)
except ValidationError as e:
    logger.error(f"Validation failed for action {action.type}: {e}")
    await self.send_error(action.player_name, "Invalid action", str(e))
except Exception as e:
    logger.exception(f"Unexpected error processing {action.type}")
    await self.send_error(action.player_name, "Server error", "Please try again")
```

#### Documentation
```python
class GameState:
    """Base class for all game phases.
    
    This class provides the enterprise architecture pattern with automatic
    broadcasting and event sourcing. All game phases should inherit from
    this class and use the update_phase_data() method for state changes.
    
    Attributes:
        phase_data: Dict containing phase-specific state
        change_history: List of all state changes with timestamps
        sequence_number: Monotonic sequence for message ordering
    """
    
    async def update_phase_data(self, updates: dict, reason: str) -> None:
        """Update phase data with automatic broadcasting.
        
        Args:
            updates: Dictionary of state changes to apply
            reason: Human-readable description of why the change is happening
            
        Raises:
            ValueError: If updates contain invalid keys
            TypeError: If updates are not JSON-serializable
        """
```

### JavaScript/TypeScript (Frontend) Standards

#### Code Style
```typescript
// Use Prettier for formatting
// Always use TypeScript for services and utilities

interface Player {
  name: string;
  hand: Piece[];
  declared: number;
  score: number;
  isBot: boolean;
}

// Use descriptive function names
const calculateValidDeclarations = (
  currentDeclarations: Record<string, number>,
  totalPlayers: number,
  isLastPlayer: boolean
): number[] => {
  const validOptions = [0, 1, 2, 3, 4, 5, 6, 7, 8];
  
  if (isLastPlayer) {
    const currentTotal = Object.values(currentDeclarations)
      .reduce((sum, val) => sum + val, 0);
    return validOptions.filter(option => currentTotal + option !== 8);
  }
  
  return validOptions;
};
```

#### React Component Patterns
```jsx
// Use functional components with hooks
const DeclarationUI = ({ 
  declarations, 
  isMyTurn, 
  validOptions, 
  onDeclare 
}) => {
  const [selectedValue, setSelectedValue] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  
  // Memoize expensive calculations
  const declarationProgress = useMemo(() => {
    return Object.keys(declarations).length / 4;
  }, [declarations]);
  
  // Clear selection when turn changes
  useEffect(() => {
    if (!isMyTurn) {
      setSelectedValue(null);
      setShowConfirmation(false);
    }
  }, [isMyTurn]);
  
  const handleDeclare = useCallback((value) => {
    setSelectedValue(value);
    setShowConfirmation(true);
  }, []);
  
  const confirmDeclaration = useCallback(() => {
    onDeclare(selectedValue);
    setShowConfirmation(false);
  }, [selectedValue, onDeclare]);
  
  if (!isMyTurn) {
    return <WaitingForTurn />;
  }
  
  return (
    <div className="declaration-ui">
      {/* Component JSX */}
    </div>
  );
};

// Always export with memo for performance
export default React.memo(DeclarationUI);
```

#### State Management
```typescript
// Use services for complex state logic
class GameService {
  private state: GameState = initialGameState;
  private listeners: Set<(state: GameState) => void> = new Set();
  
  // Immutable state updates
  private updateState(updates: Partial<GameState>): void {
    this.state = {
      ...this.state,
      ...updates,
      timestamp: Date.now()
    };
    
    this.notifyListeners();
  }
  
  // Validate actions before sending
  public async makeDeclaration(value: number): Promise<void> {
    if (!this.isValidDeclaration(value)) {
      throw new Error(`Invalid declaration: ${value}`);
    }
    
    // Optimistic update
    this.updateState({
      declarations: {
        ...this.state.declarations,
        [this.state.playerName]: value
      }
    });
    
    try {
      await this.networkService.sendAction('declare', { value });
    } catch (error) {
      // Rollback on error
      this.revertDeclaration();
      throw error;
    }
  }
}
```

---

## Testing Guidelines

### Backend Testing

#### Test Structure
```python
# tests/test_declaration_state.py
import pytest
from backend.engine.state_machine.states.declaration_state import DeclarationState
from backend.engine.state_machine.core import GameAction, ActionType

class TestDeclarationState:
    @pytest.fixture
    def declaration_state(self):
        # Create test state with known configuration
        return DeclarationState(test_game, test_room)
    
    async def test_valid_declaration(self, declaration_state):
        """Test that valid declarations are accepted."""
        action = GameAction(
            type=ActionType.DECLARE,
            player_name="Player1",
            payload={"value": 3}
        )
        
        result = await declaration_state._handle_action(action)
        
        assert result.success
        assert declaration_state.phase_data['declarations']['Player1'] == 3
    
    async def test_invalid_declaration_value(self, declaration_state):
        """Test that invalid declaration values are rejected."""
        action = GameAction(
            type=ActionType.DECLARE,
            player_name="Player1",
            payload={"value": 9}  # Invalid: must be 0-8
        )
        
        with pytest.raises(ValidationError):
            await declaration_state._handle_action(action)
    
    async def test_last_player_cannot_make_total_eight(self, declaration_state):
        """Test the last player restriction."""
        # Set up scenario where total would be 8
        declaration_state.phase_data['declarations'] = {
            'Player1': 2,
            'Player2': 3,
            'Player3': 1
        }
        declaration_state.phase_data['current_declarer'] = 'Player4'
        
        action = GameAction(
            type=ActionType.DECLARE,
            player_name="Player4",
            payload={"value": 2}  # Would make total = 8
        )
        
        with pytest.raises(ValidationError, match="cannot make total equal 8"):
            await declaration_state._handle_action(action)
```

#### Integration Tests
```python
# tests/test_full_game_flow.py
async def test_complete_game_flow():
    """Test a complete game from start to finish."""
    game_manager = GameManager()
    
    # Create room and add players
    room = await game_manager.create_room("TestHost")
    await game_manager.join_room(room.room_id, "Player1")
    await game_manager.join_room(room.room_id, "Player2")
    await game_manager.add_bot(room.room_id, 3)
    await game_manager.add_bot(room.room_id, 4)
    
    # Start game
    await game_manager.start_game(room.room_id)
    assert room.game.state_machine.current_phase == GamePhase.PREPARATION
    
    # Continue through all phases...
    # Test weak hand handling, declarations, turns, scoring
    
    # Verify final state
    assert room.game.is_complete
    assert len(room.game.winners) >= 1
```

### Frontend Testing

#### Component Tests
```javascript
// tests/components/DeclarationUI.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import DeclarationUI from '../src/components/game/DeclarationUI';

describe('DeclarationUI', () => {
  const defaultProps = {
    declarations: {},
    isMyTurn: true,
    validOptions: [0, 1, 2, 3, 4, 5, 6, 7, 8],
    onDeclare: jest.fn()
  };
  
  test('renders declaration options when it is player turn', () => {
    render(<DeclarationUI {...defaultProps} />);
    
    // Should show all valid options
    for (let i = 0; i <= 8; i++) {
      expect(screen.getByText(i.toString())).toBeInTheDocument();
    }
  });
  
  test('shows waiting state when not player turn', () => {
    const props = { ...defaultProps, isMyTurn: false };
    render(<DeclarationUI {...props} />);
    
    expect(screen.getByText(/waiting for/i)).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
  
  test('calls onDeclare when declaration is confirmed', () => {
    const onDeclare = jest.fn();
    const props = { ...defaultProps, onDeclare };
    
    render(<DeclarationUI {...props} />);
    
    // Click declaration option
    fireEvent.click(screen.getByText('3'));
    
    // Confirm in modal
    fireEvent.click(screen.getByText(/confirm/i));
    
    expect(onDeclare).toHaveBeenCalledWith(3);
  });
  
  test('filters out invalid options for last player', () => {
    const props = {
      ...defaultProps,
      declarations: { Player1: 2, Player2: 3, Player3: 1 },
      validOptions: [0, 1, 3, 4, 5, 6, 7, 8] // Excludes 2 (would make total 8)
    };
    
    render(<DeclarationUI {...props} />);
    
    expect(screen.queryByText('2')).not.toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });
});
```

#### Service Tests
```javascript
// tests/services/GameService.test.js
import GameService from '../src/services/GameService';
import NetworkService from '../src/services/NetworkService';

jest.mock('../src/services/NetworkService');

describe('GameService', () => {
  let gameService;
  let mockNetworkService;
  
  beforeEach(() => {
    mockNetworkService = new NetworkService();
    gameService = new GameService(mockNetworkService);
  });
  
  test('makeDeclaration validates input before sending', async () => {
    await expect(gameService.makeDeclaration(9))
      .rejects.toThrow('Declaration must be between 0 and 8');
    
    expect(mockNetworkService.sendAction).not.toHaveBeenCalled();
  });
  
  test('makeDeclaration sends correct action format', async () => {
    gameService.updateGameState({
      playerName: 'TestPlayer',
      currentDeclarer: 'TestPlayer'
    });
    
    await gameService.makeDeclaration(3);
    
    expect(mockNetworkService.sendAction).toHaveBeenCalledWith('declare', {
      player_name: 'TestPlayer',
      value: 3
    });
  });
});
```

### Test Coverage Goals

- **Backend**: Minimum 80% line coverage, 90% for critical paths
- **Frontend**: Minimum 70% line coverage, focus on user interactions
- **Integration**: Cover all happy paths and major error scenarios
- **End-to-End**: At least one complete game flow test

---

## Pull Request Process

### Before Creating a PR

1. **Run All Quality Checks**
   ```bash
   # Backend
   cd backend
   source venv/bin/activate
   black .  # Format code
   pylint engine/ api/ tests/  # Lint code
   python -m pytest tests/ -v  # Run tests
   
   # Frontend
   cd frontend
   npm run lint  # Lint code
   npm run type-check  # TypeScript validation
   npm test  # Run tests
   npm run build  # Verify build works
   ```

2. **Update Documentation**
   - Update API documentation if you changed endpoints
   - Add comments for complex logic
   - Update README if you changed setup process

3. **Write Tests**
   - Add unit tests for new functions
   - Add integration tests for new features
   - Update existing tests if behavior changed

### Creating the Pull Request

1. **PR Title**: Use conventional commit format
   ```
   feat(frontend): add turn result animation
   fix(backend): resolve state machine deadlock
   ```

2. **PR Description Template**:
   ```markdown
   ## Summary
   Brief description of what this PR does and why.
   
   ## Changes Made
   - [ ] Added new TurnResultsUI component
   - [ ] Implemented winner animation
   - [ ] Updated GameContainer to handle new phase
   - [ ] Added comprehensive tests
   
   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   - [ ] No breaking changes
   
   ## Screenshots/Videos
   (If UI changes, include screenshots or GIFs)
   
   ## Breaking Changes
   None / Describe any breaking changes
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests added/updated
   - [ ] No console errors or warnings
   ```

### PR Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one approval from a maintainer
3. **Testing**: Reviewer will test the changes locally
4. **Documentation**: Ensure docs are updated appropriately

### Review Criteria

**Code Quality**:
- [ ] Follows coding standards
- [ ] No code smells or anti-patterns
- [ ] Appropriate error handling
- [ ] Good variable and function names

**Architecture**:
- [ ] Uses enterprise patterns correctly
- [ ] Doesn't break existing abstractions
- [ ] Follows established patterns
- [ ] Considers performance implications

**Testing**:
- [ ] Adequate test coverage
- [ ] Tests are meaningful and correct
- [ ] Edge cases considered
- [ ] Integration tests for new features

**User Experience**:
- [ ] Intuitive and responsive UI
- [ ] Good error messages
- [ ] Consistent with existing design
- [ ] Accessible design patterns

---

## Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
A clear description of what the bug is.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What should happen instead.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g. macOS 12.0]
- Browser: [e.g. Chrome 96]
- Node.js version: [e.g. 16.14.0]
- Python version: [e.g. 3.9.7]

**Additional Context**
- Console errors
- Network tab information
- Backend logs if available
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Summary**
Brief description of the feature.

**Problem Statement**
What problem does this solve?

**Proposed Solution**
Detailed description of how it should work.

**Alternatives Considered**
Other approaches you've considered.

**Implementation Notes**
Technical considerations or constraints.

**Additional Context**
Mockups, user stories, or other relevant information.
```

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `frontend` - Frontend-related issue
- `backend` - Backend-related issue
- `priority: high/medium/low` - Priority level

---

## Documentation Standards

### Code Documentation

#### Python Docstrings
```python
def calculate_play_value(pieces: List[Piece]) -> int:
    """Calculate the total point value of a piece combination.
    
    This function sums the point values of all pieces in a play,
    which is used to determine the winner when play types are equal.
    
    Args:
        pieces: List of piece objects to calculate value for
        
    Returns:
        Total point value as integer
        
    Raises:
        ValueError: If pieces list is empty
        TypeError: If pieces contain non-Piece objects
        
    Example:
        >>> pieces = [Piece("GENERAL_RED", 10), Piece("HORSE_RED", 4)]
        >>> calculate_play_value(pieces)
        14
    """
```

#### TypeScript/JavaScript Documentation
```typescript
/**
 * Validates a declaration value for the current game state.
 * 
 * Checks if the proposed declaration is within valid range (0-8)
 * and doesn't violate the "last player cannot make total 8" rule.
 * 
 * @param value - The declaration value to validate (0-8)
 * @param currentDeclarations - Map of existing player declarations
 * @param totalPlayers - Total number of players in the game
 * @param isLastPlayer - Whether this is the last player to declare
 * @returns True if declaration is valid, false otherwise
 * 
 * @example
 * ```typescript
 * const isValid = validateDeclaration(3, {Player1: 2, Player2: 1}, 4, false);
 * // Returns: true
 * ```
 */
function validateDeclaration(
  value: number,
  currentDeclarations: Record<string, number>,
  totalPlayers: number,
  isLastPlayer: boolean
): boolean {
  // Implementation...
}
```

### API Documentation

Update the API Reference Manual when you:
- Add new WebSocket events
- Change message formats
- Add new HTTP endpoints
- Modify existing API behavior

### Architecture Documentation

Update relevant architecture docs when you:
- Add new components or services
- Change state management patterns
- Modify the state machine
- Add new external dependencies

---

## Release Process

### Version Numbering

We use **Semantic Versioning** (semver):
- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Pre-Release**
   - [ ] All tests passing
   - [ ] Documentation updated
   - [ ] Performance tested
   - [ ] Security review completed

2. **Version Bump**
   ```bash
   # Update version in package.json and pyproject.toml
   npm version minor  # or major/patch
   ```

3. **Release Notes**
   ```markdown
   ## v1.2.0 (2024-01-15)
   
   ### ✨ New Features
   - Added tournament mode with bracket management
   - Implemented spectator mode for watching games
   
   ### 🐛 Bug Fixes
   - Fixed WebSocket reconnection issue (#123)
   - Resolved state machine deadlock in turn phase (#124)
   
   ### 📝 Documentation
   - Updated API reference with new endpoints
   - Added troubleshooting guide for common issues
   
   ### ⚡ Performance
   - Optimized WebSocket message serialization
   - Reduced memory usage in long-running games
   ```

4. **Deployment**
   - Tag release in Git
   - Deploy to staging environment
   - Run smoke tests
   - Deploy to production
   - Monitor for issues

---

## Community Guidelines

### Code of Conduct

We're committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- **Be respectful** in all interactions
- **Be constructive** when giving feedback
- **Be patient** with newcomers
- **Be collaborative** in solving problems

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Pull Request Comments**: Code-specific discussions

### Getting Help

- **New to the project?** Start with the [Developer Onboarding Guide](DEVELOPER_ONBOARDING_GUIDE.md)
- **Technical questions?** Check the [Troubleshooting Guide](TROUBLESHOOTING_AND_DEBUGGING_GUIDE.md)
- **API questions?** See the [API Reference Manual](API_REFERENCE_MANUAL.md)
- **Architecture questions?** Read the [Technical Architecture Deep Dive](TECHNICAL_ARCHITECTURE_DEEP_DIVE.md)

### Recognition

Contributors will be recognized in:
- **README contributors section**
- **Release notes** for significant contributions
- **GitHub contributor graphs**
- **Special mentions** for exceptional contributions

---

## Advanced Topics

### Custom ESLint Rules

For complex projects, you might want custom linting rules:

```javascript
// .eslintrc.js
module.exports = {
  extends: ['react-app'],
  rules: {
    // Enforce enterprise architecture patterns
    'no-direct-state-mutation': 'error',
    'require-update-phase-data': 'error'
  }
};
```

### Pre-commit Hooks

Set up automatic code quality checks:

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: black
        name: black
        entry: black
        language: system
        files: \.py$
        
      - id: eslint
        name: eslint
        entry: npx eslint
        language: node
        files: \.(js|jsx|ts|tsx)$
```

### Performance Profiling

When optimizing performance:

```python
# Backend profiling
import cProfile
import pstats

def profile_game_action():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run game action
    result = await process_game_action(action)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

```javascript
// Frontend profiling
const startTime = performance.now();
await gameService.makeDeclaration(value);
const endTime = performance.now();
console.log(`Declaration took ${endTime - startTime} ms`);
```

---

## Conclusion

Thank you for contributing to Liap Tui! Your efforts help preserve a traditional game while showcasing modern software development practices. 

By following these guidelines, you'll help maintain the high quality and reliability that makes this project a great example of enterprise-grade game development.

Remember:
- **Quality over speed** - Take time to do it right
- **Test everything** - Multiplayer games are complex
- **Document your changes** - Help future contributors
- **Ask questions** - We're here to help

Happy coding! 🎮✨

---

*For technical details, see our other documentation:*
- *[Developer Onboarding Guide](DEVELOPER_ONBOARDING_GUIDE.md) - Getting started*
- *[Technical Architecture Deep Dive](TECHNICAL_ARCHITECTURE_DEEP_DIVE.md) - Understanding the system*
- *[API Reference Manual](API_REFERENCE_MANUAL.md) - Integration details*
- *[Troubleshooting Guide](TROUBLESHOOTING_AND_DEBUGGING_GUIDE.md) - Fixing issues*