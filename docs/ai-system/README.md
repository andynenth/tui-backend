# AI System Documentation

This directory contains all documentation related to the Liap Tui AI system, consolidated from multiple directories for better organization.

## Directory Structure

```
ai-system/
├── README.md                    # This file
├── overview/                    # High-level architecture and design
│   ├── AI_ARCHITECTURE.md       # System architecture
│   └── AI_SYSTEM_OVERVIEW.md    # Comprehensive system overview
│
├── debug-mode/                  # AI debugging tools and guides
│   ├── AI_DEBUG_MODE_COMPREHENSIVE.md  # Complete debug guide
│   ├── AI_DEBUG_QUICK_REFERENCE.md     # Quick reference
│   └── LOG_FORMAT.md            # Log format documentation
│
├── implementation/              # Detailed implementation docs
│   ├── declaration/            # Declaration phase AI
│   ├── evaluation/            # Hand evaluation logic
│   └── turn-play/             # Turn playing strategies
│
├── testing/                    # Testing strategies and reports
│   ├── AI_TESTING_PATTERNS.md
│   ├── AI_TESTING_WORKFLOW.md
│   └── test-results/          # Test execution results
│
└── bug-fixes/                 # Historical bug fixes and analyses
    ├── completed/             # Fixed issues
    └── analysis/              # Root cause analyses
```

## Quick Navigation

### For Users
- [AI Debug Mode Guide](./debug-mode/AI_DEBUG_MODE_COMPREHENSIVE.md) - How to debug AI behavior
- [Quick Reference](./debug-mode/AI_DEBUG_QUICK_REFERENCE.md) - Common commands and tips

### For Developers
- [AI Architecture](./overview/AI_ARCHITECTURE.md) - System design and components
- [Implementation Details](./implementation/) - Deep dive into AI logic
- [Testing Guide](./testing/AI_TESTING_WORKFLOW.md) - How to test AI changes

### For Debugging
- [Troubleshooting Guide](./debug-mode/AI_DEBUG_MODE_COMPREHENSIVE.md#troubleshooting) - Common issues
- [Log Analysis](./debug-mode/LOG_FORMAT.md) - Understanding AI logs

## Key Concepts

### AI Players
The system supports 4 AI players with consistent decision-making based on:
- Hand evaluation algorithms
- Strategic pile counting
- Risk assessment
- Pattern recognition

### Debug Mode
Special mode for testing AI behavior without WebSocket infrastructure:
- Direct game execution
- Detailed logging
- Performance profiling
- Bug detection

### Testing
Comprehensive testing framework:
- Unit tests for individual components
- Integration tests for game flow
- Performance benchmarks
- Regression tests

## Recent Updates

- **Consolidated Documentation** - All AI docs now in single directory
- **Comprehensive Debug Guide** - Merged multiple debug guides
- **Improved Organization** - Clear separation of concerns

## Contributing

When adding new AI documentation:
1. Place in appropriate subdirectory
2. Update this README
3. Follow existing naming conventions
4. Include examples where possible

## Legacy References

This directory consolidates content from:
- `/docs/07-ai-development/`
- `/docs/ai-debug-mode/`
- `/docs/ai-development/`

All content has been preserved and reorganized for better accessibility.
