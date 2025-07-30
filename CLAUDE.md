# Claude Code Configuration - SPARC Development Environment

## 🚨 CRITICAL: CONCURRENT EXECUTION FOR ALL ACTIONS

**ABSOLUTE RULE**: ALL operations MUST be concurrent/parallel in a single message:

### 🔴 MANDATORY CONCURRENT PATTERNS:
1. **TodoWrite**: ALWAYS batch ALL todos in ONE call (5-10+ todos minimum)
2. **Task tool**: ALWAYS spawn ALL agents in ONE message with full instructions
3. **File operations**: ALWAYS batch ALL reads/writes/edits in ONE message
4. **Bash commands**: ALWAYS batch ALL terminal operations in ONE message
5. **Memory operations**: ALWAYS batch ALL memory store/retrieve in ONE message

### ⚡ GOLDEN RULE: "1 MESSAGE = ALL RELATED OPERATIONS"

**Examples of CORRECT concurrent execution:**
```javascript
// ✅ CORRECT: Everything in ONE message
[Single Message]:
  - TodoWrite { todos: [10+ todos with all statuses/priorities] }
  - Task("Agent 1 with full instructions and hooks")
  - Task("Agent 2 with full instructions and hooks")
  - Task("Agent 3 with full instructions and hooks")
  - Read("file1.js")
  - Read("file2.js")
  - Write("output1.js", content)
  - Write("output2.js", content)
  - Bash("npm install")
  - Bash("npm test")
  - Bash("npm run build")
```

## Project Overview
This project uses the SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) methodology for systematic Test-Driven Development with AI assistance through Claude-Flow orchestration.

**🚀 Batchtools Optimization Enabled**: This configuration includes optimized prompts and parallel processing capabilities for improved performance and efficiency.

## Standard Build Commands
- `npm run build`: Build the project
- `npm run test`: Run the test suite
- `npm run lint`: Run linter and format checks
- `npm run typecheck`: Run TypeScript type checking

## 🚀 CRITICAL: Claude Code Does ALL Real Work

### 🎯 CLAUDE CODE IS THE ONLY EXECUTOR

**ABSOLUTE RULE**: Claude Code performs ALL actual work:

### ✅ Claude Code ALWAYS Handles:
- 🔧 **ALL file operations** (Read, Write, Edit, MultiEdit, Glob, Grep)
- 💻 **ALL code generation** and programming tasks
- 🖥️ **ALL bash commands** and system operations
- 🏗️ **ALL actual implementation** work
- 🔍 **ALL project navigation** and code analysis
- 📝 **ALL TodoWrite** and task management
- 🔄 **ALL git operations** (commit, push, merge)
- 📦 **ALL package management** (npm, pip, etc.)
- 🧪 **ALL testing** and validation
- 🔧 **ALL debugging** and troubleshooting

### 🧠 Claude Flow MCP Tools ONLY Handle:
- 🎯 **Coordination only** - Planning Claude Code's actions
- 💾 **Memory management** - Storing decisions and context
- 🤖 **Neural features** - Learning from Claude Code's work
- 📊 **Performance tracking** - Monitoring Claude Code's efficiency
- 🐝 **Swarm orchestration** - Coordinating multiple Claude Code instances
- 🔗 **GitHub integration** - Advanced repository coordination

### ⚠️ Key Principle:
**MCP tools coordinate, Claude Code executes.** Think of MCP tools as the "brain" that plans and coordinates, while Claude Code is the "hands" that do all the actual work.

## 🚀 CRITICAL: Parallel Execution & Batch Operations

### 🚨 MANDATORY RULE #1: BATCH EVERYTHING

**When using swarms, you MUST use BatchTool for ALL operations:**

1. **NEVER** send multiple messages for related operations
2. **ALWAYS** combine multiple tool calls in ONE message
3. **PARALLEL** execution is MANDATORY, not optional

### ⚡ THE GOLDEN RULE OF SWARMS

```
If you need to do X operations, they should be in 1 message, not X messages
```

### 🚨 MANDATORY TODO AND TASK BATCHING

**CRITICAL RULE FOR TODOS AND TASKS:**

1. **TodoWrite** MUST ALWAYS include ALL todos in ONE call (5-10+ todos)
2. **Task** tool calls MUST be batched - spawn multiple agents in ONE message
3. **NEVER** update todos one by one - this breaks parallel coordination
4. **NEVER** spawn agents sequentially - ALL agents spawn together

## 📋 Additional Documentation

For detailed information on specific topics, see:

- **[SPARC Commands](./docs/CLAUDE-SPARC.md)** - SPARC methodology commands and workflows
- **[Agent Reference](./docs/CLAUDE-AGENTS.md)** - Complete list of 54 available agents and usage patterns
- **[Workflow Examples](./docs/CLAUDE-WORKFLOWS.md)** - Detailed workflow examples and patterns
- **[MCP Integration](./docs/CLAUDE-MCP.md)** - Claude Flow MCP tools and integration
- **[Performance Tips](./docs/CLAUDE-PERFORMANCE.md)** - Optimization strategies and benchmarks

## Important Notes

- Always run tests before committing with parallel execution (`npm run test --parallel`)
- Use SPARC memory system with concurrent operations to maintain context across sessions
- Follow the Red-Green-Refactor cycle with parallel test generation during TDD phases
- Document architectural decisions with concurrent validation in memory
- Regular security reviews with parallel analysis for authentication or data handling code
- Claude Code slash commands provide quick access to batchtools-optimized SPARC modes
- Monitor system resources during parallel operations for optimal performance

## Support

- Documentation: https://github.com/ruvnet/claude-flow
- Issues: https://github.com/ruvnet/claude-flow/issues
- Examples: https://github.com/ruvnet/claude-flow/tree/main/examples

---

Remember: **Claude Flow coordinates, Claude Code creates!** Start with `mcp__claude-flow__swarm_init` to enhance your development workflow.