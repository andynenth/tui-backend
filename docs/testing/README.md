# Testing Documentation

This directory contains all testing-related documentation for the Liap Tui project.

## Directory Structure

### `/refresh-bug/`
Documentation related to the WebSocket refresh/reconnection bug investigation and fix.

- **01_test_summary.md** - Initial test summary of refresh behavior across game phases
- **02_test_results.md** - Detailed test results from systematic refresh testing
- **03_test_checklist.md** - Comprehensive checklist used for refresh testing
- **04_bug_fix_test.md** - Documentation of the JSON serialization fix and testing
- **05_reconnection_fix_summary.md** - Summary of the reconnection system fixes

### `/reports/`
Comprehensive bug reports and test reports.

- **comprehensive_refresh_test_report.md** - Full report on refresh testing across all game phases
- **comprehensive_bug_report.md** - Detailed bug report with root cause analysis
- **bug_report_avatar_colors.md** - Specific bug report about avatar color issues

### `/guides/`
Testing guides and procedures for various aspects of the system.

- **ai_websocket_testing_guide.md** - Guide for AI assistants on WebSocket testing procedures

## Quick Reference

### For Investigating Refresh Issues
1. Start with `refresh-bug/01_test_summary.md` for an overview
2. Check `refresh-bug/03_test_checklist.md` for test scenarios
3. Review `reports/comprehensive_bug_report.md` for known issues

### For Testing WebSocket Features
1. Follow `guides/ai_websocket_testing_guide.md`
2. Use `refresh-bug/03_test_checklist.md` as a template

### For Understanding Fixes
1. Read `refresh-bug/04_bug_fix_test.md` for the JSON serialization fix
2. Check `refresh-bug/05_reconnection_fix_summary.md` for reconnection improvements

## Related Documentation

- `/DISCONNECT_SYSTEM_ARCHITECTURE.md` - Technical architecture of the disconnect/reconnect system
- `/backend/api/docs/WEBSOCKET_API.md` - WebSocket API documentation
- `/CODE_QUALITY_CHECKLIST.md` - Overall code quality tracking
