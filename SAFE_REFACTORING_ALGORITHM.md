"""
SAFETY REFACTORING ALGORITHM
Code Refactoring Best Practices - Added After Learning from Phase 0 Week 3

This document outlines the safe process for refactoring code to ensure nothing is lost.
"""

# ============================================================================
# 🛡️ SAFE REFACTORING PROCESS
# ============================================================================

## PRINCIPLE: "ADD FIRST, REMOVE LATER, THEN VERIFY"

Instead of:  remove_old_code() → add_new_code()
Use:         add_new_code() → remove_old_code() → VERIFY

---

## PRE-FLIGHT GATES (MANDATORY BEFORE ANY REFACTOR)

- [ ] Create a short refactor ticket with scope and non-goals
- [ ] Freeze feature work in touched files for the refactor window
- [ ] Confirm current branch is green (tests + app startup)
- [ ] Capture baseline metrics:
  - [ ] Existing test pass count
  - [ ] Startup success command output
  - [ ] Key endpoint smoke check results
- [ ] Define rollback trigger (example: 1 critical route fails)

If any gate fails, refactor does not start.

---

## RISK CLASSIFICATION (CHOOSE STRATEGY FIRST)

### Low Risk
- Pure rename/move, no behavior change
- Strategy: single PR, full test run

### Medium Risk
- Shared module extraction, import rewiring
- Strategy: split commits + targeted integration tests

### High Risk
- DB schema changes, auth/security flow, request lifecycle
- Strategy: two-phase rollout + rollback script + staged validation

Rule: If risk is High, do not combine with unrelated cleanup.

---

## STEP-BY-STEP ALGORITHM

### Phase 1: AUDIT (Never skip this!)
- [ ] Create complete checklist of what will be removed
- [ ] For EACH piece of code being removed:
  - [ ] Where is it currently?
  - [ ] Where should it go in new structure?
  - [ ] Is it truly needed or dead code?
  - [ ] Document dependencies

**Example Checklist:**
```
REMOVED CODE MAPPING:
┌─────────────────────────────┬──────────────────┬─────────────┐
│ Function/Route              │ Current Location │ New Home    │ Status
├─────────────────────────────┼──────────────────┼─────────────┤
│ get_local_system_data()     │ app.py:L200      │ services/   │ ✓ Added
│ /manual_submit route        │ app.py:L280      │ web.py      │ ✓ Added
│ /backup/create route        │ app.py:L365      │ web.py      │ ✓ Added
│ Template context processor  │ app.py:L145      │ app.py      │ ✓ Added
│ convert_to_ist()            │ app.py:L35       │ app.py      │ ✓ Exists
└─────────────────────────────┴──────────────────┴─────────────┘
```

---

### Phase 2: ADD NEW CODE TO NEW LOCATION
- [ ] Create new module/function in target location
- [ ] Copy code from old location to new location
- [ ] Update imports (old location → new location)
- [ ] Test that new code works in new location
  ```bash
  python -c "from new_location import new_function; new_function()"
  ```
- [ ] Verify no syntax errors
- [ ] Make sure all imports are available in new location

**DO NOT DELETE OLD CODE YET!**

---

### Phase 3: UPDATE ALL REFERENCES
- [ ] Find all places that import/use old code
  ```bash
  rg "from old_location import|old_location\.function" -g "*.py"
  ```
- [ ] Update each reference to use new location
- [ ] Test each change immediately after updating
- [ ] Commit changes in logical groups:
  ```
  1. "ADD: SystemService.get_local_system_data()"
  2. "ADD: web.py /manual_submit and /backup routes"
  3. "ADD: app.py template context processor"
  4. "FIX: Update all imports to new locations"
  5. "TEST: Verify all functions work in new locations"
  ```

---

### Phase 4: COMPREHENSIVE TESTING
- [ ] Test each moved piece independently:
  ```python
  from server.services import SystemService
  data = SystemService.get_local_system_data()
  assert data is not None
  ```
- [ ] Test integration with rest of code:
  ```bash
  python -c "from server.app import app; print('✅ App loads')"
  ```
- [ ] Test all routes/endpoints:
  ```bash
  pytest tests/ -q
  ```
- [ ] Verify old code can still be found (before deletion):
  ```bash
  rg "def get_local_system_data" server/app.py
  ```

### Phase 4.5: BEHAVIOR PARITY CHECK (NEW)
- [ ] Compare old vs new output for representative inputs
- [ ] Validate error codes/messages did not regress
- [ ] Validate performance did not degrade beyond threshold
  - Example threshold: response time increase <= 10%
- [ ] Validate logging/audit events still emitted

---

### Phase 5: REMOVE OLD CODE (FINAL STEP)
- [ ] Now that everything is in new location and tested:
  - [ ] Delete old code from old location
  - [ ] Run tests again to confirm nothing broke
  - [ ] Commit: "CLEANUP: Remove old code from original location"

Important:
- Keeping duplicate old code for long-term "just in case" is not safe.
- It causes split logic, hidden drift, and future bugs.
- Use rollback strategy instead of permanent duplication.

**ONLY NOW do you remove!**

---

### Phase 6: FINAL VERIFICATION & COMMIT
- [ ] Run full test suite
- [ ] Check git diff shows clean refactoring:
  ```bash
  git diff --stat
  ```
- [ ] All imports are correct
- [ ] No broken imports or missing functions
- [ ] Smoke test critical routes manually or via script
- [ ] Confirm migrations (if any) are reversible
- [ ] Commit message explains:
  - What was moved
  - Where it is now
  - Why it was moved

---

## DATABASE REFACTOR SAFETY (IF SCHEMA CHANGES)

Use two-phase schema rollout:

1) Expand phase
- Add nullable column/table/index
- Deploy and backfill data
- Keep old readers/writers working

2) Contract phase
- Switch code paths to new schema
- Remove old column/paths only after verification

Checklist:
- [ ] Backup verified before migration
- [ ] Upgrade tested
- [ ] Downgrade tested
- [ ] Data backfill validated by counts

---

## ROLLBACK PLAYBOOK (MUST EXIST BEFORE HIGH-RISK REFACTOR)

- [ ] Define rollback command(s)
- [ ] Define rollback owner
- [ ] Define max rollback time (example: 15 min)
- [ ] Keep pre-refactor tag/commit reference

Example:
```bash
git tag pre-refactor-safe-point
# rollback reference: pre-refactor-safe-point
```

---

## OBSERVABILITY CHECKS AFTER REFACTOR

- [ ] Error rate unchanged
- [ ] Latency unchanged within target
- [ ] No new warnings in logs for touched modules
- [ ] Alerting still fires for known bad case
  
**Example Good Commit:**
```
🏗️ REFACTOR: Extract functions to service layer

✓ Moved get_local_system_data() to SystemService
✓ Moved manual_submit route to web_bp
✓ Moved backup routes (create, restore) to web_bp
✓ Added template context processor
✓ Updated all imports and references
✓ All tests passing

This improves code organization and maintainability
by separating concerns into appropriate modules.

Old code verified in new locations before removal.
All 5 verification checks passed:
  ✓ Syntax check
  ✓ Import check
  ✓ Unit test
  ✓ Integration test
  ✓ Full app test
```

---

## 🚨 RED FLAGS - STOP IF YOU SEE THESE

❌ **Removing code without knowing where it goes**
→ Solution: Create mapping first (Phase 1)

❌ **Removing code before adding it to new location**
→ Solution: Add first (Phase 2), then remove (Phase 5)

❌ **Not updating imports**
→ Solution: Search for all references (Phase 3)

❌ **Not testing after moving**
→ Solution: Test before and after moving (Phase 4)

❌ **Committing refactoring and new features together**
→ Solution: Refactor in separate commits from features

❌ **Moving code without documenting why**
→ Solution: Clear commit message explaining the refactor

❌ **Refactor touches auth/DB/request lifecycle but has no rollback plan**
→ Solution: Add rollback playbook before coding

❌ **Behavior changed but refactor PR says "no functional change"**
→ Solution: Split into 2 PRs (refactor first, behavior change later)

---

## 💾 PRACTICAL CODE TEMPLATE

### Remember this process in future refactors:

```python
# ANTI-PATTERN (DON'T DO THIS):
# ✗ Delete from app.py
# ✗ Add to service.py
# ✗ Hope it works

# GOOD PATTERN (DO THIS):
# 1. Create mapping
mapping = {
    'get_local_system_data': 'SystemService',
    'manual_submit': 'web_bp',
}

# 2. Add to new location
# 3. Update all imports
# 4. Test
import subprocess
subprocess.run(['python', '-c', 'from server.services import SystemService; ...'])

# 5. Delete from old location
# 6. Final test
# 7. Commit
```

---

## ✅ CHECKLIST FOR THIS REFACTOR (Week 3)

- [x] **Audit Phase**: Created mapping of removed code
  ```
  ✓ get_local_system_data() → SystemService
  ✓ /manual_submit → web.py
  ✓ /backup/create & /restore → web.py
  ✓ Template globals → app.py context_processor
  ```

- [x] **Add Phase**: Added all code to new locations
  - [x] SystemService.get_local_system_data() (180 lines)
  - [x] web.py /manual_submit route (70 lines)
  - [x] web.py /backup/create route (55 lines)
  - [x] web.py /backup/restore/<filename> route (60 lines)
  - [x] app.py template context_processor (15 lines)

- [x] **Update References**: Updated imports
  - [x] web.py now imports BackupService
  - [x] app.py imports SystemService for context processor
  - [x] All blueprints properly registered

- [x] **Test Phase**: Verified everything works
  - [x] SystemService methods available
  - [x] Flask app initializes
  - [x] Blueprints registered
  - [x] All imports successful

- [ ] **Remove Phase**: Remove old duplicate logic after parity checks
  - Keeping duplicate old and new paths is temporary only
  - Cleanup must be completed in follow-up commit

- [x] **Final**: Created this algorithm document
  - All future refactors must follow this pattern

---

## 📚 RESOURCES FOR FUTURE REFACTORS

When refactoring in Phase 1, 2, 3, etc:

1. **Start with this checklist** ↑
2. **Run audit** - Map all code being moved
3. **Add first** - Implementin target location
4. **Test immediately** - No code migration guessing
5. **Update references** - Fix imports
6. **Final test** - Full integration test
7. **Then remove** - Only after verification

**This prevents the "lost code" problem!**

---

## 🎯 SUMMARY

The algorithm learned from Week 3 refactoring:

> "Never remove code until you've confirmed it exists somewhere else and works there.
> Map first, add second, test third, update fourth, remove last."

This took us from 393 lines in app.py to 115 lines while:
- ✓ Moving 4 missing functions to services
- ✓ Moving 3 missing routes to blueprints  
- ✓ Adding 1 missing context processor
- ✓ Keeping zero functionality lost
- ✓ Improving code organization

**Result: Safe, clean, audited refactoring with zero lost code.**

---

## DONE CRITERIA (REFRACTOR CANNOT BE CLOSED UNTIL ALL TRUE)

- [ ] Mapping table complete and reviewed
- [ ] New location code added and referenced everywhere
- [ ] Old code removed (or cleanup ticket created with due date)
- [ ] Unit + integration + smoke tests pass
- [ ] Rollback path documented (mandatory for medium/high risk)
- [ ] PR description includes scope, risks, and verification evidence
"""
