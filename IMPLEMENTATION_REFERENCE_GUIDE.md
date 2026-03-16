# 🗺️ IMPLEMENTATION REFERENCE GUIDE

**Quick lookup: What to read and what to update during implementation**

---

## 📌 QUICK ANSWER

### 🔵 FILES TO READ/REFER DURING IMPLEMENTATION
```
1. WEEK_BY_WEEK_CHECKLIST.md     ← Daily tasks (MOST USED)
2. PROGRESS_TRACKER.md            ← Current phase & week status
3. UPDATED_ARCHITECTURE.md        ← System design & API structure
4. README.md                       ← Feature details you're building
5. FEATURE_COVERAGE_MAP.md         ← Verify feature you're working on
6. MASTER_ROADMAP.md              ← Detailed week breakdown
```

### 🟢 FILES TO UPDATE AFTER EACH TASK
```
1. PROGRESS_TRACKER.md            ← ✅ CHECK OFF COMPLETED FUNCTION (EVERY TASK)
2. FEATURE_COVERAGE_MAP.md        ← Update feature status (weekly)
3. Git commit message             ← Reference function completed (EVERY COMMIT)
4. Code files (app.py, etc)       ← Actual implementation (EVERY TASK)
```

---

## 📚 DETAILED FILE GUIDE

### 🟢 PRIMARY REFERENCE: WEEK_BY_WEEK_CHECKLIST.md

**When to use**: EVERY MORNING (start of day)  
**What it contains**: 
- Today's specific tasks (step-by-step)
- Dependencies (what needs to be done first)
- Code examples
- Testing requirements
- Deliverables checklist
- Git commit format

**Example usage**:
```
Good morning! What do I do today?
→ Open WEEK_BY_WEEK_CHECKLIST.md
→ Find "Week 1 - Day 3"
→ Follow the checklist
→ Mark items off when done
```

**Update frequency**: Every Sunday (plan next week)  
**Who updates it**: Team lead + developers

---

### 🟡 TRACKING: PROGRESS_TRACKER.md

**When to use**: AFTER EVERY TASK COMPLETION  
**What it contains**:
- Phase 0 detailed feature/function list
- All 157 features organized by phase
- Status checkboxes for each function
- Daily standup template
- Overall progress dashboard

**Example usage - DAILY UPDATE**:
```
Completed today:
1. Created .env file
2. Updated app.py to load from .env

Action:
→ Open PROGRESS_TRACKER.md
→ Find "Phase 0" → "Feature 1: Security Hardening"
→ Check the boxes:
   - [x] Move secrets → .env
   - [x] Create .env.example
→ Update progress counter: "2/45 functions (4%)"
→ Git commit with message referencing these functions
```

**Update frequency**: 2-3 times daily (after major tasks)  
**Who updates it**: Developer working on the task

---

### 🔵 IMPLEMENTATION FLOW

#### 📖 BEFORE YOU START (Day 1 of week)
```
1. Read: DOCUMENTATION_INDEX.md (this file location)
2. Read: WEEK_BY_WEEK_CHECKLIST.md (Week 1, Day 1-5)
3. Read: PROGRESS_TRACKER.md (Phase 0 overview)
4. Read: UPDATED_ARCHITECTURE.md (System design relevant to task)
5. Read: README.md (Feature details you're implementing)
```

#### ⚙️ DURING DEVELOPMENT (Day 1-5)
```
For each task:
1. Read: WEEK_BY_WEEK_CHECKLIST.md (for THIS task)
2. Refer: UPDATED_ARCHITECTURE.md (API structure, data models)
3. Code: Implement in Python files (app.py, agent.py, etc)
4. Update: PROGRESS_TRACKER.md (check off completed function)
5. Test: Follow testing steps in WEEK_BY_WEEK_CHECKLIST.md
6. Commit: Git commit with function name & PROGRESS_TRACKER reference
7. Verify: FEATURE_COVERAGE_MAP.md (mark feature progress)
```

#### ✅ WEEKLY REVIEW (Friday/Sunday)
```
1. Review: PROGRESS_TRACKER.md (weekly totals)
2. Update: FEATURE_COVERAGE_MAP.md (overall feature status)
3. Read: Next week's WEEK_BY_WEEK_CHECKLIST.md section
4. Plan: Dependencies for next week
5. Summary: Update weekly progress in PROGRESS_TRACKER.md
```

---

## 📋 FILE-BY-FILE REFERENCE

### 1. WEEK_BY_WEEK_CHECKLIST.md
```
PURPOSE:     Daily task execution
READ WHEN:   Every morning (especially Day 1-5)
CONTAINS:    
  - Step-by-step tasks for each week
  - Code examples and implementation patterns
  - Testing procedures
  - Deliverables
  - Git commit messages
UPDATE WHEN: Every Sunday (for next week's tasks)
FREQUENCY:   Most critical file for developer

STRUCTURE:
Week 1 (Days 1-5)
├─ Day 1: Task A, B, C
├─ Day 2: Task D, E
├─ Day 3: Task F, G, H
├─ Day 4: Testing + verification
└─ Day 5: Git commit + deliverables
Week 2...
Week 3...
Week 4...
```

---

### 2. PROGRESS_TRACKER.md
```
PURPOSE:     Track implementation progress (function-level)
READ WHEN:   Start of week + after major tasks
CONTAINS:
  - All 157 features organized by phase
  - 126 functions with status checkboxes
  - Daily standup template
  - Phase completion dashboard
UPDATE WHEN: After EVERY task completion
FREQUENCY:   2-3 times per day

STRUCTURE:
Phase 0: Features 1-2
├─ Feature 1: Security Hardening (45 functions)
│  ├─ Implementation: [ ] Task 1, [ ] Task 2, ...
│  ├─ Deliverables: [ ] File 1, [ ] File 2, ...
│  ├─ Functions: [ ] func1, [ ] func2, ...
│  └─ Tests: [ ] Test 1, [ ] Test 2, ...
│
├─ Feature 2: Architecture (25 functions)
│  ├─ Implementation: [ ] Task 1, [ ] Task 2, ...
│  └─ ...

Phase 1: Features 1-14 (brief status)
Phase 2: Features 1-127 (week breakdown)
Phase 3: Features 1-11 (Docker + K8s)
Phase 4: Features 1-3 (optimization)

Dashboard: Overall progress 0/126 → 157/157
```

---

### 3. UPDATED_ARCHITECTURE.md
```
PURPOSE:     System design reference
READ WHEN:   When implementing features that touch architecture
CONTAINS:
  - System architecture diagrams
  - API endpoint structure (30+ routes)
  - Database schema
  - Data flow examples
  - Windows Agent Architecture (6 subsystems)
  - Integration points
UPDATE WHEN: When architecture changes (rarely)
FREQUENCY:   Reference document (read-only mostly)

USE FOR:
Before coding:
  ├─ "What should the API endpoint look like?"
  ├─ "What's the database schema for this?"
  └─ "How does this feature integrate?"
```

---

### 4. README.md (92 FEATURES VISION)
```
PURPOSE:     Feature specification & architecture
READ WHEN:   When you need detailed feature description
CONTAINS:
  - All 92 original features
  - All 65 Windows features
  - System architecture vision
  - Security model
  - Feature categories (Monitoring, Logs, Alerts, etc)
UPDATE WHEN: Rarely (reference document)
FREQUENCY:   Read when implementing new area

USE FOR:
Questions like:
  ├─ "What should this alert feature do?"
  ├─ "What are the monitoring capabilities?"
  └─ "How does Windows troubleshooting work?"
```

---

### 5. FEATURE_COVERAGE_MAP.md
```
PURPOSE:     Map features to implementation status
READ WHEN:   When starting a new feature
CONTAINS:
  - All 157 features listed
  - Current status (❌ not started, 🟡 partial, ✅ done, 🔶 planned)
  - Week allocation
  - Phase assignment
UPDATE WHEN: After feature is 25%, 50%, 75%, 100% complete
FREQUENCY:   Weekly at minimum

STRUCTURE:
Feature 1 (Week 5): User Auth System
  ├─ Status: 🟡 PARTIAL
  ├─ Progress: 3/5 components done
  ├─ Phase: 1
  └─ Notes: Waiting for database migration

Feature 2 (Week 9): Alert Rules
  ├─ Status: ❌ NOT IMPLEMENTED
  ├─ Progress: 0/8 components
  ├─ Phase: 2
  └─ Notes: TBD
```

---

### 6. MASTER_ROADMAP.md
```
PURPOSE:     Complete 25-week plan reference
READ WHEN:   Weekly planning sessions
CONTAINS:
  - Executive summary
  - All 157 features by phase
  - Detailed week-by-week timeline
  - Architecture requirements
  - Testing strategy
UPDATE WHEN: Weekly (consolidate progress)
FREQUENCY:   Phase/week transition point

USE FOR:
"When is feature X supposed to start?"
→ Check MASTER_ROADMAP.md
Result: Week 9-10

"What's the full timeline for Phase 2?"
→ Check MASTER_ROADMAP.md
Result: Weeks 9-16, 127 features
```

---

## 🔄 THE UPDATE WORKFLOW

### SCENARIO: Completing "Move secrets to .env" (Week 1, Day 1-2)

#### Step 1: Check the task
```
File: WEEK_BY_WEEK_CHECKLIST.md
Content: "Week 1 > Day 1-2 > Move secrets from code to .env"
Read: Implementation details and testing requirements
```

#### Step 2: Implement in code
```
Files to modify/create:
- Create: .env (with SECRET_KEY, AGENT_API_KEY)
- Create: .env.example (template)
- Modify: app.py (load from .env)
- Update: .gitignore (add .env)
- Update: README.md (setup instructions)
```

#### Step 3: Update PROGRESS_TRACKER.md
```
PROGRESS_TRACKER.md > Phase 0 > Feature 1: Security Hardening

Before:
  Implementation:
    - [ ] Move secrets → .env (Day 1-2)
    - [ ] Create .env example (Day 1)

After:
  Implementation:
    - [x] Move secrets → .env (Day 1-2) ✅ COMPLETED
    - [x] Create .env example (Day 1) ✅ COMPLETED
    
Update counter: 2/20 tasks (10%)
```

#### Step 4: Git commit
```
Command: git commit -m "SECURITY: Move secrets to .env

- Create .env with SECRET_KEY, AGENT_API_KEY
- Create .env.example template
- Load config from environment in app.py
- Update .gitignore to exclude .env

Function completed: require_api_key base setup
Reference: PROGRESS_TRACKER.md Phase 0 Feature 1: Security Hardening
Progress: 2/45 Phase 0 functions (4%)"
```

#### Step 5: Optional - Update other trackers
```
FEATURE_COVERAGE_MAP.md >  "Security Hardening Feature"
Before: ❌ NOT STARTED
After:  🟡 PARTIAL (moved from 0/20 to 2/20)

Update: Status: 🟡 PARTIAL | Progress: 2/20 tasks
```

---

## 📊 QUICK REFERENCE TABLE

| Task | Primary Read | Primary Update | Frequency |
|------|--------------|---------------|----|
| **Morning standup** | WEEK_BY_WEEK_CHECKLIST.md | PROGRESS_TRACKER.md | Daily |
| **During coding** | UPDATED_ARCHITECTURE.md | Code files | Continuous |
| **Task completion** | README.md (feature details) | PROGRESS_TRACKER.md | 2-3x daily |
| **Testing** | WEEK_BY_WEEK_CHECKLIST.md | Code files | Per task |
| **Git commit** | (write commit message) | PROGRESS_TRACKER.md | Every commit |
| **Weekly review** | PROGRESS_TRACKER.md | FEATURE_COVERAGE_MAP.md | Weekly |
| **Week planning** | MASTER_ROADMAP.md | WEEK_BY_WEEK_CHECKLIST.md | Weekly |
| **Feature lookup** | README.md | FEATURE_COVERAGE_MAP.md | As needed |
| **Architecture Q** | UPDATED_ARCHITECTURE.md | (read-only) | As needed |
| **Historical context** | ARCHIVE/* | (reference) | As needed |

---

## 🎯 DECISION FLOW

**"What file do I read/update?"**

```
┌─ What's my question?
│
├─ "What's today's task?"
│  └─ WEEK_BY_WEEK_CHECKLIST.md 📖
│
├─ "How should I implement feature X?"
│  └─ README.md (details) + UPDATED_ARCHITECTURE.md (design) 📖
│
├─ "What functions need to be done?"
│  └─ PROGRESS_TRACKER.md 📖
│
├─ "Is feature X implemented?"
│  └─ FEATURE_COVERAGE_MAP.md 📖
│
├─ "What's the overall timeline?"
│  └─ MASTER_ROADMAP.md 📖
│
└─ "I just finished a task, what do I do?"
   ├─ Update code ✏️
   ├─ Update PROGRESS_TRACKER.md ✅
   ├─ Git commit (referencing PROGRESS_TRACKER) 📝
   └─ Optionally update FEATURE_COVERAGE_MAP.md 📊
```

---

## ⚡ GOLDEN RULES

### 1️⃣ **PROGRESS_TRACKER.md is the source of truth for status**
- Every task completion → Update PROGRESS_TRACKER.md
- Every git commit → Reference PROGRESS_TRACKER.md
- Every week → Review progress in PROGRESS_TRACKER.md

### 2️⃣ **WEEK_BY_WEEK_CHECKLIST.md is the execution guide**
- Start day with this file
- Follow its step-by-step instructions
- Update it for next week every Sunday

### 3️⃣ **Git commits should reference PROGRESS_TRACKER.md**
- Commit message format: Mention which function(s) completed
- Example: "Reference: PROGRESS_TRACKER.md Phase 0 Feature 1"

### 4️⃣ **Update frequency matters**
- PROGRESS_TRACKER.md: 2-3 times daily
- FEATURE_COVERAGE_MAP.md: Daily/weekly
- WEEK_BY_WEEK_CHECKLIST.md: Weekly
- UPDATED_ARCHITECTURE.md: Rarely (design document)
- README.md: Rarely (vision document)

### 5️⃣ **One source per question**
- Don't search multiple documents
- Use table above to find right file
- Keeps documentation consistent

---

## 📱 MOBILE-FRIENDLY QUICK LOOKUP

**No time? Just remember:**

```
👀 READ:    WEEK_BY_WEEK_CHECKLIST.md (daily tasks)
📝 WRITE:   PROGRESS_TRACKER.md (after tasks)
✅ COMMIT:  Reference functions in git commit
📊 REPORT:  Update FEATURE_COVERAGE_MAP.md (weekly)
```

---

## 🚀 START NOW

**Phase 0 starts? Then do this:**

```
1. Read WEEK_BY_WEEK_CHECKLIST.md (Week 1)
2. Read UPDATED_ARCHITECTURE.md (System design)
3. Open PROGRESS_TRACKER.md (keep in second window)
4. Implement Task 1: "Move secrets to .env"
5. Update PROGRESS_TRACKER.md (mark function complete)
6. Git commit (reference PROGRESS_TRACKER.md)
7. Git commit verification: "Progress: 1/45 Phase 0 functions"
8. Repeat for Task 2, 3, ...
```

**That's it! You're implementing! 🎉**

---

## 📞 HELP

### "I don't know what to build next"
→ WEEK_BY_WEEK_CHECKLIST.md

### "I need details about this feature"  
→ README.md + UPDATED_ARCHITECTURE.md

### "What's my current progress?"
→ PROGRESS_TRACKER.md

### "Is this feature implemented?"
→ FEATURE_COVERAGE_MAP.md

### "When should this be done?"
→ MASTER_ROADMAP.md

### "How does the full system work?"
→ UPDATED_ARCHITECTURE.md

### "Why was X decision made?"
→ ARCHIVE/ (historical documents)
