# AI Debug Mode Documentation

**📍 MIGRATION NOTICE**: This directory's content is being consolidated into [`/docs/ai-system/debug-mode/`](../ai-system/debug-mode/) for better organization.

This directory contains all documentation related to the AI Debug Mode feature of Liap Tui.

## 📚 Documentation Structure

### Getting Started
- **[AI_DEBUG_MODE_GUIDE.md](AI_DEBUG_MODE_GUIDE.md)** - Complete user guide with examples
- **[AI_DEBUG_QUICK_REFERENCE.md](AI_DEBUG_QUICK_REFERENCE.md)** - Quick command reference card

### Technical Documentation
- **[AI_DEBUG_MODE_HOW_IT_WORKS.md](AI_DEBUG_MODE_HOW_IT_WORKS.md)** - Technical deep dive into internals
- **[AI_DEBUG_MODE_FLOW_DIAGRAM.md](AI_DEBUG_MODE_FLOW_DIAGRAM.md)** - Visual flow diagrams
- **[LOG_FORMAT.md](LOG_FORMAT.md)** - JSON log format specification

### AI Analysis
- **[AI_IMPROVEMENT_INSIGHTS.md](AI_IMPROVEMENT_INSIGHTS.md)** - AI strategy analysis and improvement suggestions
- **[AI_DEBUG_TROUBLESHOOTING.md](AI_DEBUG_TROUBLESHOOTING.md)** - Common issues and solutions

### Project History
- **[AI_DEBUG_MODE_PLAN_UPDATED.md](AI_DEBUG_MODE_PLAN_UPDATED.md)** - Original plan vs actual implementation
- **[AI_DEBUG_MODE_PROGRESS.md](AI_DEBUG_MODE_PROGRESS.md)** - Implementation progress tracking
- **[AI_DEBUG_MODE_COMPLETION_SUMMARY.md](AI_DEBUG_MODE_COMPLETION_SUMMARY.md)** - Project completion summary
- **[AI_DEBUG_MODE_CHECKLIST.md](AI_DEBUG_MODE_CHECKLIST.md)** - Original implementation checklist
- **[AI_DEBUG_MODE_PLAN.md](AI_DEBUG_MODE_PLAN.md)** - Original detailed plan (historical)

## 🚀 Quick Start

If you're new to AI Debug Mode:
1. Start with the **[User Guide](AI_DEBUG_MODE_GUIDE.md)**
2. Keep the **[Quick Reference](AI_DEBUG_QUICK_REFERENCE.md)** handy
3. If you encounter issues, check **[Troubleshooting](AI_DEBUG_TROUBLESHOOTING.md)**

For developers wanting to understand the implementation:
1. Read **[How It Works](AI_DEBUG_MODE_HOW_IT_WORKS.md)**
2. Review the **[Flow Diagrams](AI_DEBUG_MODE_FLOW_DIAGRAM.md)**
3. Understand the **[Log Format](LOG_FORMAT.md)**

## 📁 Related Code

The AI Debug Mode implementation is located at:
- Main script: `backend/ai_debug_simple.py`
- Logger: `backend/services/ai_logger.py`
- Bug detector: `backend/services/ai_bug_detector.py`
- Analysis tools: `backend/tools/analyze_*.py`
- Tests: `tests/ai_debug/`

## 🎯 Purpose

AI Debug Mode allows you to:
- Run AI-only games without WebSocket infrastructure
- Analyze AI decision-making with detailed logs
- Detect bugs in AI logic automatically
- Benchmark performance (~7 games/second)
- Generate statistics for AI improvement

## 📦 Migration Status

### ✅ Completed
- **Comprehensive Guide Created**: All debug mode content merged into [AI Debug Mode Comprehensive Guide](../ai-system/debug-mode/AI_DEBUG_MODE_COMPREHENSIVE.md)
- **Directory Structure**: New location at `/docs/ai-system/debug-mode/`

### 🔄 In Progress
- Moving individual guide files
- Updating all cross-references
- Creating redirects

### 📌 New Users Should:
1. Go directly to the [Comprehensive Guide](../ai-system/debug-mode/AI_DEBUG_MODE_COMPREHENSIVE.md)
2. Use the new [`/docs/ai-system/`](../ai-system/) structure
3. Refer to the [AI System README](../ai-system/README.md) for navigation