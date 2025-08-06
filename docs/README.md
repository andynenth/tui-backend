# Liap Tui Documentation

Welcome to the comprehensive documentation for the Liap Tui project. This documentation is organized to help developers understand, contribute to, and deploy the application.

## 📚 Documentation Structure

### Teaching Materials (Organized by Category)

The teaching materials are systematically organized into 7 categories with 27 comprehensive documents:

#### 1. **[01-overview/](01-overview/)** - High-Level Architecture
- [README.md](01-overview/README.md) - Project overview and architecture diagram
- [TECH_STACK.md](01-overview/TECH_STACK.md) - Technology choices and rationale
- [DESIGN_PRINCIPLES.md](01-overview/DESIGN_PRINCIPLES.md) - Core architectural decisions

#### 2. **[02-flow-traces/](02-flow-traces/)** - Application Flows
- [STARTUP_FLOW.md](02-flow-traces/STARTUP_FLOW.md) - Application initialization sequence
- [USER_JOURNEY.md](02-flow-traces/USER_JOURNEY.md) - Complete user flow from start to game over
- [WEBSOCKET_FLOW.md](02-flow-traces/WEBSOCKET_FLOW.md) - WebSocket message patterns and lifecycle
- [STATE_TRANSITIONS.md](02-flow-traces/STATE_TRANSITIONS.md) - Game state machine transitions

#### 3. **Component Deep Dives**
##### [03-backend-deep-dives/](03-backend-deep-dives/)
- [STATE_MACHINE.md](03-backend-deep-dives/STATE_MACHINE.md) - Enterprise architecture deep dive
- [ROOM_MANAGER.md](03-backend-deep-dives/ROOM_MANAGER.md) - Room lifecycle management
- [GAME_ENGINE.md](03-backend-deep-dives/GAME_ENGINE.md) - Core game logic implementation
- [WEBSOCKET_HANDLER.md](03-backend-deep-dives/WEBSOCKET_HANDLER.md) - WebSocket connection handling

##### [03-frontend-deep-dives/](03-frontend-deep-dives/)
- [REACT_ARCHITECTURE.md](03-frontend-deep-dives/REACT_ARCHITECTURE.md) - Component hierarchy and patterns
- [CONTEXT_SYSTEM.md](03-frontend-deep-dives/CONTEXT_SYSTEM.md) - State management with React Context
- [NETWORK_SERVICE.md](03-frontend-deep-dives/NETWORK_SERVICE.md) - WebSocket client implementation
- [GAME_UI_FLOW.md](03-frontend-deep-dives/GAME_UI_FLOW.md) - Game phase UI components

#### 4. **[04-data-structures/](04-data-structures/)** - Data Formats and Schemas
- [MESSAGE_FORMATS.md](04-data-structures/MESSAGE_FORMATS.md) - WebSocket message schemas
- [GAME_STATE.md](04-data-structures/GAME_STATE.md) - State shape at each game phase
- [DATABASE_SCHEMA.md](04-data-structures/DATABASE_SCHEMA.md) - Future data persistence design
- [API_CONTRACTS.md](04-data-structures/API_CONTRACTS.md) - Frontend-backend interface contracts

#### 5. **[05-patterns-practices/](05-patterns-practices/)** - Patterns and Best Practices
- [ENTERPRISE_PATTERN.md](05-patterns-practices/ENTERPRISE_PATTERN.md) - Enterprise architecture implementation
- [ERROR_HANDLING.md](05-patterns-practices/ERROR_HANDLING.md) - Resilience and error recovery patterns
- [TESTING_STRATEGY.md](05-patterns-practices/TESTING_STRATEGY.md) - Testing architecture and patterns
- [DEPLOYMENT_PATTERNS.md](05-patterns-practices/DEPLOYMENT_PATTERNS.md) - AWS ECS deployment setup

#### 6. **[06-tutorials/](06-tutorials/)** - Hands-On Guides
- [LOCAL_DEVELOPMENT.md](06-tutorials/LOCAL_DEVELOPMENT.md) - Development environment setup
- [ADDING_FEATURES.md](06-tutorials/ADDING_FEATURES.md) - Step-by-step feature addition guide
- [DEBUGGING_GUIDE.md](06-tutorials/DEBUGGING_GUIDE.md) - Common issues and solutions
- [DEPLOYMENT_GUIDE.md](06-tutorials/DEPLOYMENT_GUIDE.md) - AWS deployment walkthrough

### Additional Documentation

These documents provide specific technical details and historical context:

#### API & Integration
- [WEBSOCKET_API.md](WEBSOCKET_API.md) - WebSocket API reference
- [API_REFERENCE_MANUAL.md](API_REFERENCE_MANUAL.md) - Complete API documentation

#### Architecture & Design
- [ENTERPRISE_ARCHITECTURE.md](ENTERPRISE_ARCHITECTURE.md) - Enterprise patterns overview
- [TECHNICAL_ARCHITECTURE_DEEP_DIVE.md](TECHNICAL_ARCHITECTURE_DEEP_DIVE.md) - Detailed architecture analysis
- [Liap Tui System Architecture Overview.md](Liap%20Tui%20System%20Architecture%20Overview.md) - System-level view

#### Game Mechanics
- [GAME_RULES_AND_FLOW.md](GAME_RULES_AND_FLOW.md) - Complete game rules
- [GAME_LIFECYCLE_DOCUMENTATION.md](GAME_LIFECYCLE_DOCUMENTATION.md) - Game lifecycle details
- [piece-system.md](piece-system.md) - Piece system implementation
- Phase Diagrams:
  - [PREPARATION_PHASE_DIAGRAM.md](PREPARATION_PHASE_DIAGRAM.md)
  - [DECLARATION_PHASE_DIAGRAM.md](DECLARATION_PHASE_DIAGRAM.md)
  - [TURN_PHASE_DIAGRAM.md](TURN_PHASE_DIAGRAM.md)
  - [SCORING_PHASE_DIAGRAM.md](SCORING_PHASE_DIAGRAM.md)

#### Operations & Monitoring
- [Monitoring and Observability System.md](Monitoring%20and%20Observability%20System.md) - Monitoring setup
- [EVENT_STORE_DOCUMENTATION.md](EVENT_STORE_DOCUMENTATION.md) - Event sourcing system
- [disconnect_handling.md](disconnect_handling.md) - Connection management

#### Development & Contributing
- [DEVELOPER_ONBOARDING_GUIDE.md](DEVELOPER_ONBOARDING_GUIDE.md) - Getting started guide
- [CONTRIBUTING_GUIDE.md](CONTRIBUTING_GUIDE.md) - Contribution guidelines
- [PROJECT_HISTORY_AND_DECISIONS.md](PROJECT_HISTORY_AND_DECISIONS.md) - Project evolution
- [CLAUDE_LOG_ACCESS.md](CLAUDE_LOG_ACCESS.md) - AI assistant integration

#### Troubleshooting
- [TROUBLESHOOTING_AND_DEBUGGING_GUIDE.md](TROUBLESHOOTING_AND_DEBUGGING_GUIDE.md) - Common issues
- [troubleshooting.md](troubleshooting.md) - Quick troubleshooting reference

#### Tools & Plugins
- [ESBUILD_CSS_MODULES_PLUGIN_GUIDE.md](ESBUILD_CSS_MODULES_PLUGIN_GUIDE.md) - CSS modules setup

## 🚀 Getting Started

1. **New to the project?** Start with:
   - [01-overview/README.md](01-overview/README.md) - Project overview
   - [06-tutorials/LOCAL_DEVELOPMENT.md](06-tutorials/LOCAL_DEVELOPMENT.md) - Setup guide
   - [02-flow-traces/USER_JOURNEY.md](02-flow-traces/USER_JOURNEY.md) - Understand the flow

2. **Contributing code?** Read:
   - [06-tutorials/ADDING_FEATURES.md](06-tutorials/ADDING_FEATURES.md) - How to add features
   - [05-patterns-practices/ENTERPRISE_PATTERN.md](05-patterns-practices/ENTERPRISE_PATTERN.md) - Code patterns
   - [CONTRIBUTING_GUIDE.md](CONTRIBUTING_GUIDE.md) - Contribution process

3. **Debugging issues?** Check:
   - [06-tutorials/DEBUGGING_GUIDE.md](06-tutorials/DEBUGGING_GUIDE.md) - Debugging guide
   - [05-patterns-practices/ERROR_HANDLING.md](05-patterns-practices/ERROR_HANDLING.md) - Error patterns
   - [troubleshooting.md](troubleshooting.md) - Quick fixes

4. **Deploying to production?** See:
   - [06-tutorials/DEPLOYMENT_GUIDE.md](06-tutorials/DEPLOYMENT_GUIDE.md) - Step-by-step deployment
   - [05-patterns-practices/DEPLOYMENT_PATTERNS.md](05-patterns-practices/DEPLOYMENT_PATTERNS.md) - AWS patterns
   - [Monitoring and Observability System.md](Monitoring%20and%20Observability%20System.md) - Monitoring setup

## 📖 Document Categories

- **Teaching Materials**: Systematically organized educational content (folders 01-06)
- **Reference**: API documentation and technical specifications
- **Architecture**: System design and architectural decisions
- **Operations**: Deployment, monitoring, and maintenance guides
- **Game Design**: Rules, mechanics, and phase documentation

## 🔍 Finding Information

1. **By Topic**: Use the categorized structure (01-06 folders)
2. **By Component**: Check the deep-dive sections (03-backend/frontend)
3. **By Task**: See tutorials (06-tutorials)
4. **By Problem**: Check debugging and troubleshooting guides

## 📝 Documentation Standards

All documentation follows these principles:
- Clear purpose statement at the beginning
- Visual diagrams where applicable
- Code examples with annotations
- Real data/message examples
- Design rationale explained
- Common pitfalls highlighted

---

Happy coding! If you can't find what you're looking for, check the [TEACHING_MATERIALS_CHECKLIST.md](../TEACHING_MATERIALS_CHECKLIST.md) for a complete list of all documentation.