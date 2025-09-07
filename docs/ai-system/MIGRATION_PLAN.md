# AI Documentation Migration Plan

This document tracks the migration of AI documentation from 3 directories into the unified `ai-system/` structure.

## Migration Status

### From `/docs/07-ai-development/`

#### To `overview/`
- [ ] AI_ARCHITECTURE.md → overview/AI_ARCHITECTURE.md
- [ ] AI_COMPREHENSIVE_ANALYSIS_REPORT.md → overview/AI_COMPREHENSIVE_ANALYSIS_REPORT.md
- [ ] AI_DATA_AVAILABILITY_SUMMARY.md → overview/AI_DATA_AVAILABILITY_SUMMARY.md

#### To `testing/`
- [ ] AI_TESTING_PATTERNS.md → testing/AI_TESTING_PATTERNS.md
- [ ] AI_TESTING_QUICK_REFERENCE.md → testing/AI_TESTING_QUICK_REFERENCE.md
- [ ] AI_TESTING_WORKFLOW.md → testing/AI_TESTING_WORKFLOW.md
- [ ] GAME_LOG_STRUCTURE.md → testing/GAME_LOG_STRUCTURE.md

#### To `implementation/`
- [ ] AI_DECLARATION_ANALYSIS.md → implementation/declaration/AI_DECLARATION_ANALYSIS.md
- [ ] AI_LOGGING_AND_ANALYSIS_PLAN.md → implementation/AI_LOGGING_AND_ANALYSIS_PLAN.md
- [ ] AI_RESPONDER_FIX_SUMMARY.md → implementation/AI_RESPONDER_FIX_SUMMARY.md
- [ ] LOGGING_IMPROVEMENTS_TODO.md → implementation/LOGGING_IMPROVEMENTS_TODO.md

#### To `bug-fixes/`
- [ ] bug-fixes/BOT4_WEAKNESS_ANALYSIS.md → bug-fixes/analysis/BOT4_WEAKNESS_ANALYSIS.md
- [ ] bug-fixes/NEVER_WIN_COMBO_*.md → bug-fixes/completed/NEVER_WIN_COMBO/
- [ ] bug-fixes/URGENCY_CALCULATION_ANALYSIS.md → bug-fixes/analysis/URGENCY_CALCULATION_ANALYSIS.md

#### Already Handled
- [x] AI_DEBUG_MODE.md → Redirects to comprehensive guide
- [ ] AI_TROUBLESHOOTING.md → Merge into debug-mode docs

### From `/docs/ai-debug-mode/`

#### To `debug-mode/`
- [x] AI_DEBUG_MODE_COMPREHENSIVE.md → debug-mode/AI_DEBUG_MODE_COMPREHENSIVE.md (copied)
- [ ] AI_DEBUG_MODE_FLOW_DIAGRAM.md → debug-mode/AI_DEBUG_MODE_FLOW_DIAGRAM.md
- [ ] AI_DEBUG_QUICK_REFERENCE.md → debug-mode/AI_DEBUG_QUICK_REFERENCE.md
- [ ] AI_DEBUG_TROUBLESHOOTING.md → Merge into comprehensive guide
- [ ] LOG_FORMAT.md → debug-mode/LOG_FORMAT.md
- [ ] AI_DEBUG_MODE_HOW_IT_WORKS.md → debug-mode/AI_DEBUG_MODE_HOW_IT_WORKS.md
- [ ] AI_IMPROVEMENT_INSIGHTS.md → debug-mode/AI_IMPROVEMENT_INSIGHTS.md

#### Already Handled
- [x] AI_DEBUG_MODE_GUIDE.md → Redirects to comprehensive guide
- [ ] README.md → Update to redirect
- [ ] INDEX.md → Update to redirect

### From `/docs/ai-development/`

#### To `overview/`
- [ ] ai_system_detailed_explanation.md → overview/AI_SYSTEM_DETAILED_EXPLANATION.md
- [ ] implementation/AI_SYSTEM_ARCHITECTURE.md → overview/AI_SYSTEM_ARCHITECTURE.md

#### To `implementation/declaration/`
- [ ] declaration/*.md → implementation/declaration/ (all 4 files)

#### To `implementation/evaluation/`
- [ ] evaluation/*.md → implementation/evaluation/ (all 3 files)

#### To `implementation/turn-play/`
- [ ] turn-play/*.md → implementation/turn-play/ (all 7 files)

#### To `implementation/`
- [ ] implementation/*.md → implementation/ (except AI_SYSTEM_ARCHITECTURE.md)
- [ ] dead_code_analysis_ai_py.md → implementation/dead_code_analysis_ai_py.md

## Migration Steps

1. **Phase 1: Structure Creation** ✅
   - Created directory structure
   - Created README.md
   - Copied AI_DEBUG_MODE_COMPREHENSIVE.md

2. **Phase 2: Core Files Migration** (Current)
   - Move architecture and overview files
   - Move testing documentation
   - Preserve file history with git mv

3. **Phase 3: Implementation Details**
   - Move all implementation subdirectories
   - Organize by functionality

4. **Phase 4: Cleanup**
   - Create redirects in old locations
   - Update all internal links
   - Remove empty directories

5. **Phase 5: Validation**
   - Verify all files moved
   - Check all links work
   - Update main documentation index

## Commands for Migration

```bash
# Example migration commands (to be run from project root)

# Move architecture files
git mv docs/07-ai-development/AI_ARCHITECTURE.md docs/ai-system/overview/
git mv docs/ai-development/implementation/AI_SYSTEM_ARCHITECTURE.md docs/ai-system/overview/

# Move testing files
git mv docs/07-ai-development/AI_TESTING_*.md docs/ai-system/testing/

# Move declaration files
git mv docs/ai-development/declaration/*.md docs/ai-system/implementation/declaration/

# Move evaluation files  
git mv docs/ai-development/evaluation/*.md docs/ai-system/implementation/evaluation/

# Move turn-play files
git mv docs/ai-development/turn-play/*.md docs/ai-system/implementation/turn-play/

# Move bug fixes
git mv docs/07-ai-development/bug-fixes/* docs/ai-system/bug-fixes/
```

## Link Updates Required

After migration, update links in:
- Main README.md
- CLAUDE.md
- Any AI-related documentation
- Test files that reference documentation

## Notes

- Use `git mv` to preserve file history
- Create redirect files in old locations
- Update this plan as migration progresses
- Some files may be consolidated during migration