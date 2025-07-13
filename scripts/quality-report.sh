#!/bin/bash
# Quality Report Generator
# Generates a comprehensive quality report for the project

echo "========================================"
echo "     CODE QUALITY REPORT"
echo "     Generated: $(date)"
echo "========================================"
echo ""

# Frontend Metrics
echo "📊 FRONTEND METRICS"
echo "==================="
echo ""

echo "ESLint Analysis:"
if command -v npm &> /dev/null; then
    ERROR_COUNT=$(npm run lint 2>&1 | grep -E "✖|error" | grep -E "[0-9]+ problems" | grep -oE "[0-9]+" | head -1)
    WARNING_COUNT=$(npm run lint 2>&1 | grep -E "⚠|warning" | grep -oE "[0-9]+" | head -1)
    echo "  - Errors: ${ERROR_COUNT:-0}"
    echo "  - Warnings: ${WARNING_COUNT:-0}"
else
    echo "  - npm not found"
fi
echo ""

echo "TypeScript Check:"
if [ -f "tsconfig.json" ]; then
    TS_ERRORS=$(npm run type-check 2>&1 | grep -c "error TS" || echo "0")
    echo "  - Type Errors: $TS_ERRORS"
else
    echo "  - No TypeScript config found"
fi
echo ""

echo "Test Coverage:"
if [ -f "jest.config.js" ]; then
    echo "  - Run 'npm run test:coverage' for detailed report"
else
    echo "  - Jest not configured"
fi
echo ""

# Backend Metrics
echo "📊 BACKEND METRICS"
echo "=================="
echo ""

echo "Python Code Quality:"
if command -v python &> /dev/null; then
    cd backend 2>/dev/null && {
        echo "  Running pylint analysis..."
        python -m pylint engine/ api/ --exit-zero 2>/dev/null | grep "Your code has been rated" || echo "  - Pylint not installed"
        cd - > /dev/null
    } || echo "  - Backend directory not found"
else
    echo "  - Python not found"
fi
echo ""

# Code Statistics
echo "📊 CODE STATISTICS"
echo "=================="
echo ""

echo "File Counts:"
echo "  - JavaScript/JSX files: $(find . -name "*.js" -o -name "*.jsx" | grep -v node_modules | wc -l)"
echo "  - TypeScript/TSX files: $(find . -name "*.ts" -o -name "*.tsx" | grep -v node_modules | wc -l)"
echo "  - Python files: $(find . -name "*.py" | grep -v __pycache__ | wc -l)"
echo "  - Test files: $(find . -name "*.test.*" -o -name "test_*.py" | grep -v node_modules | wc -l)"
echo ""

echo "Documentation:"
echo "  - Markdown files: $(find . -name "*.md" | grep -v node_modules | wc -l)"
echo "  - TODO comments: $(grep -r "TODO" --exclude-dir=node_modules --exclude-dir=.git . 2>/dev/null | wc -l)"
echo "  - FIXME comments: $(grep -r "FIXME" --exclude-dir=node_modules --exclude-dir=.git . 2>/dev/null | wc -l)"
echo ""

# Component Analysis
echo "📊 COMPONENT ANALYSIS"
echo "===================="
echo ""

echo "React Components:"
TOTAL_COMPONENTS=$(find ./frontend/src/components -name "*.jsx" -o -name "*.tsx" 2>/dev/null | wc -l)
TESTED_COMPONENTS=$(find ./frontend/src -name "*.test.jsx" -o -name "*.test.tsx" 2>/dev/null | wc -l)
echo "  - Total: $TOTAL_COMPONENTS"
echo "  - With tests: $TESTED_COMPONENTS"
echo "  - Coverage: $(( TESTED_COMPONENTS * 100 / (TOTAL_COMPONENTS + 1) ))%"
echo ""

# Git Statistics
echo "📊 GIT STATISTICS"
echo "================"
echo ""

if [ -d ".git" ]; then
    echo "Recent Activity:"
    echo "  - Commits today: $(git log --since="1 day ago" --oneline 2>/dev/null | wc -l)"
    echo "  - Commits this week: $(git log --since="1 week ago" --oneline 2>/dev/null | wc -l)"
    echo "  - Contributors: $(git log --format="%an" | sort -u | wc -l)"
else
    echo "  - Not a git repository"
fi
echo ""

# Quality Checklist Status
echo "📋 QUALITY CHECKLIST STATUS"
echo "=========================="
echo ""

if [ -f "CODE_QUALITY_CHECKLIST.md" ]; then
    TOTAL_ITEMS=$(grep -c "^- \[ \]" CODE_QUALITY_CHECKLIST.md || echo "0")
    COMPLETED_ITEMS=$(grep -c "^- \[x\]" CODE_QUALITY_CHECKLIST.md || echo "0")
    echo "  - Total items: $TOTAL_ITEMS"
    echo "  - Completed: $COMPLETED_ITEMS"
    echo "  - Progress: $(( COMPLETED_ITEMS * 100 / (TOTAL_ITEMS + 1) ))%"
else
    echo "  - CODE_QUALITY_CHECKLIST.md not found"
fi
echo ""

echo "========================================"
echo "Report complete. For detailed analysis,"
echo "check individual tool outputs."
echo "========================================"