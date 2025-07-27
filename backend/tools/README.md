# Backend Tools

This directory contains utility scripts and tools for managing the clean architecture migration and codebase maintenance.

## Available Tools

### 1. Architecture Type Identifier
**File**: `identify_architecture_type.py`

**Purpose**: Analyzes Python files to determine if they belong to legacy or clean architecture.

**Usage**:
```bash
# Analyze entire backend directory
python tools/identify_architecture_type.py --directory backend --output architecture_analysis.json

# Check a specific file
python tools/identify_architecture_type.py --file backend/domain/services/scoring_service.py --verbose

# Analyze with detailed output
python tools/identify_architecture_type.py --directory backend --verbose
```

**Output**:
- Classification of files as: `legacy`, `clean`, `hybrid`, `bridge`, or `enterprise`
- Confidence scores for each classification
- Identification of cross-dependencies
- Detailed JSON report with full analysis

## Planned Tools (Phase 7)

The following tools are planned for Phase 7 implementation:

### 2. Legacy Scanner
**File**: `legacy_scanner.py` (to be created)

**Purpose**: Deep scan for legacy code patterns and dependencies.

### 3. Legacy Monitor
**File**: `legacy_monitor.py` (to be created)

**Purpose**: Real-time monitoring of legacy code usage in production.

### 4. Removal Validator
**File**: `removal_validator.py` (to be created)

**Purpose**: Validate safety of removing specific legacy components.

### 5. Rollback Manager
**File**: `rollback_manager.py` (to be created)

**Purpose**: Manage rollback procedures for legacy code restoration.

## Usage Guidelines

1. Always run tools from the backend directory:
   ```bash
   cd backend
   python tools/identify_architecture_type.py [options]
   ```

2. Review output carefully before making architectural decisions.

3. Use verbose mode for detailed analysis of specific concerns.

4. Save JSON output for tracking progress over time.

## Related Documentation

- [Legacy vs Clean Identification Guide](../docs/task3-abstraction-coupling/implementation/guides/LEGACY_VS_CLEAN_IDENTIFICATION_GUIDE.md)
- [Phase 7: Legacy Code Removal Plan](../docs/task3-abstraction-coupling/planning/PHASE_7_LEGACY_CODE_REMOVAL.md)

---
*Last Updated: 2025-07-27*