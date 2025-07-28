# Legacy Code Quarantine

This directory contains legacy code that has been isolated during Phase 7.2 of the clean architecture migration.

## Status
- **Phase**: 7.2 (Legacy Code Isolation)
- **Date**: 2025-07-27
- **Purpose**: Temporary quarantine before permanent removal

## Directory Structure
```
legacy/
├── README.md                # This file
├── engine/                  # Legacy engine components
│   ├── room_manager.py
│   ├── async_room_manager.py
│   ├── game.py
│   ├── bot_manager.py
│   ├── scoring.py
│   └── ... (other legacy engine files)
├── tests/                   # Legacy test files
├── config/                  # Legacy configuration
└── api/                     # Legacy API components
```

## Important Notes

⚠️ **WARNING**: All files in this directory are scheduled for removal in Phase 7.4.

- These files are NO LONGER part of the active codebase
- They have been replaced by clean architecture components
- Any imports from these files indicate a problem
- The system should function without any of these files

## Migration Status

All functionality provided by these legacy files has been reimplemented in:
- `domain/` - Core business logic
- `application/` - Use cases and services
- `infrastructure/` - External integrations
- `api/adapters/` - WebSocket adapters

## Rollback Procedure

If rollback is needed:
1. Move files back to their original locations
2. Re-enable legacy feature flags
3. Restart services

## Removal Timeline

- Phase 7.2: Files moved to quarantine (CURRENT)
- Phase 7.3: Final validation with quarantined files
- Phase 7.4: Permanent deletion