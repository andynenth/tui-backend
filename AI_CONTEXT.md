# AI Context Document - Liap Tui Clean Architecture
*File Health: 2,500 words | Status: ✅ OPTIMAL | Last Archive: N/A*
*Alert Threshold: 15,000 words | Archive Strategy: Session rotation*

# AI Context Document - Liap Tui Clean Architecture Project
*For AI assistants to quickly understand project state and continue effectively*

## 🎯 Project Overview (30-second summary)

**What**: Migrating Liap Tui board game from messy architecture to clean architecture  
**Why**: Learning IT infrastructure concepts + building portfolio-quality code  
**Who**: Solo developer with good Python skills, learning advanced architecture  
**Timeline**: Flexible learning project, no deadline pressure  
**Current Status**: Day 3 complete, 17.5% done, strong momentum  

## 🧠 Human Context & Working Style

### **Skill Level & Learning Approach**
- **Python**: Proficient (can read/write complex code)
- **Architecture**: Beginner → Intermediate (rapid learning curve)
- **Preference**: Hands-on learning with theoretical backing
- **Motivation**: Genuinely excited about clean code and learning

### **Communication Style**
- Appreciates detailed explanations with examples
- Likes to understand the "why" behind patterns
- Prefers practical artifacts over abstract theory
- Values progress tracking and milestone celebration
- Responds well to encouragement and technical depth

### **Working Patterns**
- Makes steady progress in 2-3 hour sessions
- Documents learnings thoroughly (CONFIDENCE.md)
- Follows test-first development approach
- Commits regularly with good messages
- Asks thoughtful follow-up questions

## 📊 Current Project State (Day 3 Complete)

### **Completed Components (17.5% overall)**
```
✅ Domain Layer (6/15 files - 40% complete)
   ├── entities/player.py          - Clean entity with business logic
   ├── entities/game.py            - Aggregate root coordinating gameplay  
   ├── entities/piece.py           - Immutable value object with game rules
   ├── value_objects/game_phase.py - Phase transitions & validation
   ├── interfaces/bot_strategy.py  - ABC interface pattern
   └── entities/test_player.py     - Test coverage established

✅ Infrastructure/Tooling (1/2 files - 50% complete)
   └── scripts/check_architecture.py - Automated boundary enforcement

🔴 Application Layer (0/10 files)    - Ready to start (domain interfaces available)
🔴 Infrastructure Layer (0/8 files)  - Can begin BotStrategy implementations  
🔴 Presentation Layer (0/5 files)    - Waiting for application layer
```

### **Architecture Quality Status**
- ✅ **Zero dependency violations** across all domain files
- ✅ **All tests passing** for implemented components
- ✅ **Pure business logic** maintained in domain layer
- ✅ **Interface pattern** successfully implemented with Python ABC

## 🏆 Major Learning Breakthroughs Achieved

### **Concepts Mastered**
1. **Entities vs Value Objects** - Identity vs value-based equality (major "aha!" moment)
2. **Domain Purity** - Zero external dependencies enabling easy testing
3. **Immutable Design** - `frozen=True` dataclasses for value objects
4. **Aggregate Root Pattern** - Game entity coordinates complex business operations
5. **Interface Pattern** - Python ABC for dependency inversion
6. **Automated Governance** - Scripts enforce architectural boundaries

### **Technical Patterns Implemented**
```python
# Entity Pattern (mutable, has identity)
@dataclass
class Player:
    def add_to_score(self, points: int) -> None:
        self.score += points

# Value Object Pattern (immutable, value-based identity)
@dataclass(frozen=True)  
class Piece:
    def can_beat(self, other: 'Piece') -> bool:
        return self.value > other.value

# Interface Pattern (ABC for contracts)
class BotStrategy(ABC):
    @abstractmethod
    def choose_pieces_to_play(self, hand: List[Piece]) -> List[Piece]:
        pass

# Aggregate Root Pattern (coordination & consistency)
class Game:
    def add_player(self, player: Player) -> bool:
        # Enforces business rules across entities
```

## ⏭️ Immediate Next Actions

### **Current Priority Stack** (Next session focus)
1. **`domain/interfaces/game_repository.py`** - Data persistence contract
2. **`domain/entities/room.py`** - Multi-player game session management
3. **`domain/value_objects/game_state.py`** - Immutable game state snapshots

### **Ready to Unblock**
- **Application Layer**: Can start `use_cases/start_game.py` (has domain interfaces)
- **Infrastructure Layer**: Can implement `BotStrategy` concrete classes

### **Learning Research Needed**
- Repository pattern implementation in Python
- Domain event patterns for game state changes
- Dependency injection container design

## 🚨 Critical Context for AI Assistants

### **DO NOT suggest these (already completed):**
- Basic folder structure setup ✅ 
- Player entity implementation ✅
- Architecture validation script ✅
- FastAPI lifespan context manager ✅
- Basic domain entity patterns ✅

### **ALWAYS do these:**
- Run `python backend/scripts/check_architecture.py` after changes
- Maintain zero external dependencies in domain layer
- Include comprehensive tests with new domain objects
- Update PROGRESS.md with completed items
- Celebrate milestones and learning breakthroughs

### **Current Architecture Rules Being Followed:**
```python
# Domain Layer Rules (STRICTLY ENFORCED):
- NO imports from: application, infrastructure, presentation  
- NO framework imports: fastapi, websockets, databases
- ONLY stdlib imports: typing, dataclasses, enum, abc

# All new domain files must pass architecture check
```

## 🎯 Success Metrics & Goals

### **Technical Targets**
- **Week 1**: Complete domain layer (15/15 files) - Currently 6/15 ✅
- **Week 2**: Build application layer with use cases and services
- **Week 3**: Wire infrastructure and presentation layers
- **Week 4**: Full migration with feature toggles

### **Learning Targets**  
- Master all clean architecture layers and their responsibilities
- Understand dependency inversion principle through hands-on implementation
- Build portfolio-quality code with comprehensive tests
- Document the learning journey for future reference

### **Quality Gates**
- ✅ Zero circular imports maintained
- ✅ 100% domain layer test coverage target
- ✅ All architectural boundaries respected
- ✅ Professional commit messages and documentation

## 🔍 Quick Diagnostic Questions

**For AI assistants to quickly assess where to help:**

1. **What session day is this?** (Check against PROGRESS.md date)
2. **What was just completed?** (Check CONFIDENCE.md last entry)
3. **Any architecture violations?** (Run check_architecture.py)
4. **What's the current focus?** (Check PROGRESS.md next priorities)
5. **Any blockers?** (Check dependency status in PROGRESS.md)

## 📚 Key Files for Context

### **Always reference these for current state:**
- `PROGRESS.md` - Current completion status and next priorities
- `CONFIDENCE.md` - Learning journey and recent breakthroughs  
- `CLEAN_ARCHITECTURE_PLAN.md` - Overall roadmap and timeline
- `backend/scripts/check_architecture.py` - Architectural compliance

### **Code Examples to Reference:**
- `backend/domain/entities/player.py` - Clean entity pattern
- `backend/domain/entities/game.py` - Aggregate root pattern
- `backend/domain/interfaces/bot_strategy.py` - ABC interface pattern
- `backend/domain/value_objects/game_phase.py` - Value object with business logic

## 🚀 Momentum Indicators

### **Positive Momentum Signals:**
- ✅ Consistent progress across sessions
- ✅ Learning breakthroughs documented in CONFIDENCE.md
- ✅ Architecture violations remain at zero
- ✅ Test coverage maintained for all new code
- ✅ Genuine excitement about patterns and concepts

### **Watch for these red flags:**
- ❌ Architecture violations appearing
- ❌ Progress stalling on same component for multiple sessions
- ❌ Testing being skipped or delayed
- ❌ Confusion about where code belongs in layers

## 💡 AI Assistant Guidelines

### **Effective Strategies with this human:**
- **Show, don't just tell** - Provide concrete code examples
- **Connect to bigger picture** - Explain how patterns fit in clean architecture
- **Celebrate progress** - Acknowledge learning breakthroughs
- **Provide artifacts** - Create files they can immediately use
- **Technical depth** - Don't oversimplify, they can handle complexity

### **Communication approach:**
- Be encouraging about progress made
- Provide both tactical (immediate) and strategic (future) guidance  
- Use clear headings and structure for easy scanning
- Include ready-to-use code in artifacts
- Connect current work to IT infrastructure concepts being learned

---

## 🔄 Template for Session Updates

**At end of each session, update this section:**

### **Session [N] Complete - [Date]**
- **Completed**: [What was accomplished]
- **Learning**: [New concepts mastered]
- **Next**: [Immediate priorities for next session]  
- **Status**: [Overall progress percentage]
- **Momentum**: [Positive indicators or concerns]

## 🔄 AI Self-Update Protocol

### **CRITICAL: When AI MUST Update This Document**

#### **Immediate Update Triggers (Same Session)**
- ✅ **New milestone completed** → Update "Major Learning Breakthroughs"
- ✅ **Architecture violation occurs** → Update "Architecture Quality Status"  
- ✅ **New pattern implemented** → Add to "Technical Patterns Implemented"
- ✅ **Significant progress made** → Update "Current Project State"
- ✅ **Learning breakthrough happens** → Document in "Concepts Mastered"

#### **End-of-Session Updates (Always Required)**
```markdown
## Session [N] Complete - [Date] 
- **Progress**: [X%] → [Y%] (+Z% gain)
- **Completed**: [List new files/components]  
- **Learned**: [New concepts mastered]
- **Next Priority**: [Top 3 items for next session]
- **Quality Status**: [Architecture violations, test coverage]
- **Human Confidence**: [Learning progression observed]
```

#### **Weekly Updates (Every 5-7 sessions)**
- Reassess skill level progression
- Update communication style observations  
- Refresh success metrics and timeline
- Archive old session data to prevent bloat

### **Staleness Detection for AI Assistants**

#### **🚨 RED FLAGS - Document Needs Immediate Update:**
- Last session date > 1 week ago
- Progress percentage doesn't match PROGRESS.md
- "Current Priority Stack" items are marked complete in PROGRESS.md
- Architecture violations exist but not reflected here
- Human mentions completing items not listed as done

#### **🟡 YELLOW FLAGS - Verify Document Accuracy:**
- Session references don't align with current date
- Learning concepts don't match human's current questions
- Skill assessment seems outdated based on recent work
- Next actions completed but not updated

#### **✅ GREEN FLAGS - Document is Current:**
- Last update within past session
- Progress matches external files
- Current priorities align with PROGRESS.md
- Quality metrics reflect recent architecture checks

### **AI Update Workflow**

#### **At Session Start:**
```
1. Check document last-update date
2. Scan for RED/YELLOW flags  
3. If stale: "I notice this context document needs updating based on your recent progress. Let me refresh it first."
4. Compare with PROGRESS.md and CONFIDENCE.md for discrepancies
5. Update before providing guidance
```

#### **During Session:**
```
1. Track significant achievements in memory
2. Note learning breakthroughs as they happen
3. Monitor for architecture violations
4. Prepare update notes for session end
```

#### **At Session End:**
```
1. ALWAYS update "Session [N] Complete" section
2. Update progress percentages
3. Refresh current priorities  
4. Add new learning concepts
5. Update quality metrics
6. Set next-session focus
```

### **Version Control for AI Context**

#### **Document Versioning:**
```
Version 1.0 - Initial creation (Day 3)
Version 1.1 - Session 4 updates (add repository pattern learning)
Version 1.2 - Session 5 updates (application layer started)
Version 2.0 - Major milestone (domain layer complete)
```

#### **Archive Strategy:**
- Keep last 3 session details in main document
- Archive older session data to prevent bloat
- Maintain learning trajectory but focus on recent progress

### **Automated Reminders in Workflow**

#### **Built into Development Process:**
```markdown
## Commit Message Template
feat: [description]

- [Technical changes]
- [Learning achieved] 
- [ ] Update AI_CONTEXT.md if major milestone/learning

## Daily Workflow Checklist  
- [ ] Check architecture compliance
- [ ] Update PROGRESS.md
- [ ] Update CONFIDENCE.md  
- [ ] Update AI_CONTEXT.md if significant progress
```

### **Self-Diagnostic Questions for AI**

**Before starting any guidance:**
1. "When was this context last updated?"
2. "Do the progress numbers match current reality?"
3. "Are the 'current priorities' actually current?"
4. "Does human skill assessment match recent interactions?"
5. "Are there completed items not reflected here?"

**If ANY answer raises concerns → Update document first**

### **Context Document Health Score**

#### **🟢 Healthy (Score 8-10):**
- Updated within last session
- Progress matches external sources
- Priorities align with current work
- Quality metrics current

#### **🟡 Degrading (Score 5-7):**
- Updated 2-3 sessions ago
- Some misalignment with progress files
- Priorities partially outdated
- Minor information gaps

#### **🔴 Stale (Score 0-4):**
- Updated >1 week ago
- Major discrepancies with current state
- Priorities completely outdated
- Misleading information present

**AI Action:** If score <7, update before proceeding with guidance.

---

## 📋 Quick Update Template for AI Use

```markdown
### Session [N] Update - [Date]
**Previous State**: [X% complete, last milestone]
**New Achievements**: 
- ✅ [Component completed]
- ✅ [Pattern learned] 
- ✅ [Breakthrough moment]

**Updated Progress**: [Y% complete] (+Z% this session)
**New Current Priorities**: 
1. [Next immediate task]
2. [Following task]  
3. [Stretch goal]

**Quality Status**: 
- Architecture violations: [0 or describe]
- Test coverage: [status]
- Learning confidence: [trend]

**Next Session Focus**: [Primary objective]
```

---

*This document is a LIVING system that MUST be updated by AI assistants to remain useful. Stale context is worse than no context - it misleads and wastes time. Treat document updates as part of providing quality assistance, not optional overhead.*