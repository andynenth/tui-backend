# AI Bug Fix Checklist

**IMPORTANT**: This checklist MUST be followed for every AI bug fix. Check off each item as completed.

## Pre-Fix Checklist

- [ ] Bug clearly identified with specific game data
- [ ] Room ID: _______________
- [ ] Bot name: _______________
- [ ] Round/Turn: _______________
- [ ] Expected behavior vs Actual behavior documented
- [ ] Game data extracted and saved to `game-data/`

## Investigation Checklist

- [ ] Created minimal reproduction test
- [ ] Traced actual AI decision (no assumptions)
- [ ] Identified exact function and line causing issue
- [ ] Root cause documented
- [ ] Checked for similar issues in other code paths

## Fix Implementation Checklist

- [ ] Fix designed with minimal impact
- [ ] Code change implemented
- [ ] Comments added explaining the fix
- [ ] No unnecessary refactoring

## Testing Checklist

- [ ] Created regression test in `tests/ai_regression/`
- [ ] Test includes: Original bug case
- [ ] Test includes: Contrast case (opposite scenario)
- [ ] Test includes: Related edge cases
- [ ] All regression tests pass: `python tests/ai_regression/run_all_regression_tests.py`
- [ ] No existing tests broken

## Documentation Checklist

- [ ] `FIX_HISTORY.md` updated with:
  - [ ] Date
  - [ ] Bug description
  - [ ] Root cause
  - [ ] Fix details (file, line numbers)
  - [ ] Test file name
- [ ] Regression test has clear docstring
- [ ] Code comments explain why fix was needed

## Verification Checklist

- [ ] Re-ran original game scenario
- [ ] AI now makes correct decision
- [ ] No unexpected side effects observed
- [ ] Performance impact assessed (if applicable)

## Sign-off

- Date completed: _______________
- Tester: _______________
- All items checked: [ ]

---

**Reminder**: If you skip any item, document why in the commit message.
